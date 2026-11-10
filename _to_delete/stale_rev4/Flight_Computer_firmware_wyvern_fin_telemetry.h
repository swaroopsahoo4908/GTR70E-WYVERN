#pragma once
// 915 MHz LoRa downlink (and pad-only uplink) on the Feather's RFM95, via RadioLib.
// Two downlink frames, little-endian, CRC-16/CCITT over all bytes but the last two, told apart by
// the magic byte (and length): 'W' 0x57 flight state (42 B, 20 Hz in flight, 2 Hz on the pad) and
// 'M' 0x4D manoeuvre result (54 B, sent 5x when the programme ends).
// The ground station (a second Feather RP2040 RFM95) includes this same file.
#include <RadioLib.h>
#include <SPI.h>
#include "fc_config.h"
#include "shared_state.h"

#pragma pack(push, 1)
struct TlmFrame {          // 42 B
  uint8_t  magic;          // 0x57 'W'
  uint8_t  state;
  uint16_t seq;
  uint32_t t_ms;
  int16_t  alt_dm;         // altitude AGL, 0.1 m
  int16_t  vz_cms;         // vertical speed, cm/s
  int16_t  tilt_a_cdeg, tilt_b_cdeg;   // 0.01 deg
  int16_t  w_cdps[3];      // body rates, 0.1 deg/s  (field name kept short)
  int16_t  ax_cg, ay_cg, az_cg;        // specific force, 0.01 g
  int8_t   defl_hdeg[4];   // fin deflections, 0.5 deg
  uint16_t qbar_pa;
  uint16_t vbat_mv;
  int8_t   temp_c;
  uint8_t  flags;
  int16_t  auth_t_x100;    // authority-monitor t-statistic x100
  uint16_t crc;
};
#pragma pack(pop)
static_assert(sizeof(TlmFrame) == 42, "TlmFrame must be 42 bytes");

#pragma pack(push, 1)
struct ManFrame {          // 54 B
  uint8_t  magic;          // 0x4D 'M'
  uint8_t  status, valid;
  uint8_t  pad_;
  struct Ax {              // 24 B per axis
    uint16_t qbar_d, qbar_s;     // Pa
    int16_t  b_fit_x10;          // 1/s^2 per rad, x10
    int16_t  b_t_x10;
    int16_t  b_ratio_x1000;
    int8_t   step_sign;
    int8_t   spare;
    int16_t  achieved_mdeg;      // milli-deg
    int16_t  t63_ms, return63_ms;
    int16_t  overshoot_x10;      // %
    int16_t  fin_per_deg_x100;
    int16_t  peak_rate_x10;      // deg/s
  } ax[2];
  uint16_t crc;
};
#pragma pack(pop)
static_assert(sizeof(ManFrame) == 54, "ManFrame must be 54 bytes");

#pragma pack(push, 1)
struct UplinkCmd {         // 12 B
  uint8_t  magic;          // 0xA5
  uint8_t  cmd;            // 1 ARM, 2 DISARM, 3 SERVO_TEST, 4 ZERO, 5 PING
  uint16_t seq;
  uint32_t key;            // WYV_UPLINK_KEY ^ seq  (keeps casual traffic out; not crypto)
  uint16_t pad;
  uint16_t crc;
};
#pragma pack(pop)

static uint16_t crc16_ccitt(const uint8_t* d, size_t n) {
  uint16_t c = 0xFFFF;
  for (size_t i = 0; i < n; i++) { c ^= (uint16_t)d[i] << 8; for (int b = 0; b < 8; b++) c = (c & 0x8000) ? (c << 1) ^ 0x1021 : c << 1; }
  return c;
}

volatile bool g_radio_irq = false;
static void radio_isr() { g_radio_irq = true; }

