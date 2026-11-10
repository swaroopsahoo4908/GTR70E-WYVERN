// Builds GTR70E_WYVERN_Research_Proposal.docx. Two passes: run once, render to PDF, read the
// heading pages into toc_pages.json, run again (see build_proposal.sh).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, HeadingLevel, AlignmentType, Header,
  PageNumber, TabStopType, InternalHyperlink, Bookmark, PageBreak, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, LevelFormat,
} = require("docx");

const HERE = __dirname;
const FIG = path.join(HERE, "figures");
const PAGES = fs.existsSync(path.join(HERE, "toc_pages.json"))
  ? JSON.parse(fs.readFileSync(path.join(HERE, "toc_pages.json"), "utf8")) : {};
const FONT = "Times New Roman";

// ---- inline markup: _italic_, ~sub~, ^sup^ -------------------------------------------------
function runs(text, base = {}) {
  const out = [];
  const re = /((?<![A-Za-z0-9])_[^_]+_(?![A-Za-z0-9])|~[^~]+~|\^[^^]+\^)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0], inner = t.slice(1, -1);
    if (t[0] === "_") out.push(new TextRun({ text: inner, italics: true, ...base }));
    else if (t[0] === "~") out.push(new TextRun({ text: inner, subScript: true, ...base }));
    else out.push(new TextRun({ text: inner, superScript: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const body = (t) => new Paragraph({ children: runs(t), indent: { firstLine: 720 }, spacing: { after: 0, line: 264 } });
const plain = (t, opts = {}) => new Paragraph({ children: runs(t), spacing: { after: 0, line: 264 }, ...opts });
const gap = () => new Paragraph({ children: [], spacing: { after: 0 } });
const eq = (t) => new Paragraph({ children: runs(t), alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 } });
const bullet = (t) => new Paragraph({ children: runs(t), numbering: { reference: "dash", level: 0 }, spacing: { after: 0, line: 264 } });
const numbered = (t) => new Paragraph({ children: runs(t), numbering: { reference: "steps", level: 0 }, spacing: { after: 0, line: 264 } });

let bm = 0;
const tocEntries = [];
function heading(text, level, tocLevel = level) {
  const id = "h" + (++bm);
  tocEntries.push({ id, text, level: tocLevel });
  const hl = level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;
  return new Paragraph({ heading: hl, children: [new Bookmark({ id, children: [new TextRun(text)] })] });
}

let figN = 0;
function figure(file, caption, widthIn = 6.5) {
  const buf = fs.readFileSync(path.join(FIG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);   // PNG IHDR
  const W = Math.round(widthIn * 96), H = Math.round(W * h / w);
  figN += 1;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: buf, transformation: { width: W, height: H },
        altText: { title: `Figure ${figN}`, description: caption, name: file } })] }),
    new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: `Figure ${figN}. `, italics: true, size: 20 }), ...runs(caption, { size: 20 })] }),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => new TableCell({
      borders, width: { size: widths[j], type: WidthType.DXA },
      shading: i === 0 ? { fill: "E7E6E6", type: ShadingType.CLEAR, color: "auto" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: runs(c, { size: 21, bold: i === 0 }) })] })) })),
  });
}
const tableCaption = (n, t) => new Paragraph({ spacing: { before: 200, after: 80 }, keepNext: true,
  children: [new TextRun({ text: `Table ${n}. `, italics: true, size: 20 }), ...runs(t, { size: 20 })] });

// =============================================================================================
const C = [];   // main section content

// ---- Student information + introduction ----
C.push(heading("Student Information", 1));
C.push(new Paragraph({ children: [new TextRun({ text: "Student Names: ", bold: true }), new TextRun("Swaroop Sahoo, Chris Liu, Allison Hong")] }));
C.push(gap());
C.push(new Paragraph({ children: [new TextRun({ text: "Project Title: ", bold: true }), new TextRun("GTR70E WYVERN (Widespread Yield Variable Engagement Rapid-response Neutralizer): Engineering Design and Experimental Validation of Aerofoil Section and Fin Height Effects on the Control Authority of Servo-Actuated Fins in a Subscale Single-Stage Solid-Fuelled Prototype Rocket Demonstrator")] }));
C.push(gap());
C.push(new Paragraph({ children: [new TextRun({ text: "Research Pathway: ", bold: true }), new TextRun("Engineering/Innovation Design")] }));
C.push(gap());
C.push(new Paragraph({ children: [new TextRun({ text: "Intended Majors:", bold: true })] }));
C.push(bullet("_Swaroop Sahoo_: Electrical Engineering with Aerospace Engineering Minor"));
C.push(bullet("_Chris Liu_: Aerospace Engineering with Business Minor"));
C.push(bullet("_Allison Hong_: Mechanical Engineering with Aerospace Engineering Minor"));

C.push(heading("Introduction", 1));
C.push(body("Active aerodynamic control of small-scale, hobbyist-accessible rockets draws on aerodynamics, embedded real-time systems, additive manufacturing and classical control theory at once, and the least developed of these usually sets what a vehicle can do. Movable control fins are the standard steering method on tactical missiles, where they work through both the powered and the coasting phases of flight with no hardware in the exhaust, yet documented, reproducible fin-control builds at the sounding-rocket scale remain rare in the amateur and academic literature. Where hobby-scale vehicles do carry movable fins, the section and size are usually inherited from a kit or chosen for convenience: a flat plate cut from sheet stock, or a rounded leading edge sanded by hand. Published low-Reynolds-number aerofoil data (Selig, 2003; Mueller & DeLaurier, 2003) is mostly two-dimensional and taken on wings of moderate to high aspect ratio. A small triangular control fin is neither. At a 60 mm root chord it operates at a Reynolds number near 4 × 10^4^ in a bench tunnel and up to about 2 × 10^5^ at motor burnout, with an aspect ratio between 1.3 and 2.7, partly immersed in the boundary layer of the body it is mounted on. Whether the section shape matters at all in that regime, and how quickly authority grows as the fin gets taller, are open practical questions for anyone designing a fin-controlled rocket."));
C.push(body("GTR70E WYVERN addresses this gap with a deliberately focused architecture: a 58 mm, single-stage rocket steered by four servo-driven triangular control fins at a single station, with fixed stabilizers aft that keep the airframe passively stable. The experimental variables are the fin's aerofoil section and its height. A bench wind tunnel, modified to hold one flight-identical fin on a reflection plane, produces the primary dataset; a simulation chain predicts the same quantities in parallel; and a flight-validation phase of three launches demonstrates that the selected fin performs as designed under real atmospheric and motor-burn conditions. Because the program centers on one research question, every configuration shares the same planform, hub, servo, material and tunnel; differences in the measurements can then be attributed to section and height alone, and the dataset is large enough for formal statistics."));

