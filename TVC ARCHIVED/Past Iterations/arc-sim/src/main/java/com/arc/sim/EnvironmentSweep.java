package com.arc.sim;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.streaming.SXSSFSheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;

import java.io.File;
import java.io.FileOutputStream;
import java.util.Random;

/**
 * ENGINE 1: EnvironmentSweep
 *
 * Holds the rocket design EXACTLY as uploaded (no ballast/fin changes -- that's Engine 3's job)
 * and Monte Carlo samples across the full environmental envelope you specified (wind, turbulence,
 * temp, pressure), so you can see what fraction of realistic launch-day conditions still land you
 * in the 243.84 m (800 ft) / 37.5-39.5 s window, and which variable your result is most sensitive to.
 *
 * This is a random SAMPLE of the envelope, not the full factorial grid (the full grid is
 * ~1.3 trillion points and isn't runnable -- see chat). 5,000-20,000 samples is normally enough
 * to get a stable picture; bump SAMPLE_COUNT if you want tighter confidence intervals.
 *
 * Distributions below are UNIFORM across your stated ranges (a conservative "cover everything"
 * choice). If you have real historical wind/temp/pressure data for your launch date, swap the
 * relevant sampleX() method for a Gaussian/Rayleigh draw fit to that data -- that will give you
 * a much more realistic (and probably much higher) success probability than the worst-case
 * uniform assumption.
 */
public class EnvironmentSweep {

    private static final double TARGET_APOGEE_M = 243.84; // 800 ft
    private static final double APOGEE_TOLERANCE_M = 0.25;
    private static final double TARGET_TIME_CENTER_S = 38.5; // midpoint of the 37.5-39.5s window
    private static final double TIME_TOLERANCE_S = 1.0; // half-width of the 37.5-39.5s window

