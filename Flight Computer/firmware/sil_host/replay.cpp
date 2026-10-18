// SIL replay: feeds a wf_flightsim trace (CSV: t,th,q,dl,qbar,tilt_total,alt) for one axis into the
// firmware's ManeuverSeq + AuthorityMonitor and prints the firmware's own metrics as JSON.
// Build: g++ -O2 -std=c++17 -I shim -I ../wyvern_fin replay.cpp -o replay
#define SIL_HOST 1
#include "shared_state.h"
#include "controller.h"
int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "usage: replay trace.csv axis(0|1) [launch_offset_s]\n"); return 1; }
  FILE* f = fopen(argv[1], "r"); int ax = atoi(argv[2]);
  char line[512]; fgets(line, sizeof line, f);
  ManeuverSeq man; double tprev = -1; uint8_t fl = 0;
  while (fgets(line, sizeof line, f)) {
    double t, th, q, dl, qbar, tt, alt;
    if (sscanf(line, "%lf,%lf,%lf,%lf,%lf,%lf,%lf", &t, &th, &q, &dl, &qbar, &tt, &alt) != 7) continue;
    double dt = tprev < 0 ? 0.005 : t - tprev; tprev = t;
    ManIn mi{}; mi.tl = (uint32_t)llround(t * 1000.0); mi.qbar = qbar; mi.tilt_total = tt; mi.alt = alt;
    // sim convention: +delta -> +theta torque. firmware: +delta restores +theta. -> dpair = -delta
    mi.th[ax] = th; mi.thd[ax] = q; mi.dpair[ax] = -dl;
    float ref[2], inj[2]; man.tick(mi, (float)dt, ref, inj, fl);
  }
  const ManAxis& A = man.R.ax[ax];
  printf("{\"status\":%u,\"valid\":%u,\"qbar_d\":%.2f,\"b_fit\":%.4f,\"b_t\":%.3f,\"b_ratio\":%.4f,\"qbar_s\":%.2f,"
         "\"step_sign\":%.0f,\"achieved_deg\":%.4f,\"t63_s\":%.4f,\"overshoot_pct\":%.3f,\"return63_s\":%.4f,\"fin_per_deg\":%.4f,\"peak_rate_dps\":%.3f}\n",
         man.R.status, man.R.valid, A.qbar_d, A.b_fit, A.b_t, A.b_ratio, A.qbar_s, A.step_sign, A.achieved_deg, A.t63_s,
         A.overshoot_pct, A.return63_s, A.fin_per_deg, A.peak_rate_dps);
}
