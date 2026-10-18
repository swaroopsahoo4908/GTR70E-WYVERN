#pragma once
// microSD log (data of record, 100 Hz binary), core 1. Rev 3c dropped the LittleFS copy on the
// QSPI flash: the card sits in a push-push socket on the spine under 1.6 mm of wall, the airframe
// lands at ~6 m/s under the chute, and the 20 Hz downlink is the backup record anyway.
// Binary record (LogRec, 96 B): attitude quaternion, tilts, rates, accel, vertical channel, fins,
// axis commands + references, axial (high-g) channel, baro, state.
// MANxxx.TXT: one-line-per-axis text summary of the authority manoeuvre, written when it ends.
#include <SdFat.h>
#include "fc_config.h"
#include "shared_state.h"
#include "telemetry.h"

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
  float a_axial;              // m/s^2, axial channel (BNO085 or ADXL375 above 7 g)
  float baro_hpa;
  uint8_t state, flags;
  uint16_t vbat_mv;
};
#pragma pack(pop)
static_assert(sizeof(LogRec) == 96, "LogRec must be 96 bytes (host/wyvern_host.py LOGREC)");

class Logger {
 public:
  bool begin_sd() {
    sd_ok_ = sd_.begin(SdSpiConfig(WYV_PIN_SD_CS, SHARED_SPI, SD_SCK_MHZ(16), &SPI1));
    if (!sd_ok_) return false;
    for (int i = 0; i < 1000; i++) { snprintf(name_, sizeof(name_), "WYF%03d.BIN", i); if (!sd_.exists(name_)) break; }
    sd_ok_ = f_.open(name_, O_WRONLY | O_CREAT | O_EXCL);
    return sd_ok_;
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
  void write_sd(const LogRec& r)    { if (sd_ok_) { f_.write(&r, sizeof(r)); if (++n_sd_ % 100 == 0) f_.flush(); } }
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
    t.close(); f_.flush();
  }
  void close() { if (sd_ok_) { f_.flush(); f_.close(); } }
  bool sd_ok() const { return sd_ok_; }
 private:
  SdFat sd_; FsFile f_; char name_[16] = "WYF000.BIN";
  bool sd_ok_ = false; uint32_t n_sd_ = 0;
};
