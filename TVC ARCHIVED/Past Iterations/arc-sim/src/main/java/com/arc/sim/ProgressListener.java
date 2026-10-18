package com.arc.sim;

/** Callback for long-running engines to report progress + an estimated-time-remaining. */
public interface ProgressListener {
    /**
     * @param processed   combinations/samples completed so far
     * @param total       total combinations/samples for this run
     * @param etaSeconds  estimated seconds remaining, based on actual measured rate so far
     *                    (NaN if not enough data yet to estimate)
     */
    void onProgress(long processed, long total, double etaSeconds);

    /** A no-op listener, used when nobody's listening (e.g. some CLI paths). */
    ProgressListener NONE = (processed, total, etaSeconds) -> {};
}
