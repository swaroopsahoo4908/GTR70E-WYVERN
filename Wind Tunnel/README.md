# Wind tunnel

- `STEM+Tunnel+Promo+-+0.4n_stls/`, `.3mf`: Jerrod H's modular STEM wind tunnel, unchanged. Measured internals: 202 mm square upstream ducts, 4:1 contraction, 100 x 100 x 175 mm test section, NF-A14 fan.
- Two phases: A, a single fin on a reflection-plane panel in the stock section (main research question); B, the full four-fin control tube with a removable stabilizer tail in a new 200 x 200 x 750 mm section (stabilizer study). See `Documentation/Wind_Tunnel_Adaptation.md` and drawing `Documentation/diagrams/D4_wind_tunnel_adaptation.png`. The new printed parts are in `3D parts/wind_tunnel/`.
- `wt_balance_daq/`: Pico 2 W firmware for the balance (Phase A: 2 cells under the servo cradle; Phase B: 3 cells under the strut; NAU7802s behind the PCA9548 mux) and the SDP810 pitot. Writes CSV over USB.
