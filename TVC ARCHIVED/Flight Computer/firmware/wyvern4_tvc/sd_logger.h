// GTR70E WYVERN -- SPI microSD flight logger, drained from the inter-core FIFO on core 1.
// ==========================================================================================
// Core 0 pushes one LogFrame per 500 Hz control tick into a lock-free shared-RAM SPSC ring
// (see the transport section below -- this was the hardware inter-core FIFO, which was 8 words
// deep against a 37-word frame and therefore dropped 100% of samples; fixed 2026-08).
// Core 1 drains the ring and flushes to the SD card in bursts. This means an SD write that takes a few ms (common with SPI microSD) never blocks core 0
// -- it just makes the FIFO momentarily fuller, which core 1 catches up on, by design
// (01_FlightComputer_Spec.md section 1: "SD writes and Wi-Fi can stall here for milliseconds
// without ever jittering the control loop on core 0").
//
// SCHEMA v2 (expanded post-flight-readiness pass): every quantity the control loop already
// computes each tick is now logged -- not just the final actuator command. This is the difference
// between a post-flight CSV that can only say "here's what the gimbal did" and one that can say
// "here's WHY it did that" (setpoint, error, individual P/I/D contributions, IMU vote health, and
// loop-timing jitter), which is what root-causing an anomaly from data (rather than a repeat test
// flight) requires. Nothing here changes the control loop's own math -- these are read-only
// telemetry taps on state the loop already holds.
//
// File: WYV4_FLIGHT.csv -- header + one CSV row per control tick, columns documented below.
#pragma once
#include <SPI.h>
#include <SD.h>
#include "pico/multicore.h"

// One flight log record. Kept POD/flat so it can be copied into the shared ring by value.
// Size MUST stay a whole number of 32-bit words (static_assert below enforces this at compile time).
struct LogFrame {
  uint32_t t_ms;              // millis() at this tick
  float    t_flight_s;        // seconds since launch detect; NAN before launch (no t=0 yet)
  uint32_t loop_dt_us;        // actual elapsed micros() since the previous tick (500 Hz jitter diag)

  uint8_t state;              // FlightState enum value, see wyvern4_tvc.ino
  uint8_t imu_fault;          // TriImu::vote_fault()
  uint8_t rbf_pulled;         // 1 = remove-before-flight pin pulled (armed-eligible), 0 = inserted
  uint8_t batt_flags;         // bit0 = low_battery, bit1 = critical (BatteryMonitor thresholds)

  float qb_w, qb_x, qb_y, qb_z;      // voted body quaternion (onboard BNO085, 2-of-2 vote)
  float qg_w, qg_x, qg_y, qg_z;      // external BNO085 quaternion (STEMMA-QT, same shared bus as body)
  float vote_disagree_rad;           // TriImu::vote_disagreement_rad(); -1 = only one IMU reporting

  float body_pitch_rad, body_yaw_rad;    // small-angle Euler readout of qb (control loop's own use)
  float defl_pitch_rad, defl_yaw_rad;    // q_body^-1 (x) q_gimbal -- actual nozzle deflection

  float setp_pitch_rad;               // commanded pitch setpoint this tick (0 outside BOOST/maneuver)
  float err_pitch_rad, err_yaw_rad;   // PID input error each axis (setpoint - measurement)

  float pid_p_pitch, pid_i_pitch, pid_d_pitch;   // pitch PID term breakdown, kp*err / ki*integral / kd*deriv
  float pid_p_yaw,   pid_i_yaw,   pid_d_yaw;     // yaw PID term breakdown

  float cmd_pitch_rad, cmd_yaw_rad;   // PID output commanded to servos (post slew-limit/clamp)

  float baro_alt_m, baro_temp_c;
  float accel_mag_g;
  float batt_v;                       // 2S LiPo pack voltage (BatteryMonitor, cross-core snapshot -- see
                                       // g_batt_v in wyvern4_tvc.ino; FIXED from schema v1, which left
                                       // this NAN because core 0 never had a battery reading to log)
  uint32_t dropped_frames_cum;        // cumulative g_dropped_log_frames at this tick (FIFO-full drops)
};
static_assert(sizeof(LogFrame) % 4 == 0, "LogFrame must be a whole number of 32-bit words for the FIFO");

constexpr size_t LOGFRAME_WORDS = sizeof(LogFrame) / 4;

