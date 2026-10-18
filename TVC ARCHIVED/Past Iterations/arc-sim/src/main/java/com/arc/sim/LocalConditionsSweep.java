package com.arc.sim;

import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.xssf.streaming.SXSSFSheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;

import java.io.File;
import java.io.FileOutputStream;
import java.util.Random;

/**
 * ENGINE 6 helper: LocalConditionsSweep
 *
 * Evaluates an ALREADY-SOLVED design (fixed ballast/fin height/hole radius -- this does not solve
 * anything, unlike Engine 1/2/3) across a NARROW, locally-realistic envelope of conditions
 * centered on a real pulled weather reading, rather than Engine 1's wide worst-case envelope. The
 * question this answers is "given the rocket I'm about to fly and the conditions I'm actually
 * expecting on launch day, how much does day-of variability (a gustier or calmer few minutes, a
 * few degrees warmer, a slightly different pressure reading) move the result?" -- not "what's the
 * worst case across the entire year's plausible weather" (that's Engine 1's job).
 *
 * Sampling (uniform, centered on the pulled reading):
 *   - wind speed:      centerWindAvg +/- 2 x windStdDevMs (clipped >= 0)
 *   - wind direction:  centerWindDir +/- 20 deg (wrapped 0-360)
 *   - temperature:     centerTempC +/- 3 C
 *   - pressure:        centerPressureMbar +/- 5 mbar
 *   - wind std dev / turbulence: held FIXED at the reported/estimated values (these describe the
 *     day's gustiness "character", not something we're independently uncertain about at the
 *     envelope level)
 * These spreads are deliberately conservative engineering guesses for same-day short-term
 * variability, NOT a statistical model fit to real variance data -- tune them if you have better
 * local knowledge (a full day's forecast history, a nearby station's historical variance, etc).
 */
public class LocalConditionsSweep {

    private static final double WIND_SPREAD_SIGMA_MULT = 2.0;
    private static final double WIND_DIR_SPREAD_DEG = 20.0;
    private static final double TEMP_SPREAD_C = 3.0;
    private static final double PRESSURE_SPREAD_MBAR = 5.0;
    private static final double APOGEE_TOLERANCE_M = 0.25;
    private static final double TIME_TOLERANCE_S = 0.5;

