package com.arc.sim;

import java.util.List;

/** Callback for long-running engines to push a live "top N" leaderboard update to the GUI. */
public interface LeaderboardListener {
    void onUpdate(List<LeaderboardRow> topResults);

    /** A no-op listener, used when nobody's listening (e.g. CLI paths). */
    LeaderboardListener NONE = topResults -> {};
}
