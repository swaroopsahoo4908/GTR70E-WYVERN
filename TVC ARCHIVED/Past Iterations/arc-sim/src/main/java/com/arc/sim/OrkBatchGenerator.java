package com.arc.sim;

import info.openrocket.core.file.GeneralRocketSaver;
import info.openrocket.core.rocketcomponent.MassComponent;
import info.openrocket.core.rocketcomponent.Parachute;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.TrapezoidFinSet;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

/**
 * ENGINE 4: OrkBatchGenerator
 *
 * Takes ONE base .ork file and a grid of design-parameter values -- ballast mass, fin height, fin
 * sweep, and parachute center hole radius (the same four physical knobs Engine 3 solves for) --
 * and writes out EVERY combination as its own standalone .ork file.
 *
 * Two modes, both producing a linking "manifest.csv" alongside the generated .ork files:
 *
 *   1. PURE VARIANT GENERATION (no [simCheck] block in the grid config): exactly the original
 *      behavior -- no simulation runs, files are written as fast as OpenRocket can save them.
 *      The manifest just records which design-parameter values ended up in which filename.
 *
 *   2. SIMULATE + CHECK AGAINST TARGETS (targetApogeeM/targetTimeMinS/targetTimeMaxS + one fixed
 *      atmosphere/site are all present in the config -- the exact same target+atmosphere shape
 *      Engine 3 takes): each variant is ALSO simulated under that one fixed condition before being
 *      saved, so (a) the saved .ork's own Simulation 1 already has real simulated apogee/flight-time
 *      data cached in it (open it in the OpenRocket GUI and the numbers are already there -- the
 *      same idea as Engine 1's runs, just applied per design variant instead of per atmosphere
 *      sample), and (b) the manifest records apogee_m/flight_time_s/meets_apogee/meets_time/
 *      meets_both for every variant, so you can sort/filter the manifest to find which design
 *      variants actually hit the targets without opening any of the 100s of individual files.
 *
 * Either way, "manifest.csv" (written into the same batch subfolder as the .ork files) is the
 * link between each row and its file: an ork_filename column gives the exact filename, sitting
 * right next to it in the same folder.
 */
public class OrkBatchGenerator {

    private static final double IN_TO_M = 0.0254;
    private static final long DEFAULT_MAX_FILES_SAFETY = 5000;
    private static final double APOGEE_TOLERANCE_M = 0.25;

    /** One resolved grid: any axis may be null, meaning "don't vary -- keep the base file's value". */
    public static class BatchConfig {
        public GridAxis ballastKg;      // total ballast mass, kg
        public GridAxis finHeightM;     // fin height, m
        public GridAxis finSweepM;      // fin sweep, m
        public GridAxis holeRadiusIn;   // parachute center spill-hole radius, INCHES (matches Engine 3's GUI units)
        public long maxFilesSafety = DEFAULT_MAX_FILES_SAFETY;
        public SimCheck simCheck; // null unless the config's [simCheck] properties are all present

        public long totalCombos() {
            return count(ballastKg) * count(finHeightM) * count(finSweepM) * count(holeRadiusIn);
        }

        private static long count(GridAxis axis) {
            return axis == null ? 1 : axis.count();
        }
    }

    /**
     * The same target+atmosphere shape Engine 3 (DesignSolver) takes -- one fixed condition to
     * simulate every generated variant under, plus the apogee/flight-time window to check each
     * variant against. Either ALL of these are set (simulate every variant) or none are (pure
     * variant generation, Engine 4's original behavior).
     */
    public static class SimCheck {
        public double targetApogeeM;
        public double targetTimeMinS;
        public double targetTimeMaxS;
        public LaunchSite site;
        public double windAvgMs;
        public double windStdDevMs;
        public double turbulencePct;
        public double windDirDeg;
        public double tempC;
        public double pressureMbar;

        EnvironmentPoint toEnvironmentPoint() {
            return new EnvironmentPoint(windAvgMs, windStdDevMs, turbulencePct / 100.0, windDirDeg, tempC, pressureMbar, site);
        }
    }

