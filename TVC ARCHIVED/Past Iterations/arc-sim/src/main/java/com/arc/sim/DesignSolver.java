package com.arc.sim;

import info.openrocket.core.file.GeneralRocketSaver;
import info.openrocket.core.rocketcomponent.MassComponent;
import info.openrocket.core.rocketcomponent.Parachute;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.TrapezoidFinSet;

import java.io.File;
import java.util.List;

/**
 * ENGINE 3: DesignSolver
 *
 * Given ONE fixed atmospheric/wind condition and a target apogee + flight-time window, solves
 * for ballast mass + fin height that hit those targets.
 *
 * PHYSICAL ROLES (3 unknowns / 2 targets):
 *   - BALLAST MASS is the primary lever for TOTAL FLIGHT TIME. With the parachute fixed, a
 *     heavier rocket descends faster under the same canopy, shortening total flight time.
 *   - FIN HEIGHT is the primary lever for APOGEE. Bigger fins = more parasitic drag during
 *     ascent = lower apogee. Effect on total flight time is small (descent is dominated by the
 *     parachute).
 *   - PARACHUTE CENTER HOLE RADIUS (0-4 in radius / 0-8 in diameter, 0-0.1016 m) is a secondary
 *     lever for TOTAL FLIGHT TIME, solved AFTER ballast and fin height each outer round. A spill hole reduces effective
 *     canopy area, which increases descent rate -- same directional effect as ballast, but a
 *     second independent knob to reach the flight-time window when ballast alone saturates at a
 *     bound, without having to touch fin height (which would re-drift apogee).
 *
 * FIN SWEEP IS NOT TOUCHED. It's read once for logging and left exactly as it was in the
 * uploaded file -- never passed to setSweep(). (An earlier version of this solver used sweep as
 * a last-resort apogee trim; removed because its effect on apogee is weak/noisy relative to its
 * effect on stability margin, and a solver reaching for a near-flat lever tends to just walk it
 * to whichever bound looks marginally better on noise, effectively zeroing it out for no benefit.
 * The GUI button and this solver do not expose fin sweep as a control at all.)
 *
 * CONVERGENCE ORDER MATTERS: each outer iteration solves ballast (for flight time) FIRST using
 * the previous fin height/hole radius, then solves fin height (for apogee) using the
 * just-updated ballast, then solves parachute hole radius (for flight time, again) LAST using the
 * just-updated fin height. Ending on a flight-time solve after the apogee solve means both
 * targets get a fresh pass on the newest fin-height value each round; fin height itself is always
 * solved most-recently among the apogee-affecting variables, so apogee doesn't re-drift after the
 * last time it was tuned.
 *
 * PHASE 2 -- PATTERN SEARCH (escapes the bisection fixed point): the 3-way alternating bisection
 * above is a Gauss-Seidel-style fixed-point iteration -- each knob is solved to exactly zero its
 * OWN target, holding the others fixed, which is fast but is NOT the same thing as minimizing the
 * combined apogee+time error jointly. On a fixed atmosphere with fixed targets it is fully
 * deterministic, so once the triple (ballast, fin height, hole radius) it produces stops changing
 * between passes, every subsequent bisection pass reproduces that exact same triple forever --
 * there is nothing left for it to find. When STAGNATION_LIMIT consecutive passes fail to beat the
 * best combined error seen so far, the solver switches to a direct compass/pattern search on the
 * actual combined-error objective: each pass nudges ballast, then fin height, then hole radius by
 * a step size (trying +step and -step, keeping whichever reduces combined error, else leaving that
 * knob alone), starting from the best point found so far. Any accepted move updates the running
 * best immediately (so the leaderboard keeps moving instead of sitting on one entry). A pass that
 * finds no improving move in any of the three directions halves the step size and tries again from
 * the same point; once all three step sizes have shrunk below a tiny fraction of their bound
 * range, the solver stops -- that's the closest achievable given the search resolution, rather
 * than an artifact of the bisection's fixed point.
 *
 * CONVERGENCE BUDGET: the outer loop keeps iterating -- alternating ballast / fin height / hole
 * radius bisection passes, then (after stagnation) pattern-search passes -- until BOTH targets are
 * simultaneously within tolerance, the pattern search's step size underflows its resolution floor,
 * or it hits MAX_OUTER_ITERS (default 1000, adjustable via Bounds.maxOuterIters) outer passes,
 * whichever comes first. There is no wall-clock cap -- this is deliberate: getting apogee/
 * flight-time as close as possible to the requested targets matters more than a fixed time budget.
 * The final design is whatever pass (bisection or pattern-search) achieved the lowest combined
 * error across the whole run (a "not converged" note is printed if both targets aren't met within
 * tolerance at that point).
 *
 * WORKS WITH ANY .ork FILE via two mechanisms:
 *   1. Auto-detection (RocketComponents) as a default guess -- lowest body tube for ballast,
 *      first parachute/fin set found.
 *   2. ComponentSelection lets a caller (typically the GUI, via RocketInspector) override any of
 *      those picks explicitly -- required for rockets where the guess is wrong: multi-stage
 *      rockets, rockets with a drogue + main chute, multiple fin sets, etc.
 * Bounds controls the search range for ballast/fin height -- defaults are sized for small to
 * mid-size rockets; raise them for a large/heavy airframe (see Bounds.big() for a starting point).
 */
