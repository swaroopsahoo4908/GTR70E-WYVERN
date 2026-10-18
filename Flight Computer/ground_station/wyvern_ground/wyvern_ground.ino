// =================================================================================================
// GTR70E WYVERN -- ground station: a second Adafruit Feather RP2040 RFM95 (PID 5714), the same
// board as the flight computer, so the radio, pins, frame format and RadioLib build are identical.
//
//  * Receives the two downlink frames (SF7 / 500 kHz / 915 MHz / sync 0x57):
//      'W' flight state (20 Hz in flight), 'M' manoeuvre result (5x after it ends).
//  * Streams every decoded frame on USB serial as one tagged CSV line (host/wyvern_host.py records
//    and plots it):   T,<flight columns>,rssi,snr      M,<axis A>,<axis B>
//  * Pad uplink commands typed on USB serial: ARM, DISARM, SERVO, ZERO, PING. Each is retried
//    after every pad frame until the downlinked state shows it took (or 10 s pass).
//  * Onboard red LED blinks on every good frame; NeoPixel-free so no extra library.
//
// Wiring: none for the radio (on the board). uFL -> SMA pigtail -> 915 MHz Yagi or 1/2-wave whip.
//   USB-C to the laptop.
// Core: arduino-pico, board "Adafruit Feather RP2040 RFM". Libs: RadioLib.
// =================================================================================================
#include <SPI.h>
#include <RadioLib.h>
#include "fc_config.h"
#include "shared_state.h"
#include "telemetry.h"   // frame structs + CRC (generated copy, see sync_headers.py)

SX1276 gs = new Module(WYV_PIN_RFM_CS, WYV_PIN_RFM_DIO0, WYV_PIN_RFM_RST, WYV_PIN_RFM_DIO1, SPI1);
volatile bool rx_flag = false;
void gs_isr() { rx_flag = true; }

TlmFrame last{};
uint32_t n_ok = 0, n_bad = 0;
uint16_t up_seq = 1; int pending_cmd = 0; uint32_t pending_until = 0;

void send_cmd(uint8_t cmd) {
  UplinkCmd u{}; u.magic = 0xA5; u.cmd = cmd; u.seq = up_seq++; u.key = WYV_UPLINK_KEY ^ u.seq;
  u.crc = crc16_ccitt((uint8_t*)&u, sizeof(u) - 2);
  gs.transmit((uint8_t*)&u, sizeof(u));      // blocking ~9 ms; fine on the ground
  gs.startReceive();
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  SPI1.setRX(WYV_PIN_MISO); SPI1.setTX(WYV_PIN_MOSI); SPI1.setSCK(WYV_PIN_SCK); SPI1.begin();
  int st = gs.begin(WYV_LORA_FREQ_MHZ, WYV_LORA_BW_KHZ, WYV_LORA_SF, WYV_LORA_CR, WYV_LORA_SYNC, 17, WYV_LORA_PREAMBLE);
  Serial.printf("# radio init %d\n", st);
  gs.setCRC(true); gs.setDio0Action(gs_isr, RISING); gs.startReceive();
  Serial.println("# T,t_ms,state,seq,alt_m,vz,tilt_a,tilt_b,wx,wy,wz,ax_g,ay_g,az_g,d0,d1,d2,d3,qbar,vbat,temp,flags,auth_t,rssi,snr");
  Serial.println("# M,status,valid,[A: qbar_d,b_fit,b_t,b_ratio,qbar_s,sign,achieved,t63,return63,overshoot,fin_per_deg,peak_rate] x2");
}

void loop() {
  if (rx_flag) {
    rx_flag = false;
    uint8_t b[64]; size_t n = gs.getPacketLength();
    bool good = n <= sizeof(b) && gs.readData(b, n) == RADIOLIB_ERR_NONE && n >= 3 && crc16_ccitt(b, n - 2) == (uint16_t)(b[n - 2] | (b[n - 1] << 8));
    int16_t rssi = gs.getRSSI(); float snr = gs.getSNR();
    if (good && b[0] == 0x57 && n == sizeof(TlmFrame)) {
      TlmFrame& f = *(TlmFrame*)b; last = f; n_ok++;
      Serial.printf("T,%lu,%u,%u,%.1f,%.2f,%.2f,%.2f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.1f,%.1f,%.1f,%.1f,%u,%.2f,%d,%u,%.2f,%d,%.1f\n",
        (unsigned long)f.t_ms, f.state, f.seq, f.alt_dm / 10.0, f.vz_cms / 100.0, f.tilt_a_cdeg / 100.0, f.tilt_b_cdeg / 100.0,
        f.w_cdps[0] / 10.0, f.w_cdps[1] / 10.0, f.w_cdps[2] / 10.0, f.ax_cg / 100.0, f.ay_cg / 100.0, f.az_cg / 100.0,
        f.defl_hdeg[0] / 2.0, f.defl_hdeg[1] / 2.0, f.defl_hdeg[2] / 2.0, f.defl_hdeg[3] / 2.0, f.qbar_pa, f.vbat_mv / 1000.0,
        f.temp_c, f.flags, f.auth_t_x100 / 100.0, rssi, snr);
      // the rocket opens its uplink window right after each pad frame
      // ARM / DISARM are retried until the downlinked state shows them; SERVO / ZERO / PING go once
      if (pending_cmd && millis() < pending_until && f.state <= 3) {
        bool done = (pending_cmd == 1 && f.state == 3) || (pending_cmd == 2 && f.state == 2);
        if (done) { pending_cmd = 0; Serial.println("# command acknowledged"); }
        else { send_cmd(pending_cmd); if (pending_cmd >= 3) pending_cmd = 0; }
      }
    } else if (good && b[0] == 0x4D && n == sizeof(ManFrame)) {
      ManFrame& f = *(ManFrame*)b; n_ok++;
      Serial.printf("M,%u,%u", f.status, f.valid);
      for (int i = 0; i < 2; i++) {
        const ManFrame::Ax& a = f.ax[i];
        Serial.printf(",%u,%.1f,%.1f,%.3f,%u,%d,%.3f,%.3f,%.3f,%.1f,%.2f,%.1f", a.qbar_d, a.b_fit_x10 / 10.0, a.b_t_x10 / 10.0,
          a.b_ratio_x1000 / 1000.0, a.qbar_s, a.step_sign, a.achieved_mdeg / 1000.0, a.t63_ms / 1000.0, a.return63_ms / 1000.0,
          a.overshoot_x10 / 10.0, a.fin_per_deg_x100 / 100.0, a.peak_rate_x10 / 10.0);
      }
      Serial.println();
    } else n_bad++;
    if (good) digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    gs.startReceive();
  }
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n'); s.trim(); s.toUpperCase();
    int c = s == "ARM" ? 1 : s == "DISARM" ? 2 : s == "SERVO" ? 3 : s == "ZERO" ? 4 : s == "PING" ? 5 : 0;
    if (c) { pending_cmd = c; pending_until = millis() + 10000; Serial.printf("# queued %s\n", s.c_str()); }
    else if (s == "STATS") Serial.printf("# frames ok %lu bad %lu\n", (unsigned long)n_ok, (unsigned long)n_bad);
  }
}
