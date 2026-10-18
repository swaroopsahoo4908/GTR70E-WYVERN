package com.arc.sim;

/** One environmental condition set: wind model + atmosphere + site. */
public class EnvironmentPoint {
    public double windSpeedAvgMs;      // m/s
    public double windSpeedStdDevMs;   // m/s
    public double turbulenceIntensity; // fraction, e.g. 0.08 = 8%
    public double windDirectionDeg;    // 0-360, meteorological (degrees from north)
    public double temperatureC;        // deg C
    public double pressureMbar;        // mbar (hPa)
    public LaunchSite site;

    public EnvironmentPoint(double windSpeedAvgMs, double windSpeedStdDevMs, double turbulenceIntensity,
                             double windDirectionDeg, double temperatureC, double pressureMbar, LaunchSite site) {
        this.windSpeedAvgMs = windSpeedAvgMs;
        this.windSpeedStdDevMs = windSpeedStdDevMs;
        this.turbulenceIntensity = turbulenceIntensity;
        this.windDirectionDeg = windDirectionDeg;
        this.temperatureC = temperatureC;
        this.pressureMbar = pressureMbar;
        this.site = site;
    }

    // Standard Temperature & Pressure reference values used for the zero-condition baseline row.
    public static final double STP_TEMP_C = 15.0;            // ISA sea-level standard temperature
    public static final double STP_PRESSURE_MBAR = 1013.25;  // ISA sea-level standard pressure

    /**
     * "Everything-zero" baseline condition: no wind, no wind std dev, no turbulence, no wind
     * direction bias, atmosphere at STP (15 C / 1013.25 mbar) -- but still using the REAL
     * lat/long/altitude of the given launch site (so site elevation still affects air density).
     * Written as a fixed reference row in every output sheet so every run has a clean, repeatable
     * apples-to-apples baseline alongside whatever environmental envelope was swept.
     */
    public static EnvironmentPoint stpBaseline(LaunchSite site) {
        return new EnvironmentPoint(0.0, 0.0, 0.0, 0.0, STP_TEMP_C, STP_PRESSURE_MBAR, site);
    }
}
