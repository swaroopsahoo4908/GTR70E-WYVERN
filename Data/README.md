# Data

- `Wind Tunnel/`: one CSV per configuration, named `<profile>_H<h>_rep<n>.csv`, with balance + q from `wt_balance_daq` and `WT,<ms>,<deg>` markers from the t2 sweep.
- `Flight/`: `WYFxxx.BIN` from the microSD, decoded with `ground_station/host/wyvern_host.py --decode`, the ground-station recording, and the launch-site wind and temperature.
- `Motor (thrust curves)/`: static-stand G40-7W (and F15 reference) runs.