    public static void main(String[] args) {
        if (args.length < 3) {
            System.err.println("Usage: EnvironmentSweep <input.ork> <site: MDRA_SOD_FARM|SPAAR_LANCASTER> <numSamples> [outputDir]");
            System.err.println("  outputDir defaults to the input .ork file's own folder if omitted.");
            System.err.println("  Output filename is auto-generated as <orkName>_montecarlo_<timestamp>.xlsx -- never overwrites a previous run.");
            System.exit(1);
        }
        try {
            File outDir = args.length > 3 ? new File(args[3]) : null;
            run(new File(args[0]), LaunchSite.parse(args[1]), Integer.parseInt(args[2]), outDir,
                    (processed, total, eta) -> {
                        if (processed % 500 == 0 || processed == total) {
                            System.out.printf("...%d / %d samples done -- ETA %s%n", processed, total, EtaTracker.formatDuration(eta));
                        }
                    });
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    /** Backward-compatible overload with no progress reporting. outDir may be null (defaults to the ork's own folder). */
    public static File run(File orkFile, LaunchSite site, int sampleCount, File outDir) throws Exception {
        return run(orkFile, site, sampleCount, outDir, ProgressListener.NONE);
    }

    /** Backward-compatible overload with no live leaderboard. */
    public static File run(File orkFile, LaunchSite site, int sampleCount, File outDir, ProgressListener listener) throws Exception {
        return run(orkFile, site, sampleCount, outDir, listener, LeaderboardListener.NONE);
    }

    /**
     * Programmatic entry point (no System.exit) -- safe to call from the GUI or other Java code.
     * outDir is the FOLDER to write into (may be null to default to the ork file's own folder) --
     * the actual filename is auto-generated ("<orkName>_montecarlo_<timestamp>.xlsx") via
     * OutputNaming, so repeated runs never overwrite each other. Returns the file written.
     *
     * leaderboardListener gets a live "most favorable conditions seen so far" top-10 push
     * (ranked by normalized combined error against the apogee/flight-time targets) every time the
     * table actually changes -- same idea as Engine 3's "closest simulation" tracking.
     */
    public static File run(File orkFile, LaunchSite site, int sampleCount, File outDir, ProgressListener listener,
                            LeaderboardListener leaderboardListener) throws Exception {
        File outFile = OutputNaming.uniqueFile(orkFile, outDir, "montecarlo", "xlsx");
        SimRunner runner = new SimRunner(orkFile);
        Random rng = new Random(42); // fixed seed for reproducibility; change or remove for true randomness
        EtaTracker eta = new EtaTracker(sampleCount);
        TopNLeaderboard leaderboard = new TopNLeaderboard(10);

        // keep at most ~100 rows in memory at a time before flushing to disk (SXSSF streaming)
        try (SXSSFWorkbook wb = new SXSSFWorkbook(100)) {
            SXSSFSheet dataSheet = wb.createSheet("Runs");
            writeHeader(dataSheet);

            // Row 2: fixed "all-zero" baseline (0 wind/stddev/turbulence/direction, STP atmosphere,
            // real site lat/long/altitude) -- a repeatable reference point alongside the sampled envelope.
            EnvironmentPoint stpEnv = EnvironmentPoint.stpBaseline(site);
            SimRunner.FlightResult stpResult = runner.run(stpEnv);
            writeConditionRow(dataSheet, 1, stpEnv, site, stpResult, "STP_ZERO_BASELINE");

            int rowNum = 2;
            int meetsBothCount = 0;
            double[] apogees = new double[sampleCount];
            double[] times = new double[sampleCount];
            double[] windAvgs = new double[sampleCount];
            double[] temps = new double[sampleCount];
            double[] pressures = new double[sampleCount];

            for (int i = 0; i < sampleCount; i++) {
                if (Thread.currentThread().isInterrupted()) {
                    System.out.println("Cancelled after " + i + " / " + sampleCount + " samples -- no output file written.");
                    return null;
                }
                double windAvg = sampleUniform(rng, 0.0, 20.0);
                double windStdDev = sampleUniform(rng, 0.0, 5.0);
                double turbulence = sampleUniform(rng, 0.0, 0.50);
                double windDir = sampleUniform(rng, 0.0, 360.0);
                double temp = sampleUniform(rng, -5.0, 35.0);
                double pressure = sampleUniform(rng, 980.0, 1020.0);

                EnvironmentPoint env = new EnvironmentPoint(windAvg, windStdDev, turbulence, windDir, temp, pressure, site);
                SimRunner.FlightResult r = runner.run(env);

                Row row = dataSheet.createRow(rowNum++);
                row.createCell(0).setCellValue(windAvg);
                row.createCell(1).setCellValue(windStdDev);
                row.createCell(2).setCellValue(turbulence * 100.0); // store as %
                row.createCell(3).setCellValue(windDir);
                row.createCell(4).setCellValue(temp);
                row.createCell(5).setCellValue(pressure);
                row.createCell(6).setCellValue(site.label);
                if (r.ok) {
                    boolean meetsApogee = Math.abs(r.apogeeM - TARGET_APOGEE_M) <= APOGEE_TOLERANCE_M;
                    boolean meetsTime = Math.abs(r.flightTimeS - TARGET_TIME_CENTER_S) <= TIME_TOLERANCE_S;
                    row.createCell(7).setCellValue(r.apogeeM);
                    row.createCell(8).setCellValue(r.flightTimeS);
                    row.createCell(9).setCellValue(meetsApogee);
                    row.createCell(10).setCellValue(meetsTime);
                    row.createCell(11).setCellValue(meetsApogee && meetsTime);
                    if (meetsApogee && meetsTime) meetsBothCount++;
                    apogees[i] = r.apogeeM;
                    times[i] = r.flightTimeS;

                    double apogeeErrNorm = Math.abs(r.apogeeM - TARGET_APOGEE_M) / Math.max(APOGEE_TOLERANCE_M, 1e-9);
                    double timeErrNorm = Math.abs(r.flightTimeS - TARGET_TIME_CENTER_S) / Math.max(TIME_TOLERANCE_S, 1e-9);
                    double combinedErr = apogeeErrNorm + timeErrNorm;
                    String detail = String.format("wind %.1f±%.1f m/s @%.0f°, turb %.1f%%, %.1f°C, %.0f mbar",
                            windAvg, windStdDev, windDir, turbulence * 100.0, temp, pressure);
                    if (leaderboard.offer(combinedErr, r.apogeeM, r.flightTimeS, detail)) {
                        leaderboardListener.onUpdate(leaderboard.snapshot());
                    }
                } else {
                    row.createCell(7).setCellValue("ERROR");
                    row.createCell(8).setCellValue(r.error == null ? "" : r.error);
                    apogees[i] = Double.NaN;
                    times[i] = Double.NaN;
                }
                row.createCell(12).setCellValue("monte_carlo");
                windAvgs[i] = windAvg;
                temps[i] = temp;
                pressures[i] = pressure;

                if (i % 200 == 0 || i == sampleCount - 1) {
                    listener.onProgress(i + 1, sampleCount, eta.etaSeconds(i + 1));
                }
            }

            writeSummarySheet(wb, sampleCount, meetsBothCount, apogees, times, windAvgs, temps, pressures);

            try (FileOutputStream fos = new FileOutputStream(outFile)) {
                wb.write(fos);
            }
            wb.dispose(); // clean up SXSSF temp files
        }

        System.out.println("Wrote " + sampleCount + " samples to " + outFile.getAbsolutePath());
        return outFile;
    }

    private static void writeHeader(Sheet sheet) {
        Row header = sheet.createRow(0);
        String[] cols = {
                "wind_avg_ms", "wind_stddev_ms", "turbulence_pct", "wind_dir_deg",
                "temp_c", "pressure_mbar", "site",
                "apogee_m", "flight_time_s", "meets_apogee", "meets_time", "meets_both", "condition"
        };
        for (int i = 0; i < cols.length; i++) {
            header.createCell(i).setCellValue(cols[i]);
        }
    }

    /** Writes a single fixed-condition row (used for the STP/all-zero baseline row). */
    private static void writeConditionRow(Sheet sheet, int rowNum, EnvironmentPoint env, LaunchSite site,
                                           SimRunner.FlightResult r, String conditionLabel) {
        Row row = sheet.createRow(rowNum);
        row.createCell(0).setCellValue(env.windSpeedAvgMs);
        row.createCell(1).setCellValue(env.windSpeedStdDevMs);
        row.createCell(2).setCellValue(env.turbulenceIntensity * 100.0);
        row.createCell(3).setCellValue(env.windDirectionDeg);
        row.createCell(4).setCellValue(env.temperatureC);
        row.createCell(5).setCellValue(env.pressureMbar);
        row.createCell(6).setCellValue(site.label);
        if (r.ok) {
            boolean meetsApogee = Math.abs(r.apogeeM - TARGET_APOGEE_M) <= APOGEE_TOLERANCE_M;
            boolean meetsTime = Math.abs(r.flightTimeS - TARGET_TIME_CENTER_S) <= TIME_TOLERANCE_S;
            row.createCell(7).setCellValue(r.apogeeM);
            row.createCell(8).setCellValue(r.flightTimeS);
            row.createCell(9).setCellValue(meetsApogee);
            row.createCell(10).setCellValue(meetsTime);
            row.createCell(11).setCellValue(meetsApogee && meetsTime);
        } else {
            row.createCell(7).setCellValue("ERROR");
            row.createCell(8).setCellValue(r.error == null ? "" : r.error);
        }
        row.createCell(12).setCellValue(conditionLabel);
    }

    private static void writeSummarySheet(SXSSFWorkbook wb, int n, int meetsBoth,
                                           double[] apogees, double[] times,
                                           double[] windAvgs, double[] temps, double[] pressures) {
        Sheet summary = wb.createSheet("Summary");
        int r = 0;
        summary.createRow(r++).createCell(0).setCellValue("Total samples");
        summary.getRow(r - 1).createCell(1).setCellValue(n);

        summary.createRow(r++).createCell(0).setCellValue("Runs meeting BOTH targets (apogee " + TARGET_APOGEE_M + "m +/- " + APOGEE_TOLERANCE_M + "m, time " + TARGET_TIME_CENTER_S + "s +/- " + TIME_TOLERANCE_S + "s)");
        summary.getRow(r - 1).createCell(1).setCellValue(meetsBoth);

        summary.createRow(r++).createCell(0).setCellValue("Success rate");
        summary.getRow(r - 1).createCell(1).setCellValue((double) meetsBoth / n);

        summary.createRow(r++).createCell(0).setCellValue("Mean apogee (m)");
        summary.getRow(r - 1).createCell(1).setCellValue(mean(apogees));

        summary.createRow(r++).createCell(0).setCellValue("Std dev apogee (m)");
        summary.getRow(r - 1).createCell(1).setCellValue(stddev(apogees));

        summary.createRow(r++).createCell(0).setCellValue("Mean flight time (s)");
        summary.getRow(r - 1).createCell(1).setCellValue(mean(times));

        summary.createRow(r++).createCell(0).setCellValue("Std dev flight time (s)");
        summary.getRow(r - 1).createCell(1).setCellValue(stddev(times));

        r++; // blank row
        summary.createRow(r++).createCell(0).setCellValue("Sensitivity (Pearson correlation with apogee):");
        summary.createRow(r++).createCell(0).setCellValue("  wind_avg_ms");
        summary.getRow(r - 1).createCell(1).setCellValue(correlation(windAvgs, apogees));
        summary.createRow(r++).createCell(0).setCellValue("  temp_c");
        summary.getRow(r - 1).createCell(1).setCellValue(correlation(temps, apogees));
        summary.createRow(r++).createCell(0).setCellValue("  pressure_mbar");
        summary.getRow(r - 1).createCell(1).setCellValue(correlation(pressures, apogees));

        r++;
        summary.createRow(r++).createCell(0).setCellValue("Sensitivity (Pearson correlation with flight time):");
        summary.createRow(r++).createCell(0).setCellValue("  wind_avg_ms");
        summary.getRow(r - 1).createCell(1).setCellValue(correlation(windAvgs, times));
        summary.createRow(r++).createCell(0).setCellValue("  temp_c");
        summary.getRow(r - 1).createCell(1).setCellValue(correlation(temps, times));
        summary.createRow(r++).createCell(0).setCellValue("  pressure_mbar");
        summary.getRow(r - 1).createCell(1).setCellValue(correlation(pressures, times));
    }

    private static double sampleUniform(Random rng, double lo, double hi) {
        return lo + rng.nextDouble() * (hi - lo);
    }

    private static double mean(double[] vals) {
        double sum = 0; int n = 0;
        for (double v : vals) if (!Double.isNaN(v)) { sum += v; n++; }
        return n == 0 ? Double.NaN : sum / n;
    }

    private static double stddev(double[] vals) {
        double m = mean(vals);
        double sumSq = 0; int n = 0;
        for (double v : vals) if (!Double.isNaN(v)) { sumSq += (v - m) * (v - m); n++; }
        return n < 2 ? Double.NaN : Math.sqrt(sumSq / (n - 1));
    }

    private static double correlation(double[] x, double[] y) {
        double mx = mean(x), my = mean(y);
        double sxy = 0, sxx = 0, syy = 0;
        int n = 0;
        for (int i = 0; i < x.length; i++) {
            if (Double.isNaN(x[i]) || Double.isNaN(y[i])) continue;
            double dx = x[i] - mx, dy = y[i] - my;
            sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
            n++;
        }
        if (n < 2 || sxx == 0 || syy == 0) return Double.NaN;
        return sxy / Math.sqrt(sxx * syy);
    }
}