// =================================================================================================
// INTER-CORE LOG TRANSPORT — shared-RAM SPSC ring buffer
// =================================================================================================
// FIXED 2026-08. THIS WAS THE SINGLE MOST SERIOUS DEFECT IN THE FIRMWARE: as written, the flight
// computer logged NOTHING.
//
// The previous implementation pushed each LogFrame through the RP2350's *hardware* inter-core FIFO
// (`rp2040.fifo`). Two independent, individually fatal problems:
//
//   1. THE HARDWARE FIFO IS 8 WORDS DEEP. A LogFrame is 37 words (148 bytes). A whole frame can
//      never fit, under any circumstances, no matter how fast core 1 drains.
//
//   2. `rp2040.fifo.available()` REPORTS WORDS WAITING TO BE *READ* on the calling core's inbound
//      FIFO -- it is not free space on the outbound side. Core 0 never receives anything from
//      core 1, so `available()` returned 0 forever, `0 < 37` was always true, and log_push()
//      therefore returned false on EVERY tick. The flight CSV would have contained a header row
//      and nothing else, while `dropped_frames_cum` climbed at 500 Hz.
//
//   (And had the guard ever passed, `rp2040.fifo.push()` BLOCKS until space frees -- which would
//   have stalled the 500 Hz control loop on core 1's SD latency, destroying the exact determinism
//   the dual-core split exists to protect. There was no correct outcome available.)
//
// Both cores on the RP2350 share SRAM, so the right transport is a lock-free single-producer /
// single-consumer ring in ordinary memory. Core 0 is the ONLY writer of `s_head`; core 1 is the
// ONLY writer of `s_tail`. Each side reads the other's index but never writes it, so no mutex is
// required and neither core can ever block on the other. Memory barriers order the payload write
// against the index publish, which matters on a dual-issue M33.
//
// Capacity: 256 frames = ~38 kB of the RP2350's 520 kB SRAM, and 0.51 s of continuous 500 Hz
// logging. Core 1 only needs to keep up on average; this absorbs any realistic SD write stall
// (typ. 2-8 ms, worst-case block-erase ~100 ms) without dropping a single sample.
static constexpr size_t LOG_RING_FRAMES = 256;
static LogFrame  s_log_ring[LOG_RING_FRAMES];
static volatile uint32_t s_head = 0;   // writer: core 0 only
static volatile uint32_t s_tail = 0;   // writer: core 1 only

// ---- core 0 side: push one frame. Never blocks. Drops (returns false) only if core 1 has fallen
// more than a full ring behind -- a dropped log sample is acceptable, a jittered control loop is not.
inline bool log_push(const LogFrame& f) {
  uint32_t head = s_head;
  uint32_t next = (head + 1) % LOG_RING_FRAMES;
  if (next == s_tail) return false;          // ring full: core 1 is >256 frames behind
  s_log_ring[head] = f;                       // write payload...
  __dmb();                                    // ...and make it visible BEFORE publishing the index
  s_head = next;
  return true;
}

// ---- core 1 side: drain whatever whole frames are available right now.
inline size_t log_drain(LogFrame* out, size_t max_frames) {
  size_t n = 0;
  uint32_t tail = s_tail;
  while (n < max_frames && tail != s_head) {
    out[n++] = s_log_ring[tail];
    tail = (tail + 1) % LOG_RING_FRAMES;
  }
  __dmb();                                    // consume payload before releasing the slots
  s_tail = tail;
  return n;
}

// Ring occupancy, for the self-test and the heartbeat. Core 1 falling persistently behind is a
// finding (slow card / too-small FLUSH_EVERY), not a benign condition.
inline uint32_t log_pending() {
  uint32_t h = s_head, t = s_tail;
  return (h >= t) ? (h - t) : (LOG_RING_FRAMES - t + h);
}

class SdLogger {
public:
  // GP2-GP5 are NOT SD pins on this board -- they're the four servo/JST connector signal lines
  // (U8-U11, see wyvern4_tvc.ino's pin map). The microSD card (CARD1, TF-01A) is wired to a
  // separate group of GPIOs entirely.
  //
  // All four pins below are CONFIRMED (not best-effort): traced every CARD1 pin against the
  // netlist and matched against CARD1's schematic-labeled pinout (DAT2(RSV), DAT3(CS), CMD(DI),
  // VDD, CLK, VSS, DAT0(D0), DAT1(RSV) -- standard TF-01A dual SD/SPI-mode labeling). Pin1 (DAT2)
  // and pin8 (DAT1) are correctly unconnected -- both are reserved/unused in SPI mode, not an
  // oversight.
  static constexpr uint8_t PIN_MISO = 8;    // CARD1 pin7, DAT0(D0)
  static constexpr uint8_t PIN_CS   = 9;    // CARD1 pin2, DAT3(CS)
  static constexpr uint8_t PIN_SCK  = 10;   // CARD1 pin5, CLK
  static constexpr uint8_t PIN_MOSI = 11;   // CARD1 pin3, CMD(DI)
  // FLAGGED, real finding: CARD1 pin4 -- the position a standard TF-01A pinout would call VDD --
  // traces to the board's GND net in the netlist, not to 3V3. Pins 6 and 9 (both legitimately GND
  // per the standard pinout) also trace to GND, so this isn't a mislabeling of the whole connector,
  // just pin4 specifically reading as GND where card power would be expected. If this is accurate,
  // the microSD socket has no power pin wired and SD.begin() will simply never succeed on this board
  // rev. Bench-check with a multimeter (continuity from CARD1 pin4 to the 3V3 rail vs. to GND)
  // before spending time debugging this as a firmware problem -- it may not be one.
  static constexpr const char* FILENAME = "WYV4_FLIGHT.csv";
  static constexpr size_t BURST_FRAMES = 32;     // frames pulled off the FIFO per service() call