public class DesignSolver {

    private static final double APOGEE_TOLERANCE_M = 0.25;
    private static final double TIME_TOLERANCE_S = 0.5; // used only for early-exit convergence check
    private static final int MAX_BISECTION_ITERS = 30;
    private static final int DEFAULT_MAX_OUTER_ITERS = 1000;     // default/max-suggested outer-pass budget (now adjustable via Bounds.maxOuterIters)
    private static final double IN_TO_M = 0.0254;
    private static final double MAX_HOLE_RADIUS_IN = 2.0; // 4 in hole DIAMETER default max

    // Phase-2 pattern search (see class comment): triggers after this many consecutive bisection
    // passes fail to beat the best combined error found so far -- 2 is enough since the bisection
    // map is fully deterministic given a fixed atmosphere, so a repeat is conclusive, not noise.
    private static final int STAGNATION_LIMIT = 2;
    private static final double PATTERN_INITIAL_STEP_FRACTION = 0.08; // vs. each knob's bound range
    private static final double PATTERN_MIN_STEP_FRACTION = 1e-4;     // stop once steps shrink below this
    private static final double PATTERN_SHRINK_FACTOR = 0.5;

    /** Optional explicit component picks -- if any field is null, falls back to auto-detection. */
    public static class ComponentSelection {
        public List<MassComponent> ballastComponents;
        public Parachute parachute;
        public TrapezoidFinSet finSet;
    }

    /** Search bounds for ballast/fin height. Defaults suit small/mid rockets; scale up for large ones. */
    public static class Bounds {
        public double minBallastKg = 0.0;
        public double maxBallastKg = 5.0;
        public double minFinHeightM = 0.01;
        public double maxFinHeightM = 0.5;
        public double minHoleRadiusM = 0.0;
        public double maxHoleRadiusM = MAX_HOLE_RADIUS_IN * IN_TO_M; // 2 in radius (4 in diameter) default cap
        public int maxOuterIters = DEFAULT_MAX_OUTER_ITERS; // adjustable solver-pass budget; see class comment

        public static Bounds defaults() {
            return new Bounds();
        }

        /** A generous starting point for large/heavy rockets (bigger ballast capacity, bigger fins). */
        public static Bounds big() {
            Bounds b = new Bounds();
            b.maxBallastKg = 25.0;
            b.maxFinHeightM = 1.2;
            return b;
        }
    }

    /**
     * The final solved design plus the flight it produced. Returned by the core run() overload so
     * a caller (e.g. Engine 6 / WeatherDrivenDesign) can chain further work off the SAME solved
     * values -- exporting CAD of the solved geometry, re-solving fin height alone for margin
     * conditions, etc -- without having to re-parse the saved .ork file or re-run the solver.
     */
    public static class Result {
        public final double ballastKg;
        public final double finHeightM;
        public final double holeRadiusM;
        public final double fixedSweepM;
        public final SimRunner.FlightResult flightResult;
        public final boolean apogeeOk;
        public final boolean timeOk;
        public final File savedOrkFile;

        Result(double ballastKg, double finHeightM, double holeRadiusM, double fixedSweepM,
               SimRunner.FlightResult flightResult, boolean apogeeOk, boolean timeOk, File savedOrkFile) {
            this.ballastKg = ballastKg;
            this.finHeightM = finHeightM;
            this.holeRadiusM = holeRadiusM;
            this.fixedSweepM = fixedSweepM;
            this.flightResult = flightResult;
            this.apogeeOk = apogeeOk;
            this.timeOk = timeOk;
            this.savedOrkFile = savedOrkFile;
        }
    }