// ---- Research question ----
C.push(heading("Research Question", 1));
C.push(heading("Main Research Question - Aerofoil Section and Fin Height Effects on Fin Control Authority", 2));
C.push(body("Holding the planform (a right-triangular fin with a 60 mm root chord, hinged at 45 % of the chord), the material (PETG-CF at 100 % infill), the actuator (EMAX ES9251 II) and the test conditions constant, how do aerofoil section (2.4 mm flat plate, 6 % double wedge, NACA 0006 and NACA 0012) and fin height (20, 25, 30, 35 and 40 mm) determine the control authority of a servo-actuated triangular control fin on a 58 mm rocket, and which combination gives the most usable authority?"));
C.push(body("Control authority is defined here as the normal-force slope with deflection, _C_~Nδ~, fitted over ±10° and referenced to the measured dynamic pressure, together with how linear _C_~N~(_δ_) stays out to the ±15° travel limit. On the vehicle that slope becomes the pitching-moment slope _C_~mδ~ about the center of gravity, the quantity the flight controller works with. Four hypotheses frame the question:"));
C.push(bullet("H1 (section, linear range). Panel-method results rank the two-dimensional lift slopes NACA 0012 > flat plate > NACA 0006 > double wedge (6.88, 6.72, 6.57 and 6.44 per radian), but at aspect ratios of 1.3 to 2.7 the three-dimensional correction squeezes the spread to about 2.5 % (vortex-lattice _C_~Nα~ at H = 40 mm: 2.77 to 2.70 per radian). The linear slopes alone should barely separate the sections."));
C.push(bullet("H2 (section, nonlinear range). Past roughly 8°, sharp leading edges shed a leading-edge vortex and gain vortex lift by the suction analogy (Polhamus, 1966). With assumed suction-retention factors, the model gives the double wedge 17 % more normal force than linear theory at 10°, the flat plate 7 %, NACA 0006 5 % and NACA 0012 -1.5 %. The sections are most likely to separate here, and the curvature of the measured _C_~N~(_δ_) tests the prediction."));
C.push(bullet("H3 (height). Authority grows faster than linearly with height, because aspect ratio rises and more of the fin clears the body boundary layer (modelled effectiveness 0.78 at H = 20 mm, 0.88 at H = 40 mm). The predicted Phase A normal force for one NACA 0006 fin at 10° and 11 m/s is 13, 19, 26, 34 and 42 mN at H = 20 to 40 mm."));
C.push(bullet("H4 (what it buys). In the simulated closed-loop gust case the extra height costs about 1 m of apogee per 5 mm while the simulated peak hinge moment stays near a thirteenth of the servo's stall torque (about half of it in the worst corner, 15° at maximum dynamic pressure), so the tallest fin that fits the airframe should be the best choice for flight."));

C.push(heading("Sub-RQ1 - Stabilizer Interference on Installed Authority", 2));
C.push(body("How much do the four fixed rectangular stabilizers reduce the installed authority of the control fins, and how does that loss depend on stabilizer span (0 to 40 mm) and on their azimuth relative to the control fins (0°, 22.5° and 45°)? A deflected control fin sheds a tip vortex that streams aft past the stabilizers, and its downwash pushes on them opposite to the control force. The stabilizers buy static margin and take back control power at the same time. The single-vortex model predicts an interference ratio of -0.10 for the flown 20 mm stabilizers at 45° and predicts that stabilizers in line with the control fins (0°) could reverse the control derivative outright. This sub-question is answered by the simulation sweep and, as time allows, a full-model tunnel phase."));
C.push(heading("Sub-RQ2 - Predictive Accuracy from Simulation to Wind Tunnel to Flight", 2));
C.push(body("How well does the simulation chain (panel method, vortex lattice, slender-body carry-over, boundary-layer effectiveness and vortex interference) predict what the tunnel measures, and how much of the tunnel-calibrated prediction survives in flight? The tunnel half is a point-by-point comparison across the 20 configurations, scored by percent error and by whether the ranking holds (Spearman rank correlation). The flight half comes from an authority manoeuvre flown on each of three launches, which measures _M_~δ~/_I_ directly and compares it against the tunnel-calibrated model."));

C.push(heading("Project Goal", 1));
C.push(body("The goal of the GTR70E WYVERN project is to measure, rather than assume, how aerofoil section and fin height set the control authority of a small servo-actuated fin, and to carry that answer onto a recoverable 58 mm fin-controlled rocket. The program delivers an open dataset of 2,440 wind-tunnel balance points across 20 fin configurations, a simulation chain whose errors against that dataset are quantified, a low-cost and reproducible tunnel balance built from hobbyist parts, and three instrumented flights of the selected fin. Every design file, script and dataset is version-controlled so another team can rebuild the tunnel rig, rerun the predictions and compare their own fins against ours."));

