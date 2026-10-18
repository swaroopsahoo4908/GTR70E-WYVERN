package com.arc.sim;

import info.openrocket.core.rocketcomponent.BodyTube;
import info.openrocket.core.rocketcomponent.MassComponent;
import info.openrocket.core.rocketcomponent.Parachute;
import info.openrocket.core.rocketcomponent.Rocket;
import info.openrocket.core.rocketcomponent.RocketComponent;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Finds ballast and recovery components by STRUCTURAL POSITION rather than by name, because
 * CSWARCMOD1D.ork (and probably your other iterations) names every MassComponent generically
 * "Mass Component" -- there's nothing unique to match on by name.
 *
 * Convention used here, matching how you described the design:
 *   - "Ballast" = whatever MassComponent(s) live directly inside the LOWEST (bottommost /
 *     aft-most) BodyTube of the rocket -- i.e. the tube that also holds the fin set and motor
 *     mount in your file. If there are several MassComponents in that tube, their masses are
 *     scaled together (proportionally, preserving their relative split) when the solver drives
 *     "total ballast" up or down.
 *   - "Recovery" = the first Parachute component found anywhere in the tree (your file only has
 *     one: the "18" parachute" in the upper body tube).
 *
 * If your actual ballast lives somewhere else (e.g. you add a dedicated ballast tube later),
 * update findLowestBodyTube() below accordingly -- e.g. match on a specific body tube name/id
 * instead of "last body tube in the last top-level stage".
 *
 * NOTE: deliberately does NOT import/reference OpenRocket's stage class by name (it's been
 * renamed between versions -- Stage vs AxialStage -- and differs by core version). Instead we
 * just take the LAST top-level child of Rocket as "the stage" (true for single-stage rockets
 * regardless of what that class is actually called) and walk its children generically.
 */
public class RocketComponents {

    public static BodyTube findLowestBodyTube(Rocket rocket) {
        List<RocketComponent> topLevel = rocket.getChildren();
        if (topLevel.isEmpty()) {
            throw new IllegalStateException("Rocket has no top-level components -- is this a valid .ork file?");
        }
        RocketComponent lastStage = topLevel.get(topLevel.size() - 1); // last stage = sustainer/only stage

        BodyTube lowest = null;
        for (RocketComponent c : lastStage.getChildren()) {
            if (c instanceof BodyTube) lowest = (BodyTube) c; // last one wins -> bottommost
        }
        if (lowest == null) {
            throw new IllegalStateException("No BodyTube found in stage '" + lastStage.getName() + "'.");
        }
        return lowest;
    }

    public static List<MassComponent> findBallastComponents(Rocket rocket) {
        BodyTube lowest = findLowestBodyTube(rocket);
        List<MassComponent> result = new ArrayList<>();
        for (RocketComponent c : lowest.getChildren()) {
            if (c instanceof MassComponent) result.add((MassComponent) c);
        }
        if (result.isEmpty()) {
            throw new IllegalStateException("No MassComponent found inside the lowest body tube ('" +
                    lowest.getName() + "'). Add one there in the OpenRocket GUI to act as ballast " +
                    "(the solver will drive its mass; starting value doesn't matter).");
        }
        return result;
    }

    public static Parachute findMainParachute(Rocket rocket) {
        return findFirst(rocket, Parachute.class)
                .orElseThrow(() -> new IllegalStateException("No Parachute component found anywhere in the rocket."));
    }

    public static info.openrocket.core.rocketcomponent.TrapezoidFinSet findFinSet(Rocket rocket) {
        return findFirst(rocket, info.openrocket.core.rocketcomponent.TrapezoidFinSet.class)
                .orElseThrow(() -> new IllegalStateException("No TrapezoidFinSet found anywhere in the rocket."));
    }

    @SuppressWarnings("unchecked")
    private static <T> Optional<T> findFirst(RocketComponent node, Class<T> type) {
        if (type.isInstance(node)) return Optional.of((T) node);
        for (RocketComponent child : node.getChildren()) {
            Optional<T> r = findFirst(child, type);
            if (r.isPresent()) return r;
        }
        return Optional.empty();
    }

    /**
     * Controls a group of MassComponents as a single "total ballast mass" knob, preserving
     * their original relative mass split (or splitting evenly if they all started at ~0).
     */
    public static class BallastControl {
        private final List<MassComponent> components;
        private final double[] baseMasses;
        private final double baseSum;

        public BallastControl(List<MassComponent> components) {
            this.components = components;
            this.baseMasses = new double[components.size()];
            double sum = 0;
            for (int i = 0; i < components.size(); i++) {
                baseMasses[i] = components.get(i).getComponentMass();
                sum += baseMasses[i];
            }
            this.baseSum = sum;
        }

        public void setTotalKg(double totalKg) {
            if (baseSum <= 1e-9) {
                double each = totalKg / components.size();
                for (MassComponent m : components) m.setComponentMass(each);
            } else {
                for (int i = 0; i < components.size(); i++) {
                    components.get(i).setComponentMass(totalKg * (baseMasses[i] / baseSum));
                }
            }
        }

        public double getCurrentTotalKg() {
            double sum = 0;
            for (MassComponent m : components) sum += m.getComponentMass();
            return sum;
        }

        public int count() {
            return components.size();
        }
    }

    /**
     * Controls a circular center "spill hole" cut into the main parachute canopy, modeled as an
     * effective-diameter reduction: a hole of radius r removes pi*r^2 of canopy area, so the
     * equivalent full circular canopy that would produce the same open area has
     * effectiveDiameter = sqrt(fullDiameter^2 - (2r)^2). This is a standard approximation for
     * spill-hole drag reduction and is simple/robust against Parachute-Cd API differences between
     * OpenRocket core versions.
     *
     * The chute's ORIGINAL diameter (as loaded from the .ork file) is captured once at
     * construction and used as the reference "full canopy" size for every subsequent hole-radius
     * setting, so repeated setHoleRadiusM() calls during a bisection search don't compound.
     */
    public static class ParachuteHoleControl {
        private final Parachute chute;
        private final double baseDiameterM;

        public ParachuteHoleControl(Parachute chute) {
            this.chute = chute;
            this.baseDiameterM = chute.getDiameter();
        }

        public double getBaseDiameterM() {
            return baseDiameterM;
        }

        /** Sets the spill-hole radius (meters); clamps to keep the effective diameter non-negative. */
        public void setHoleRadiusM(double holeRadiusM) {
            double holeDiam = 2.0 * Math.max(0.0, holeRadiusM);
            double underRoot = (baseDiameterM * baseDiameterM) - (holeDiam * holeDiam);
            double effectiveDiameterM = underRoot > 0 ? Math.sqrt(underRoot) : 0.0;
            chute.setDiameter(effectiveDiameterM);
        }

        /** Restores the parachute to its original (no-hole) diameter. */
        public void clearHole() {
            chute.setDiameter(baseDiameterM);
        }
    }
}