    /**
     * Runs sampleCount sims of the design currently applied to `runner` (caller is responsible for
     * having already set ballast/fin height/hole radius to whatever design should be evaluated --
     * this class never touches rocket components, only the environment). Returns the .xlsx file
     * written, or null if cancelled before any output was produced.
     */
    public static File run(SimRunner runner, LaunchSite site,
                            double centerWindAvgMs, double windStdDevMs, double turbulencePct, double centerWindDirDeg,
                            double centerTempC, double centerPressureMbar,
                            double targetApogeeM, double targetTimeCenterS,
                            int sampleCount, File orkFile, File outDir,
                            ProgressListener listener, LeaderboardListener leaderboardListener) throws Exception {
        File outFile = OutputNaming.uniqueFile(orkFile, outDir, "localweather", "xlsx");
        Random rng = new Random(); // true randomness -- this is a "what might actually happen" check, not a reproducible baseline
        EtaTracker eta = new EtaTracker(sampleCount);
        TopNLeaderboard leaderboard = new TopNLeaderboard(10);

        double windLo = Math.max(0.0, centerWindAvgMs - WIND_SPREAD_SIGMA_MULT * windStdDevMs);
        double windHi = centerWindAvgMs + WIND_SPREAD_SIGMA_MULT * windStdDevMs;

        try (SXSSFWorkbook wb = new SXSSFWorkbook(100)) {
            SXSSFSheet dataSheet = wb.createSheet("Runs");
            writeHeader(dataSheet);

            int rowNum = 1;
            int meetsBothCount = 0;
            double[] apogees = new double[sampleCount];
            double[] times = new double[sampleCount];

            for (int i = 0; i < sampleCount; i++) {
                if (Thread.currentThread().isInterrupted()) {
                    System.out.println("Cancelled after " + i + " / " + sampleCount + " local-conditions samples -- no output file written.");
                    return null;
                }
                double windAvg = sampleUniform(rng, windLo, windHi);
                double windDir = wrap360(sampleUniform(rng, centerWindDirDeg - WIND_DIR_SPREAD_DEG, centerWindDirDeg + WIND_DIR_SPREAD_DEG));
                double temp = sampleUniform(rng, centerTempC - TEMP_SPREAD_C, centerTempC + TEMP_SPREAD_C);
                double pressure = sampleUniform(rng, centerPressureMbar - PRESSURE_SPREAD_MBAR, centerPressureMbar + PRESSURE_SPREAD_MBAR);

                EnvironmentPoint env = new EnvironmentPoint(windAvg, windStdDevMs, turbulencePct / 100.0, windDir, temp, pressure, site);
                SimRunner.FlightResult r = runner.run(env);

                Row row = dataSheet.createRow(rowNum++);
                row.createCell(0).setCellValue(windAvg);
                row.createCell(1).setCellValue(windDir);
                row.createCell(2).setCellValue(temp);
                row.createCell(3).setCellValue(pressure);
                if (r.ok) {
                    boolean meetsApogee = Math.abs(r.apogeeM - targetApogeeM) <= APOGEE_TOLERANCE_M;
                    boolean meetsTime = Math.abs(r.flightTimeS - targetTimeCenterS) <= TIME_TOLERANCE_S;
                    row.createCell(4).setCellValue(r.apogeeM);
                    row.createCell(5).setCellValue(r.flightTimeS);
                    row.createCell(6).setCellValue(meetsApogee);
                    row.createCell(7).setCellValue(meetsTime);
                    row.createCell(8).setCellValue(meetsApogee && meetsTime);
                    if (meetsApogee && meetsTime) meetsBothCount++;
                    apogees[i] = r.apogeeM;
                    times[i] = r.flightTimeS;

                    double apogeeErrNorm = Math.abs(r.apogeeM - targetApogeeM) / Math.max(APOGEE_TOLERANCE_M, 1e-9);
                    double timeErrNorm = Math.abs(r.flightTimeS - targetTimeCenterS) / Math.max(TIME_TOLERANCE_S, 1e-9);
                    double combinedErr = apogeeErrNorm + timeErrNorm;
                    String detail = String.format("wind %.2f m/s @%.0f deg, %.1f C, %.0f mbar", windAvg, windDir, temp, pressure);
                    if (leaderboard.offer(combinedErr, r.apogeeM, r.flightTimeS, detail)) {
                        leaderboardListener.onUpdate(leaderboard.snapshot());
                    }
                } else {
                    row.createCell(4).setCellValue("ERROR");
                    row.createCell(5).setCellValue(r.error == null ? "" : r.error);
                    apogees[i] = Double.NaN;
                    times[i] = Double.NaN;
                }

                if (i % 100 == 0 || i == sampleCount - 1) {
                    listener.onProgress(i + 1, sampleCount, eta.etaSeconds(i + 1));
                }
            }

            writeSummarySheet(wb, sampleCount, meetsBothCount, apogees, times, targetApogeeM, targetTimeCenterS,
                    centerWindAvgMs, windStdDevMs, windLo, windHi);

            try (FileOutputStream fos = new FileOutputStream(outFile)) {
                wb.write(fos);
            }
            wb.dispose();
        }

        System.out.println("Wrote " + sampleCount + " local-conditions samples to " + outFile.getAbsolutePath());
        return outFile;
    }

    private static void writeHeader(Sheet sheet) {
        Row header = sheet.createRow(0);
        String[] cols = {"wind_avg_ms", "wind_dir_deg", "temp_c", "pressure_mbar",
                "apogee_m", "flight_time_s", "meets_apogee", "meets_time", "meets_both"};
        for (int i = 0; i < cols.length; i++) header.createCell(i).setCellValue(cols[i]);
    }

    private static void writeSummarySheet(SXSSFWorkbook wb, int n, int meetsBoth, double[] apogees, double[] times,
                                           double targetApogeeM, double targetTimeCenterS,
                                           double centerWindAvgMs, double windStdDevMs, double windLo, double windHi) {
        Sheet summary = wb.createSheet("Summary");
        int r = 0;
        summary.createRow(r++).createCell(0).setCellValue("Center wind speed (m/s, from pulled weather)");
        summary.getRow(r - 1).createCell(1).setCellValue(centerWindAvgMs);
        summary.createRow(r++).createCell(0).setCellValue("Wind std dev used (m/s)");
        summary.getRow(r - 1).createCell(1).setCellValue(windStdDevMs);
        summary.createRow(r++).createCell(0).setCellValue("Sampled wind speed range (m/s)");
        summary.getRow(r - 1).createCell(1).setCellValue(windLo + " - " + windHi);
        summary.createRow(r++).createCell(0).setCellValue("Total samples");
        summary.getRow(r - 1).createCell(1).setCellValue(n);
        summary.createRow(r++).createCell(0).setCellValue("Runs meeting BOTH targets (apogee " + targetApogeeM +
                "m +/- " + APOGEE_TOLERANCE_M + "m, time " + targetTimeCenterS + "s +/- " + TIME_TOLERANCE_S + "s)");
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
    }

    private static double sampleUniform(Random rng, double lo, double hi) {
        if (hi <= lo) return lo;
        return lo + rng.nextDouble() * (hi - lo);
    }

    private static double wrap360(double deg) {
        double d = deg % 360.0;
        return d < 0 ? d + 360.0 : d;
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
}