// ---- Methodologies ----
C.push(heading("Proposed Methodologies", 1));
C.push(body("The flight vehicle is a 58 mm outer-diameter, single-stage airframe 693 mm long, built in four printed sections: a 150 mm tangent-ogive nose, a 250 mm recovery bay, a 174 mm control tube and a 119 mm motor bay. Four triangular control fins sit at one station 535 mm from the nose, each driven directly by its own servo, and four 81 × 20 mm stabilizers sit at 45° to them along the motor bay. Liftoff mass is 785 g on an AeroTech Econojet F42-4T (52.9 N·s total impulse), falling to 758 g at burnout. The center of gravity sits at 338.3 mm against a center of pressure at 421.5 mm, a static margin of 1.44 calibers at liftoff that rises to 1.63 at burnout; 253 g of nose ballast sets both that margin and a 195.5 mm control arm. Thrust-to-weight is 4.68 average and 8.45 peak, the vehicle leaves a 6 ft rail at 15.0 m/s, and the predicted apogee is 176 m (577 ft) at 6.34 s with a maximum dynamic pressure of 1.81 kPa. These figures come from one source-of-truth geometry file that drives every simulation, drawing and CAD part, so they are the reference configuration against which each method below is sized."));
C.push(...figure("Fig1_cad_renders.png", "Flight vehicle rendered from the production STL files. The control-tube section (c) shows the four servos at one station around the central ejection bypass tube."));
C.push(...figure("Fig2_vehicle_layout.png", "Flight vehicle, side elevation through the pitch plane. Dimensions in millimetres."));
C.push(body("The program uses three tiers: simulation, ground-based wind-tunnel testing and in-situ powered flight. The main research question rests on the tunnel and the simulation, which predict and measure the same quantities point by point. Flight is a deliberately small third tier: three launches that confirm the selected fin works on the real vehicle and add one installed authority measurement per axis per flight. All fabrication uses hobbyist-accessible methods and commercially available parts, nearly all from Adafruit, SparkFun and Amazon."));
C.push(...figure("Fig3_research_plan.png", "Research plan. Simulation predicts both tunnel phases; Phase A selects the section P*, simulation selects the height H*, and three flights at H* − 5, H* and H* + 5 mm check the result."));

C.push(heading("Experimental Design", 2));
C.push(body("The Phase A experiment is a full-factorial design of four sections by five heights, with deflection swept as a continuous variable inside each run. One printed fin per configuration is enough, which cuts the fin budget to about a fifth of what full four-fin sets would cost. Configuration order is randomised and each configuration is swept twice."));
C.push(tableCaption(1, "Phase A factors and levels."));
C.push(table([2600, 6760], [
  ["Factor", "Levels"],
  ["Aerofoil section", "flat plate (2.4 mm), double wedge 6 %, NACA 0006, NACA 0012"],
  ["Fin height _H_", "20, 25, 30, 35, 40 mm in the tunnel; 15 to 50 mm in simulation"],
  ["Deflection _δ_", "-15° to +15° in 0.5° steps; 1 s settle, last 2 s of each 3 s dwell averaged"],
  ["Repeats", "two sweeps per configuration, randomised order"],
  ["Held constant", "planform (60 mm root, 45 % hinge), PETG-CF at 100 % infill, hub, servo, tunnel speed"],
  ["Total", "20 configurations × 61 angles × 2 = 2,440 balance points"],
]));
C.push(gap());
C.push(body("The selection rule ties the tunnel to the flights. The section with the most observed authority, the largest corrected _C_~Nδ~ over ±10° with linearity to 15° as the tie-break, becomes P*. The height with the most simulated installed authority becomes H*. Simulated authority rises monotonically with height for every section, so H* is currently 40 mm and the flights use 35, 40 and 45 mm. The 45 mm fin lies one step outside the tunnel set, which makes that flight an out-of-sample check on the height trend."));

C.push(heading("Wind Tunnel", 2));
C.push(body("The tunnel is the open-return modular STEM tunnel of Hofferth (2025): an inlet, a honeycomb module, 40-mesh and 80-mesh screen modules, a 4:1 contraction from a 202 mm to a 100 mm square section, and a 100 × 100 × 175 mm test section. Its internal dimensions were measured by slicing the published STL files, because the design page gives only the window size. The contraction and screen spacing are checked against the low-speed tunnel rules of Bell and Mehta (1988) and Mehta and Bradshaw (1979). Three printed parts adapt it for this project, and everything upstream of the test section stays stock."));
C.push(body("A reflection-plane wall panel replaces one side wall of the test section, with a bevelled leading edge so its boundary layer starts thin and a 10 mm bore for the fin hub. Outside the wall, a cradle holds an EMAX ES9251 II with the same ear pad and window geometry as the flight control tube. A tunnel version of the flight hub, with the same fin interface and the fin root 1.0 mm off the panel as on the rocket, carries a printed 40-tooth gear that turns a 20-tooth gear at 2:1; a magnet in that gear spins over an AS5600 magnetic angle sensor, so the fin deflection is measured on the hub to 0.04° rather than taken from the servo command, which would hide the servo's gear backlash and its wind-up under aerodynamic load. A light rubber-band preload keeps the printed mesh on one flank, and the whole gear train rides on the balance cradle. A printed transition, a 7° diffuser from the 100 mm square section to 6 in round, replaces the stock diffuser and 140 mm PC fan with a 6 in EC inline duct fan rated at 405 CFM free air, set by its speed controller. Against the losses of the honeycomb, screens and contraction, the expected test-section speed is about 11 to 12 m/s, which the pitot measures every session. At H = 40 mm and 10° deflection the fin blocks about 2 to 3 % of the section, and its semi-span is 0.40 of the section width, inside the usual half-model limits."));
C.push(...figure("Fig4_wind_tunnel_adaptation.png", "Tunnel configurations, side view, not to scale vertically. (a) Stock tunnel (Hofferth, 2025). (b) Phase A: one fin on the reflection-plane wall panel, servo cradle and load cells outside the wall, 6 in EC fan. (c) Phase B: full control tube and stabilizer tail on a strut balance in a 200 × 200 × 750 mm section."));
C.push(tableCaption(2, "Predicted Phase A normal force (mN) on one fin at 10° deflection and 11 m/s; force scales with (V/11)^2^."));
C.push(table([2360, 1400, 1400, 1400, 1400, 1400], [["Section", "H = 20", "H = 25", "H = 30", "H = 35", "H = 40"], ["Flat plate", "13.2", "19.4", "26.6", "34.4", "42.9"], ["6 % double wedge", "15.0", "21.7", "29.2", "37.5", "46.4"], ["NACA 0006", "12.7", "18.9", "25.8", "33.5", "41.7"], ["NACA 0012", "11.7", "17.6", "24.3", "31.8", "40.0"]]));
C.push(gap());

C.push(...figure("Fig5_wind_tunnel_parts.png", "Printed Phase A tunnel parts and twelve of the twenty test fins, rendered from the production STL files."));