    public static BatchConfig loadConfig(File propsFile) throws Exception {
        Properties p = new Properties();
        try (FileInputStream in = new FileInputStream(propsFile)) {
            p.load(in);
        }
        BatchConfig cfg = new BatchConfig();
        cfg.ballastKg = optionalAxis(p, "ballastKg");
        cfg.finHeightM = optionalAxis(p, "finHeightM");
        cfg.finSweepM = optionalAxis(p, "finSweepM");
        cfg.holeRadiusIn = optionalAxis(p, "holeRadiusIn");
        cfg.maxFilesSafety = Long.parseLong(p.getProperty("maxFilesSafety", String.valueOf(DEFAULT_MAX_FILES_SAFETY)));
        cfg.simCheck = optionalSimCheck(p);
        return cfg;
    }

    /** Returns null (axis not varied) unless ALL of prefix.min/.max/.step are present in the file. */
    private static GridAxis optionalAxis(Properties p, String prefix) {
        String min = p.getProperty(prefix + ".min");
        String max = p.getProperty(prefix + ".max");
        String step = p.getProperty(prefix + ".step");
        if (min == null && max == null && step == null) return null;
        if (min == null || max == null || step == null) {
            throw new IllegalArgumentException("Incomplete axis '" + prefix + "' in config -- need all of " +
                    prefix + ".min, " + prefix + ".max, " + prefix + ".step, or none of them (to leave that " +
                    "parameter unvaried, keeping the base file's value).");
        }
        double stepVal = Double.parseDouble(step);
        if (stepVal <= 0) {
            throw new IllegalArgumentException(prefix + ".step must be > 0, got: " + step);
        }
        return new GridAxis(Double.parseDouble(min), Double.parseDouble(max), stepVal);
    }