  bool begin() {
    SPI.setSCK(PIN_SCK); SPI.setTX(PIN_MOSI); SPI.setRX(PIN_MISO);
    if (!SD.begin(PIN_CS)) { ok_ = false; return false; }
    file_ = SD.open(FILENAME, FILE_WRITE);
    if (!file_) { ok_ = false; return false; }
    file_.println(
      "t_ms,t_flight_s,loop_dt_us,state,imu_fault,rbf_pulled,batt_low,batt_critical,"
      "qb_w,qb_x,qb_y,qb_z,qg_w,qg_x,qg_y,qg_z,vote_disagree_deg,"
      "body_pitch_deg,body_yaw_deg,defl_pitch_deg,defl_yaw_deg,"
      "setp_pitch_deg,err_pitch_deg,err_yaw_deg,"
      "pid_p_pitch_deg,pid_i_pitch_deg,pid_d_pitch_deg,pid_p_yaw_deg,pid_i_yaw_deg,pid_d_yaw_deg,"
      "cmd_pitch_deg,cmd_yaw_deg,baro_alt_m,baro_temp_c,accel_g,batt_v,dropped_frames_cum");
    file_.flush();
    ok_ = true;
    return true;
  }

  // Call from loop1() every iteration. Drains up to BURST_FRAMES from the FIFO and appends them.
  // Flushes periodically (not every row -- flushing every row would make every write a multi-ms
  // SD stall; flushing every ~FLUSH_EVERY rows trades a small worst-case data-loss window on power
  // loss for dramatically less SPI bus time per row).
  void service() {
    if (!ok_) return;
    LogFrame buf[BURST_FRAMES];
    size_t n = log_drain(buf, BURST_FRAMES);
    for (size_t i = 0; i < n; i++) {
      const LogFrame& f = buf[i];
      bool batt_low = f.batt_flags & 0x01;
      bool batt_crit = f.batt_flags & 0x02;
      // vote_disagree_rad is -1 as a "only one IMU reporting" sentinel; keep that sentinel in
      // degrees too (-57.3) rather than silently degrees()-converting it into a bogus small angle.
      float vote_disagree_deg = (f.vote_disagree_rad < 0.0f) ? f.vote_disagree_rad
                                                              : degrees(f.vote_disagree_rad);
      file_.printf(
        "%lu,%.3f,%lu,%u,%u,%u,%u,%u,"
        "%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.3f,"
        "%.3f,%.3f,%.3f,%.3f,"
        "%.3f,%.3f,%.3f,"
        "%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,"
        "%.3f,%.3f,%.2f,%.2f,%.3f,%.3f,%lu\n",
        (unsigned long)f.t_ms, f.t_flight_s, (unsigned long)f.loop_dt_us,
        f.state, f.imu_fault, f.rbf_pulled, (unsigned)batt_low, (unsigned)batt_crit,
        f.qb_w, f.qb_x, f.qb_y, f.qb_z, f.qg_w, f.qg_x, f.qg_y, f.qg_z, vote_disagree_deg,
        degrees(f.body_pitch_rad), degrees(f.body_yaw_rad),
        degrees(f.defl_pitch_rad), degrees(f.defl_yaw_rad),
        degrees(f.setp_pitch_rad), degrees(f.err_pitch_rad), degrees(f.err_yaw_rad),
        degrees(f.pid_p_pitch), degrees(f.pid_i_pitch), degrees(f.pid_d_pitch),
        degrees(f.pid_p_yaw), degrees(f.pid_i_yaw), degrees(f.pid_d_yaw),
        degrees(f.cmd_pitch_rad), degrees(f.cmd_yaw_rad),
        f.baro_alt_m, f.baro_temp_c, f.accel_mag_g, f.batt_v,
        (unsigned long)f.dropped_frames_cum);
      rows_since_flush_++;
    }
    if (rows_since_flush_ >= FLUSH_EVERY) { file_.flush(); rows_since_flush_ = 0; }
    if (n > peak_drain_) peak_drain_ = n;
    uint32_t pend = log_pending();
    if (pend > peak_pending_) peak_pending_ = pend;
  }

  // Diagnostics for the bench self-test and the post-flight report: how full the ring ever got and
  // the largest burst core 1 had to absorb. peak_pending_ approaching LOG_RING_FRAMES means the
  // card is too slow for the configured FLUSH_EVERY and samples are about to be lost.
  uint32_t peak_pending() const { return peak_pending_; }
  size_t peak_drain() const { return peak_drain_; }

  // Force a flush + close, e.g. on LANDED state entry so the card is safe to remove.
  void finalize() { if (ok_) { file_.flush(); file_.close(); ok_ = false; } }
  bool ok() const { return ok_; }

private:
  static constexpr int FLUSH_EVERY = 50;   // ~0.1 s of data at 500 Hz before a forced flush
  File file_;
  bool ok_ = false;
  int rows_since_flush_ = 0;
  uint32_t peak_pending_ = 0;
  size_t peak_drain_ = 0;
};