C.push(heading("Force Balance", 3, 3));
C.push(body("The servo cradle sits on two 1 kg straight-bar load cells, 60 mm apart along the chord and outside the tunnel wall. The fin's normal force pushes the cradle into both cells, so their sum is the normal force and the split between them locates the chordwise center of pressure:"));
C.push(eq("_N_ = (_F_~fore~ + _F_~aft~) _g_,          _x_~cp~ = (_d_/2) · (_F_~aft~ − _F_~fore~) / (_F_~fore~ + _F_~aft~),          _d_ = 60 mm"));
C.push(body("Each cell is read by its own HX711 24-bit bridge amplifier at a gain of 128, excited at 3.3 V. At that excitation a 1 kg cell's roughly 1 mV/V output is about 3.3 µV per gram, and the HX711's input noise (about 50 nV rms at 10 samples per second, per its datasheet) is about 15 mg per sample, or about 3 mg (0.03 mN) after the 2 s average at each step. The smallest predicted reading, 12 mN at H = 20 mm, is about 1.2 g, so noise stays near 0.3 %. Creep and hysteresis in the cells are the larger error, a few tenths of a gram, so every sweep is bracketed by tares and run in both directions, and the session procedure below catches what remains. Because the fin's force acts about 20 mm out from the wall, the cells also see a spanwise moment. An in-situ calibration removes that crosstalk: known masses hung by thread over a pulley from three chord stations on the fin give a 2 × 2 calibration matrix, loaded and unloaded in five steps at the start of each test day."));
C.push(heading("Airspeed and Air Density", 3, 3));
C.push(body("A fixed fan setting is not a fixed airspeed. Screens collect dust, mains voltage moves and room temperature changes air density, and every force coefficient needs the dynamic pressure _q_. A pitot-static tube upstream of the fin feeds a printed 1:10 inclined water manometer, which reads _q_ with no calibration of its own:"));
C.push(eq("_q_ = _ρ_~w~ _g L_ sin _θ_ (1 + _A_~tube~/_A_~cup~),          _V_ = (2 _q_/_ρ_~air~)^1/2^"));
C.push(body("Here _L_ is the column travel along the ramp (sin _θ_ = 0.0995) and _A_~tube~/_A_~cup~ = (3.175/40)^2^ corrects for the reservoir level drop. At 11 m/s, _q_ ≈ 73 Pa, which is 7.4 mm of water head and 74 mm of travel along the tube; reading the meniscus to ±0.5 mm gives about ±0.7 % on _q_. Air density comes from a BME688 sensor's temperature, pressure and humidity, with the vapour partial pressure from the Magnus formula. Before any fin testing, the pitot is traversed across the test-section core at full fan speed to map the velocity distribution, against a uniformity target of 2 % RMS in the core flow."));
C.push(heading("Data Acquisition and Test Procedure", 3, 3));
C.push(body("One Adafruit Metro M4 Express, programmed in the Arduino IDE, runs the whole rig. It drives the cradle servo, reads both HX711s and the BME688, takes the manometer reading typed in by the operator, and streams CSV over USB to a laptop: a raw line for every sample, a marker at each sweep step, and a result line per step carrying normal force, center of pressure, _q_, _V_ and _C_~N~. The servo is powered from its own 5 V wall supply, with its negative tied to the Metro's ground, so servo current never flows on the rail the load cells share. A single session runs as follows:"));
C.push(numbered("Fan off: level the manometer, zero the meniscus, fit the fin, and zero the angle sensor with a printed jig whose V-grooves hold the fin's root leading and trailing edges on the chord line; the 2:1 tooth count fixes the scale."));
C.push(numbered("Tare both cells; on the first session of the day, run the thread-and-pulley calibration."));
C.push(numbered("Fan to its full-speed stop, wait 60 s, read the manometer and enter the travel and fin height."));
C.push(numbered("Sweep -15° to +15° in 0.5° steps (about three minutes)."));
C.push(numbered("Fan off and tare again; the zero shift is the drift record for that sweep."));
C.push(numbered("Repeat in randomised order. The same check-standard fin (double wedge, H = 40 mm) is swept first and last in every session, and a session is flagged if its slope moves by more than 2 %."));
C.push(body("Sewing-thread tufts taped at the leading edge, mid-chord and tip of the fin show attached against separated flow through a clear acrylic top window at 10° to 15°. That is the visual check on hypothesis H2, whether the double wedge's sharp edge sheds a leading-edge vortex. Smoke and a laser sheet can be added for photographs but are not needed for the data."));
C.push(heading("Phase B (Sub-RQ1)", 3, 3));
C.push(body("A second tunnel phase keeps everything upstream of the contraction and replaces the rest with a 200 × 200 × 750 mm acrylic section. The test article is the real 58 mm control tube with all four fins, a printed nose fairing and a removable stabilizer tail section whose slots take 20, 30 or 40 mm blades or blanking plugs, mounted on a three-cell strut balance. The difference in pair side force between stabilizers on and off measures the interference ratio directly; at 7 m/s, 10° and H = 40 mm the model expects 45.1 mN with the stabilizers off and 40.1 mN with the flight 20 mm set. Blockage is about 11 to 12 % and is corrected (Barlow, Rae, & Pope, 1999). Phase B is the part of the program to drop if time or money runs short, in which case Sub-RQ1 rests on the simulation and the flight manoeuvre."));

C.push(heading("Fins & Aerofoil Profiles", 2));
C.push(body("All four sections are printed to the same right-triangular planform, root chord 60 mm, with a 10 mm root boss that takes the hub's cross-pin, so only the cross-section and height change between test articles. The sections are a 2.4 mm flat plate, a 6 % double wedge with sharp leading and trailing edges, and the symmetric NACA 0006 and NACA 0012. Tabulated section data from Abbott and Von Doenhoff (1959), the NACA 0012 characterisation in NACA TN 2502, and the low-speed data of Selig (2003) and Selig, Donovan and Fraser (1989) give the reference behaviour for the NACA sections, framed by the low-Reynolds-number reviews of Lissaman (1983) and Mueller and DeLaurier (2003). The double wedge and flat plate are included because sharp edges are cheap to print and are the sections most likely to show vortex lift at larger deflections (Polhamus, 1966)."));
C.push(body("Fins are printed flat on the bed in PETG-CF at 100 % infill. Layer height, wall count, temperatures and cooling are held fixed across all twenty fins, following the parameter-control approach of Popescu et al. (2018), so print variation does not masquerade as a section effect. Every fin is checked for thickness at three chord stations with calipers before it is tested."));

