package com.arc.sim;

import info.openrocket.core.rocketcomponent.MassComponent;
import info.openrocket.core.rocketcomponent.Parachute;
import info.openrocket.core.rocketcomponent.TrapezoidFinSet;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.plaf.ColorUIResource;
import javax.swing.plaf.metal.DefaultMetalTheme;
import javax.swing.plaf.metal.MetalLookAndFeel;
import java.awt.*;
import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * Desktop GUI for the six arc-sim engines plus a built-in data viewer. Wraps EnvironmentSweep,
 * FullFactorialSweep, DesignSolver, OrkBatchGenerator, MeshExporter, and WeatherDrivenDesign
 * behind forms + file pickers + a live log + a progress bar, instead of positional CLI args. The
 * "Data Viewer" tab (DataViewerPanel) is a read-only browser for this toolkit's three tabular
 * output formats: .xlsx (Engine 1), .parquet (Engine 2, via the dependency-free MiniParquet
 * reader), and .csv (Engine 4's batch manifest).
 *
 * Engines 1, 2, 3, and 6 each show one or two live top-10 leaderboards (LeaderboardPanel) while
 * running -- "most favorable conditions seen so far" for the sweep engines, "closest simulation to
 * target seen so far" for the design solver -- updated in place every time a new result displaces
 * an entry on the table.
 *
 * Jobs run one at a time on a single background worker thread so two engines never touch the
 * OpenRocket core simultaneously. Cancel interrupts the running job; all long-running engines
 * (EnvironmentSweep, FullFactorialSweep, DesignSolver, OrkBatchGenerator, WeatherDrivenDesign)
 * check for interruption periodically and stop cleanly, writing/using whatever partial results
 * they'd accumulated so far.
 */
public class ArcSimGui extends JFrame {

    private final JTextArea log = new JTextArea();
    private final JLabel statusLabel = new JLabel("Idle");
    private final JProgressBar progressBar = new JProgressBar(0, 100);
    private final JLabel etaLabel = new JLabel(" ");
    private final JButton cancelButton = new JButton("Cancel");
    private final ExecutorService jobExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "arc-sim-job");
        t.setDaemon(true);
        return t;
    });
    private volatile Future<?> currentJob;
    private static File lastDir = new File(System.getProperty("user.dir"));

    public ArcSimGui() {
        super("ARC Rocket Simulation Toolkit");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(960, 780);          // fallback size for window managers that ignore MAXIMIZED_BOTH
        setMinimumSize(new java.awt.Dimension(800, 600));
        setLocationRelativeTo(null);
        setExtendedState(getExtendedState() | JFrame.MAXIMIZED_BOTH); // fill the screen on open

        redirectSystemStreamsToLog();

        JTabbedPane tabs = new JTabbedPane();
        tabs.addTab("Engine 1: Monte Carlo Sweep", buildSweepTab());
        tabs.addTab("Engine 2: Full Factorial Sweep", buildFullSweepTab());
        tabs.addTab("Engine 3: Design Solver", buildDesignTab());
        tabs.addTab("Engine 4: Ork Batch Generator", buildBatchTab());
        tabs.addTab("Engine 5: Geometry Export", buildGeometryExportTab());
        tabs.addTab("Engine 6: Weather-Driven Design", buildWeatherTab());
        tabs.addTab("Data Viewer", new DataViewerPanel());

        log.setEditable(false);
        log.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        log.setBackground(new Color(0x15, 0x15, 0x19));
        log.setForeground(new Color(0xe8, 0xe8, 0xec));
        log.setCaretColor(new Color(0xff, 0x7a, 0x3d));
        JScrollPane logScroll = new JScrollPane(log);
        logScroll.setBorder(BorderFactory.createTitledBorder("Log"));
        logScroll.setPreferredSize(new Dimension(900, 230));

        statusLabel.setFont(statusLabel.getFont().deriveFont(Font.BOLD));
        progressBar.setStringPainted(true);
        progressBar.setPreferredSize(new Dimension(220, 20));

        JPanel statusBar = new JPanel(new BorderLayout(8, 0));
        statusBar.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createMatteBorder(1, 0, 0, 0, new Color(0x3c, 0x3c, 0x48)),
                new EmptyBorder(6, 8, 6, 8)));
        JPanel leftStatus = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        leftStatus.add(statusLabel);
        leftStatus.add(progressBar);
        leftStatus.add(etaLabel);
        statusBar.add(leftStatus, BorderLayout.WEST);

        JButton clearLogButton = new JButton("Clear Log");
        clearLogButton.addActionListener(e -> log.setText(""));
        JPanel rightButtons = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        cancelButton.setEnabled(false);
        cancelButton.setFont(cancelButton.getFont().deriveFont(Font.BOLD));
        cancelButton.setForeground(new Color(0xff, 0x6b, 0x6b));
        cancelButton.setToolTipText("Interrupts the running job -- it stops at its next safe checkpoint and " +
                "uses/saves whatever partial result it had so far, rather than just hanging.");
        cancelButton.addActionListener(e -> {
            if (currentJob != null) {
                currentJob.cancel(true);
                appendLog("Cancel requested -- stopping at the next safe checkpoint...\n");
            }
        });
        rightButtons.add(clearLogButton);
        rightButtons.add(cancelButton);
        statusBar.add(rightButtons, BorderLayout.EAST);

        JPanel bottom = new JPanel(new BorderLayout());
        bottom.add(logScroll, BorderLayout.CENTER);
        bottom.add(statusBar, BorderLayout.SOUTH);

        JSplitPane split = new JSplitPane(JSplitPane.VERTICAL_SPLIT, tabs, bottom);
        split.setResizeWeight(0.55);
        setContentPane(split);

        appendLog("ARC Rocket Simulation Toolkit ready. Pick a tab, fill in the form, and click Run.\n");
    }

    // ---------------------------------------------------------------- Engine 1: Monte Carlo

    private JPanel buildSweepTab() {
        JTextField orkField = new JTextField();
        SiteSelector siteSelector = new SiteSelector();
        JSpinner samplesSpinner = new JSpinner(new SpinnerNumberModel(5000, 100, 2_000_000, 500));
        JTextField outDirField = new JTextField();

        FormBuilder form = new FormBuilder();
        form.addFileRow("Rocket (.ork) file:", orkField, true, "OpenRocket files (*.ork)", "ork");
        form.addRow("Launch site:", siteSelector);
        form.addRow("Number of Monte Carlo samples:", samplesSpinner);
        form.addDirRow("Output folder (blank = \"" + OutputNaming.MONTE_CARLO_FOLDER + "\" next to the rocket file):", outDirField);
        form.addRow("", hintLabel("Filename is generated automatically as " +
                "&lt;rocketName&gt;_montecarlo_&lt;timestamp&gt;.xlsx -- never overwrites a previous run."));

        LeaderboardPanel leaderboardPanel = new LeaderboardPanel(
                "Most favorable conditions seen so far (live, closest to apogee/time target)", "Error score");

        JButton runButton = new JButton("Run Monte Carlo Sweep");
        stylePrimaryButton(runButton);
        runButton.addActionListener(e -> {
            File ork = requireFile(orkField, "rocket .ork file");
            if (ork == null) return;
            File outDir = resolveOutDir(outDirField, ork, OutputNaming.MONTE_CARLO_FOLDER);
            LaunchSite site = siteSelector.getSelectedSite();
            int samples = (Integer) samplesSpinner.getValue();

            leaderboardPanel.clear();
            runJob("Engine 1: Monte Carlo Sweep", listener -> {
                File out = EnvironmentSweep.run(ork, site, samples, outDir, listener, leaderboardPanel::update);
                if (out != null) openFileLocation(out);
            });
        });

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(verticalSplit(form.panel(), leaderboardPanel, 0.35), BorderLayout.CENTER);
        panel.add(buttonRow(runButton), BorderLayout.SOUTH);
        return withPadding(panel);
    }

    // ---------------------------------------------------------------- Engine 2: Full factorial

    private JPanel buildFullSweepTab() {
        JTextField orkField = new JTextField();
        JTextField configField = new JTextField(new File(lastDir, "sweep_grid.properties").getPath());
        JTextField outDirField = new JTextField();
        JCheckBox forceBox = new JCheckBox("Force run even if over the safety cap");

        FormBuilder form = new FormBuilder();
        form.addFileRow("Rocket (.ork) file:", orkField, true, "OpenRocket files (*.ork)", "ork");
        JPanel configRow = form.addFileRow("Grid config (.properties):", configField, true, "Properties files (*.properties)", "properties");
        JButton editConfigButton = new JButton("Edit config...");
        editConfigButton.addActionListener(e -> editPropertiesFile(new File(configField.getText().trim())));
        configRow.add(editConfigButton);
        form.addDirRow("Output folder (blank = \"" + OutputNaming.FULL_FACTORIAL_FOLDER + "\" next to the rocket file):", outDirField);
        form.addRow("", hintLabel("Filename is generated automatically as " +
                "&lt;rocketName&gt;_fullfactorial_&lt;timestamp&gt;.parquet -- never overwrites a previous run. " +
                "Parquet instead of xlsx because a true full-factorial run can produce far more rows than Excel's " +
                "~1,048,576-row-per-sheet limit; open it in the Data Viewer tab, or pandas/DuckDB/Excel-with-a-plugin. " +
                "A companion &lt;...&gt;_summary.csv (success rate + correlations) is written alongside it."));
        form.addRow("", forceBox);
        form.addRow("", hintLabel("Sites for this engine are set inside the config file " +
                "(comma-separated: MDRA_SOD_FARM, SPAAR_LANCASTER, or CUSTOM:lat|lon|alt) -- click Edit config to change them."));

        LeaderboardPanel leaderboardPanel = new LeaderboardPanel(
                "Most favorable conditions seen so far (live, closest to apogee/time target)", "Error score");

        JButton previewButton = new JButton("Preview combination count & time estimate");
        JButton runButton = new JButton("Run Full Factorial Sweep");
        stylePrimaryButton(runButton);

        previewButton.addActionListener(e -> {
            File configFile = requireExistingFile(configField, "grid config .properties file");
            if (configFile == null) return;
            runJob("Preview grid size", listener -> {
                GridAxis.SweepConfig cfg = GridAxis.load(configFile);
                long total = cfg.totalCombos();
                double estSec = total * 0.03;
                System.out.printf("Grid total: %,d combinations%n", total);
                System.out.printf("Estimated time: ~%.1f hours single-threaded, ~%.1f hours across %d threads%n",
                        estSec / 3600.0, estSec / 3600.0 / cfg.threads, cfg.threads);
                if (total > cfg.maxCombosSafety) {
                    System.out.println("This EXCEEDS the safety cap (" + cfg.maxCombosSafety +
                            ") -- you'll need to check 'Force' or coarsen the grid to actually run it.");
                }
            });
        });

        runButton.addActionListener(e -> {
            File ork = requireFile(orkField, "rocket .ork file");
            if (ork == null) return;
            File configFile = requireExistingFile(configField, "grid config .properties file");
            if (configFile == null) return;
            File outDir = resolveOutDir(outDirField, ork, OutputNaming.FULL_FACTORIAL_FOLDER);
            boolean force = forceBox.isSelected();

            leaderboardPanel.clear();
            runJob("Engine 2: Full Factorial Sweep", listener -> {
                File out = FullFactorialSweep.run(ork, configFile, outDir, force, listener, leaderboardPanel::update);
                if (out != null) openFileLocation(out);
            });
        });

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(verticalSplit(form.panel(), leaderboardPanel, 0.35), BorderLayout.CENTER);
        panel.add(buttonRow(previewButton, runButton), BorderLayout.SOUTH);
        return withPadding(panel);
    }

    // ---------------------------------------------------------------- Engine 3: Design solver

    private JPanel buildDesignTab() {
        JTextField orkField = new JTextField();
        JButton inspectButton = new JButton("Inspect Rocket");

        JComboBox<RocketInspector.Item<MassComponent>> ballastCombo = new JComboBox<>();
        JComboBox<RocketInspector.Item<Parachute>> parachuteCombo = new JComboBox<>();
        JComboBox<RocketInspector.Item<TrapezoidFinSet>> finSetCombo = new JComboBox<>();
        ballastCombo.setEnabled(false);
        parachuteCombo.setEnabled(false);
        finSetCombo.setEnabled(false);

        RocketPreviewPanel previewPanel = new RocketPreviewPanel();
        previewPanel.setPreferredSize(new Dimension(880, 180));
        previewPanel.setBorder(BorderFactory.createTitledBorder("Rocket preview (approximate schematic, not to-scale CAD)"));

        SiteSelector siteSelector = new SiteSelector();
        JSpinner targetApogee = new JSpinner(new SpinnerNumberModel(243.84, 0.0, 100000.0, 1.0)); // 800 ft default
        JSpinner targetTimeMin = new JSpinner(new SpinnerNumberModel(37.5, 0.0, 600.0, 0.5));
        JSpinner targetTimeMax = new JSpinner(new SpinnerNumberModel(39.5, 0.0, 600.0, 0.5));
        JSpinner windAvg = new JSpinner(new SpinnerNumberModel(3.8, 0.0, 20.0, 0.1));
        JSpinner windStdDev = new JSpinner(new SpinnerNumberModel(0.6, 0.0, 5.0, 0.1));
        JSpinner turbulencePct = new JSpinner(new SpinnerNumberModel(13.4, 0.0, 50.0, 0.5));
        JSpinner windDir = new JSpinner(new SpinnerNumberModel(270.0, 0.0, 360.0, 0.5));
        JSpinner tempC = new JSpinner(new SpinnerNumberModel(7.06, -50.0, 60.0, 0.5));
        JSpinner pressureMbar = new JSpinner(new SpinnerNumberModel(999.76, 800.0, 1100.0, 0.5));

        JSpinner maxBallastKg = new JSpinner(new SpinnerNumberModel(5.0, 0.0, 1000.0, 0.5));
        JSpinner maxFinHeightM = new JSpinner(new SpinnerNumberModel(0.5, 0.01, 10.0, 0.05));
        JSpinner maxHoleRadiusIn = new JSpinner(new SpinnerNumberModel(2.0, 0.0, 4.0, 0.1));
        JSpinner maxSolverPasses = new JSpinner(new SpinnerNumberModel(1000, 1, 100000, 50));
        JTextField outDirField = new JTextField();
        JButton bigRocketButton = new JButton("Big rocket? Use larger bounds");
        bigRocketButton.addActionListener(e -> {
            DesignSolver.Bounds big = DesignSolver.Bounds.big();
            maxBallastKg.setValue(big.maxBallastKg);
            maxFinHeightM.setValue(big.maxFinHeightM);
        });

        // Holds the SimRunner created by "Inspect Rocket" so Run uses the SAME loaded document
        // (and therefore the SAME component object instances the combos reference).
        final SimRunner[] inspectedRunner = new SimRunner[1];

        inspectButton.addActionListener(e -> {
            File ork = requireFile(orkField, "rocket .ork file");
            if (ork == null) return;
            try {
                SimRunner runner = new SimRunner(ork);
                inspectedRunner[0] = runner;
                info.openrocket.core.rocketcomponent.Rocket rocket = runner.getDocument().getRocket();

                previewPanel.setGeometry(RocketGeometryExtractor.extract(rocket), ork.getName());

                List<RocketInspector.Item<MassComponent>> masses = RocketInspector.listMassComponents(rocket);
                List<RocketInspector.Item<Parachute>> chutes = RocketInspector.listParachutes(rocket);
                List<RocketInspector.Item<TrapezoidFinSet>> fins = RocketInspector.listTrapezoidFinSets(rocket);

                ballastCombo.setModel(new DefaultComboBoxModel<>(masses.toArray(new RocketInspector.Item[0])));
                parachuteCombo.setModel(new DefaultComboBoxModel<>(chutes.toArray(new RocketInspector.Item[0])));
                finSetCombo.setModel(new DefaultComboBoxModel<>(fins.toArray(new RocketInspector.Item[0])));

                selectMatching(ballastCombo, RocketInspector.suggestBallastDefault(rocket));
                selectMatching(parachuteCombo, RocketInspector.suggestMainParachuteDefault(chutes));
                selectMatching(finSetCombo, RocketInspector.suggestFinSetDefault(fins));

                ballastCombo.setEnabled(!masses.isEmpty());
                parachuteCombo.setEnabled(!chutes.isEmpty());
                finSetCombo.setEnabled(!fins.isEmpty());

                appendLog(String.format("Inspected %s: found %d mass component(s), %d parachute(s), %d trapezoidal fin set(s). " +
                        "Defaults pre-selected -- override any of them below if the guess is wrong.%n",
                        ork.getName(), masses.size(), chutes.size(), fins.size()));
                if (fins.isEmpty()) {
                    appendLog("WARNING: no trapezoidal fin sets found -- Engine 3 needs one to drive fin height/sweep. " +
                            "If your fins are a different shape (freeform/elliptical), this engine can't solve fin geometry for this rocket.\n");
                }
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Could not inspect rocket: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
        });

        FormBuilder rocketForm = new FormBuilder();
        rocketForm.addFileRow("Rocket (.ork) file:", orkField, true, "OpenRocket files (*.ork)", "ork");
        rocketForm.addRow("", inspectButton);
        rocketForm.addRow("Ballast component:", ballastCombo);
        rocketForm.addRow("Parachute (held fixed):", parachuteCombo);
        rocketForm.addRow("Fin set to solve:", finSetCombo);

        FormBuilder targetForm = new FormBuilder();
        targetForm.addRow("Target apogee (m):", targetApogee);
        targetForm.addRow("Target flight time min (s):", targetTimeMin);
        targetForm.addRow("Target flight time max (s):", targetTimeMax);
        targetForm.addRow("Launch site:", siteSelector);

        FormBuilder envForm = new FormBuilder();
        envForm.addRow("Wind average (m/s):", windAvg);
        envForm.addRow("Wind std dev (m/s):", windStdDev);
        envForm.addRow("Turbulence intensity (%):", turbulencePct);
        envForm.addRow("Wind direction (deg):", windDir);
        envForm.addRow("Temperature (C):", tempC);
        envForm.addRow("Pressure (mbar):", pressureMbar);

        FormBuilder boundsForm = new FormBuilder();
        boundsForm.addRow("Max ballast (kg):", maxBallastKg);
        boundsForm.addRow("Max fin height (m):", maxFinHeightM);
        boundsForm.addRow("Max parachute center hole radius (in, 4 in = 8 in diameter max):", maxHoleRadiusIn);
        boundsForm.addRow("Max solver passes (ballast+fin+hole rounds):", maxSolverPasses);
        boundsForm.addRow("", bigRocketButton);
        boundsForm.addDirRow("Output folder (blank = \"" + OutputNaming.OPENROCKET_SOLVES_FOLDER + "\" next to the rocket file):", outDirField);

        Box groupedForm = Box.createVerticalBox();
        groupedForm.add(titledGroup("Rocket & components", rocketForm.panel()));
        groupedForm.add(titledGroup("Targets & launch site", targetForm.panel()));
        groupedForm.add(titledGroup("Fixed environment (single condition)", envForm.panel()));
        groupedForm.add(titledGroup("Search bounds", boundsForm.panel()));

        LeaderboardPanel leaderboardPanel = new LeaderboardPanel(
                "Closest simulation to target seen so far (live)", "Error score");

        JButton runButton = new JButton("Solve Ballast + Fin Height + Parachute Hole");
        runButton.addActionListener(e -> {
            if (inspectedRunner[0] == null) {
                JOptionPane.showMessageDialog(this, "Click 'Inspect Rocket' first so the solver knows which " +
                        "ballast/parachute/fin set to use.", "Not inspected yet", JOptionPane.WARNING_MESSAGE);
                return;
            }
            LaunchSite site = siteSelector.getSelectedSite();

            DesignSolver.ComponentSelection selection = new DesignSolver.ComponentSelection();
            RocketInspector.Item<MassComponent> ballastItem = (RocketInspector.Item<MassComponent>) ballastCombo.getSelectedItem();
            RocketInspector.Item<Parachute> chuteItem = (RocketInspector.Item<Parachute>) parachuteCombo.getSelectedItem();
            RocketInspector.Item<TrapezoidFinSet> finItem = (RocketInspector.Item<TrapezoidFinSet>) finSetCombo.getSelectedItem();
            if (ballastItem != null) selection.ballastComponents = List.of(ballastItem.component);
            if (chuteItem != null) selection.parachute = chuteItem.component;
            if (finItem != null) selection.finSet = finItem.component;

            DesignSolver.Bounds bounds = new DesignSolver.Bounds();
            bounds.maxBallastKg = (Double) maxBallastKg.getValue();
            bounds.maxFinHeightM = (Double) maxFinHeightM.getValue();
            bounds.maxHoleRadiusM = (Double) maxHoleRadiusIn.getValue() * 0.0254; // in -> m
            bounds.maxOuterIters = (Integer) maxSolverPasses.getValue();

            SimRunner runner = inspectedRunner[0];
            File ork = new File(orkField.getText().trim());
            File outDir = resolveOutDir(outDirField, ork, OutputNaming.OPENROCKET_SOLVES_FOLDER);

            leaderboardPanel.clear();
            runJob("Engine 3: Design Solver", listener -> DesignSolver.run(
                    runner, ork,
                    (Double) targetApogee.getValue(),
                    (Double) targetTimeMin.getValue(),
                    (Double) targetTimeMax.getValue(),
                    site,
                    (Double) windAvg.getValue(),
                    (Double) windStdDev.getValue(),
                    (Double) turbulencePct.getValue(),
                    (Double) windDir.getValue(),
                    (Double) tempC.getValue(),
                    (Double) pressureMbar.getValue(),
                    selection, bounds, outDir, listener, leaderboardPanel::update
            ));
        });

        stylePrimaryButton(runButton);

        JPanel top = new JPanel(new BorderLayout());
        top.add(previewPanel, BorderLayout.NORTH);
        JScrollPane scroll = new JScrollPane(groupedForm);
        scroll.setBorder(null);
        scroll.getVerticalScrollBar().setUnitIncrement(16);
        top.add(scroll, BorderLayout.CENTER);

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(verticalSplit(top, leaderboardPanel, 0.6), BorderLayout.CENTER);
        panel.add(buttonRow(runButton), BorderLayout.SOUTH);
        return withPadding(panel);
    }

    // ---------------------------------------------------------------- Engine 4: Ork batch generator

    private JPanel buildBatchTab() {
        JTextField orkField = new JTextField();
        JTextField configField = new JTextField(new File(lastDir, "batch_grid.properties").getPath());
        JTextField outParentDirField = new JTextField();
        JCheckBox forceBox = new JCheckBox("Force run even if over the safety cap");

        FormBuilder form = new FormBuilder();
        form.addFileRow("Rocket (.ork) file:", orkField, true, "OpenRocket files (*.ork)", "ork");
        JPanel configRow = form.addFileRow("Design grid config (.properties):", configField, true, "Properties files (*.properties)", "properties");
        JButton editConfigButton = new JButton("Edit config...");
        editConfigButton.addActionListener(e -> editPropertiesFile(new File(configField.getText().trim())));
        configRow.add(editConfigButton);
        form.addDirRow("Output parent folder (blank = \"" + OutputNaming.OPENROCKET_SOLVES_FOLDER + "\" next to the rocket file):", outParentDirField);
        form.addRow("", hintLabel("Every generated .ork lands together in one new subfolder (inside the parent folder " +
                "above): &lt;rocketName&gt;_batch_&lt;timestamp&gt;/ -- individual files are named with their varied " +
                "parameter values baked in, so nothing in this batch (or any previous batch) ever gets overwritten. " +
                "A manifest.csv lands in that same subfolder, linking every .ork's filename to its parameter values " +
                "(open it in the Data Viewer tab)."));
        form.addRow("", forceBox);
        form.addRow("", hintLabel("Design variants: ballast / fin height / fin sweep / parachute hole " +
                "radius. Leave an axis's .min/.max/.step OUT of the config entirely to keep that parameter unvaried " +
                "across every generated file. By default NO simulation is run -- add the config's optional " +
                "simCheck.* properties (click Edit config) to ALSO simulate every variant under one fixed atmosphere " +
                "and check it against a target apogee/flight-time window (same shape as Engine 3); the manifest then " +
                "gets apogee/flight-time/meets-target columns too, and each saved .ork carries its own simulated " +
                "result."));

        JButton previewButton = new JButton("Preview file count");
        JButton runButton = new JButton("Run Batch Generator");
        stylePrimaryButton(runButton);

        previewButton.addActionListener(e -> {
            File configFile = requireExistingFile(configField, "design grid .properties file");
            if (configFile == null) return;
            runJob("Preview batch size", listener -> {
                OrkBatchGenerator.BatchConfig cfg = OrkBatchGenerator.loadConfig(configFile);
                long total = cfg.totalCombos();
                System.out.printf("TOTAL FILES: %,d%n", total);
                if (total > cfg.maxFilesSafety) {
                    System.out.println("This EXCEEDS the safety cap (" + cfg.maxFilesSafety +
                            ") -- you'll need to check 'Force' or coarsen the grid to actually run it.");
                }
            });
        });

        runButton.addActionListener(e -> {
            File ork = requireFile(orkField, "rocket .ork file");
            if (ork == null) return;
            File configFile = requireExistingFile(configField, "design grid .properties file");
            if (configFile == null) return;
            File outParentDir = resolveOutDir(outParentDirField, ork, OutputNaming.OPENROCKET_SOLVES_FOLDER);
            boolean force = forceBox.isSelected();

            runJob("Engine 4: Ork Batch Generator", listener -> {
                File batchDir = OrkBatchGenerator.run(ork, configFile, outParentDir, force, listener);
                if (batchDir != null) openDirectory(batchDir);
            });
        });

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(form.panel(), BorderLayout.NORTH);
        panel.add(buttonRow(previewButton, runButton), BorderLayout.SOUTH);
        return withPadding(panel);
    }

    // ---------------------------------------------------------------- Engine 5: Geometry export

    private JPanel buildGeometryExportTab() {
        JTextField orkField = new JTextField();
        JButton loadButton = new JButton("Load Rocket");
        RocketPreviewPanel previewPanel = new RocketPreviewPanel();
        previewPanel.setPreferredSize(new Dimension(880, 180));
        previewPanel.setBorder(BorderFactory.createTitledBorder("Rocket preview (approximate schematic, not to-scale CAD)"));

        JCheckBox stlBox = new JCheckBox("STL", true);
        JCheckBox objBox = new JCheckBox("OBJ", true);
        JTextField outDirField = new JTextField();

        final RocketGeometryExtractor.Geometry[] loadedGeometry = new RocketGeometryExtractor.Geometry[1];
        final File[] loadedOrk = new File[1];

        loadButton.addActionListener(e -> {
            File ork = requireFile(orkField, "rocket .ork file");
            if (ork == null) return;
            try {
                SimRunner runner = new SimRunner(ork);
                info.openrocket.core.rocketcomponent.Rocket rocket = runner.getDocument().getRocket();
                RocketGeometryExtractor.Geometry geo = RocketGeometryExtractor.extract(rocket);
                previewPanel.setGeometry(geo, ork.getName());
                loadedGeometry[0] = geo;
                loadedOrk[0] = ork;
                appendLog(String.format("Loaded %s: %d body section(s), %d fin set(s), total length %.3f m.%n",
                        ork.getName(), geo.bodies.size(), geo.fins.size(), geo.totalLength));
                if (!geo.skipped.isEmpty()) {
                    appendLog("Skipped (not renderable as external geometry): " + geo.skipped + "\n");
                }
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Could not load rocket: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
        });

        FormBuilder form = new FormBuilder();
        form.addFileRow("Rocket (.ork) file:", orkField, true, "OpenRocket files (*.ork)", "ork");
        form.addRow("", loadButton);
        JPanel formatRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 12, 0));
        formatRow.add(stlBox);
        formatRow.add(objBox);
        form.addRow("Export format(s):", formatRow);
        form.addDirRow("Output folder (blank = \"" + OutputNaming.CAD_FILES_FOLDER + "\" next to the rocket file):", outDirField);
        form.addRow("", hintLabel("Basic body-of-revolution + flat-fin mesh (not CAD-fidelity) -- good for a " +
                "quick 3D-print / CAD-import sanity check of the outer mold line, not a substitute for real CAD " +
                "geometry. No wall thickness, internal components, or airfoil fin sections. Units: millimeters. " +
                "Each run gets its own new subfolder (&lt;rocketName&gt;_geometry_&lt;timestamp&gt;/) inside the " +
                "output folder above, so nothing is ever overwritten and every export's files stay together."));

        JButton exportButton = new JButton("Export Mesh");
        stylePrimaryButton(exportButton);
        exportButton.addActionListener(e -> {
            if (loadedGeometry[0] == null) {
                JOptionPane.showMessageDialog(this, "Click 'Load Rocket' first.", "Not loaded yet", JOptionPane.WARNING_MESSAGE);
                return;
            }
            if (!stlBox.isSelected() && !objBox.isSelected()) {
                JOptionPane.showMessageDialog(this, "Pick at least one export format.", "Nothing to export", JOptionPane.WARNING_MESSAGE);
                return;
            }
            RocketGeometryExtractor.Geometry geo = loadedGeometry[0];
            File ork = loadedOrk[0];
            File outDir = resolveOutDir(outDirField, ork, OutputNaming.CAD_FILES_FOLDER);
            boolean doStl = stlBox.isSelected(), doObj = objBox.isSelected();

            runJob("Engine 5: Geometry Export", listener -> {
                // Each run gets its own new "<rocketName>_geometry_<timestamp>/" subfolder (same
                // pattern Engine 4's batch generator uses) so re-exporting the same rocket never
                // overwrites a previous run and all of a run's files (STL + OBJ) stay grouped
                // together instead of scattered loose in the output folder.
                File runDir = OutputNaming.uniqueDir(ork, outDir, "geometry");
                String base = OutputNaming.baseName(ork);
                List<MeshExporter.Triangle> tris = MeshExporter.buildMesh(geo);
                System.out.println("Built mesh: " + tris.size() + " triangles. Writing to " + runDir.getAbsolutePath());
                File written = null;
                if (doStl) {
                    File stlOut = new File(runDir, base + ".stl");
                    MeshExporter.writeStl(tris, stlOut, ork.getName());
                    System.out.println("Wrote " + stlOut.getAbsolutePath());
                    written = stlOut;
                }
                if (doObj) {
                    File objOut = new File(runDir, base + ".obj");
                    MeshExporter.writeObj(tris, objOut, ork.getName());
                    System.out.println("Wrote " + objOut.getAbsolutePath());
                    written = objOut;
                }
                if (written != null) openDirectory(runDir);
            });
        });

        JScrollPane scroll = new JScrollPane(form.panel());
        scroll.setBorder(null);

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(verticalSplit(previewPanel, scroll, 0.4), BorderLayout.CENTER);
        panel.add(buttonRow(exportButton), BorderLayout.SOUTH);
        return withPadding(panel);
    }

    // ---------------------------------------------------------------- Engine 6: Weather-driven design

    private JPanel buildWeatherTab() {
        WeatherClient weatherClient = new WeatherClient("1a9eb4ca137442acb3b164018261507");
        SiteSelector weatherSiteSelector = new SiteSelector();

        JLabel weatherStatusLabel = new JLabel("Not fetched yet.");
        weatherStatusLabel.setForeground(Color.GRAY);
        JSpinner windAvgSpinner = new JSpinner(new SpinnerNumberModel(0.0, 0.0, 100.0, 0.1));
        JSpinner windGustSpinner = new JSpinner(new SpinnerNumberModel(0.0, 0.0, 150.0, 0.1));
        JSpinner windStdDevSpinner = new JSpinner(new SpinnerNumberModel(0.5, 0.0, 20.0, 0.1));
        JSpinner turbulencePctSpinner = new JSpinner(new SpinnerNumberModel(10.0, 0.0, 50.0, 0.5));
        JSpinner windDirSpinner = new JSpinner(new SpinnerNumberModel(0.0, 0.0, 360.0, 0.5));
        JSpinner tempSpinner = new JSpinner(new SpinnerNumberModel(15.0, -50.0, 60.0, 0.5));
        JSpinner pressureSpinner = new JSpinner(new SpinnerNumberModel(1013.25, 800.0, 1100.0, 0.5));
        windAvgSpinner.setEnabled(false);
        windGustSpinner.setEnabled(false); // gust is informational/read-only -- std dev spinner is the editable derived value

        JButton fetchButton = new JButton("Fetch Weather Now");

        Runnable[] doFetch = new Runnable[1];
        doFetch[0] = () -> {
            weatherStatusLabel.setText("Fetching...");
            fetchButton.setEnabled(false);
            LaunchSite site = weatherSiteSelector.getSelectedSite();
            Thread t = new Thread(() -> {
                try {
                    WeatherClient.Reading r = weatherClient.getCurrent(site.latitudeDeg, site.longitudeDeg);
                    SwingUtilities.invokeLater(() -> {
                        windAvgSpinner.setValue(r.windAvgMs);
                        windGustSpinner.setValue(r.windGustMs);
                        windStdDevSpinner.setValue(r.estimatedWindStdDevMs());
                        windDirSpinner.setValue(r.windDirDeg);
                        tempSpinner.setValue(r.tempC);
                        pressureSpinner.setValue(r.pressureMbar);
                        long cooldownMin = weatherClient.msUntilNextAllowedFetch() / 60000;
                        weatherStatusLabel.setText(String.format(
                                "%s -- \"%s\" -- fetched %s (next auto-refresh available in ~%d min)",
                                r.locationName, r.conditionText, r.formattedFetchTime(), cooldownMin));
                        appendLog(String.format("Weather pulled for %s: wind %.2f m/s (gust %.2f m/s), %.0f deg, " +
                                        "%.1f C, %.1f mbar -- \"%s\" (fetched %s)%n",
                                r.locationName, r.windAvgMs, r.windGustMs, r.windDirDeg, r.tempC, r.pressureMbar,
                                r.conditionText, r.formattedFetchTime()));
                        fetchButton.setEnabled(true);
                    });
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> {
                        weatherStatusLabel.setText("Fetch failed: " + ex.getMessage());
                        fetchButton.setEnabled(true);
                    });
                }
            }, "weather-fetch");
            t.setDaemon(true);
            t.start();
        };
        fetchButton.addActionListener(e -> doFetch[0].run());
        // Fetch once as soon as this tab is built ("when the engine starts") -- every later click of
        // Fetch/Run reuses WeatherClient's own hourly cache/cooldown, so this never calls out more
        // than once an hour no matter how the tab or Run button are used.
        SwingUtilities.invokeLater(() -> doFetch[0].run());

        FormBuilder weatherForm = new FormBuilder();
        weatherForm.addRow("Launch site (weather pulled for this location):", weatherSiteSelector);
        weatherForm.addRow("", fetchButton);
        weatherForm.addRow("", weatherStatusLabel);
        weatherForm.addRow("Wind average (m/s, from API):", windAvgSpinner);
        weatherForm.addRow("Wind gust (m/s, from API, informational):", windGustSpinner);
        weatherForm.addRow("Wind std dev (m/s, ESTIMATED from gust -- override if you know better):", windStdDevSpinner);
        weatherForm.addRow("Turbulence intensity (%, NOT from API -- typical default, override as needed):", turbulencePctSpinner);
        weatherForm.addRow("Wind direction (deg, from API):", windDirSpinner);
        weatherForm.addRow("Temperature (C, from API):", tempSpinner);
        weatherForm.addRow("Pressure (mbar, from API):", pressureSpinner);
        weatherForm.addRow("", hintLabel("Wind std dev isn't reported by the weather API -- it's estimated from the " +
                "gust value ((gust - avg) / 2.5, a rough turbulence rule of thumb), pre-filled but editable. " +
                "Turbulence intensity isn't reported either and defaults to 10% -- override both if you have better " +
                "local knowledge (a nearby anemometer log, prior field experience, etc)."));

        JTextField orkField = new JTextField();
        JButton inspectButton = new JButton("Inspect Rocket");
        JComboBox<RocketInspector.Item<MassComponent>> ballastCombo = new JComboBox<>();
        JComboBox<RocketInspector.Item<Parachute>> parachuteCombo = new JComboBox<>();
        JComboBox<RocketInspector.Item<TrapezoidFinSet>> finSetCombo = new JComboBox<>();
        ballastCombo.setEnabled(false);
        parachuteCombo.setEnabled(false);
        finSetCombo.setEnabled(false);

        RocketPreviewPanel previewPanel = new RocketPreviewPanel();
        previewPanel.setPreferredSize(new Dimension(880, 160));
        previewPanel.setBorder(BorderFactory.createTitledBorder("Rocket preview (approximate schematic, not to-scale CAD)"));

        final SimRunner[] inspectedRunner = new SimRunner[1];

        inspectButton.addActionListener(e -> {
            File ork = requireFile(orkField, "rocket .ork file");
            if (ork == null) return;
            try {
                SimRunner runner = new SimRunner(ork);
                inspectedRunner[0] = runner;
                info.openrocket.core.rocketcomponent.Rocket rocket = runner.getDocument().getRocket();

                previewPanel.setGeometry(RocketGeometryExtractor.extract(rocket), ork.getName());

                List<RocketInspector.Item<MassComponent>> masses = RocketInspector.listMassComponents(rocket);
                List<RocketInspector.Item<Parachute>> chutes = RocketInspector.listParachutes(rocket);
                List<RocketInspector.Item<TrapezoidFinSet>> fins = RocketInspector.listTrapezoidFinSets(rocket);

                ballastCombo.setModel(new DefaultComboBoxModel<>(masses.toArray(new RocketInspector.Item[0])));
                parachuteCombo.setModel(new DefaultComboBoxModel<>(chutes.toArray(new RocketInspector.Item[0])));
                finSetCombo.setModel(new DefaultComboBoxModel<>(fins.toArray(new RocketInspector.Item[0])));

                selectMatching(ballastCombo, RocketInspector.suggestBallastDefault(rocket));
                selectMatching(parachuteCombo, RocketInspector.suggestMainParachuteDefault(chutes));
                selectMatching(finSetCombo, RocketInspector.suggestFinSetDefault(fins));

                ballastCombo.setEnabled(!masses.isEmpty());
                parachuteCombo.setEnabled(!chutes.isEmpty());
                finSetCombo.setEnabled(!fins.isEmpty());

                appendLog(String.format("Inspected %s: found %d mass component(s), %d parachute(s), %d trapezoidal fin set(s).%n",
                        ork.getName(), masses.size(), chutes.size(), fins.size()));
                if (fins.isEmpty()) {
                    appendLog("WARNING: no trapezoidal fin sets found -- Engine 6 needs one, same as Engine 3.\n");
                }
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Could not inspect rocket: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
        });

        FormBuilder rocketForm = new FormBuilder();
        rocketForm.addFileRow("Rocket (.ork) file:", orkField, true, "OpenRocket files (*.ork)", "ork");
        rocketForm.addRow("", inspectButton);
        rocketForm.addRow("Ballast component:", ballastCombo);
        rocketForm.addRow("Parachute (held fixed):", parachuteCombo);
        rocketForm.addRow("Fin set to solve:", finSetCombo);

        JSpinner targetApogee = new JSpinner(new SpinnerNumberModel(243.84, 0.0, 100000.0, 1.0));
        JSpinner targetTimeMin = new JSpinner(new SpinnerNumberModel(37.5, 0.0, 600.0, 0.5));
        JSpinner targetTimeMax = new JSpinner(new SpinnerNumberModel(39.5, 0.0, 600.0, 0.5));

        FormBuilder targetForm = new FormBuilder();
        targetForm.addRow("Target apogee (m):", targetApogee);
        targetForm.addRow("Target flight time min (s):", targetTimeMin);
        targetForm.addRow("Target flight time max (s):", targetTimeMax);

        JSpinner maxBallastKg = new JSpinner(new SpinnerNumberModel(5.0, 0.0, 1000.0, 0.5));
        JSpinner maxFinHeightM = new JSpinner(new SpinnerNumberModel(0.5, 0.01, 10.0, 0.05));
        JSpinner maxHoleRadiusIn = new JSpinner(new SpinnerNumberModel(2.0, 0.0, 4.0, 0.1));
        JSpinner maxSolverPasses = new JSpinner(new SpinnerNumberModel(1000, 1, 100000, 50));
        JSpinner localSweepSamples = new JSpinner(new SpinnerNumberModel(1000, 50, 200000, 100));
        JButton bigRocketButton = new JButton("Big rocket? Use larger bounds");
        bigRocketButton.addActionListener(e -> {
            DesignSolver.Bounds big = DesignSolver.Bounds.big();
            maxBallastKg.setValue(big.maxBallastKg);
            maxFinHeightM.setValue(big.maxFinHeightM);
        });

        FormBuilder boundsForm = new FormBuilder();
        boundsForm.addRow("Max ballast (kg):", maxBallastKg);
        boundsForm.addRow("Max fin height (m):", maxFinHeightM);
        boundsForm.addRow("Max parachute center hole radius (in, 4 in = 8 in diameter max):", maxHoleRadiusIn);
        boundsForm.addRow("Max solver passes (ballast+fin+hole rounds):", maxSolverPasses);
        boundsForm.addRow("Local-conditions sweep sample count:", localSweepSamples);
        boundsForm.addRow("", bigRocketButton);
        boundsForm.addRow("", hintLabel("The local-conditions sweep re-uses the ALREADY-SOLVED design (fixed ballast/" +
                "fin height/hole radius) across a narrow, realistic day-of envelope centered on the pulled weather -- " +
                "not Engine 1's wide worst-case envelope. Margin fin sets always re-solve fin height only at +/-0.5 " +
                "and +/-1.0 wind-speed std deviations around the pulled average, holding ballast and hole radius fixed."));

        JTextField outDirField = new JTextField();
        FormBuilder outputForm = new FormBuilder();
        outputForm.addDirRow("Output folder (blank = \"" + OutputNaming.ENGINE_6_FOLDER + "\" next to the rocket file):", outDirField);

        Box groupedForm = Box.createVerticalBox();
        groupedForm.add(titledGroup("Live weather source", weatherForm.panel()));
        groupedForm.add(titledGroup("Rocket & components", rocketForm.panel()));
        groupedForm.add(titledGroup("Targets", targetForm.panel()));
        groupedForm.add(titledGroup("Search bounds & local sweep settings", boundsForm.panel()));
        groupedForm.add(titledGroup("Output", outputForm.panel()));

        LeaderboardPanel mainLeaderboard = new LeaderboardPanel(
                "Closest simulation to target seen so far -- main solve (live)", "Error score");
        LeaderboardPanel localLeaderboard = new LeaderboardPanel(
                "Most favorable local conditions seen so far -- day-of variability check (live)", "Error score");
        JPanel leaderboards = new JPanel(new GridLayout(2, 1, 0, 6));
        leaderboards.add(mainLeaderboard);
        leaderboards.add(localLeaderboard);

        JButton runButton = new JButton("Run Weather-Driven Design (Solve + CAD + Sweep + Margin Fins)");
        stylePrimaryButton(runButton);
        runButton.addActionListener(e -> {
            if (inspectedRunner[0] == null) {
                JOptionPane.showMessageDialog(this, "Click 'Inspect Rocket' first so the solver knows which " +
                        "ballast/parachute/fin set to use.", "Not inspected yet", JOptionPane.WARNING_MESSAGE);
                return;
            }
            if (!weatherClient.hasCached()) {
                JOptionPane.showMessageDialog(this, "No weather data yet -- wait for the fetch to finish (see status above).",
                        "Weather not ready", JOptionPane.WARNING_MESSAGE);
                return;
            }
            LaunchSite site = weatherSiteSelector.getSelectedSite();

            DesignSolver.ComponentSelection selection = new DesignSolver.ComponentSelection();
            RocketInspector.Item<MassComponent> ballastItem = (RocketInspector.Item<MassComponent>) ballastCombo.getSelectedItem();
            RocketInspector.Item<Parachute> chuteItem = (RocketInspector.Item<Parachute>) parachuteCombo.getSelectedItem();
            RocketInspector.Item<TrapezoidFinSet> finItem = (RocketInspector.Item<TrapezoidFinSet>) finSetCombo.getSelectedItem();
            if (ballastItem != null) selection.ballastComponents = List.of(ballastItem.component);
            if (chuteItem != null) selection.parachute = chuteItem.component;
            if (finItem != null) selection.finSet = finItem.component;

            DesignSolver.Bounds bounds = new DesignSolver.Bounds();
            bounds.maxBallastKg = (Double) maxBallastKg.getValue();
            bounds.maxFinHeightM = (Double) maxFinHeightM.getValue();
            bounds.maxHoleRadiusM = (Double) maxHoleRadiusIn.getValue() * 0.0254;
            bounds.maxOuterIters = (Integer) maxSolverPasses.getValue();

            SimRunner runner = inspectedRunner[0];
            File ork = new File(orkField.getText().trim());
            File outDir = resolveOutDir(outDirField, ork, OutputNaming.ENGINE_6_FOLDER);
            int sweepSamples = (Integer) localSweepSamples.getValue();

            // Build a synthetic Reading from the (possibly user-edited) spinner values, rather than
            // the raw cached API reading, so any manual overrides above actually take effect.
            WeatherClient.Reading base = weatherClient.cachedReading();
            WeatherClient.Reading effective = new WeatherClient.Reading(
                    base.locationName, (Double) windAvgSpinner.getValue(), (Double) windGustSpinner.getValue(),
                    (Double) windDirSpinner.getValue(), (Double) tempSpinner.getValue(), (Double) pressureSpinner.getValue(),
                    base.conditionText, base.fetchedAt);
            double windStdDevMs = (Double) windStdDevSpinner.getValue();
            double turbulencePct = (Double) turbulencePctSpinner.getValue();

            mainLeaderboard.clear();
            localLeaderboard.clear();
            runJob("Engine 6: Weather-Driven Design", listener -> WeatherDrivenDesign.run(
                    runner, ork, effective, windStdDevMs, turbulencePct,
                    (Double) targetApogee.getValue(), (Double) targetTimeMin.getValue(), (Double) targetTimeMax.getValue(),
                    site, selection, bounds, sweepSamples, outDir, listener, mainLeaderboard::update, localLeaderboard::update
            ));
        });

        JPanel top = new JPanel(new BorderLayout());
        top.add(previewPanel, BorderLayout.NORTH);
        JScrollPane scroll = new JScrollPane(groupedForm);
        scroll.setBorder(null);
        scroll.getVerticalScrollBar().setUnitIncrement(16);
        top.add(scroll, BorderLayout.CENTER);

        JPanel panel = new JPanel(new BorderLayout());
        panel.add(verticalSplit(top, leaderboards, 0.6), BorderLayout.CENTER);
        panel.add(buttonRow(runButton), BorderLayout.SOUTH);
        return withPadding(panel);
    }

    @SuppressWarnings("unchecked")
    private static <T> void selectMatching(JComboBox<RocketInspector.Item<T>> combo, T target) {
        if (target == null) return;
        ComboBoxModel<RocketInspector.Item<T>> model = combo.getModel();
        for (int i = 0; i < model.getSize(); i++) {
            if (model.getElementAt(i).component == target) {
                combo.setSelectedIndex(i);
                return;
            }
        }
    }

    // ---------------------------------------------------------------- Custom/predefined site picker

    /** Combo of predefined sites + "Custom...", revealing lat/long/altitude fields when Custom is picked. */
    private class SiteSelector extends JPanel {
        private final JComboBox<String> combo;
        private final JSpinner latSpinner;
        private final JSpinner lonSpinner;
        private final JSpinner altSpinner;

        SiteSelector() {
            super(new FlowLayout(FlowLayout.LEFT, 6, 0));
            combo = new JComboBox<>(new String[]{
                    LaunchSite.MDRA_SOD_FARM.label, LaunchSite.SPAAR_LANCASTER.label, "Custom..."
            });
            latSpinner = new JSpinner(new SpinnerNumberModel(39.0, -90.0, 90.0, 0.0001));
            lonSpinner = new JSpinner(new SpinnerNumberModel(-76.1, -180.0, 180.0, 0.0001));
            altSpinner = new JSpinner(new SpinnerNumberModel(100.0, -500.0, 10000.0, 1.0));
            ((JSpinner.NumberEditor) latSpinner.getEditor()).getFormat().setMaximumFractionDigits(5);
            ((JSpinner.NumberEditor) lonSpinner.getEditor()).getFormat().setMaximumFractionDigits(5);
            latSpinner.setPreferredSize(new Dimension(90, latSpinner.getPreferredSize().height));
            lonSpinner.setPreferredSize(new Dimension(90, lonSpinner.getPreferredSize().height));
            altSpinner.setPreferredSize(new Dimension(70, altSpinner.getPreferredSize().height));

            setCustomFieldsEnabled(false);
            combo.addActionListener(e -> setCustomFieldsEnabled(combo.getSelectedIndex() == 2));

            add(combo);
            add(new JLabel("lat:"));
            add(latSpinner);
            add(new JLabel("lon:"));
            add(lonSpinner);
            add(new JLabel("alt(m):"));
            add(altSpinner);
        }

        private void setCustomFieldsEnabled(boolean enabled) {
            latSpinner.setEnabled(enabled);
            lonSpinner.setEnabled(enabled);
            altSpinner.setEnabled(enabled);
        }

        LaunchSite getSelectedSite() {
            switch (combo.getSelectedIndex()) {
                case 0: return LaunchSite.MDRA_SOD_FARM;
                case 1: return LaunchSite.SPAAR_LANCASTER;
                default: return LaunchSite.custom((Double) latSpinner.getValue(), (Double) lonSpinner.getValue(), (Double) altSpinner.getValue());
            }
        }
    }

    // ---------------------------------------------------------------- Job execution plumbing

    private interface Job {
        void run(ProgressListener listener) throws Exception;
    }

    private void runJob(String name, Job job) {
        setRunning(true);
        SwingUtilities.invokeLater(() -> {
            progressBar.setIndeterminate(true);
            progressBar.setValue(0);
            etaLabel.setText(" ");
        });
        appendLog(">>> Starting: " + name + "\n");

        ProgressListener guiListener = (processed, total, etaSeconds) -> SwingUtilities.invokeLater(() -> {
            if (total > 0) {
                progressBar.setIndeterminate(false);
                int pct = (int) Math.round(100.0 * processed / total);
                progressBar.setValue(Math.min(100, Math.max(0, pct)));
                progressBar.setString(processed + " / " + total);
            }
            etaLabel.setText(Double.isNaN(etaSeconds) ? " " : "ETA: " + EtaTracker.formatDuration(etaSeconds));
        });

        currentJob = jobExecutor.submit(() -> {
            long start = System.currentTimeMillis();
            try {
                job.run(guiListener);
                double secs = (System.currentTimeMillis() - start) / 1000.0;
                appendLog(String.format(">>> Finished: %s (%.1fs)%n", name, secs));
            } catch (Exception ex) {
                appendLog(">>> FAILED: " + name + " -- " + ex + "\n");
                for (StackTraceElement el : ex.getStackTrace()) {
                    appendLog("    at " + el + "\n");
                }
            } finally {
                SwingUtilities.invokeLater(() -> {
                    setRunning(false);
                    progressBar.setIndeterminate(false);
                    progressBar.setValue(0);
                    progressBar.setString("");
                    etaLabel.setText(" ");
                });
            }
        });
    }

    private void setRunning(boolean running) {
        statusLabel.setText(running ? "Running..." : "Idle");
        cancelButton.setEnabled(running);
    }

    private void appendLog(String text) {
        if (SwingUtilities.isEventDispatchThread()) {
            log.append(text);
            log.setCaretPosition(log.getDocument().getLength());
        } else {
            SwingUtilities.invokeLater(() -> appendLog(text));
        }
    }

    private void redirectSystemStreamsToLog() {
        PrintStream original = System.out;
        OutputStream teeOut = new OutputStream() {
            @Override
            public void write(int b) {
                original.write(b);
                appendLog(String.valueOf((char) b));
            }

            @Override
            public void write(byte[] b, int off, int len) {
                original.write(b, off, len);
                appendLog(new String(b, off, len, StandardCharsets.UTF_8));
            }
        };
        PrintStream teeStream = new PrintStream(teeOut, true, StandardCharsets.UTF_8);
        System.setOut(teeStream);
        System.setErr(teeStream);
    }

    // ---------------------------------------------------------------- Small UI helpers

    private JPanel withPadding(JPanel p) {
        p.setBorder(new EmptyBorder(12, 12, 12, 12));
        return p;
    }

    private JPanel buttonRow(JButton... buttons) {
        JPanel row = new JPanel(new FlowLayout(FlowLayout.LEFT));
        for (JButton b : buttons) row.add(b);
        return row;
    }

    /**
     * A draggable-divider vertical split between two stacked sections of a tab (e.g. the input
     * form on top, a live leaderboard on the bottom) -- the same resize-by-dragging behavior as
     * the main window's tabs/log divider, applied WITHIN a single engine tab so any section that's
     * competing for space (a tall form vs. a leaderboard table, or a rocket preview vs. a form) can
     * be resized to taste instead of using a fixed split.
     */
    private JSplitPane verticalSplit(JComponent top, JComponent bottom, double resizeWeight) {
        JSplitPane split = new JSplitPane(JSplitPane.VERTICAL_SPLIT, top, bottom);
        split.setResizeWeight(resizeWeight);
        split.setOneTouchExpandable(true);
        split.setContinuousLayout(true);
        split.setBorder(null);
        return split;
    }

    /**
     * Wraps a section of a form in a titled, padded panel -- used to break up the busier tabs
     * (Engine 3 especially) into visually distinct groups instead of one long flat list of rows.
     */
    private JPanel titledGroup(String title, JComponent content) {
        JPanel wrapper = new JPanel(new BorderLayout());
        wrapper.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createTitledBorder(title),
                new EmptyBorder(2, 4, 6, 4)));
        wrapper.add(content, BorderLayout.CENTER);
        wrapper.setAlignmentX(Component.LEFT_ALIGNMENT);
        content.setAlignmentX(Component.LEFT_ALIGNMENT);
        return wrapper;
    }

    /** Makes the tab's main action (Run/Solve/Export) visually stand out from secondary buttons like Browse/Edit. */
    private void stylePrimaryButton(JButton b) {
        b.setFont(b.getFont().deriveFont(Font.BOLD));
        b.setMargin(new Insets(6, 16, 6, 16));
    }

    /**
     * Small gray italic explanatory label, word-wrapped to a fixed pixel width. Plain
     * "&lt;html&gt;&lt;i&gt;...&lt;/i&gt;&lt;/html&gt;" JLabels report their preferred width as the ENTIRE text
     * laid out on one line -- for the longer hint strings in this GUI that's 2000+ px, which blows
     * out the whole form's GridBagLayout column width and forces a horizontal scrollbar on any tab
     * whose form sits in a JScrollPane (Engine 3, Engine 5). Wrapping the HTML body in a fixed
     * "width:" style makes Swing's HTML renderer actually wrap the text into multiple lines instead.
     */
    private JLabel hintLabel(String htmlBodyText) {
        JLabel label = new JLabel("<html><body style='width: 560px'><i>" + htmlBodyText + "</i></body></html>");
        label.setForeground(Color.GRAY);
        return label;
    }

    private File requireFile(JTextField field, String label) {
        String path = field.getText().trim();
        if (path.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please choose a " + label + ".", "Missing input", JOptionPane.WARNING_MESSAGE);
            return null;
        }
        File f = new File(path);
        if (!f.exists()) {
            JOptionPane.showMessageDialog(this, "File not found: " + path, "Missing input", JOptionPane.WARNING_MESSAGE);
            return null;
        }
        return f;
    }

    private File requireExistingFile(JTextField field, String label) {
        return requireFile(field, label);
    }

    /**
     * Reads an optional "output folder" field: blank -> the named default subfolder, created next
     * to orkFile (e.g. "Monte Carlo", "OpenRocket Solves"). Typing an explicit path overrides this
     * entirely and is used as-is.
     */
    private File resolveOutDir(JTextField field, File orkFile, String defaultFolderName) {
        String path = field.getText().trim();
        if (!path.isEmpty()) return new File(path);
        return OutputNaming.namedSubfolder(orkFile, defaultFolderName);
    }

    private void openFileLocation(File f) {
        try {
            if (Desktop.isDesktopSupported() && f.getParentFile() != null) {
                Desktop.getDesktop().open(f.getParentFile());
            }
        } catch (Exception ignored) {
            // best-effort convenience only
        }
    }

    /** Like openFileLocation, but for a File that's already the directory to open (e.g. a batch output folder). */
    private void openDirectory(File dir) {
        try {
            if (Desktop.isDesktopSupported()) {
                Desktop.getDesktop().open(dir);
            }
        } catch (Exception ignored) {
            // best-effort convenience only
        }
    }

    private void editPropertiesFile(File file) {
        try {
            String content = file.exists() ? new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8) : "";
            JTextArea editor = new JTextArea(content, 28, 70);
            editor.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
            JScrollPane scroll = new JScrollPane(editor);
            int result = JOptionPane.showConfirmDialog(this, scroll, "Edit " + file.getName(),
                    JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);
            if (result == JOptionPane.OK_OPTION) {
                Files.write(file.toPath(), editor.getText().getBytes(StandardCharsets.UTF_8));
                appendLog("Saved " + file.getAbsolutePath() + "\n");
            }
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this, "Could not read/write file: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
        }
    }

    /** Small helper for label+field form rows using GridBagLayout, with a file-picker variant. */
    private class FormBuilder {
        private final JPanel p = new JPanel(new GridBagLayout());
        private int row = 0;

        JPanel panel() { return p; }

        void addRow(String label, JComponent field) {
            GridBagConstraints c = new GridBagConstraints();
            c.insets = new Insets(4, 4, 4, 4);
            c.gridx = 0; c.gridy = row; c.anchor = GridBagConstraints.WEST;
            p.add(new JLabel(label), c);
            c.gridx = 1; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1;
            p.add(field, c);
            row++;
        }

        /**
         * Adds a text field + Browse button row for picking a FOLDER (not a specific file) --
         * used for the "output folder" rows now that every engine auto-generates its own
         * filename (see OutputNaming). Leaving the field blank means "same folder as the rocket
         * file", which the caller is responsible for treating as null when invoking the engine.
         */
        JPanel addDirRow(String label, JTextField field) {
            JPanel rowPanel = new JPanel(new BorderLayout(4, 0));
            rowPanel.add(field, BorderLayout.CENTER);
            JPanel buttonsPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
            JButton browse = new JButton("Browse...");
            browse.addActionListener(e -> {
                JFileChooser chooser = new JFileChooser(lastDir);
                chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                int result = chooser.showOpenDialog(ArcSimGui.this);
                if (result == JFileChooser.APPROVE_OPTION) {
                    File f = chooser.getSelectedFile();
                    field.setText(f.getPath());
                    lastDir = f;
                }
            });
            buttonsPanel.add(browse);
            rowPanel.add(buttonsPanel, BorderLayout.EAST);

            GridBagConstraints c = new GridBagConstraints();
            c.insets = new Insets(4, 4, 4, 4);
            c.gridx = 0; c.gridy = row; c.anchor = GridBagConstraints.WEST;
            p.add(new JLabel(label), c);
            c.gridx = 1; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1;
            p.add(rowPanel, c);
            row++;
            return buttonsPanel;
        }

        /** Adds a text field + Browse button row; returns the button panel so callers can append more buttons. */
        JPanel addFileRow(String label, JTextField field, boolean open, String filterDesc, String ext) {
            JPanel rowPanel = new JPanel(new BorderLayout(4, 0));
            rowPanel.add(field, BorderLayout.CENTER);
            JPanel buttonsPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 0));
            JButton browse = new JButton("Browse...");
            browse.addActionListener(e -> {
                JFileChooser chooser = new JFileChooser(lastDir);
                chooser.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(filterDesc, ext));
                int result = open ? chooser.showOpenDialog(ArcSimGui.this) : chooser.showSaveDialog(ArcSimGui.this);
                if (result == JFileChooser.APPROVE_OPTION) {
                    File f = chooser.getSelectedFile();
                    if (!open && !f.getName().toLowerCase().endsWith("." + ext)) {
                        f = new File(f.getParentFile(), f.getName() + "." + ext);
                    }
                    field.setText(f.getPath());
                    lastDir = f.getParentFile() != null ? f.getParentFile() : lastDir;
                }
            });
            buttonsPanel.add(browse);
            rowPanel.add(buttonsPanel, BorderLayout.EAST);

            GridBagConstraints c = new GridBagConstraints();
            c.insets = new Insets(4, 4, 4, 4);
            c.gridx = 0; c.gridy = row; c.anchor = GridBagConstraints.WEST;
            p.add(new JLabel(label), c);
            c.gridx = 1; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1;
            p.add(rowPanel, c);
            row++;
            return buttonsPanel;
        }
    }

    /**
     * Homebrew dark theme -- no external LAF library (FlatLaf etc. aren't reachable from this
     * sandboxed build, and this keeps the tool dependency-free anyway). Built as a MetalTheme
     * subclass, which is the standard way to reskin Swing's pure-Java "Metal" look and feel:
     * Metal renders everything itself (unlike the native system LAFs), so overriding its color
     * getters reliably recolors every stock component -- buttons, tabs, spinners, scrollbars,
     * menus -- without touching each one by hand. Rocket-flame-orange accent on charcoal.
     */
    private static final class ArcRocketDarkTheme extends DefaultMetalTheme {
        private final ColorUIResource bgDark = new ColorUIResource(0x1b1b22);
        private final ColorUIResource bgPanel = new ColorUIResource(0x24242c);
        private final ColorUIResource bgControl = new ColorUIResource(0x2c2c36);
        private final ColorUIResource borderGray = new ColorUIResource(0x3c3c48);
        private final ColorUIResource textLight = new ColorUIResource(0xe8e8ec);
        private final ColorUIResource textDim = new ColorUIResource(0xa0a0ac);
        private final ColorUIResource flameOrange = new ColorUIResource(0xff7a3d);
        private final ColorUIResource flameOrangeDim = new ColorUIResource(0xc65a2a);
        private final ColorUIResource flameOrangeBright = new ColorUIResource(0xffa46b);

        @Override
        public String getName() {
            return "ARC Rocket Dark";
        }

        // primary1/2/3: focus rings, scrollbar thumbs, selected-tab/menu highlights -- the accent.
        @Override
        protected ColorUIResource getPrimary1() {
            return flameOrangeDim;
        }

        @Override
        protected ColorUIResource getPrimary2() {
            return flameOrange;
        }

        @Override
        protected ColorUIResource getPrimary3() {
            return flameOrangeBright;
        }

        // secondary1/2/3: neutral control/background grays, darkest to lightest.
        @Override
        protected ColorUIResource getSecondary1() {
            return borderGray;
        }

        @Override
        protected ColorUIResource getSecondary2() {
            return bgControl;
        }

        @Override
        protected ColorUIResource getSecondary3() {
            return bgPanel;
        }

        // Metal derives most default text/background colors from "black"/"white" -- flipping
        // these two is what actually turns the theme dark instead of just accenting a light one.
        @Override
        protected ColorUIResource getBlack() {
            return textLight;
        }

        @Override
        protected ColorUIResource getWhite() {
            return bgDark;
        }

        @Override
        public ColorUIResource getControlTextColor() {
            return textLight;
        }

        @Override
        public ColorUIResource getSystemTextColor() {
            return textLight;
        }

        @Override
        public ColorUIResource getUserTextColor() {
            return textLight;
        }

        @Override
        public ColorUIResource getInactiveControlTextColor() {
            return textDim;
        }

        @Override
        public ColorUIResource getInactiveSystemTextColor() {
            return textDim;
        }

        @Override
        public ColorUIResource getMenuDisabledForeground() {
            return textDim;
        }

        @Override
        public ColorUIResource getWindowTitleForeground() {
            return textLight;
        }

        @Override
        public ColorUIResource getWindowTitleBackground() {
            return bgPanel;
        }

        @Override
        public ColorUIResource getDesktopColor() {
            return bgDark;
        }

        @Override
        public ColorUIResource getFocusColor() {
            return flameOrange;
        }
    }

    /** Applies the homebrew dark theme, plus a few explicit puts for components Metal doesn't fully cover. */
    private static void installDarkTheme() {
        try {
            MetalLookAndFeel.setCurrentTheme(new ArcRocketDarkTheme());
            UIManager.setLookAndFeel(new MetalLookAndFeel());
        } catch (Exception ignored) {
            return; // fall back to whatever default LAF is active
        }
        Color bgDark = new Color(0x1b1b22);
        Color bgConsole = new Color(0x151519);
        Color textLight = new Color(0xe8e8ec);
        Color flameOrange = new Color(0xff7a3d);
        Color borderGray = new Color(0x3c3c48);

        UIManager.put("TextArea.background", bgConsole);
        UIManager.put("TextArea.foreground", textLight);
        UIManager.put("TextArea.caretForeground", flameOrange);
        UIManager.put("TextField.background", bgDark);
        UIManager.put("TextField.foreground", textLight);
        UIManager.put("TextField.caretForeground", flameOrange);
        UIManager.put("FormattedTextField.background", bgDark);
        UIManager.put("FormattedTextField.foreground", textLight);
        UIManager.put("Spinner.background", bgDark);
        UIManager.put("Spinner.foreground", textLight);
        UIManager.put("ComboBox.background", bgDark);
        UIManager.put("ComboBox.foreground", textLight);
        UIManager.put("List.background", bgDark);
        UIManager.put("List.foreground", textLight);
        UIManager.put("List.selectionBackground", flameOrange);
        UIManager.put("Table.background", bgDark);
        UIManager.put("Table.foreground", textLight);
        UIManager.put("Table.gridColor", borderGray);
        UIManager.put("Table.selectionBackground", flameOrange);
        UIManager.put("TableHeader.background", new Color(0x24242c));
        UIManager.put("TableHeader.foreground", textLight);
        UIManager.put("ScrollPane.background", bgDark);
        UIManager.put("Viewport.background", bgDark);
        UIManager.put("ProgressBar.foreground", flameOrange);
        UIManager.put("ProgressBar.selectionForeground", bgDark);
        UIManager.put("ProgressBar.selectionBackground", textLight);
        UIManager.put("ToolTip.background", new Color(0x2c2c36));
        UIManager.put("ToolTip.foreground", textLight);
        UIManager.put("OptionPane.background", bgDark);
        UIManager.put("Panel.background", bgDark);
        UIManager.put("PopupMenu.background", new Color(0x24242c));
        UIManager.put("MenuItem.background", new Color(0x24242c));
        UIManager.put("MenuItem.foreground", textLight);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            installDarkTheme();
            new ArcSimGui().setVisible(true);
        });
    }
}
