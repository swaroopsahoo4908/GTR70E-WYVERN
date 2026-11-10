// t3 -- LoRa range/packet-loss walk test. Flash on the Feather (TX); the ground station sketch
// receives it unchanged (same frame format, state = 2 "PAD"). Walk the airframe away from the
// ground station, note RSSI/SNR vs distance in host/wyvern_host.py's recording.
#include "fc_config.h"
#include "shared_state.h"
#include "telemetry.h"
SeqBox<NavState> g_nav; SeqBox<CtrlState> g_ctrl; SeqBox<AuxState> g_aux;
Telemetry tlm;
void setup() { Serial.begin(115200); Serial.printf("radio %s\n", tlm.begin() ? "ok" : "FAIL"); }
void loop() {
  static uint32_t t = 0; AuxState a{}; a.vbat = 7.6f;
  if (millis() - t >= 50 && !tlm.busy()) { t = millis(); NavState n{}; n.t_ms = t; CtrlState c{}; c.state = ST_PAD; tlm.send(n, c, a); }
  tlm.service(false, a);
}
