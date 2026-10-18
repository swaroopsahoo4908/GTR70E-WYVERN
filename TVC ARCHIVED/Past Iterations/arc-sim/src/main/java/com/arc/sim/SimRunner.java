package com.arc.sim;

import info.openrocket.core.document.OpenRocketDocument;
import info.openrocket.core.document.Simulation;
import info.openrocket.core.file.GeneralRocketLoader;
import info.openrocket.core.simulation.FlightData;
import info.openrocket.core.simulation.SimulationOptions;
import info.openrocket.core.startup.OpenRocketCore;

import java.io.File;

/**
 * Thin wrapper around the OpenRocket core simulation engine.
 *
 * *** UNIT WARNING - READ BEFORE TRUSTING RESULTS ***
 * OpenRocket's core module works internally in SI units and radians for angles. The setter
 * names below (setWindDirection, setLaunchTemperature, setLaunchPressure, etc.) are correct as
 * of the OpenRocket 23.09+ / info.openrocket.core API, but exact accepted units for a couple of
 * fields (Kelvin vs Celsius for temperature, Pa vs mbar for pressure, radians vs degrees for
 * wind direction) can silently differ between versions and are the single most likely source of
 * a wrong-but-plausible-looking result. Before trusting any output from this tool:
 *   1. Open SimulationOptions.java (or its javadoc) for the exact core version in pom.xml and
 *      confirm the unit each setter expects.
 *   2. Run one sanity simulation through this tool AND through the OpenRocket GUI with
 *      identical inputs, and confirm apogee/flight time match within numerical noise.
 * Do not skip step 2 -- it costs five minutes and catches unit-conversion bugs that no amount
 * of code review will.
 */
public class SimRunner {

    private final OpenRocketDocument document;

    public SimRunner(File orkFile) throws Exception {
        OpenRocketCore.initialize();
        GeneralRocketLoader loader = new GeneralRocketLoader(orkFile);
        this.document = loader.load();
    }

    public OpenRocketDocument getDocument() {
        return document;
    }

    /** Runs simulation index 0 in the document with the given environment applied. */
    public FlightResult run(EnvironmentPoint env) {
        return run(0, env);
    }

    public FlightResult run(int simulationIndex, EnvironmentPoint env) {
        Simulation sim = document.getSimulation(simulationIndex);
        SimulationOptions opt = sim.getOptions();

        // --- Wind model ---
        opt.setWindSpeedAverage(env.windSpeedAvgMs);
        opt.setWindSpeedDeviation(env.windSpeedStdDevMs);
        opt.setWindTurbulenceIntensity(env.turbulenceIntensity); // fraction, e.g. 0.08
        opt.setWindDirection(Math.toRadians(env.windDirectionDeg));

        // --- Atmosphere: turn off ISA standard atmosphere so custom temp/pressure are used ---
        opt.setISAAtmosphere(false);
        opt.setLaunchTemperature(env.temperatureC + 273.15);      // Celsius -> Kelvin
        opt.setLaunchPressure(env.pressureMbar * 100.0);          // mbar -> Pa

        // --- Launch site geodetics ---
        opt.setLaunchLatitude(env.site.latitudeDeg);
        opt.setLaunchLongitude(env.site.longitudeDeg);
        opt.setLaunchAltitude(env.site.altitudeM);

        try {
            sim.simulate();
            FlightData data = sim.getSimulatedData();
            double apogee = data.getMaxAltitude();     // meters AGL
            double flightTime = data.getFlightTime();  // seconds, pad to landing
            return FlightResult.success(apogee, flightTime);
        } catch (Exception e) {
            return FlightResult.failure(e.getMessage());
        }
    }

    /** Simple result holder. */
    public static class FlightResult {
        public final boolean ok;
        public final double apogeeM;
        public final double flightTimeS;
        public final String error;

        private FlightResult(boolean ok, double apogeeM, double flightTimeS, String error) {
            this.ok = ok;
            this.apogeeM = apogeeM;
            this.flightTimeS = flightTimeS;
            this.error = error;
        }

        static FlightResult success(double apogeeM, double flightTimeS) {
            return new FlightResult(true, apogeeM, flightTimeS, null);
        }

        static FlightResult failure(String error) {
            return new FlightResult(false, Double.NaN, Double.NaN, error);
        }
    }
}
