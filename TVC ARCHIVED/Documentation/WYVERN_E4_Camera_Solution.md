# GTR70E WYVERN, Camera Solution

**Authors:** Swaroop Sahoo, Chris Liu, Allison Hong  
**Program:** GTR70E WYVERN


## The problem
The OV2640 over SPI (ArduCAM-style) cannot sustain 720p30, SPI readout caps it at roughly VGA/SVGA
JPEG ~15–30 fps, or 720p at ~5–10 fps. Worse, running camera readout + SD writes on the same Pico
that closes the 500 Hz TVC loop steals deterministic CPU time from the control task.

## Decision, offload video to a self-contained thumb camera
Do **not** make the flight computer responsible for video. Use a self-contained thumb camera that
runs on **its own battery** and records to **its own microSD**, wholly independent of the FC:

- **As purchased: i3 4K Thumb Action Camera** (Amazon B0DDSH1W1N), ~36 g, 4K, tiny thumb form factor
  with a spring clip, built-in battery + microSD. Self-contained, zero Pico load, guaranteed clean
  footage, and fits the 66 mm-ID bay. Viewport cut in the FC-bay body wall, aimed outward/slightly
  down. Chosen over a ~10 g RunCam Thumb-class cam purely on cost.
  ⚠ **Mass note (folded into the flight numbers):** the i3 is ~26 g heavier than the ~10 g thumb-cam
  the budget originally assumed. This has been **carried through the whole cascade**, FC bay 96 → 122 g,
  liftoff 679 → **792 g**, apogee 471 → **324 ft**, T/W 2.16/3.80 → **1.85/3.26**. Because the camera
  sits at ~0.42 m (forward of the 0.49 m CG), the aft-CG shift is *favourable*: static margin rises
  from 1.04 to **1.14 cal** (more stable). Net: a small altitude/TWR cost for the cheaper camera, with
  a slight stability *gain*.
- **Keep the OV2640 as *optional***: only if you want a few Pico-grabbed JPEG frames time-synced
  to the flight log for a telemetry overlay, run it at VGA, low fps, best-effort (never blocking
  the control loop). It is **not** the flight video source.

## Why this is the right call
1. The TVC loop keeps 100 % of the Pico's real-time budget.
2. Video quality is decoupled from the SPI/SD bottleneck → reliable 1080p/4K.
3. Fully self-contained (own battery + card + one viewport); no FC power rail or wiring involvement.
4. Cheapest self-contained 4K option; the ~26 g mass penalty is accounted for in the flight budget.

## Integration
The i3 runs on its own battery, so no FC power rail is required, start it manually (or via its
power-on-record mode) at the pad during the arming sequence. If you prefer bus power, it charges over
USB-5 V; confirm its record-on-power behaviour on the bench first.
Cut the viewport at the FC station in the **Upper BT** (nose end, alongside the camera/FC/battery
stack, see `WYVERN_E4_Recovery.md` §1), lens flush with a thin PLA window or open port. Confirm the
exact viewport position against the Upper BT's built length before cutting rather than working from
an approximate figure. The flight computer logs an arm timestamp so video and sensor logs can be
aligned in post.
