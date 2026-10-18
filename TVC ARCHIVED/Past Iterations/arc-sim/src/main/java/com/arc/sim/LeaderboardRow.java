package com.arc.sim;

/**
 * One ranked entry in a live "top N" leaderboard -- either "closest simulation to target"
 * (Engine 3) or "most favorable conditions" (Engine 1 / 2). Score is a normalized combined
 * error against the run's target(s); LOWER is always better/closer, regardless of which engine
 * produced it, so a single table/column layout works for all three.
 */
public class LeaderboardRow {
    public final int rank;
    public final double score;
    public final double apogeeM;
    public final double flightTimeS;
    public final String detail;

    public LeaderboardRow(int rank, double score, double apogeeM, double flightTimeS, String detail) {
        this.rank = rank;
        this.score = score;
        this.apogeeM = apogeeM;
        this.flightTimeS = flightTimeS;
        this.detail = detail;
    }
}
