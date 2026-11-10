#pragma once
// microSD log (data of record, 100 Hz binary) on an Adafruit 4682 breakout, SPI0 (rev 4b, Pico 2 W).
// No radio, so this card is the only record of the flight: it has to survive the landing (~6 m/s under
// the chute; a strip of Kapton over the card keeps it in its socket) and it must never stall the loop.
//   * The file is pre-allocated contiguously at open (WYV_LOG_PREALLOC_MB), so a write never has to
//     walk the FAT or allocate clusters mid-flight.
//   * Records go into a 32 kB RAM ring buffer; one 512 B sector is written out only when the card
//     reports not-busy (FsFile::isBusy), so a slow card's internal housekeeping (up to ~100 ms on
//     cheap cards) costs buffer space, not loop time. 32 kB holds 3.4 s of records.
//     (Pattern from the SdFat TeensySdioLogger example by Bill Greiman.)
//   * On landing (or when the pre-allocation fills) the buffer is drained and the file truncated.
// Binary record (LogRec, 96 B): attitude quaternion, tilts, rates, accel, vertical channel, fins,
// axis commands + references, axial channel, baro, state. Layout unchanged from rev 3 so
// host/wyvern_host.py --decode reads both.
// MANxxx.TXT: one-line-per-axis text summary of the authority manoeuvre, written when it ends.
#include <SPI.h>
#include <SdFat.h>
#include <RingBuf.h>
#include "fc_config.h"
#include "shared_state.h"

#pragma pack(push, 1)
struct LogRec {               // 96 B
  uint32_t t_ms;
  float q[4];
  float tilt_a, tilt_b;
  float w[3];
  float a[3];
  float alt, vz, qbar;
  int8_t defl_hdeg[4];
  float u_a, u_b;
  float ref_a, ref_b;         // deg, manoeuvre attitude references
  float a_axial;              // m/s^2, axial channel (BNO085, thrust model while the BNO is clipped)
  float baro_hpa;             // BMP388
  uint8_t state, flags;
  uint16_t vbat_mv;
};
#pragma pack(pop)
static_assert(sizeof(LogRec) == 96, "LogRec must be 96 bytes (host/wyvern_host.py LOGREC)");

class Logger {
 public:
  bool begin_sd() {
    WYV_SD_SPI.setRX(WYV_PIN_SD_MISO); WYV_SD_SPI.setTX(WYV_PIN_SD_MOSI); WYV_SD_SPI.setSCK(WYV_PIN_SD_SCK);
    sd_ok_ = sd_.begin(SdSpiConfig(WYV_PIN_SD_CS, DEDICATED_SPI, SD_SCK_MHZ(WYV_SD_MHZ), &WYV_SD_SPI));
    if (!sd_ok_) return false;
    for (int i = 0; i < 1000; i++) { snprintf(name_, sizeof(name_), "WYF%03d.BIN", i); if (!sd_.exists(name_)) break; }
    sd_ok_ = f_.open(name_, O_RDWR | O_CREAT | O_TRUNC);
    if (!sd_ok_) return false;
    cap_ = (uint64_t)WYV_LOG_PREALLOC_MB << 20;
    if (!f_.preAllocate(cap_)) { f_.close(); sd_ok_ = false; return false; }
    rb_.begin(&f_);
    return true;
  }
  static LogRec pack(const NavState& n, const CtrlState& c, const AuxState& a) {
    LogRec r{};
    r.t_ms = n.t_ms; memcpy(r.q, n.q, sizeof(r.q)); r.tilt_a = n.tilt_a; r.tilt_b = n.tilt_b;
    memcpy(r.w, n.w, sizeof(r.w)); memcpy(r.a, n.a_body, sizeof(r.a));
    r.alt = n.alt_m; r.vz = n.vz; r.qbar = n.qbar;
    for (int i = 0; i < 4; i++) r.defl_hdeg[i] = (int8_t)constrain(c.defl_cmd[i] * 2.f, -127.f, 127.f);
    r.u_a = c.u_a; r.u_b = c.u_b; r.ref_a = c.ref_a; r.ref_b = c.ref_b; r.a_axial = c.a_axial; r.baro_hpa = a.baro_hpa; r.state = c.state; r.flags = c.flags;
    r.vbat_mv = (uint16_t)(a.vbat * 1000);
    return r;
  }
  void write(const LogRec& r) {
    if (!sd_ok_ || closed_) return;
    if (rb_.bytesFree() < sizeof(r)) { dropped_++; return; }
    rb_.write((const uint8_t*)&r, sizeof(r));
  }
  // Call every loop: writes at most one 512 B sector, and only when the card is idle.
  void service() {
    if (!sd_ok_ || closed_) return;
    if (rb_.bytesUsed() >= 512 && !f_.isBusy()) {
      if (f_.curPosition() + 512 > cap_) { close(); return; }   // pre-allocation full
      if (rb_.writeOut(512) != 512) { sd_ok_ = false; }
    }
  }
  void write_man(const ManResult& m) {           // human-readable summary next to the binary log
    if (!sd_ok_) return;
    FsFile t; char name[16]; strncpy(name, name_, sizeof(name)); memcpy(name, "MAN", 3); strcpy(name + 6, ".TXT");
    if (!t.open(name, O_WRONLY | O_CREAT | O_TRUNC)) return;
    t.printf("status %u valid 0x%02X  (status: 2 done, 3 skipped by gates, 4 aborted)\n", m.status, m.valid);
    t.println("axis,qbar_doublet_Pa,b_fit_1/s2/rad,t_stat,b_ratio_meas/model,qbar_step_Pa,step_sign,achieved_deg,t63_s,overshoot_pct,return63_s,fin_per_deg,peak_rate_dps");
    for (int i = 0; i < 2; i++) {
      const ManAxis& a = m.ax[i];
      t.printf("%c,%.0f,%.2f,%.1f,%.3f,%.0f,%.0f,%.3f,%.3f,%.1f,%.3f,%.2f,%.1f\n", i ? 'B' : 'A', a.qbar_d, a.b_fit, a.b_t,
               a.b_ratio, a.qbar_s, a.step_sign, a.achieved_deg, a.t63_s, a.overshoot_pct, a.return63_s, a.fin_per_deg, a.peak_rate_dps);
    }
    t.close();
  }
  void close() {
    if (!sd_ok_ || closed_) return;
    rb_.sync(); f_.truncate(); f_.close(); closed_ = true;
  }
  bool sd_ok() const { return sd_ok_; }
  uint32_t dropped() const { return dropped_; }
 private:
  SdFs sd_; FsFile f_; RingBuf<FsFile, WYV_LOG_RING_BYTES> rb_;
  char name_[16] = "WYF000.BIN"; uint64_t cap_ = 0;
  bool sd_ok_ = false, closed_ = false; uint32_t dropped_ = 0;
};