    /** Returns null (no simulation -- pure variant generation) unless ALL simCheck.* keys are present. */
    private static SimCheck optionalSimCheck(Properties p) {
        String[] keys = {"simCheck.targetApogeeM", "simCheck.targetTimeMinS", "simCheck.targetTimeMaxS",
                "simCheck.site", "simCheck.windAvgMs", "simCheck.windStdDevMs", "simCheck.turbulencePct",
                "simCheck.windDirDeg", "simCheck.tempC", "simCheck.pressureMbar"};
        int present = 0;
        for (String k : keys) if (p.getProperty(k) != null) present++;
        if (present == 0) return null;
        if (present < keys.length) {
            StringBuilder missing = new StringBuilder();
            for (String k : keys) if (p.getProperty(k) == null) missing.append(k).append(" ");
            throw new IllegalArgumentException("Partial simCheck.* config -- either set ALL of them (to simulate " +
                    "every variant against one fixed atmosphere + target, same shape as Engine 3) or NONE of them " +
                    "(pure variant generation, no simulation). Missing: " + missing);
        }
        try {
            SimCheck sc = new SimCheck();
            sc.targetApogeeM = Double.parseDouble(p.getProperty("simCheck.targetApogeeM"));
            sc.targetTimeMinS = Double.parseDouble(p.getProperty("simCheck.targetTimeMinS"));
            sc.targetTimeMaxS = Double.parseDouble(p.getProperty("simCheck.targetTimeMaxS"));
            sc.site = LaunchSite.parse(p.getProperty("simCheck.site"));
            sc.windAvgMs = Double.parseDouble(p.getProperty("simCheck.windAvgMs"));
            sc.windStdDevMs = Double.parseDouble(p.getProperty("simCheck.windStdDevMs"));
            sc.turbulencePct = Double.parseDouble(p.getProperty("simCheck.turbulencePct"));
            sc.windDirDeg = Double.parseDouble(p.getProperty("simCheck.windDirDeg"));
            sc.tempC = Double.parseDouble(p.getProperty("simCheck.tempC"));
            sc.pressureMbar = Double.parseDouble(p.getProperty("simCheck.pressureMbar"));
            return sc;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Could not parse one of the simCheck.* values in the config: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: OrkBatchGenerator <input.ork> <batch_grid.properties> [outputParentDir] [--force]");
            System.err.println("  outputParentDir defaults to the input .ork file's own folder if omitted.");
            System.err.println("  All generated .ork files land together in a new subfolder: <orkName>_batch_<timestamp>/");
            System.err.println("  A manifest.csv linking each .ork's filename to its parameters (and, if the config's");
            System.err.println("  simCheck.* properties are set, its simulated apogee/flight-time vs target) lands there too.");
            System.exit(1);
        }
        File outParentDir = (args.length > 2 && !args[2].equals("--force")) ? new File(args[2]) : null;
        boolean force = java.util.Arrays.asList(args).contains("--force");
        try {
            run(new File(args[0]), new File(args[1]), outParentDir, force,
                    (processed, total, eta) -> {
                        if (processed % 50 == 0 || processed == total) {
                            System.out.printf("...%,d / %,d files written -- ETA %s%n", processed, total, EtaTracker.formatDuration(eta));
                        }
                    });
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    /** Backward-compatible overload with no progress reporting. */
    public static File run(File orkFile, File configFile, File outParentDir, boolean force) throws Exception {
        return run(orkFile, configFile, outParentDir, force, ProgressListener.NONE);
    }

    /**
     * Programmatic entry point (no System.exit) -- safe to call from the GUI or other Java code.
     * outParentDir is the folder the NEW batch subfolder gets created inside (may be null to
     * default to the ork file's own folder). Returns the batch subfolder all the generated .ork
     * files (and manifest.csv) were written into.
     */
    public static File run(File orkFile, File configFile, File outParentDir, boolean force, ProgressListener listener) throws Exception {
        BatchConfig cfg = loadConfig(configFile);
        long total = cfg.totalCombos();
        System.out.printf("Grid: ballastKg=%d x finHeightM=%d x finSweepM=%d x holeRadiusIn=%d%n",
                axisCount(cfg.ballastKg), axisCount(cfg.finHeightM), axisCount(cfg.finSweepM), axisCount(cfg.holeRadiusIn));
        System.out.printf("TOTAL FILES: %,d%n", total);
        System.out.println(cfg.simCheck != null
                ? "simCheck configured -- each variant will ALSO be simulated under the configured atmosphere and " +
                  "checked against the target apogee/flight-time window (same targets Engine 3 uses)."
                : "No simCheck configured -- pure variant generation, no simulation (set simCheck.* in the grid " +
                  "config to also simulate + check targets).");

        if (total > cfg.maxFilesSafety && !force) {
            throw new IllegalStateException(String.format(
                    "Refusing to run: %,d files exceeds the safety cap of %,d (set in the grid config as " +
                    "maxFilesSafety). Coarsen the increments, raise maxFilesSafety, or force the run.",
                    total, cfg.maxFilesSafety));
        }
        if (total == 1) {
            System.out.println("NOTE: no axes set in the config (or every axis collapses to a single point) -- " +
                    "this will write exactly one .ork, an unmodified copy of the base file.");
        }

        File batchDir = OutputNaming.uniqueDir(orkFile, outParentDir, "batch");
        EtaTracker eta = new EtaTracker(total);

        double[] ballastVals = values(cfg.ballastKg);
        double[] finHeightVals = values(cfg.finHeightM);
        double[] finSweepVals = values(cfg.finSweepM);
        double[] holeRadiusVals = values(cfg.holeRadiusIn);

        File manifestFile = new File(batchDir, "manifest.csv");
        long written = 0;
        long meetsBoth = 0;
        try (PrintWriter manifest = new PrintWriter(new FileWriter(manifestFile))) {
            writeManifestHeader(manifest, cfg);

            outer:
            for (double ballastKg : ballastVals) {
                for (double finHeightM : finHeightVals) {
                    for (double finSweepM : finSweepVals) {
                        for (double holeRadiusIn : holeRadiusVals) {
                            if (Thread.currentThread().isInterrupted()) {
                                System.out.println("Cancelled after " + written + " / " + total + " files.");
                                break outer;
                            }
                            VariantResult vr = writeVariant(orkFile, batchDir, cfg, ballastKg, finHeightM, finSweepM, holeRadiusIn);
                            writeManifestRow(manifest, cfg, vr);
                            if (vr.meetsBoth) meetsBoth++;
                            written++;
                            if (written % 25 == 0 || written == total) {
                                listener.onProgress(written, total, eta.etaSeconds(written));
                            }
                        }
                    }
                }
            }
        }

        System.out.println("Wrote " + written + " .ork file(s) to " + batchDir.getAbsolutePath());
        System.out.println("Wrote manifest linking each .ork to its parameters" +
                (cfg.simCheck != null ? " and simulated apogee/flight-time" : "") + ": " + manifestFile.getAbsolutePath());
        if (cfg.simCheck != null) {
            System.out.printf("%,d / %,d variant(s) met BOTH targets (apogee %.2f m +/- %.2f m, time %.1f-%.1f s).%n",
                    meetsBoth, written, cfg.simCheck.targetApogeeM, APOGEE_TOLERANCE_M,
                    cfg.simCheck.targetTimeMinS, cfg.simCheck.targetTimeMaxS);
        }
        return batchDir;
    }

    /** One generated variant's outcome, used both to save the .ork and to write its manifest row. */
    private static final class VariantResult {
        String fileName;
        boolean ballastVaried, finHeightVaried, finSweepVaried, holeRadiusVaried;
        double ballastKg, finHeightM, finSweepM, holeRadiusIn;
        boolean simulated;
        boolean ok;
        double apogeeM, flightTimeS;
        boolean meetsApogee, meetsTime, meetsBoth;
        String error;
    }

    /** Loads a fresh copy of the base rocket, applies whichever of the 4 knobs are being varied, optionally
     *  simulates it under the configured atmosphere, and saves it. */
    private static VariantResult writeVariant(File orkFile, File batchDir, BatchConfig cfg,
                                               double ballastKg, double finHeightM, double finSweepM, double holeRadiusIn) throws Exception {
        SimRunner runner = new SimRunner(orkFile); // fresh document per file -- no shared mutable state across variants
        Rocket rocket = runner.getDocument().getRocket();

        VariantResult vr = new VariantResult();
        vr.ballastKg = ballastKg; vr.finHeightM = finHeightM; vr.finSweepM = finSweepM; vr.holeRadiusIn = holeRadiusIn;

        StringBuilder nameSuffix = new StringBuilder();

        if (cfg.ballastKg != null) {
            vr.ballastVaried = true;
            List<MassComponent> ballastComps = RocketComponents.findBallastComponents(rocket);
            new RocketComponents.BallastControl(ballastComps).setTotalKg(ballastKg);
            nameSuffix.append("_ballast").append(fmt(ballastKg * 1000)).append("g");
        }
        if (cfg.finHeightM != null) {
            vr.finHeightVaried = true;
            TrapezoidFinSet finSet = RocketComponents.findFinSet(rocket);
            finSet.setHeight(finHeightM);
            nameSuffix.append("_finH").append(fmt(finHeightM * 1000)).append("mm");
        }
        if (cfg.finSweepM != null) {
            vr.finSweepVaried = true;
            TrapezoidFinSet finSet = RocketComponents.findFinSet(rocket);
            finSet.setSweep(finSweepM);
            nameSuffix.append("_finSweep").append(fmt(finSweepM * 1000)).append("mm");
        }
        if (cfg.holeRadiusIn != null) {
            vr.holeRadiusVaried = true;
            Parachute chute = RocketComponents.findMainParachute(rocket);
            new RocketComponents.ParachuteHoleControl(chute).setHoleRadiusM(holeRadiusIn * IN_TO_M);
            nameSuffix.append("_hole").append(fmt(holeRadiusIn)).append("in");
        }

        // OutputNaming.uniqueFile is built for "<orkBase>_<simType>_<timestamp>", which isn't
        // quite the shape we want per-file here (values embedded, whole batch shares one
        // timestamp via the folder name) -- so this engine builds its own base name, but reuses
        // the exact same collision-avoidance loop so nothing inside the batch can overwrite
        // anything else either.
        String base = OutputNaming.baseName(orkFile) + nameSuffix;
        File outFile = new File(batchDir, base + ".ork");
        int suffix = 2;
        while (outFile.exists()) {
            outFile = new File(batchDir, base + "_" + suffix + ".ork");
            suffix++;
        }

        if (cfg.simCheck != null) {
            // This is the "generate the orks the way Engine 1 would -- but for design variants
            // instead of atmosphere samples" idea: actually run the simulation under the fixed
            // target atmosphere before saving, so the saved .ork's own Simulation 1 has real
            // cached flight data in it (open it in the OpenRocket GUI and the apogee/flight-time
            // are already there), not just design values nobody's checked yet.
            vr.simulated = true;
            SimRunner.FlightResult r = runner.run(cfg.simCheck.toEnvironmentPoint());
            vr.ok = r.ok;
            if (r.ok) {
                vr.apogeeM = r.apogeeM;
                vr.flightTimeS = r.flightTimeS;
                vr.meetsApogee = Math.abs(r.apogeeM - cfg.simCheck.targetApogeeM) <= APOGEE_TOLERANCE_M;
                vr.meetsTime = r.flightTimeS >= cfg.simCheck.targetTimeMinS && r.flightTimeS <= cfg.simCheck.targetTimeMaxS;
                vr.meetsBoth = vr.meetsApogee && vr.meetsTime;
            } else {
                vr.error = r.error;
            }
        }

        new GeneralRocketSaver().save(outFile, runner.getDocument());
        vr.fileName = outFile.getName();
        return vr;
    }

    private static void writeManifestHeader(PrintWriter manifest, BatchConfig cfg) {
        List<String> cols = new ArrayList<>();
        cols.add("ork_filename");
        if (cfg.ballastKg != null) cols.add("ballast_g");
        if (cfg.finHeightM != null) cols.add("fin_height_mm");
        if (cfg.finSweepM != null) cols.add("fin_sweep_mm");
        if (cfg.holeRadiusIn != null) cols.add("hole_radius_in");
        if (cfg.simCheck != null) {
            cols.add("apogee_m");
            cols.add("flight_time_s");
            cols.add("meets_apogee");
            cols.add("meets_time");
            cols.add("meets_both");
            cols.add("sim_ok");
            cols.add("sim_error");
        }
        manifest.println(CsvUtil.row(cols.toArray()));
    }

    private static void writeManifestRow(PrintWriter manifest, BatchConfig cfg, VariantResult vr) {
        List<Object> vals = new ArrayList<>();
        vals.add(vr.fileName);
        if (cfg.ballastKg != null) vals.add(vr.ballastKg * 1000);
        if (cfg.finHeightM != null) vals.add(vr.finHeightM * 1000);
        if (cfg.finSweepM != null) vals.add(vr.finSweepM * 1000);
        if (cfg.holeRadiusIn != null) vals.add(vr.holeRadiusIn);
        if (cfg.simCheck != null) {
            vals.add(vr.ok ? vr.apogeeM : "");
            vals.add(vr.ok ? vr.flightTimeS : "");
            vals.add(vr.ok ? vr.meetsApogee : "");
            vals.add(vr.ok ? vr.meetsTime : "");
            vals.add(vr.ok ? vr.meetsBoth : "");
            vals.add(vr.ok);
            vals.add(vr.error == null ? "" : vr.error);
        }
        manifest.println(CsvUtil.row(vals.toArray()));
    }

    private static double[] values(GridAxis axis) {
        if (axis == null) return new double[]{Double.NaN}; // single "don't touch" pass; never read since the knob is skipped
        double[] out = new double[axis.count()];
        for (int i = 0; i < out.length; i++) out[i] = axis.value(i);
        return out;
    }

    private static int axisCount(GridAxis axis) {
        return axis == null ? 1 : axis.count();
    }

    /** Formats a number for use in a filename: whole numbers with no decimal, else 1 decimal place. */
    private static String fmt(double v) {
        double rounded = Math.round(v * 10.0) / 10.0;
        if (rounded == Math.rint(rounded)) return String.valueOf((long) rounded);
        return String.valueOf(rounded);
    }
}
