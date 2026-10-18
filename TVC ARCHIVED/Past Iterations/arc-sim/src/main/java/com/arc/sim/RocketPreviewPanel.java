package com.arc.sim;

import javax.swing.*;
import java.awt.*;
import java.awt.geom.GeneralPath;
import java.util.List;

/** Paints a RocketGeometryExtractor.Geometry as a simple 2D side-profile schematic. */
public class RocketPreviewPanel extends JPanel {

    private RocketGeometryExtractor.Geometry geometry;
    private String rocketName = "";

    public void setGeometry(RocketGeometryExtractor.Geometry geometry, String rocketName) {
        this.geometry = geometry;
        this.rocketName = rocketName;
        repaint();
    }

    @Override
    protected void paintComponent(Graphics g0) {
        super.paintComponent(g0);
        Graphics2D g = (Graphics2D) g0;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, getWidth(), getHeight());

        if (geometry == null || geometry.totalLength <= 0) {
            g.setColor(Color.GRAY);
            g.drawString("No rocket loaded yet.", 16, 24);
            return;
        }

        int margin = 40;
        int w = getWidth() - 2 * margin;
        int h = getHeight() - 2 * margin;
        if (w <= 10 || h <= 10) return;

        double maxDim = Math.max(geometry.totalLength, geometry.maxRadius * 2 * 1.6); // leave room for fins sticking out
        double scale = Math.min(w / geometry.totalLength, h / (geometry.maxRadius * 2 * 2.2));
        int centerY = getHeight() / 2;

        g.setColor(new Color(40, 60, 90));
        g.setStroke(new BasicStroke(1.5f));
        g.setFont(g.getFont().deriveFont(11f));

        // Body components: draw the TRUE sampled radius profile (curved for ogive/ellipsoid/power/
        // parabolic/Haack nose cones and transitions, straight for conical/tube), top half only,
        // mirrored for the bottom (symmetric side profile) -- rather than always connecting just
        // the fore/aft endpoints with a straight line, which flattens every shape into a cone.
        for (RocketGeometryExtractor.BodyShape s : geometry.bodies) {
            double[] profile = s.profileR;
            int stations = profile.length;
            double dx = s.length / (double) (stations - 1);

            GeneralPath top = new GeneralPath();
            GeneralPath bottom = new GeneralPath();
            for (int i = 0; i < stations; i++) {
                int x = margin + (int) ((s.xStart + i * dx) * scale);
                int rTop = centerY - (int) (profile[i] * scale);
                int rBot = centerY + (int) (profile[i] * scale);
                if (i == 0) { top.moveTo(x, rTop); bottom.moveTo(x, rBot); }
                else { top.lineTo(x, rTop); bottom.lineTo(x, rBot); }
            }
            // Close top+bottom into one outline: top profile left-to-right, then bottom profile
            // right-to-left, back to the start.
            GeneralPath path = new GeneralPath(top);
            for (int i = stations - 1; i >= 0; i--) {
                int x = margin + (int) ((s.xStart + i * dx) * scale);
                int rBot = centerY + (int) (profile[i] * scale);
                path.lineTo(x, rBot);
            }
            path.closePath();

            g.setColor(new Color(225, 235, 245));
            g.fill(path);
            g.setColor(new Color(40, 60, 90));
            g.draw(path);
        }

        // Fins: draw above and below the body tube (2D side view shows both sides of a 4-fin rocket
        // as two projected fins; for 3-fin rockets this over-draws slightly, which is an accepted
        // simplification for a quick visual check).
        for (RocketGeometryExtractor.FinShape f : geometry.fins) {
            int rootX1 = margin + (int) (f.xStart * scale);
            int rootX2 = margin + (int) ((f.xStart + f.rootChord) * scale);
            int tipX1 = margin + (int) ((f.xStart + f.sweep) * scale);
            int tipX2 = margin + (int) ((f.xStart + f.sweep + f.tipChord) * scale);
            int bodyTop = centerY - (int) (f.parentRadius * scale);
            int bodyBottom = centerY + (int) (f.parentRadius * scale);
            int finTipTop = bodyTop - (int) (f.height * scale);
            int finTipBottom = bodyBottom + (int) (f.height * scale);

            g.setColor(new Color(200, 90, 60, 180));
            GeneralPath top = new GeneralPath();
            top.moveTo(rootX1, bodyTop);
            top.lineTo(tipX1, finTipTop);
            top.lineTo(tipX2, finTipTop);
            top.lineTo(rootX2, bodyTop);
            top.closePath();
            g.fill(top);
            g.setColor(new Color(140, 50, 30));
            g.draw(top);

            g.setColor(new Color(200, 90, 60, 180));
            GeneralPath bottom = new GeneralPath();
            bottom.moveTo(rootX1, bodyBottom);
            bottom.lineTo(tipX1, finTipBottom);
            bottom.lineTo(tipX2, finTipBottom);
            bottom.lineTo(rootX2, bodyBottom);
            bottom.closePath();
            g.fill(bottom);
            g.setColor(new Color(140, 50, 30));
            g.draw(bottom);
        }

        g.setColor(Color.DARK_GRAY);
        g.drawString(rocketName + "   (length \u2248 " + String.format("%.2f", geometry.totalLength) + " m, "
                + "max diameter \u2248 " + String.format("%.3f", geometry.maxRadius * 2) + " m)", margin, 20);
        g.setFont(g.getFont().deriveFont(Font.ITALIC, 10f));
        g.setColor(Color.GRAY);
        g.drawString("Simplified schematic -- approximate axial positions, not to-scale CAD. Serial staging only.", margin, getHeight() - 10);

        if (!geometry.skipped.isEmpty()) {
            g.setColor(new Color(180, 120, 0));
            g.drawString("Not rendered (unsupported/unreadable): " + String.join(", ", geometry.skipped), margin, 34);
        }
    }
}