class Telemetry {
 public:
  bool begin() {
    SPI1.setRX(WYV_PIN_MISO); SPI1.setTX(WYV_PIN_MOSI); SPI1.setSCK(WYV_PIN_SCK);
    SPI1.begin();
    int st = radio_.begin(WYV_LORA_FREQ_MHZ, WYV_LORA_BW_KHZ, WYV_LORA_SF, WYV_LORA_CR,
                          WYV_LORA_SYNC, WYV_LORA_DBM, WYV_LORA_PREAMBLE);
    if (st != RADIOLIB_ERR_NONE) return false;
    radio_.setCRC(true);
    radio_.setDio0Action(radio_isr, RISING);
    ok_ = true; return true;
  }
  // non-blocking: returns immediately; finish() is handled in service()
  void send(const NavState& n, const CtrlState& c, const AuxState& a) {
    if (!ok_ || busy_) return;
    TlmFrame f{};
    f.magic = 0x57; f.state = c.state; f.seq = seq_++; f.t_ms = n.t_ms;
    f.alt_dm = (int16_t)constrain(n.alt_m * 10.f, -32000.f, 32000.f);
    f.vz_cms = (int16_t)constrain(n.vz * 100.f, -32000.f, 32000.f);
    f.tilt_a_cdeg = (int16_t)(n.tilt_a * 5729.58f); f.tilt_b_cdeg = (int16_t)(n.tilt_b * 5729.58f);
    for (int i = 0; i < 3; i++) f.w_cdps[i] = (int16_t)constrain(n.w[i] * 572.958f, -32000.f, 32000.f);
    f.ax_cg = (int16_t)(n.a_body[0] * 10.197f); f.ay_cg = (int16_t)(n.a_body[1] * 10.197f); f.az_cg = (int16_t)(n.a_body[2] * 10.197f);
    for (int i = 0; i < 4; i++) f.defl_hdeg[i] = (int8_t)constrain(c.defl_cmd[i] * 2.f, -127.f, 127.f);
    f.qbar_pa = (uint16_t)constrain(n.qbar, 0.f, 65000.f);
    f.vbat_mv = (uint16_t)(a.vbat * 1000.f); f.temp_c = (int8_t)a.temp_c; f.flags = c.flags;
    f.auth_t_x100 = (int16_t)constrain(c.auth_t_a * 100.f, -32000.f, 32000.f);
    f.crc = crc16_ccitt((uint8_t*)&f, sizeof(f) - 2);
    tx_((uint8_t*)&f, sizeof(f));
  }
  void send_man(const ManResult& m) {
    if (!ok_ || busy_) return;
    ManFrame f{}; f.magic = 0x4D; f.status = m.status; f.valid = m.valid;
    for (int i = 0; i < 2; i++) {
      const ManAxis& a = m.ax[i]; ManFrame::Ax& o = f.ax[i];
      o.qbar_d = (uint16_t)constrain(a.qbar_d, 0.f, 65000.f); o.qbar_s = (uint16_t)constrain(a.qbar_s, 0.f, 65000.f);
      o.b_fit_x10 = (int16_t)constrain(a.b_fit * 10.f, -32000.f, 32000.f); o.b_t_x10 = (int16_t)constrain(a.b_t * 10.f, -32000.f, 32000.f);
      o.b_ratio_x1000 = (int16_t)constrain(a.b_ratio * 1000.f, -32000.f, 32000.f);
      o.step_sign = (int8_t)a.step_sign;
      o.achieved_mdeg = (int16_t)constrain(a.achieved_deg * 1000.f, -32000.f, 32000.f);
      o.t63_ms = (int16_t)(a.t63_s * 1000.f); o.return63_ms = (int16_t)(a.return63_s * 1000.f);
      o.overshoot_x10 = (int16_t)constrain(a.overshoot_pct * 10.f, -32000.f, 32000.f);
      o.fin_per_deg_x100 = (int16_t)constrain(a.fin_per_deg * 100.f, -32000.f, 32000.f);
      o.peak_rate_x10 = (int16_t)constrain(a.peak_rate_dps * 10.f, -32000.f, 32000.f);
    }
    f.crc = crc16_ccitt((uint8_t*)&f, sizeof(f) - 2);
    tx_((uint8_t*)&f, sizeof(f));
  }
  // call every loop1 pass. allow_uplink only on the pad.
  void service(bool allow_uplink, AuxState& aux) {
    if (!ok_) return;
    if (busy_ && (g_radio_irq || millis() - tx_start_ > 100)) {
      radio_.finishTransmit(); busy_ = false; g_radio_irq = false;
      if (allow_uplink) { radio_.startReceive(); rx_until_ = millis() + WYV_UPLINK_WINDOW_MS; rx_ = true; }
    }
    if (rx_) {
      if (g_radio_irq) {
        g_radio_irq = false;
        UplinkCmd u{}; size_t len = radio_.getPacketLength();
        if (len == sizeof(u) && radio_.readData((uint8_t*)&u, sizeof(u)) == RADIOLIB_ERR_NONE) handle_(u, aux);
        radio_.startReceive();
      }
      if ((int32_t)(millis() - rx_until_) > 0) { radio_.standby(); rx_ = false; }
    }
  }
  bool busy() const { return busy_ || rx_; }
  bool ok() const { return ok_; }
 private:
  void tx_(uint8_t* b, size_t n) {
    g_radio_irq = false;
    if (radio_.startTransmit(b, n) == RADIOLIB_ERR_NONE) { busy_ = true; tx_start_ = millis(); }
  }
  void handle_(const UplinkCmd& u, AuxState& aux) {
    if (u.magic != 0xA5) return;
    if (crc16_ccitt((const uint8_t*)&u, sizeof(u) - 2) != u.crc) return;
    if (u.key != (WYV_UPLINK_KEY ^ u.seq)) return;
    if (u.seq <= last_cmd_seq_ && last_cmd_seq_ - u.seq < 1000) return;   // replay guard
    last_cmd_seq_ = u.seq;
    switch (u.cmd) {
      case 1: aux.cmd_arm = 1; break;
      case 2: aux.cmd_arm = 0; break;
      case 3: aux.cmd_servo_test++; break;   // counters: core 0 acts on change
      case 4: aux.cmd_zero++; break;
      default: break;
    }
  }
  SX1276 radio_ = new Module(WYV_PIN_RFM_CS, WYV_PIN_RFM_DIO0, WYV_PIN_RFM_RST, WYV_PIN_RFM_DIO1, SPI1);
  bool ok_ = false, busy_ = false, rx_ = false;
  uint16_t seq_ = 0, last_cmd_seq_ = 0;
  uint32_t tx_start_ = 0, rx_until_ = 0;
};
