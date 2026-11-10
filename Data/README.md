# Data

- `Wind Tunnel/`: one CSV per configuration, named `<profile>_H<h>_rep<n>.csv`, the serial log from `wt_balance_daq` v2.0: `D` raw samples, `WT,<ms>,<deg>` step markers and one `R` line per step (N, x_cp, q, V, C_N). Put the manometer reading, room T / p / RH and the check-standard result in the file header.
- `Flight/`: `WYFxxx.BIN` from the microSD, decoded with `ground_station/host/wyvern_host.py --decode`, the ground-station recording, and the launch-site wind and temperature.
- `Motor (thrust curves)/`: reference curves only; the static stand was dropped in rev 3e, so the F42-4T is flown on its thrustcurve.org curve.