C.push(heading("Simulations and Modelling", 2));
C.push(body("Every simulated number in this proposal is produced by a version-controlled script from one geometry file, so a change to a mass or dimension reruns the whole chain rather than being edited by hand. The aerodynamic chain runs in five steps. A constant-strength two-dimensional vortex-panel method (Kuethe & Chow, 1998) gives each section's lift slope and pressure distribution. A vortex-lattice model (Katz & Plotkin, 2001) carries that to the low-aspect-ratio three-dimensional fin. Slender-body theory adds the body carry-over factor _K_~W(B)~ (Pitts, Nielsen, & Kaattari, 1957), and a boundary-layer effectiveness factor accounts for the inboard part of the fin sitting in the body's boundary layer. Finally a single rolled-up-vortex model with a body image estimates the downwash the control-fin vortex induces on the stabilizers (Nielsen, 1960). Static margin and drag are cross-checked with the Barrowman (1967) method."));
C.push(...figure("Fig6_authority_predictions.png", "Predicted effect of fin height for the four sections. (a) Normal-force slope of one fin on the body. (b) Phase A normal force at 10° deflection and 11 m/s. (c) Normal force at 10° relative to linear theory, showing the modelled vortex-lift gain of the sharp-edged sections. Shading marks the tunnel test range."));
C.push(body("Those aerodynamic derivatives feed a three-degree-of-freedom flight simulation that integrates the digitised F42-4T thrust curve with a dynamic-pressure-scheduled PID controller, a servo model with rate and travel limits, sensor noise and turbulence-driven gusts. Monte Carlo dispersion over wind, mass, CG and impulse gives the distributions of apogee, tilt, drift and margin. In the reference case (4 m/s wind plus a 4 m/s gust) the controller holds RMS tilt to 0.6°, against 10.8° with the fins locked. The same chain sweeps stabilizer span and azimuth for Sub-RQ1. Ten SimScale RANS cases, covering the Phase A fin at four deflections and four sections and the full rocket with and without stabilizers, sit between the potential-flow models and the tunnel as an independent check."));
C.push(...figure("Fig7_stabilizer_interference.png", "Simulated effect of stabilizer span and azimuth offset (Sub-RQ1). (a) Static margin at liftoff. (b) Interference ratio. (c) Trim angle of attack per unit fin deflection. The circled point is the flown configuration, 20 mm span at 45°."));
C.push(body("The tunnel balance is also modelled at the signal level, covering cell full scale, bridge noise, amplifier rate and quantisation, so the expected reading and its uncertainty at every configuration were known before the rig was built, and any departure of the real rig from that prediction is itself detectable."));

C.push(heading("Airframe & Materials", 2));
C.push(body("All structural parts are printed on a Bambu Lab printer with a 0.4 mm hardened-steel nozzle, and every part fits a 256 mm cubic build volume. Material follows thermal exposure and load: foamed ASA (ASA-Aero) for the four airframe tubes and the nose, where neither motor heat nor ejection gas reaches; PETG-CF for the control fins, stabilizers, hubs and avionics spine, which carry the aerodynamic loads; and fire-retardant polycarbonate (PC-FR) for the plenum, motor mount, retainer and ejection bypass tube, which see the ejection gas. Material is held fixed across the program and is not a research variable. A full digital fit check of every printed part, servo, board and harness in the assembled vehicle reports zero interferences with the fins swept through ±15°."));
C.push(body("The servo ring sets the airframe diameter. Four EMAX ES9251 II servos bolt by their mounting tabs to pads printed into the control-tube wall with their output shafts pointing radially outward into the fin hubs, and the printed bypass tube runs down the centreline 0.25 mm clear of the servo bases. A 1.6 mm wall then gives the 58 mm outer diameter."));

C.push(heading("Flight Computer Systems & Avionics", 2));
C.push(body("The flight computer is a Raspberry Pi Pico 2 W (RP2350, 150 MHz, its radio left off), mounted on standoffs on an avionics spine that slides over the bypass tube. One loop on one core does everything: it reads the sensors and services the card on every pass and runs the control step (attitude update, control law, servo command) every 5 ms, which takes a few hundred microseconds. A BNO085 inertial unit provides attitude and acceleration; its ±8 g accelerometer saturates for about the first 0.2 s of the F42-4T burn, and for those samples the axial channel substitutes a thrust-curve model so the velocity estimate does not drift low. A BMP388 barometer is the primary altimeter at 50 Hz, and a BME688 supplies the launch-site temperature and humidity used to compute measured air density for the dynamic pressure and the density reconstruction. The inertial unit has an I²C bus to itself and the two barometers share the second. Every channel is logged as 96-byte records at 100 Hz to a microSD card on an Adafruit 4682 breakout, the only record of the flight: the file is pre-allocated and written from a RAM buffer only when the card is idle, so card delays never reach the control loop. There is no radio. The rocket is armed on the pad by holding a recessed button through the airframe wall for two seconds, after which it zeroes its attitude reference and refuses to arm unless the log, sensors, battery and rail angle all check out."));
C.push(body("Power comes from a two-cell 450 mAh LiPo through a Pololu MOSFET slide switch. Two Adafruit MPM3610 buck regulators make 5 V: one for the Pico, whose own regulator feeds the sensors and the card, and one for the four servos, which are rated for 4.5 to 6 V. A 470 µF capacitor on the servo rail absorbs start-up transients, and a resistive divider reports pack voltage. The mission budget is 35 mAh, a 6.9× margin on the pack. The control law is a PID controller per axis whose gains scale with measured dynamic pressure (proportional 4.5, integral 1.0, derivative 0.8 at a 1.5 kPa reference), with output limited to the ±15° fin travel. Control arms at rail exit, and a fault centres the fins, leaving the vehicle passively stable at 1.44 calibers."));

