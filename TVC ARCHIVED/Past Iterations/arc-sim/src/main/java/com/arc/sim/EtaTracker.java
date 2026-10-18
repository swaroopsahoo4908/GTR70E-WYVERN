package com.arc.sim;

/** Tracks elapsed time vs. items processed to produce a live "estimated time remaining". */
public class EtaTracker {
    private final long startMillis = System.currentTimeMillis();
    private final long total;

    public EtaTracker(long total) {
        this.total = total;
    }

    /** Seconds remaining, estimated from actual throughput so far. NaN until we have data. */
    public double etaSeconds(long processed) {
        if (processed <= 0) return Double.NaN;
        double elapsedSec = (System.currentTimeMillis() - startMillis) / 1000.0;
        double rate = processed / elapsedSec; // items/sec
        if (rate <= 0) return Double.NaN;
        return (total - processed) / rate;
    }

    public static String formatDuration(double seconds) {
        if (Double.isNaN(seconds) || seconds < 0) return "calculating...";
        long s = Math.round(seconds);
        long h = s / 3600;
        long m = (s % 3600) / 60;
        long sec = s % 60;
        if (h > 0) return String.format("%dh %dm %ds", h, m, sec);
        if (m > 0) return String.format("%dm %ds", m, sec);
        return String.format("%ds", sec);
    }
}
