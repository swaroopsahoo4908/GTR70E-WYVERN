package com.arc.sim;

import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.TrapezoidFinSet;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * ENGINE 6: WeatherDrivenDesign
 *
 * Pulls a real current weather reading (WeatherClient), then chains together:
 *   1. Engine 3 (DesignSolver) -- solves ballast/fin height/hole radius against that ONE pulled
 *      atmosphere, exactly like running Engine 3 by hand with typed-in numbers, except the numbers
 *      come from a live API pull instead of a guess.
 *   2. Engine 5 (MeshExporter) -- exports full STL/OBJ CAD of the solved design.
 *   3. LocalConditionsSweep -- runs the solved (fixed) design across a NARROW, locally-realistic
 *      envelope centered on the pulled conditions (not Engine 1's wide worst-case envelope), to
 *      see how much same-day variability could move the result.
 *   4. Margin fin sets -- re-solves FIN HEIGHT ONLY (ballast and hole radius stay exactly as
 *      solved in step 1) at four wind-speed variants: centerWind -1.0 sigma, -0.5 sigma, +0.5
 *      sigma, +1.0 sigma (sigma = the wind std dev used in step 1), and exports each as a
 *      standalone fin-set-only STL/OBJ -- physical spare fin sets a team could swap in if launch
 *      day actually lands on one of those wind speeds instead of dead-center on the forecast.
 *
 * Nothing here duplicates DesignSolver's bisection logic for the main solve -- it calls
 * DesignSolver.run() directly and reads the returned Result. The margin-fin re-solve is a much
 * simpler one-variable bisection (ballast/hole radius aren't touched -- they're already sitting on
 * the rocket's real components at their step-1 solved values), so it's implemented locally here
 * rather than reusing DesignSolver's three-variable-coupled private bisection methods.
 */
public class WeatherDrivenDesign {

    private static final int FIN_BISECTION_ITERS = 30;
    private static final double APOGEE_TOLERANCE_M = 0.25;
    // Standard margin points requested: +/-0.5 sigma and +/-1.0 sigma wind speed around the solved
    // (center) condition, holding everything else (std dev, turbulence, direction, temp, pressure)
    // fixed at the pulled reading.
    private static final double[] MARGIN_SIGMA_MULTIPLIERS = {-1.0, -0.5, 0.5, 1.0};

    public static class MarginFin {
        public final double windSpeedMs;
        public final double finHeightM;
        public final SimRunner.FlightResult flightResult;
        public final File stlFile;
        public final File objFile;

        MarginFin(double windSpeedMs, double finHeightM, SimRunner.FlightResult flightResult, File stlFile, File objFile) {
            this.windSpeedMs = windSpeedMs;
            this.finHeightM = finHeightM;
            this.flightResult = flightResult;
            this.stlFile = stlFile;
            this.objFile = objFile;
        }
    }

    public static class Result {
        public DesignSolver.Result mainSolve;
        public File mainCadStl;
        public File mainCadObj;
        public File localSweepXlsx;
        public final List<MarginFin> marginFins = new ArrayList<>();
    }

    /**
     * Core entry point. `runner` must already be loaded (typically via the GUI's "Inspect Rocket"
     * flow, same as Engine 3) so selection.finSet/ballastComponents/parachute (if provided) refer
     * to real component instances on THIS document.
     *
     * mainLeaderboardListener mirrors Engine 3's live "closest simulation to target" leaderboard;
     * localSweepLeaderboardListener mirrors Engine 1's live "most favorable conditions" leaderboard,
     * applied to step 3's local envelope sweep.
     */
    public static Result run(SimRunner runner, File orkFile, WeatherClient.Reading weather,
                              double windStdDevMs, double turbulencePct,
                              double targetApogeeM, double targetTimeMinS, double targetTimeMaxS,
                              LaunchSite site, DesignSolver.ComponentSelection selection, DesignSolver.Bounds bounds,
                              int localSweepSamples, File outDir,
                              ProgressListener listener, LeaderboardListener mainLeaderboardListener,
                              LeaderboardListener localSweepLeaderboardListener) throws Exception {
        if (bounds == null) bounds = DesignSolver.Bounds.defaults();
        double targetTimeCenterS = (targetTimeMinS + targetTimeMaxS) / 2.0;

        System.out.println("=== ENGINE 6: Weather-Driven Design ===");
        System.out.printf("Weather @ %s (fetched %s): wind %.2f m/s (gust %.2f m/s, std dev used %.2f m/s), " +
                        "dir %.0f deg, %.1f C, %.1f mbar -- \"%s\"%n",
                weather.locationName, weather.formattedFetchTime(), weather.windAvgMs, weather.windGustMs,
                windStdDevMs, weather.windDirDeg, weather.tempC, weather.pressureMbar, weather.conditionText);

        // --- 1) Main solve at the pulled/fixed atmosphere (Engine 3) ---
        DesignSolver.Result mainSolve = DesignSolver.run(runner, orkFile, targetApogeeM, targetTimeMinS, targetTimeMaxS,
                site, weather.windAvgMs, windStdDevMs, turbulencePct, weather.windDirDeg, weather.tempC, weather.pressureMbar,
                selection, bounds, outDir, listener, mainLeaderboardListener);

        Result result = new Result();
        result.mainSolve = mainSolve;
        if (mainSolve == null) {
            System.out.println("Main solve was cancelled before any pass completed -- stopping Engine 6 here.");
            return result;
        }

        Rocket rocket = runner.getDocument().getRocket();
        TrapezoidFinSet finSet = (selection != null && selection.finSet != null) ? selection.finSet : RocketComponents.findFinSet(rocket);
        // fixedSweepM is read back from the solved document (DesignSolver always restores it to
        // the original file's value before saving) rather than re-derived, so this can never drift.
        double fixedSweepM = mainSolve.fixedSweepM;

        // --- 2) Export full CAD of the solved design (Engine 5) ---
        if (Thread.currentThread().isInterrupted()) return result;
        RocketGeometryExtractor.Geometry mainGeo = RocketGeometryExtractor.extract(rocket);
        List<MeshExporter.Triangle> mainMesh = MeshExporter.buildMesh(mainGeo);
        result.mainCadStl = OutputNaming.uniqueFile(orkFile, outDir, "weatherdesign", "stl");
        MeshExporter.writeStl(mainMesh, result.mainCadStl, orkFile.getName());
        result.mainCadObj = OutputNaming.uniqueFile(orkFile, outDir, "weatherdesign", "obj");
        MeshExporter.writeObj(mainMesh, result.mainCadObj, orkFile.getName());
        System.out.println("Exported main design CAD: " + result.mainCadStl.getName() + " / " + result.mainCadObj.getName());

        // --- 3) Local realistic-envelope sweep of the solved (fixed) design ---
        if (Thread.currentThread().isInterrupted()) return result;
        result.localSweepXlsx = LocalConditionsSweep.run(runner, site,
                weather.windAvgMs, windStdDevMs, turbulencePct, weather.windDirDeg, weather.tempC, weather.pressureMbar,
                targetApogeeM, targetTimeCenterS, localSweepSamples, orkFile, outDir, listener, localSweepLeaderboardListener);
        if (result.localSweepXlsx != null) {
            System.out.println("Wrote local-conditions sweep: " + result.localSweepXlsx.getName());
        }

        // --- 4) Margin fin sets at +/-0.5 sigma and +/-1.0 sigma wind speed ---
        for (double mult : MARGIN_SIGMA_MULTIPLIERS) {
            if (Thread.currentThread().isInterrupted()) break;
            double marginWindMs = Math.max(0.0, weather.windAvgMs + mult * windStdDevMs);
            EnvironmentPoint marginEnv = new EnvironmentPoint(marginWindMs, windStdDevMs, turbulencePct / 100.0,
                    weather.windDirDeg, weather.tempC, weather.pressureMbar, site);

            double solvedFinHeightM = solveFinHeightOnly(runner, finSet, fixedSweepM, marginEnv, targetApogeeM,
                    mainSolve.finHeightM, bounds);
            finSet.setHeight(solvedFinHeightM);
            finSet.setSweep(fixedSweepM);
            SimRunner.FlightResult r = runner.run(marginEnv);

            RocketGeometryExtractor.Geometry marginGeo = RocketGeometryExtractor.extract(rocket);
            List<MeshExporter.Triangle> finMesh = MeshExporter.buildFinSetMesh(marginGeo.fins);
            String tag = ("finset_wind" + String.format("%.2f", marginWindMs) + "ms").replace('.', '_');
            File finStl = OutputNaming.uniqueFile(orkFile, outDir, tag, "stl");
            MeshExporter.writeStl(finMesh, finStl, orkFile.getName() + "_" + tag);
            File finObj = OutputNaming.uniqueFile(orkFile, outDir, tag, "obj");
            MeshExporter.writeObj(finMesh, finObj, orkFile.getName() + "_" + tag);

            System.out.printf("Margin fin set @ wind %.2f m/s (%+.1f sigma): fin height %.4f m -> apogee %.2f m " +
                            "(target %.2f m +/- %.2f m), time %.2f s. CAD: %s / %s%n",
                    marginWindMs, mult, solvedFinHeightM, r.apogeeM, targetApogeeM, APOGEE_TOLERANCE_M, r.flightTimeS,
                    finStl.getName(), finObj.getName());

            result.marginFins.add(new MarginFin(marginWindMs, solvedFinHeightM, r, finStl, finObj));
        }

        // --- Restore the MAIN solved fin height -- the margin loop above mutated the rocket's fin
        // set on every pass, and we don't want the in-memory document (or a subsequent Data
        // Viewer/preview look) left sitting on whatever margin variant ran last. The already-saved
        // solved .ork file (written by DesignSolver.run in step 1) is unaffected either way.
        finSet.setHeight(mainSolve.finHeightM);
        finSet.setSweep(fixedSweepM);
        runner.run(new EnvironmentPoint(weather.windAvgMs, windStdDevMs, turbulencePct / 100.0,
                weather.windDirDeg, weather.tempC, weather.pressureMbar, site));

        System.out.println("=== ENGINE 6 complete ===");
        return result;
    }

    /**
     * Bisection on fin height ONLY, targeting apogee under the given environment -- ballast and
     * hole radius are NOT touched (the caller has already set them to the main-solved values on
     * the real rocket components, and this method never references a BallastControl/
     * ParachuteHoleControl at all, so there's no risk of it re-deriving a wrong "base" value from
     * an already-modified component, the way constructing a fresh control object post-solve
     * would).
     */
    private static double solveFinHeightOnly(SimRunner runner, TrapezoidFinSet finSet, double fixedSweepM,
                                              EnvironmentPoint env, double targetApogeeM, double initialGuessM,
                                              DesignSolver.Bounds bounds) {
        double lo = bounds.minFinHeightM, hi = bounds.maxFinHeightM;
        double mid = Math.max(lo, Math.min(hi, initialGuessM));
        for (int i = 0; i < FIN_BISECTION_ITERS; i++) {
            if (Thread.currentThread().isInterrupted()) break;
            mid = (lo + hi) / 2.0;
            finSet.setHeight(mid);
            finSet.setSweep(fixedSweepM);
            SimRunner.FlightResult r = runner.run(env);
            if (!r.ok) {
                System.err.println("Sim failed at fin height=" + mid + "m (margin solve): " + r.error);
                break;
            }
            if (Math.abs(r.apogeeM - targetApogeeM) <= APOGEE_TOLERANCE_M) break;
            if (r.apogeeM > targetApogeeM) {
                lo = mid; // too high apogee -> need more drag -> bigger fins
            } else {
                hi = mid; // too low apogee -> need less drag -> smaller fins
            }
        }
        return mid;
    }
}