C.push(heading("Flight Test Plan & Authority Manoeuvre", 2));
C.push(body("Three flights fly the selected section P* at H* - 5, H* and H* + 5 mm, swapping only the control fins between flights. Authority is measured rather than inferred. Starting 250 ms after burnout, the firmware runs a 2.6 s programme on each axis in turn: a ±5° doublet added to the controller output, from which it fits the pitch dynamics by least squares,"));
C.push(eq("_ω̇_ = _c_ + _aθ_ + _m_~q~ _ω_ + _b δ_,          _b_ = _M_~δ~/_I_,          _C_~mδ~ = _b I_ / (_q̄ A_~ref~ _d_)"));
C.push(body("followed by a 1° attitude step that records the achieved angle, the 63 % rise time, overshoot and fin deflection per degree. The programme only starts if dynamic pressure is at least 800 Pa, tilt is under 10° and altitude is above 30 m, and it aborts back to plain attitude hold if the vehicle wanders more than 8°. Across 40 simulated flights in 0 to 7 m/s of wind, the fitted _M_~δ~/_I_ lands within about ±14 % (one standard deviation) of the model, and the flight firmware's manoeuvre code, compiled for the desktop and replayed against simulated flights, reproduces the simulator's numbers to three decimal places. Because the estimator has already been checked against the simulator, a flight value outside that band points to an error in the aerodynamic model. Three flights give six axis-points against the tunnel-calibrated prediction for Sub-RQ2."));
C.push(...figure("Fig8_authority_manoeuvre.png", "Simulated authority manoeuvre on the F42-4T in a 4 m/s wind. (a) Tilt and commanded attitude. (b) Fin-pair deflection and injected doublet. (c) Pitch rate, with dynamic pressure on the right axis. Dashed vertical line: programme start, 250 ms after burnout.", 5.6));

C.push(heading("Recovery System", 2));
C.push(body("Recovery uses the motor's own ejection charge, with no separate altimeter, battery or pyrotechnic circuit. The F42-4T's 4 s delay fires about 0.9 s before the predicted apogee, the closest available delay to the 4.87 s optimum. The charge vents into a gas gallery under the plenum bulkhead and runs 205 mm up the centreline through the printed PC-FR bypass tube, past the avionics, into the recovery bay. In the internal-ballistics model a 0.3 g charge peaks at 177 kPa in the bay and pushes on the friction-fit nose with 418 N, while the hoop stress in the 1.0 mm tube wall stays near 5 MPa against a material strength roughly ten times higher. The nose pops, deploying a 24 in rip-stop parachute tied to a printed anchor on the recovery-bay floor by aramid shock cord. Descent is about 6.3 m/s. Because the motor's charge mass is not published, a ground ejection test with the full stack sets the nose fit before any flight."));

C.push(heading("Data Analysis", 2));
C.push(body("Tunnel data are corrected for solid and wake blockage and, in Phase A, for the reflection plane (Barlow, Rae, & Pope, 1999; Maskell, 1963). Slopes _C_~Nδ~ are fitted by least squares over ±10° with 95 % confidence intervals, and curvature from a cubic fit out to ±15°. A two-way ANOVA on the Phase A slopes separates the section effect, the height effect and their interaction. For Sub-RQ1, the interference ratio is reported with its confidence interval at each span and regressed on span. For Sub-RQ2, each configuration's prediction error is reported alongside the Spearman rank correlation between simulated and measured authority; the interference scale factor is then fitted to Phase B, and the three flights are compared with the model before and after that fit. All raw logs, reduced data and analysis scripts are archived in the same repository as the design files."));

C.push(heading("Safety & Compliance", 2));
C.push(body("All flights follow the NAR (2023) model rocket safety code, with a NAR representative or similarly qualified adult present at each launch. The F42-4T is a single-use F motor with about 27 g of propellant, and the 785 g liftoff mass is well under the FAA Class 1 model rocket limits of 1,500 g and 125 g of propellant (14 CFR Part 101), so no waiver or high-power certification is needed. Range procedures include remote ignition, igniter installation last at the pad, and a fail-safe that centres all four fins on any control fault. The 176 m apogee is within the NAR site dimension for an F motor; the field is confirmed with the range safety officer. On the bench, the tunnel fan runs behind its guard, the flight packs are charged in LiPo bags to no more than 4.20 V per cell, and nothing is placed in the test section while the fan is running."));

C.push(heading("Expected Outcomes", 1));
C.push(body("We expect the main result to be a measured map of control authority against section and height for small triangular fins at low Reynolds numbers, with confidence intervals tight enough to say whether the section matters. Our working prediction is that the linear slopes of the four sections will sit within a few percent of each other and that height will dominate, with the sections separating, if at all, past about 8° where sharp edges may gain vortex lift. If the double wedge or the flat plate does show that gain, the cheapest sections to print are also the best ones for hobby-scale fin control. If none of the sections separate, builders can choose the section for printability and strength and spend their effort on fin height instead."));
C.push(body("The two sub-questions add a measured stabilizer penalty and a scored comparison of the simulation chain against both the tunnel and flight, so other teams know how far to trust a low-order model of a fin-controlled rocket before they build one. The modified tunnel and its two-cell balance can be rebuilt by other teams for about $336 in parts, controller and sensors included. We plan to release the tunnel dataset, the flight logs, the CAD and the analysis code through a public repository under open-source licences."));

