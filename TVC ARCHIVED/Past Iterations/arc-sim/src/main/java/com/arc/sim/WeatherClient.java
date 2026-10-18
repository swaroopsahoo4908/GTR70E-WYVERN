package com.arc.sim;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.time.ZoneId;

/**
 * Pulls current local weather conditions from weatherapi.com for Engine 6 (WeatherDrivenDesign),
 * so a design solve can run against real launch-day-ish conditions instead of hand-typed guesses.
 *
 * RATE LIMITING: one instance is created per GUI session/tab and lives for as long as the tab
 * does. getCurrent() only calls out to the network if this is the very first call (no cache yet)
 * or force=true is passed AND the hourly cooldown has elapsed; otherwise it returns the cached
 * reading. This gives the desired "fetch when the engine starts, then at most once an hour"
 * behavior for free -- the GUI calls getCurrent(false) once when the tab is built, and every
 * subsequent Run/Refresh click reuses the cache until an hour has passed.
 */
public class WeatherClient {
    private static final long REFRESH_INTERVAL_MS = 60L * 60L * 1000L; // 1 hour
    private static final String API_BASE = "https://api.weatherapi.com/v1/current.json";

    private final String apiKey;
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    private Reading cached;
    private long lastFetchMs = -1;

    public WeatherClient(String apiKey) {
        this.apiKey = apiKey;
    }

    /** One pulled weather reading, plus the (documented, NOT measured) wind std-dev estimate derived from gust. */
    public static class Reading {
        public final String locationName;
        public final double windAvgMs;
        public final double windGustMs;
        public final double windDirDeg;
        public final double tempC;
        public final double pressureMbar;
        public final String conditionText;
        public final Instant fetchedAt;

        Reading(String locationName, double windAvgMs, double windGustMs, double windDirDeg,
                double tempC, double pressureMbar, String conditionText, Instant fetchedAt) {
            this.locationName = locationName;
            this.windAvgMs = windAvgMs;
            this.windGustMs = windGustMs;
            this.windDirDeg = windDirDeg;
            this.tempC = tempC;
            this.pressureMbar = pressureMbar;
            this.conditionText = conditionText;
            this.fetchedAt = fetchedAt;
        }

        /**
         * weatherapi.com reports an instantaneous gust, not a wind speed variance/std-dev, so
         * there's no directly-reported number to hand the solver's windStdDevMs input. This is an
         * ORDER-OF-MAGNITUDE ESTIMATE ONLY, using the common rule-of-thumb that a short-term gust
         * sits roughly 2-3 standard deviations above the mean in turbulent surface wind --
         * (gust - avg) / 2.5. It is pre-filled into an editable GUI field specifically so it can
         * be overridden with better local knowledge (a nearby anemometer log, a forecast model
         * that reports variance, prior field experience at this site, etc).
         */
        public double estimatedWindStdDevMs() {
            return Math.max(0.0, (windGustMs - windAvgMs) / 2.5);
        }

        public String formattedFetchTime() {
            return DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss").withZone(ZoneId.systemDefault()).format(fetchedAt);
        }
    }

    public boolean hasCached() {
        return cached != null;
    }

    public Reading cachedReading() {
        return cached;
    }

    /** Milliseconds until getCurrent(false) will hit the network again instead of returning the cache. */
    public long msUntilNextAllowedFetch() {
        if (lastFetchMs < 0) return 0;
        long elapsed = System.currentTimeMillis() - lastFetchMs;
        return Math.max(0, REFRESH_INTERVAL_MS - elapsed);
    }

    /**
     * Returns the current weather, hitting the network only if there's no cache yet (first call,
     * i.e. "when the engine starts") or the hourly cooldown has elapsed -- otherwise returns the
     * cached reading untouched. There is deliberately no way to bypass the cooldown (no "force"
     * option): the caller asked for at most one call per hour, full stop. Runs synchronously --
     * invoke this off the Swing EDT (a background thread), same as any other network call.
     */
    public Reading getCurrent(double lat, double lon) throws Exception {
        if (cached != null && msUntilNextAllowedFetch() > 0) {
            return cached;
        }
        String url = API_BASE + "?key=" + apiKey + "&q=" + lat + "," + lon;
        HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(15))
                .GET()
                .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        if (resp.statusCode() != 200) {
            throw new RuntimeException("Weather API returned HTTP " + resp.statusCode() + ": " + resp.body());
        }
        Object root = MiniJson.parse(resp.body());
        Object current = MiniJson.get(root, "current");
        Object location = MiniJson.get(root, "location");
        if (current == null) {
            throw new RuntimeException("Unexpected weather API response (no 'current' field): " + resp.body());
        }

        double windKph = MiniJson.asDouble(MiniJson.get(current, "wind_kph"), 0.0);
        double gustKph = MiniJson.asDouble(MiniJson.get(current, "gust_kph"), windKph);
        double windDirDeg = MiniJson.asDouble(MiniJson.get(current, "wind_degree"), 0.0);
        double tempC = MiniJson.asDouble(MiniJson.get(current, "temp_c"), 15.0);
        double pressureMbar = MiniJson.asDouble(MiniJson.get(current, "pressure_mb"), 1013.25);
        String conditionText = MiniJson.asString(MiniJson.get(current, "condition", "text"), "unknown");
        String locationName = MiniJson.asString(MiniJson.get(location, "name"), "Unknown location");

        Reading r = new Reading(locationName, windKph / 3.6, gustKph / 3.6, windDirDeg, tempC, pressureMbar,
                conditionText, Instant.now());
        cached = r;
        lastFetchMs = System.currentTimeMillis();
        return r;
    }
}