    public static void main(String[] args) {
        if (args.length < 11) {
            System.err.println("Usage: DesignSolver <input.ork> <targetApogeeM> <targetTimeMinS> <targetTimeMaxS> " +
                    "<site: MDRA_SOD_FARM|SPAAR_LANCASTER|CUSTOM:lat|lon|alt> <windAvgMs> <windStdDevMs> <turbulencePct> <windDirDeg> <tempC> <pressureMbar>");
            System.err.println("Example: DesignSolver CSWARCMOD1D.ork 243.84 37.5 39.5 MDRA_SOD_FARM 3.8 0.6 13.4 270 7.06 999.76");
            System.exit(1);
        }
        try {
            run(new File(args[0]), Double.parseDouble(args[1]), Double.parseDouble(args[2]), Double.parseDouble(args[3]),
                    LaunchSite.parse(args[4]), Double.parseDouble(args[5]), Double.parseDouble(args[6]),
                    Double.parseDouble(args[7]), Double.parseDouble(args[8]), Double.parseDouble(args[9]), Double.parseDouble(args[10]));
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    /** Simplest entry point: auto-detect components, default bounds. CLI-only -- saves next to the input file. */
    public static void run(File orkFile, double targetApogeeM, double targetTimeMinS, double targetTimeMaxS,
                            LaunchSite site, double windAvg, double windStdDev, double turbulencePct,
                            double windDir, double tempC, double pressureMbar) throws Exception {
        run(new SimRunner(orkFile), orkFile, targetApogeeM, targetTimeMinS, targetTimeMaxS, site, windAvg,
                windStdDev, turbulencePct, windDir, tempC, pressureMbar, null, null, null, ProgressListener.NONE);
    }

    /** With explicit component selection and/or bounds (either may be null for defaults/auto-detect). CLI-only -- saves next to the input file. */
    public static void run(File orkFile, double targetApogeeM, double targetTimeMinS, double targetTimeMaxS,
                            LaunchSite site, double windAvg, double windStdDev, double turbulencePct,
                            double windDir, double tempC, double pressureMbar,
                            ComponentSelection selection, Bounds bounds) throws Exception {
        run(new SimRunner(orkFile), orkFile, targetApogeeM, targetTimeMinS, targetTimeMaxS, site, windAvg,
                windStdDev, turbulencePct, windDir, tempC, pressureMbar, selection, bounds, null, ProgressListener.NONE);
    }

    /** Backward-compatible overload with no live leaderboard. outDir may be null (defaults to next to the input file). */
    public static Result run(SimRunner runner, File orkFile, double targetApogeeM, double targetTimeMinS, double targetTimeMaxS,
                            LaunchSite site, double windAvg, double windStdDev, double turbulencePct,
                            double windDir, double tempC, double pressureMbar,
                            ComponentSelection selection, Bounds bounds, File outDir, ProgressListener listener) throws Exception {
        return run(runner, orkFile, targetApogeeM, targetTimeMinS, targetTimeMaxS, site, windAvg, windStdDev, turbulencePct,
                windDir, tempC, pressureMbar, selection, bounds, outDir, listener, LeaderboardListener.NONE);
    }

    /**
     * Core entry point. Takes an already-loaded SimRunner so a caller (the GUI) can inspect the
     * rocket's components first -- via RocketInspector, picking exact ballast/parachute/fin set
     * objects -- and then run on that SAME loaded document, without re-loading the file (which
     * would produce a different set of component object instances and break the selection).
     *
     * leaderboardListener gets a live "closest simulation to target" top-10 push (ranked by the
     * same normalized combined apogee+time error used for bestErr below) every outer pass that
     * changes the table.
     */
    public static Result run(SimRunner runner, File orkFile, double targetApogeeM, double targetTimeMinS, double targetTimeMaxS,
                            LaunchSite site, double windAvg, double windStdDev, double turbulencePct,
                            double windDir, double tempC, double pressureMbar,
                            ComponentSelection selection, Bounds bounds, File outDir, ProgressListener listener,
                            LeaderboardListener leaderboardListener) throws Exception {
        if (bounds == null) bounds = Bounds.defaults();
        Rocket rocket = runner.getDocument().getRocket();

        List<MassComponent> ballastComps =
                (selection != null && selection.ballastComponents != null && !selection.ballastComponents.isEmpty())
                        ? selection.ballastComponents : RocketComponents.findBallastComponents(rocket);
        RocketComponents.BallastControl ballast = new RocketComponents.BallastControl(ballastComps);
        TrapezoidFinSet finSet = (selection != null && selection.finSet != null) ? selection.finSet : RocketComponents.findFinSet(rocket);
        Parachute chute = (selection != null && selection.parachute != null) ? selection.parachute : RocketComponents.findMainParachute(rocket); // diameter driven only via the hole-radius knob

        double fixedSweepM = finSet.getSweep(); // read once, NEVER modified -- see class comment
        RocketComponents.ParachuteHoleControl hole = new RocketComponents.ParachuteHoleControl(chute);

        System.out.printf("Ballast starting total: %.1f g%n", ballast.getCurrentTotalKg() * 1000);
        System.out.printf("Fin set starting: height=%.4f m, sweep=%.4f m (sweep held fixed, not driven by this solver), root chord=%.4f m%n",
                finSet.getHeight(), fixedSweepM, finSet.getRootChord());
        System.out.printf("Parachute '%s' base diameter %.3f m; center hole radius is driven by this engine (0-%.2f in)%n",
                chute.getName(), hole.getBaseDiameterM(), bounds.maxHoleRadiusM / IN_TO_M);
        System.out.printf("Search bounds: ballast %.2f-%.2f kg, fin height %.3f-%.3f m, hole radius %.2f-%.2f in%n",
                bounds.minBallastKg, bounds.maxBallastKg, bounds.minFinHeightM, bounds.maxFinHeightM,
                bounds.minHoleRadiusM / IN_TO_M, bounds.maxHoleRadiusM / IN_TO_M);
        System.out.printf("Convergence budget: up to %d outer passes (no wall-clock cap -- runs until it converges or exhausts passes)%n",
                bounds.maxOuterIters);

        EnvironmentPoint env = new EnvironmentPoint(windAvg, windStdDev, turbulencePct / 100.0, windDir, tempC, pressureMbar, site);
        double targetTimeCenterS = (targetTimeMinS + targetTimeMaxS) / 2.0;

        double ballastKg = clamp(Math.max(ballast.getCurrentTotalKg(), 0.05), bounds.minBallastKg, bounds.maxBallastKg);
        double finHeightM = clamp(finSet.getHeight(), bounds.minFinHeightM, bounds.maxFinHeightM);
        double holeRadiusM = clamp(0.0, bounds.minHoleRadiusM, bounds.maxHoleRadiusM);

        long startMs = System.currentTimeMillis();
        SimRunner.FlightResult last = null;
        int outer = 0;
        boolean converged = false;
        // Live time estimator: measures actual seconds/pass so far and projects the remainder --
        // each outer pass costs a variable number of sim runs (bisection can early-exit per knob),
        // so a flat "passes remaining * first-pass time" guess would drift; EtaTracker instead uses
        // the running average rate, which self-corrects as passes complete.
        EtaTracker eta = new EtaTracker(bounds.maxOuterIters);

        // Track the closest-to-target result seen across all passes -- since the loop can end on
        // bounds.maxOuterIters without perfect convergence, we want to report/save whichever pass
        // got nearest to BOTH targets (normalized combined error), not just whatever the final
        // pass happened to land on. Shared by both the bisection phase and the pattern-search
        // phase below (see class comment).
        TopNLeaderboard leaderboard = new TopNLeaderboard(10);
        BestTracker tracker = new BestTracker(ballastKg, finHeightM, holeRadiusM, leaderboard, leaderboardListener);
        boolean cancelled = false;
        int noImprovePasses = 0;
        boolean patternSearchMode = false;

        // Pattern-search step sizes, as fractions of each knob's bound range; only used once
        // patternSearchMode flips on. Shrinks (never grows) as the search narrows in.
        double stepBallastKg = (bounds.maxBallastKg - bounds.minBallastKg) * PATTERN_INITIAL_STEP_FRACTION;
        double stepFinHeightM = (bounds.maxFinHeightM - bounds.minFinHeightM) * PATTERN_INITIAL_STEP_FRACTION;
        double stepHoleRadiusM = (bounds.maxHoleRadiusM - bounds.minHoleRadiusM) * PATTERN_INITIAL_STEP_FRACTION;

        for (; outer < bounds.maxOuterIters; outer++) {
            if (Thread.currentThread().isInterrupted()) {
                System.out.println("Cancelled after " + outer + " / " + bounds.maxOuterIters + " outer passes -- using the closest pass found so far.");
                cancelled = true;
                break;
            }

            boolean improvedThisPass;

            if (!patternSearchMode) {
                // --- Phase 1: alternating bisection (fast, but converges to a fixed point) ---
                // 1) Ballast FIRST (using the fin height/hole radius from the previous round)...
                ballastKg = solveBallastForFlightTime(runner, ballast, finSet, finHeightM, fixedSweepM, hole, holeRadiusM,
                        env, targetTimeMinS, targetTimeMaxS, ballastKg, bounds);

                // 2) ...then fin height, against the just-updated ballast, tuning apogee...
                finHeightM = solveFinHeightForApogee(runner, ballast, finSet, ballastKg, fixedSweepM, hole, holeRadiusM,
                        env, targetApogeeM, finHeightM, bounds);

                // 3) ...then parachute hole radius LAST, a second independent flight-time trim
                // against the just-updated fin height, for cases where ballast alone saturates.
                holeRadiusM = solveHoleRadiusForFlightTime(runner, ballast, ballastKg, finSet, finHeightM, fixedSweepM,
                        hole, env, targetTimeMinS, targetTimeMaxS, holeRadiusM, bounds);

                Eval eval = evaluate(runner, ballast, ballastKg, finSet, finHeightM, fixedSweepM, hole, holeRadiusM,
                        env, targetApogeeM, targetTimeCenterS);
                last = eval.result;
                System.out.printf("[outer %d/%d, ETA %s] ballast=%.1f g, fin height=%.4f m, hole radius=%.2f in -> apogee=%.2f m, time=%.2f s%n",
                        outer, bounds.maxOuterIters, EtaTracker.formatDuration(eta.etaSeconds(outer + 1)),
                        ballastKg * 1000, finHeightM, holeRadiusM / IN_TO_M, last.apogeeM, last.flightTimeS);

                improvedThisPass = tracker.offer(eval, ballastKg, finHeightM, holeRadiusM,
                        designDetail(ballastKg, finHeightM, holeRadiusM, outer, false));

                if (improvedThisPass) {
                    noImprovePasses = 0;
                } else {
                    noImprovePasses++;
                    if (noImprovePasses >= STAGNATION_LIMIT) {
                        // The bisection map is deterministic given a fixed atmosphere: a repeat
                        // means every future bisection pass would reproduce the exact same triple
                        // forever. Switch to directly minimizing the combined error instead of
                        // burning the rest of the budget re-deriving the same fixed point.
                        patternSearchMode = true;
                        ballastKg = tracker.bestBallastKg;
                        finHeightM = tracker.bestFinHeightM;
                        holeRadiusM = tracker.bestHoleRadiusM;
                        System.out.printf("Alternating bisection stagnated after %d pass(es) without improvement -- " +
                                "switching to direct pattern-search refinement (combined error %.3f) to keep closing the gap.%n",
                                noImprovePasses, tracker.bestErr);
                    }
                }
            } else {
                // --- Phase 2: compass/pattern search directly on combined error (see class comment) ---
                double workBallast = tracker.bestBallastKg, workFin = tracker.bestFinHeightM, workHole = tracker.bestHoleRadiusM;
                improvedThisPass = false;

                if (stepBallastKg > 0) {
                    double plus = clamp(workBallast + stepBallastKg, bounds.minBallastKg, bounds.maxBallastKg);
                    Eval e = evaluate(runner, ballast, plus, finSet, workFin, fixedSweepM, hole, workHole, env, targetApogeeM, targetTimeCenterS);
                    if (tracker.offer(e, plus, workFin, workHole, designDetail(plus, workFin, workHole, outer, true))) {
                        workBallast = plus; improvedThisPass = true;
                    } else {
                        double minus = clamp(workBallast - stepBallastKg, bounds.minBallastKg, bounds.maxBallastKg);
                        Eval e2 = evaluate(runner, ballast, minus, finSet, workFin, fixedSweepM, hole, workHole, env, targetApogeeM, targetTimeCenterS);
                        if (tracker.offer(e2, minus, workFin, workHole, designDetail(minus, workFin, workHole, outer, true))) {
                            workBallast = minus; improvedThisPass = true;
                        }
                    }
                }
                if (stepFinHeightM > 0 && !Thread.currentThread().isInterrupted()) {
                    double plus = clamp(workFin + stepFinHeightM, bounds.minFinHeightM, bounds.maxFinHeightM);
                    Eval e = evaluate(runner, ballast, workBallast, finSet, plus, fixedSweepM, hole, workHole, env, targetApogeeM, targetTimeCenterS);
                    if (tracker.offer(e, workBallast, plus, workHole, designDetail(workBallast, plus, workHole, outer, true))) {
                        workFin = plus; improvedThisPass = true;
                    } else {
                        double minus = clamp(workFin - stepFinHeightM, bounds.minFinHeightM, bounds.maxFinHeightM);
                        Eval e2 = evaluate(runner, ballast, workBallast, finSet, minus, fixedSweepM, hole, workHole, env, targetApogeeM, targetTimeCenterS);
                        if (tracker.offer(e2, workBallast, minus, workHole, designDetail(workBallast, minus, workHole, outer, true))) {
                            workFin = minus; improvedThisPass = true;
                        }
                    }
                }
                if (stepHoleRadiusM > 0 && !Thread.currentThread().isInterrupted()) {
                    double plus = clamp(workHole + stepHoleRadiusM, bounds.minHoleRadiusM, bounds.maxHoleRadiusM);
                    Eval e = evaluate(runner, ballast, workBallast, finSet, workFin, fixedSweepM, hole, plus, env, targetApogeeM, targetTimeCenterS);
                    if (tracker.offer(e, workBallast, workFin, plus, designDetail(workBallast, workFin, plus, outer, true))) {
                        workHole = plus; improvedThisPass = true;
                    } else {
                        double minus = clamp(workHole - stepHoleRadiusM, bounds.minHoleRadiusM, bounds.maxHoleRadiusM);
                        Eval e2 = evaluate(runner, ballast, workBallast, finSet, workFin, fixedSweepM, hole, minus, env, targetApogeeM, targetTimeCenterS);
                        if (tracker.offer(e2, workBallast, workFin, minus, designDetail(workBallast, workFin, minus, outer, true))) {
                            workHole = minus; improvedThisPass = true;
                        }
                    }
                }

                ballastKg = tracker.bestBallastKg;
                finHeightM = tracker.bestFinHeightM;
                holeRadiusM = tracker.bestHoleRadiusM;
                last = tracker.best;
                if (last == null) {
                    // Every evaluation so far (bisection AND pattern search) has failed to simulate --
                    // nothing to score against, so there's nothing pattern search can do either.
                    System.out.println("No successful simulation yet after " + (outer + 1) + " passes -- check the rocket file/environment; stopping.");
                    break;
                }
                System.out.printf("[outer %d/%d pattern-search, ETA %s] ballast=%.1f g, fin height=%.4f m, hole radius=%.2f in -> " +
                        "apogee=%.2f m, time=%.2f s (combined err %.4f, step ballast=%.2fg fin=%.3fmm hole=%.3fin)%n",
                        outer, bounds.maxOuterIters, EtaTracker.formatDuration(eta.etaSeconds(outer + 1)),
                        ballastKg * 1000, finHeightM, holeRadiusM / IN_TO_M, last.apogeeM, last.flightTimeS, tracker.bestErr,
                        stepBallastKg * 1000, stepFinHeightM * 1000, stepHoleRadiusM / IN_TO_M);

                if (!improvedThisPass) {
                    stepBallastKg *= PATTERN_SHRINK_FACTOR;
                    stepFinHeightM *= PATTERN_SHRINK_FACTOR;
                    stepHoleRadiusM *= PATTERN_SHRINK_FACTOR;

                    boolean ballastDone = (bounds.maxBallastKg - bounds.minBallastKg) <= 0
                            || stepBallastKg < (bounds.maxBallastKg - bounds.minBallastKg) * PATTERN_MIN_STEP_FRACTION;
                    boolean finDone = (bounds.maxFinHeightM - bounds.minFinHeightM) <= 0
                            || stepFinHeightM < (bounds.maxFinHeightM - bounds.minFinHeightM) * PATTERN_MIN_STEP_FRACTION;
                    boolean holeDone = (bounds.maxHoleRadiusM - bounds.minHoleRadiusM) <= 0
                            || stepHoleRadiusM < (bounds.maxHoleRadiusM - bounds.minHoleRadiusM) * PATTERN_MIN_STEP_FRACTION;
                    if (ballastDone && finDone && holeDone) {
                        System.out.printf("Pattern-search step size has shrunk below resolution after %d total passes -- " +
                                "this is the closest achievable within the current bounds. Stopping.%n", outer + 1);
                        listener.onProgress(outer + 1, bounds.maxOuterIters, eta.etaSeconds(outer + 1));
                        break;
                    }
                }
            }

            listener.onProgress(outer + 1, bounds.maxOuterIters, eta.etaSeconds(outer + 1));

            boolean apogeeOk = last != null && last.ok && Math.abs(last.apogeeM - targetApogeeM) <= APOGEE_TOLERANCE_M;
            boolean timeOk = last != null && last.ok && Math.abs(last.flightTimeS - targetTimeCenterS) <= TIME_TOLERANCE_S;
            if (apogeeOk && timeOk) {
                System.out.println("Converged within tolerance -- both targets met, stopping early.");
                converged = true;
                break;
            }
        }
        if (!converged && outer >= bounds.maxOuterIters) {
            System.out.println("Hit " + bounds.maxOuterIters + "-pass cap -- stopping. Using the closest-to-target pass found.");
        } else if (cancelled) {
            System.out.println("Stopped early by Cancel -- using the closest-to-target pass found across the " + outer + " completed passes.");
        }
        if (cancelled && tracker.best == null) {
            System.out.println("Cancelled before any pass completed -- nothing to save.");
            return null;
        }

        // Use the best pass found across BOTH phases (which IS the final pass if it converged,
        // since that's strictly the lowest combined error by construction) rather than blindly
        // trusting the last pass.
        if (tracker.best != null && tracker.best != last) {
            ballastKg = tracker.bestBallastKg;
            finHeightM = tracker.bestFinHeightM;
            holeRadiusM = tracker.bestHoleRadiusM;
            last = tracker.best;
        }

        ballast.setTotalKg(ballastKg);
        finSet.setHeight(finHeightM);
        finSet.setSweep(fixedSweepM);
        hole.setHoleRadiusM(holeRadiusM);
        SimRunner.FlightResult check = last != null ? last : runner.run(env);

        System.out.println("=== FINAL DESIGN (fixed atmosphere) ===");
        System.out.printf("Ballast total: %.1f g%n", ballastKg * 1000);
        System.out.printf("Fin height: %.4f m%n", finHeightM);
        System.out.printf("Fin sweep: %.4f m (UNCHANGED from original file)%n", fixedSweepM);
        System.out.printf("Parachute center hole radius: %.2f in (effective diameter %.3f m, base %.3f m)%n",
                holeRadiusM / IN_TO_M, chute.getDiameter(), hole.getBaseDiameterM());
        System.out.printf("Apogee: %.2f m (target %.2f m +/- %.2f m)%n", check.apogeeM, targetApogeeM, APOGEE_TOLERANCE_M);
        System.out.printf("Flight time: %.2f s (target %.1f-%.1f s)%n", check.flightTimeS, targetTimeMinS, targetTimeMaxS);
        System.out.printf("Passes used: %d (cap %d), elapsed %.1f s%n",
                outer + 1, bounds.maxOuterIters, (System.currentTimeMillis() - startMs) / 1000.0);
        if (!check.ok) {
            System.err.println("Simulation error: " + check.error);
        }

        boolean apogeeOk = Math.abs(check.apogeeM - targetApogeeM) <= APOGEE_TOLERANCE_M;
        boolean timeOk = check.flightTimeS >= targetTimeMinS && check.flightTimeS <= targetTimeMaxS;
        if (!apogeeOk || !timeOk) {
            System.out.println("NOTE: targets not both hit within tolerance after " + (outer + 1) + " outer passes.");
            System.out.printf("  Fin height ended at %.4f m (bounds %.3f-%.3f m) -- at a bound means you need wider bounds.%n",
                    finHeightM, bounds.minFinHeightM, bounds.maxFinHeightM);
            System.out.printf("  Ballast ended at %.1f g (bounds %.0f-%.0f g) -- at a bound means you need wider bounds.%n",
                    ballastKg * 1000, bounds.minBallastKg * 1000, bounds.maxBallastKg * 1000);
            System.out.printf("  Hole radius ended at %.2f in (bounds %.2f-%.2f in) -- at a bound means you need a wider hole cap.%n",
                    holeRadiusM / IN_TO_M, bounds.minHoleRadiusM / IN_TO_M, bounds.maxHoleRadiusM / IN_TO_M);
            System.out.println("  If none are at a bound, the targets may simply conflict for this airframe+motor " +
                    "-- try a different motor, or accept a tolerance trade.");
        } else {
            System.out.println("Both targets met.");
        }

        // Always write the solved design to a NEW file -- the original input .ork is never
        // touched (it's only ever read via SimRunner), and we don't reuse a fixed output name
        // either, so re-running the solver (on this file or any other) never clobbers a previous
        // solved result. Name is "<orkBase>_solved_<timestamp>.ork", written alongside the
        // original -- see OutputNaming for the shared collision-safe naming scheme used by every
        // engine.
        File resolvedOutDir = outDir != null ? outDir : OutputNaming.namedSubfolder(orkFile, OutputNaming.OPENROCKET_SOLVES_FOLDER);
        File outFile = OutputNaming.uniqueFile(orkFile, resolvedOutDir, "solved", "ork");
        new GeneralRocketSaver().save(outFile, runner.getDocument());
        System.out.println("Saved solved design to: " + outFile.getAbsolutePath() + " (original input file left untouched)");

        return new Result(ballastKg, finHeightM, holeRadiusM, fixedSweepM, check, apogeeOk, timeOk, outFile);
    }

    /** Bisection on fin height; apogee decreases monotonically as fin height (drag) increases. */
    private static double solveFinHeightForApogee(SimRunner runner, RocketComponents.BallastControl ballast, TrapezoidFinSet finSet,
                                                    double ballastKg, double fixedSweepM,
                                                    RocketComponents.ParachuteHoleControl hole, double holeRadiusM,
                                                    EnvironmentPoint env, double targetApogeeM, double initialGuessM, Bounds bounds) {
        ballast.setTotalKg(ballastKg);
        finSet.setSweep(fixedSweepM);
        hole.setHoleRadiusM(holeRadiusM);
        double lo = bounds.minFinHeightM, hi = bounds.maxFinHeightM;

        double mid = clamp(initialGuessM, lo, hi);
        for (int i = 0; i < MAX_BISECTION_ITERS; i++) {
            if (Thread.currentThread().isInterrupted()) break;
            mid = (lo + hi) / 2.0;
            finSet.setHeight(mid);
            SimRunner.FlightResult r = runner.run(env);
            if (!r.ok) {
                System.err.println("Sim failed at fin height=" + mid + "m: " + r.error);
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

    /** Bisection on ballast mass; total flight time decreases monotonically as ballast (descent rate) increases. */
    private static double solveBallastForFlightTime(SimRunner runner, RocketComponents.BallastControl ballast, TrapezoidFinSet finSet,
                                                      double finHeightM, double fixedSweepM,
                                                      RocketComponents.ParachuteHoleControl hole, double holeRadiusM,
                                                      EnvironmentPoint env, double targetTimeMinS, double targetTimeMaxS,
                                                      double initialGuessKg, Bounds bounds) {
        finSet.setHeight(finHeightM);
        finSet.setSweep(fixedSweepM);
        hole.setHoleRadiusM(holeRadiusM);
        double targetMid = (targetTimeMinS + targetTimeMaxS) / 2.0;
        double lo = bounds.minBallastKg, hi = bounds.maxBallastKg;

        double mid = clamp(initialGuessKg, lo, hi);
        for (int i = 0; i < MAX_BISECTION_ITERS; i++) {
            if (Thread.currentThread().isInterrupted()) break;
            mid = (lo + hi) / 2.0;
            ballast.setTotalKg(mid);
            SimRunner.FlightResult r = runner.run(env);
            if (!r.ok) {
                System.err.println("Sim failed at ballast=" + mid + "kg: " + r.error);
                break;
            }
            if (r.flightTimeS >= targetTimeMinS && r.flightTimeS <= targetTimeMaxS) break;
            if (r.flightTimeS > targetMid) {
                lo = mid; // too slow/long -> need more mass -> faster descent
            } else {
                hi = mid; // too fast/short -> need less mass -> slower descent
            }
        }
        return mid;
    }

    /**
     * Bisection on parachute center-hole radius; flight time decreases monotonically as hole
     * radius increases (less canopy area -> less drag -> faster descent). Solved LAST each outer
     * round as a second, independent flight-time trim -- useful when ballast alone has saturated
     * at a bound and the flight-time target still isn't met.
     */
    private static double solveHoleRadiusForFlightTime(SimRunner runner, RocketComponents.BallastControl ballast, double ballastKg,
                                                         TrapezoidFinSet finSet, double finHeightM, double fixedSweepM,
                                                         RocketComponents.ParachuteHoleControl hole, EnvironmentPoint env,
                                                         double targetTimeMinS, double targetTimeMaxS,
                                                         double initialGuessM, Bounds bounds) {
        ballast.setTotalKg(ballastKg);
        finSet.setHeight(finHeightM);
        finSet.setSweep(fixedSweepM);
        double targetMid = (targetTimeMinS + targetTimeMaxS) / 2.0;
        double lo = bounds.minHoleRadiusM, hi = bounds.maxHoleRadiusM;

        double mid = clamp(initialGuessM, lo, hi);
        for (int i = 0; i < MAX_BISECTION_ITERS; i++) {
            if (Thread.currentThread().isInterrupted()) break;
            mid = (lo + hi) / 2.0;
            hole.setHoleRadiusM(mid);
            SimRunner.FlightResult r = runner.run(env);
            if (!r.ok) {
                System.err.println("Sim failed at hole radius=" + mid + "m: " + r.error);
                break;
            }
            if (r.flightTimeS >= targetTimeMinS && r.flightTimeS <= targetTimeMaxS) break;
            if (r.flightTimeS > targetMid) {
                lo = mid; // too slow/long -> need a bigger hole -> faster descent
            } else {
                hi = mid; // too fast/short -> need a smaller hole -> slower descent
            }
        }
        return mid;
    }

    private static double clamp(double v, double lo, double hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    /** Normalized combined error so apogee (meters) and time (seconds) are directly comparable. */
    private static double combinedError(double apogeeM, double flightTimeS, double targetApogeeM, double targetTimeCenterS) {
        double apogeeErrNorm = Math.abs(apogeeM - targetApogeeM) / Math.max(APOGEE_TOLERANCE_M, 1e-9);
        double timeErrNorm = Math.abs(flightTimeS - targetTimeCenterS) / Math.max(TIME_TOLERANCE_S, 1e-9);
        return apogeeErrNorm + timeErrNorm;
    }

    /** One simulated design point: the raw flight result plus its combined error (+Infinity if the sim failed). */
    private static final class Eval {
        final SimRunner.FlightResult result;
        final double err;

        Eval(SimRunner.FlightResult result, double err) {
            this.result = result;
            this.err = err;
        }
    }

    /** Sets ballast/fin height/hole radius (sweep always restored to its fixed value), runs one sim, scores it. */
    private static Eval evaluate(SimRunner runner, RocketComponents.BallastControl ballast, double ballastKg,
                                  TrapezoidFinSet finSet, double finHeightM, double fixedSweepM,
                                  RocketComponents.ParachuteHoleControl hole, double holeRadiusM,
                                  EnvironmentPoint env, double targetApogeeM, double targetTimeCenterS) {
        ballast.setTotalKg(ballastKg);
        finSet.setHeight(finHeightM);
        finSet.setSweep(fixedSweepM);
        hole.setHoleRadiusM(holeRadiusM);
        SimRunner.FlightResult r = runner.run(env);
        double err = r.ok ? combinedError(r.apogeeM, r.flightTimeS, targetApogeeM, targetTimeCenterS) : Double.POSITIVE_INFINITY;
        return new Eval(r, err);
    }

    private static String designDetail(double ballastKg, double finHeightM, double holeRadiusM, int pass, boolean patternSearch) {
        return String.format("ballast %.1f g, fin height %.3f m, hole radius %.2f in (%s, pass %d)",
                ballastKg * 1000, finHeightM, holeRadiusM / IN_TO_M, patternSearch ? "pattern search" : "bisection", pass + 1);
    }

    /**
     * Tracks the best (lowest combined-error) design point found so far across BOTH the bisection
     * and pattern-search phases, and pushes every candidate through the live leaderboard. Kept as
     * a single running incumbent so the pattern-search phase always explores outward from
     * whatever is truly best, regardless of which phase found it.
     */
    private static final class BestTracker {
        private final TopNLeaderboard leaderboard;
        private final LeaderboardListener leaderboardListener;
        double bestErr = Double.POSITIVE_INFINITY;
        double bestBallastKg, bestFinHeightM, bestHoleRadiusM;
        SimRunner.FlightResult best;

        BestTracker(double ballastKg, double finHeightM, double holeRadiusM,
                    TopNLeaderboard leaderboard, LeaderboardListener leaderboardListener) {
            this.bestBallastKg = ballastKg;
            this.bestFinHeightM = finHeightM;
            this.bestHoleRadiusM = holeRadiusM;
            this.leaderboard = leaderboard;
            this.leaderboardListener = leaderboardListener;
        }

        /** Always pushes ok candidates to the leaderboard; returns true only if this is a NEW global best. */
        boolean offer(Eval eval, double ballastKg, double finHeightM, double holeRadiusM, String detail) {
            if (!eval.result.ok) return false;
            if (leaderboard.offer(eval.err, eval.result.apogeeM, eval.result.flightTimeS, detail)) {
                leaderboardListener.onUpdate(leaderboard.snapshot());
            }
            if (eval.err < bestErr) {
                bestErr = eval.err;
                bestBallastKg = ballastKg;
                bestFinHeightM = finHeightM;
                bestHoleRadiusM = holeRadiusM;
                best = eval.result;
                return true;
            }
            return false;
        }
    }
}