// ---- References ----
const REFS = [
  "Abbott, I. H., & Von Doenhoff, A. E. (1959). _Theory of wing sections: Including a summary of airfoil data_. Dover Publications. https://store.doverpublications.com/0486605868.html",
  "Adafruit Industries. (n.d.). _Adafruit Metro M4 feat. Microchip ATSAMD51_ (Product ID 3382). https://www.adafruit.com/product/3382",
  "Avia Semiconductor. (n.d.). _HX711: 24-bit analog-to-digital converter (ADC) for weigh scales_ [Datasheet].",
  "Barlow, J. B., Rae, W. H., & Pope, A. (1999). _Low-speed wind tunnel testing_ (3rd ed.). John Wiley & Sons.",
  "Barrowman, J. S. (1967). _The practical calculation of the aerodynamic characteristics of slender finned vehicles_ (NASA NTRS accession 20010047838). https://ntrs.nasa.gov/citations/20010047838",
  "Barrowman, J. S. (1967). _The theoretical prediction of the center of pressure_. Apogee Rockets. https://www.apogeerockets.com/downloads/barrowman_report.pdf",
  "Bell, J. H., & Mehta, R. D. (1988). _Contraction design for small low-speed wind tunnels_ (NASA CR-182747). https://ntrs.nasa.gov/api/citations/19880012661/downloads/19880012661.pdf",
  "Federal Aviation Administration. (n.d.). Title 14 CFR Part 101, Subpart C, Amateur rockets.",
  "Hofferth, J. (2025). Modular wind tunnel for STEM education. _AIAA SciTech 2025 Forum_. https://doi.org/10.2514/6.2025-2630",
  "Katz, J., & Plotkin, A. (2001). _Low-speed aerodynamics_ (2nd ed.). Cambridge University Press. https://doi.org/10.1017/CBO9780511810329",
  "Kuethe, A. M., & Chow, C.-Y. (1998). _Foundations of aerodynamics: Bases of aerodynamic design_ (5th ed.). John Wiley & Sons.",
  "Lissaman, P. B. S. (1983). Low-Reynolds-number airfoils. _Annual Review of Fluid Mechanics, 15_, 223–239. https://bpb-us-w1.wpmucdn.com/sites.usc.edu/dist/4/81/files/2023/05/lissaman-arfm-1983.pdf",
  "Maskell, E. C. (1963). _A theory of the blockage effects on bluff bodies and stalled wings in a closed wind tunnel_ (ARC R&M 3400). Aeronautical Research Council. https://reports.aerade.cranfield.ac.uk/handle/1826.2/3452",
  "Mehta, R. D., & Bradshaw, P. (1979). Design rules for small low-speed wind tunnels. _Aeronautical Journal, 83_(827), 443–449. https://doi.org/10.1017/S0001924000031985",
  "Mueller, T. J., & DeLaurier, J. D. (2003). Aerodynamics of small vehicles. _Annual Review of Fluid Mechanics, 35_, 89–111. https://doi.org/10.1146/annurev.fluid.35.101101.161102",
  "National Advisory Committee for Aeronautics. (1951). _Aerodynamic characteristics of NACA 0012 airfoil section at angles of attack from 0° to 180°_ (NACA TN 2502). https://ntrs.nasa.gov/citations/19930082895",
  "National Association of Rocketry. (2023). _NAR safety code and motor classification standards_. https://www.nar.org/safety-information/",
  "Nielsen, J. N. (1960). _Missile aerodynamics_. McGraw-Hill.",
  "Pitts, W. C., Nielsen, J. N., & Kaattari, G. E. (1957). _Lift and center of pressure of wing-body-tail combinations at subsonic, transonic, and supersonic speeds_ (NACA Report 1307). https://ntrs.nasa.gov/citations/19930091008",
  "Polhamus, E. C. (1966). _A concept of the vortex lift of sharp-edge delta wings based on a leading-edge-suction analogy_ (NASA TN D-3767). https://ntrs.nasa.gov/citations/19670003842",
  "Pope, A., & Harper, J. J. (1966). _Low-speed wind tunnel testing_. Wiley. https://archive.org/details/lowspeedwindtunn0000pope",
  "Popescu, D., Zapciu, A., Amza, C., Baciu, F., & Marinescu, R. (2018). FDM process parameters influence over the mechanical properties of polymer specimens. _Polymer Testing, 69_, 157–166. https://doi.org/10.1016/j.polymertesting.2018.05.020",
  "Sahoo, S. (2026, April 11). _WYVERN PTD portal_. https://wyvern-ptd-portal.base44.app/",
  "Selig, M. S. (2003). _UIUC airfoil data site_. University of Illinois at Urbana-Champaign. https://m-selig.ae.illinois.edu/ads.html",
  "Selig, M. S., Donovan, J. F., & Fraser, D. B. (1989). _Airfoils at low speeds_ (Soartech 8). SoarTech Publications. https://m-selig.ae.illinois.edu/ads/afplots/airfoils_at_low_speeds.pdf",
];
C.push(new Paragraph({ children: [new PageBreak()] }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new Bookmark({ id: "refs", children: [new TextRun({ text: "References", bold: true })] })] }));
tocEntries.push({ id: "refs", text: "References", level: 1 });
for (const r of REFS) C.push(new Paragraph({ children: runs(r), indent: { left: 720, hanging: 720 }, spacing: { line: 480, after: 0 } }));

