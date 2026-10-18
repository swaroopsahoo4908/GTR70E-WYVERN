package com.arc.sim;

import info.openrocket.core.rocketcomponent.*;

import java.util.ArrayList;
import java.util.List;

/**
 * Builds a SIMPLIFIED 2D side-profile schematic from any rocket tree -- nose cone, body tubes,
 * transitions, fin sets, stacked nose-to-tail. This is a quick visual sanity check, NOT
 * to-scale/exact CAD: it assumes components within a stage are stacked back-to-back with no
 * gaps or overlaps (true for most simple rockets, approximate for anything with unusual axial
 * offsets), and it doesn't render parallel staging (side-by-side boosters/pods) -- only serial
 * stacking (nose to tail).
 *
 * Every component is read defensively (try/catch per component) so one unexpected component
 * type or a missing getter just gets skipped rather than crashing the whole preview.
 */
public class RocketGeometryExtractor {

    // Number of axial stations (minus 1 = number of segments) sampled along each nose cone /
    // body tube / transition via SymmetricComponent.getRadius(x) -- OpenRocket's own true radius
    // profile function for whatever shape is configured (conical, ogive, ellipsoid, power series,
    // parabolic, Haack/Von Karman, ...). Sampling this directly (rather than just reading fore/aft
    // radius and interpolating a straight line between them) is what makes curved nose cone/
    // transition shapes actually render/export as curves instead of always looking like a cone.
    private static final int PROFILE_SAMPLES = 32;

    public enum BodyKind { NOSE_CONE, BODY_TUBE, TRANSITION }

    public static class BodyShape {
        public BodyKind kind;
        public double xStart, length, foreRadius, aftRadius;
        /** Radius at PROFILE_SAMPLES+1 evenly-spaced axial stations from x=0 (fore) to x=length (aft) --
         *  the TRUE shape profile (curved for ogive/ellipsoid/etc, straight for conical/tube), sampled
         *  directly from OpenRocket's own SymmetricComponent.getRadius(x). foreRadius/aftRadius above
         *  are just profileR[0]/profileR[last], kept for any code that only needs the endpoints. */
        public double[] profileR;
        public String label;
    }

    public static class FinShape {
        public double xStart; // axial position where the fin root chord begins
        public double rootChord, tipChord, sweep, height;
        public double parentRadius; // radius of the tube the fin is mounted on
        public int finCount = 4; // defaults to 4 if the component doesn't report a count
        public double baseRotationRad = 0; // radial angle of the first fin, radians
        public String label;
    }

    public static class Geometry {
        public List<BodyShape> bodies = new ArrayList<>();
        public List<FinShape> fins = new ArrayList<>();
        public double totalLength;
        public double maxRadius;
        public List<String> skipped = new ArrayList<>(); // components we couldn't render, for transparency
    }

    public static Geometry extract(Rocket rocket) {
        Geometry g = new Geometry();
        double x = 0;
        for (RocketComponent stage : rocket.getChildren()) {
            x = walkStage(stage, x, g);
        }
        g.totalLength = x;
        return g;
    }

    private static double walkStage(RocketComponent stage, double xStart, Geometry g) {
        double x = xStart;
        for (RocketComponent c : stage.getChildren()) {
            try {
                if (c instanceof NoseCone) {
                    NoseCone nc = (NoseCone) c;
                    double len = nc.getLength();
                    addBody(g, BodyKind.NOSE_CONE, x, len, sampleProfile(nc, len), safeName(c));
                    x += len;
                } else if (c instanceof BodyTube) {
                    BodyTube bt = (BodyTube) c;
                    double len = bt.getLength();
                    double r = bt.getOuterRadius();
                    addBody(g, BodyKind.BODY_TUBE, x, len, sampleProfile(bt, len), safeName(c));
                    extractFins(bt, x, len, r, g);
                    x += len;
                } else if (c instanceof Transition) {
                    Transition t = (Transition) c;
                    double len = t.getLength();
                    addBody(g, BodyKind.TRANSITION, x, len, sampleProfile(t, len), safeName(c));
                    x += len;
                } else {
                    // Internal components (mass, parachute, inner tube, bulkhead, etc.) aren't
                    // externally visible, so they're intentionally not drawn -- not an error.
                }
            } catch (Throwable t) {
                g.skipped.add(safeName(c) + " (" + t.getClass().getSimpleName() + ")");
            }
        }
        return x;
    }

    private static void extractFins(BodyTube bt, double tubeXStart, double tubeLength, double tubeRadius, Geometry g) {
        for (RocketComponent child : bt.getChildren()) {
            if (child instanceof TrapezoidFinSet) {
                try {
                    TrapezoidFinSet f = (TrapezoidFinSet) child;
                    FinShape fs = new FinShape();
                    fs.rootChord = f.getRootChord();
                    fs.tipChord = f.getTipChord();
                    fs.sweep = f.getSweep();
                    fs.height = f.getHeight();
                    fs.parentRadius = tubeRadius;
                    try {
                        fs.finCount = Math.max(1, f.getFinCount());
                        fs.baseRotationRad = f.getBaseRotation();
                    } catch (Throwable ignored) {
                        // keep the defaults (4 fins, 0 rad) set above
                    }
                    fs.label = safeName(child);
                    // Approximation: fins usually sit at the aft end of their tube.
                    fs.xStart = tubeXStart + tubeLength - fs.rootChord;
                    g.fins.add(fs);
                } catch (Throwable t) {
                    g.skipped.add(safeName(child) + " (" + t.getClass().getSimpleName() + ")");
                }
            }
        }
    }

    /**
     * Samples a component's TRUE radius profile via SymmetricComponent.getRadius(x) -- the same
     * function OpenRocket's own 3D renderer and CG/CD calculations use -- at PROFILE_SAMPLES+1
     * evenly-spaced axial stations from x=0 to x=length. This is what makes ellipsoid/ogive/power/
     * parabolic/Haack nose cones and transitions actually come out curved instead of always being
     * drawn as a straight-sided cone (which is only correct for Shape.CONICAL).
     */
    private static double[] sampleProfile(SymmetricComponent c, double length) {
        double[] r = new double[PROFILE_SAMPLES + 1];
        for (int i = 0; i <= PROFILE_SAMPLES; i++) {
            double x = length * i / (double) PROFILE_SAMPLES;
            r[i] = c.getRadius(x);
        }
        return r;
    }

    private static void addBody(Geometry g, BodyKind kind, double xStart, double length,
                                 double[] profileR, String label) {
        BodyShape s = new BodyShape();
        s.kind = kind;
        s.xStart = xStart;
        s.length = length;
        s.profileR = profileR;
        s.foreRadius = profileR[0];
        s.aftRadius = profileR[profileR.length - 1];
        s.label = label;
        g.bodies.add(s);
        double maxR = 0;
        for (double v : profileR) maxR = Math.max(maxR, v);
        g.maxRadius = Math.max(g.maxRadius, maxR);
    }

    private static String safeName(RocketComponent c) {
        try {
            String n = c.getName();
            return (n == null || n.isBlank()) ? c.getClass().getSimpleName() : n;
        } catch (Exception e) {
            return c.getClass().getSimpleName();
        }
    }
}
