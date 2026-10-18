// GTR70E WYVERN — optional WiFi/UDP bench telemetry broadcaster. INERT on the Pico 2 W perfboard as fabricated: this
// board has no CYW43439 or any other radio chip populated, so WIFI_ENABLED stays 0 (set in
// wyvern4_tvc.ino) and this code path never runs in flight. Kept for a future board rev or an
// external WiFi module, not deleted.
// =====================================================================================================
// Purpose: bench/preflight monitoring only -- a live readout of attitude/deflection/baro/battery
// without a USB cable, e.g. while the vehicle is on the rail. Per 01_FlightComputer_Spec.md, this
// runs entirely on core 1 and must NEVER touch core 0 or its 500 Hz timing. Two safety properties
// enforced here:
//   1. WiFi association is attempted with a hard timeout and never retried in a tight blocking loop
//      during flight -- if it doesn't come up within WIFI_CONNECT_TIMEOUT_MS at boot, this module
//      goes permanently inert (silent no-op) rather than stalling core 1's housekeeping loop.
//   2. UDP sends are fire-and-forget (no ACK wait, no retry-on-fail) so a dropped bench link during
//      flight cannot block SD logging on the same core.
// Disable entirely by not calling begin(), or by setting ENABLE_WIFI_TELEMETRY=0 in the main sketch.
#pragma once
#include <WiFi.h>
#include <WiFiUdp.h>

struct WifiTelemetryConfig {
  const char* ssid;
  const char* password;
  const char* dest_ip;      // bench laptop's IP on the same network/hotspot
  uint16_t dest_port = 4444;
  uint16_t local_port = 4445;
};

class WifiTelemetry {
public:
  static constexpr unsigned long WIFI_CONNECT_TIMEOUT_MS = 8000;
  static constexpr unsigned long SEND_PERIOD_MS = 50;   // ~20 Hz bench telemetry rate

  bool begin(const WifiTelemetryConfig& cfg) {
    cfg_ = cfg;
    WiFi.mode(WIFI_STA);
    WiFi.begin(cfg_.ssid, cfg_.password);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED) {
      if (millis() - start > WIFI_CONNECT_TIMEOUT_MS) {
        inert_ = true;     // never blocks again after this -- see header note
        return false;
      }
      delay(100);   // acceptable here: this runs once at boot on core 1, before flight, not in loop1()
    }
    udp_.begin(cfg_.local_port);
    inert_ = false;
    ready_ = true;
    return true;
  }

  // Call from loop1() every iteration; internally rate-limited to SEND_PERIOD_MS, and a complete
  // no-op (single bool check, no WiFi-stack calls) once `inert_` is set.
  void service(unsigned long now_ms, float pitch_deg, float yaw_deg, float defl_pitch_deg,
               float defl_yaw_deg, float baro_alt_m, float batt_v, uint8_t state, uint8_t imu_fault) {
    if (inert_ || !ready_) return;
    if (now_ms - last_send_ms_ < SEND_PERIOD_MS) return;
    last_send_ms_ = now_ms;

    // Plain comma-separated text packet -- trivial to parse on the bench side (Python/serial-style
    // tooling already used elsewhere in this project, e.g. host_monitor.py) without needing a
    // binary schema or extra library on the receiving laptop.
    int n = snprintf(packet_, sizeof(packet_),
      "WYV4,%lu,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%u,%u\n",
      (unsigned long)now_ms, pitch_deg, yaw_deg, defl_pitch_deg, defl_yaw_deg, baro_alt_m, batt_v,
      state, imu_fault);
    if (n > 0) {
      udp_.beginPacket(cfg_.dest_ip, cfg_.dest_port);
      udp_.write((const uint8_t*)packet_, (size_t)n);
      udp_.endPacket();   // fire-and-forget -- no blocking ACK wait, per header note
    }
  }

  bool ready() const { return ready_ && !inert_; }

private:
  WifiTelemetryConfig cfg_;
  WiFiUDP udp_;
  bool ready_ = false;
  bool inert_ = false;
  unsigned long last_send_ms_ = 0;
  char packet_[128];
};