// ---- Past abstracts (unchanged from the earlier proposal) ----
C.push(new Paragraph({ children: [new PageBreak()] }));
C.push(heading("Past Abstracts", 1));
const ABS = [
  ["Swaroop Sahoo", "Evaluating the Efficiency, Practicality, and Effectiveness of Emission/Reception-Capable LiDAR and RaDAR Detection Systems in Autonomous Navigation",
   "Autonomous vehicles are swiftly evolving from experimental prototypes to a social norm. Advanced emitter-based sensor technologies, including LiDAR and RaDAR, are at the heart of these developments. This research has explored, through an analysis of raw performance, what is best for autonomous navigation systems. With an R2 Smart Car, we had extensive testing with the setup to ascertain detection capability across various terrains and conditions. We hypothesized that if an autonomous vehicle employs LiDAR sensors rather than RaDAR sensors, it will realize better detection owing to its higher resolution, precision, and finer performance for short-range distances. During our trials, LiDAR always outperformed RaDAR concerning precision and the recognition of objects within close and medium ranges. However, RaDAR showed better performance in adverse weather conditions, proving that it is more resistant to environmental stressors. Despite LiDAR's superior detection performance, several challenges were identified: higher cost, greater energy demands, and limited field of view. RaDAR, though less effective in performance, claims advantages regarding cost-efficiency, weather robustness, and lower battery requirements. These considerations become critical in balancing efficiency against function while designing a self-driving vehicle. This experiment shows that such a multi-sensor approach is needed to put together the strengths of LiDAR and RaDAR to attain maximum detection accuracy and system reliability. Such integration will be imperative for making robust, cost-effective autonomous systems that are capable of navigating diverse real-world conditions and thereby fostering the feasibility and safety of autonomous vehicles in mainstream society."],
  ["Chris Liu", "In-Situ resource utilization-derived iron perchlorate redox flow battery for Mars: electrolyte characterization and extreme cold performance validation",
   "Sustained habitation on Mars demands robust energy storage systems capable of reliable operation under extreme cold, especially during night and dust storm periods that render conventional lithium-ion batteries ineffective. This work introduces an in-situ resource utilization (ISRU) strategy for constructing iron perchlorate redox flow batteries, fully leveraging Martian-available materials to achieve extreme cold resilience. Eutectic freezing points and ionic conductivities of three Martian-available electrolytes (iron sulfate, iron chloride, and iron perchlorate) were systematically characterized. Iron perchlorate aqueous solution at 45 wt% displayed a eutectic freezing point of −78 °C, outperforming iron chloride (−55 °C) and iron sulfate (−10 °C). Laboratory-scale single cells were developed via computer-aided design and 3D printing, then tested under simulated Martian low-temperature conditions. The iron perchlorate system maintained 56% of its room-temperature capacity at −50 °C and remained operational at −70 °C, while iron chloride cells retained only 25% at −50 °C and lost functionality at lower temperatures. Electrochemical impedance measurements revealed that, although electrolyte resistance increases at lower temperature, charge transfer resistance becomes the dominant limiting factor under extreme cold. The results establish that ISRU-derived iron perchlorate flow batteries offer a feasible, cold-resilient solution for reliable energy storage in future Mars surface operations and settlement, with further performance gains likely through advanced perchlorate brine formulation."],
  ["Allison Hong", "The Effects of Different Types of Synthetic Retinoids on Bacteria Inhibition: Antibacterial Properties",
   "Retinoids are a group of compounds including naturally occurring and synthetic vitamin A metabolites and analogs. The two most common synthetic vitamin derivatives are Tretinoin and Adapelene. This experiment aims to determine the inhibitory properties of Adapalene and Tretinoin on Escherichia Coli. K-12. We hypothesized that the tretinoin group would have a greater inhibitory effect than the adapalene group. We created agar petri dishes and swabbed E. coli. The dishes were incubated for six days in total. Adapalene Gel 0.1% and Tretinoin Gel 0.1% were measured and diluted with Methyl Alcohol. The solutions were added on day two of incubation. The bacterial growth was counted after the incubation period for the number of colonies formed on each dish. The retinoids, especially adapalene, were found to promote the growth of bacteria instead of inhibiting its growth. The data of all three groups represent a polynomial regression, with adapalene and tretinoin exhibiting an exponential pattern and the control group exhibiting a logarithmic pattern. Each result was evaluated with the statistical analysis of a t-test, and all data was significant and not random. Further research is suggested to better understand the retinoids' effects on bacterial growth and inhibition."],
];
ABS.forEach(([name, title, text], i) => {
  if (i > 0) C.push(new Paragraph({ children: [new PageBreak()] }));
  C.push(heading(name, 2));
  C.push(new Paragraph({ spacing: { line: 480, after: 0 }, children: [new Bookmark({ id: "abs" + i, children: [new TextRun({ text: title, bold: true })] })] }));
  tocEntries.push({ id: "abs" + i, text: title, level: 3 });
  C.push(new Paragraph({ children: [new TextRun(text)], indent: { firstLine: 720 }, spacing: { line: 480, after: 0 } }));
});

// ---- TOC (manual, two-pass page numbers) ----
function tocPara(e) {
  const indent = e.level === 1 ? 0 : e.level === 2 ? 360 : 720;
  const pg = PAGES[e.text] !== undefined ? String(PAGES[e.text]) : "0";
  return new Paragraph({
    indent: { left: indent }, spacing: { after: 0 },
    tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
    children: [new InternalHyperlink({ anchor: e.id, children: [
      new TextRun({ text: e.text, style: "Hyperlink" }), new TextRun({ text: "\t" + pg, style: "Hyperlink" })] })],
  });
}
// heading levels 3 inside the methodology (Force Balance etc.) stay out of the TOC, like the original
const TOC = [new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new Bookmark({ id: "toc", children: [new TextRun("Table of Contents")] })] })];
const tocList = [{ id: "toc", text: "Table of Contents", level: 1 }]
  .concat(tocEntries.filter(e => !(e.level === 3 && !e.id.startsWith("abs"))));
for (const e of tocList) TOC.push(tocPara(e));
TOC.push(new Paragraph({ children: [new PageBreak()] }));
fs.writeFileSync(path.join(HERE, "toc_entries.json"), JSON.stringify(tocList.map(e => e.text), null, 1));

// ---- title page ----
const TITLE = "GTR70E WYVERN (Widespread Yield Variable Engagement Rapid-response Neutralizer): Engineering Design and Experimental Validation of Aerofoil Section and Fin Height Effects on the Control Authority of Servo-Actuated Fins in a Subscale Single-Stage Solid-Fuelled Prototype Rocket Demonstrator";
const titlePage = [
  ...Array.from({ length: 12 }, () => new Paragraph({ children: [] })),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: 480 }, children: [new TextRun({ text: TITLE, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, line: 480 }, children: [new TextRun("Allison Hong, Chris Liu, Swaroop K. Sahoo")] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, line: 480 }, children: [new TextRun("October 24th, 2026")] }),
];

const header = new Header({ children: [new Paragraph({
  tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
  children: [new TextRun("GTR70E WYVERN Flight Demonstrator Project"), new TextRun("\t"), new TextRun({ children: [PageNumber.CURRENT] })] })] });

const page = { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440, header: 720 } };
const doc = new Document({
  creator: "Swaroop Sahoo", title: "GTR70E WYVERN Research Proposal",
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 40, bold: true }, paragraph: { spacing: { before: 240, after: 60 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 240, after: 40 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, italics: true }, paragraph: { spacing: { before: 160, after: 20 }, outlineLevel: 2, keepNext: true } },
    ],
    characterStyles: [{ id: "Hyperlink", name: "Hyperlink", run: { color: "1155CC", underline: { type: "single" } } }],
  },
  numbering: { config: [
    { reference: "dash", levels: [{ level: 0, format: LevelFormat.BULLET, text: "-", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [
    { properties: { page }, children: titlePage },
    { properties: { page: { ...page, pageNumbers: { start: 1 } } }, headers: { default: header }, children: [...TOC, ...C] },
  ],
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(path.join(HERE, "GTR70E_WYVERN_Research_Proposal.docx"), b);
  console.log("wrote docx");
});
