package com.arc.sim;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Central helper for generating output file/folder names across all engines, so that:
 *   1. Every generated file is self-describing: "<orkBaseName>_<simType>_<timestamp>.<ext>"
 *   2. Nothing is ever silently overwritten -- if that exact name is somehow already taken
 *      (e.g. two runs kicked off in the same second), a "_2", "_3", ... suffix is appended
 *      until a free name is found.
 *
 * Used by EnvironmentSweep (simType "montecarlo"), FullFactorialSweep ("fullfactorial"),
 * DesignSolver ("solved"), and OrkBatchGenerator ("batch", for the subfolder name).
 */
public class OutputNaming {

    // Default output folder names, one per engine, each created as a SIBLING of whatever .ork
    // file is being processed (not a fixed project-root location) -- so outputs stay organized
    // and co-located with the design file they came from no matter where that file lives. Used as
    // the GUI's default "Output folder" whenever that field is left blank; typing an explicit path
    // still overrides it.
    public static final String MONTE_CARLO_FOLDER = "Monte Carlo";
    public static final String FULL_FACTORIAL_FOLDER = "Full Factorial";
    public static final String OPENROCKET_SOLVES_FOLDER = "OpenRocket Solves";
    public static final String CAD_FILES_FOLDER = "CAD Files";
    public static final String ENGINE_6_FOLDER = "Engine 6";

    // yyyyMMdd_HHmmss has 1-second resolution -- the collision loop below covers same-second
    // reruns. Format is not shared as a static SimpleDateFormat because SimpleDateFormat isn't
    // thread-safe and FullFactorialSweep/OrkBatchGenerator naming can happen from GUI + worker
    // threads.
    private static SimpleDateFormat newFormat() {
        return new SimpleDateFormat("yyyyMMdd_HHmmss");
    }

    /** Strips the extension off a filename, e.g. "WYVERN_E4.ork" -> "WYVERN_E4". */
    public static String baseName(File f) {
        String name = f.getName();
        int dot = name.lastIndexOf('.');
        return dot > 0 ? name.substring(0, dot) : name;
    }

    public static String timestamp() {
        return newFormat().format(new Date());
    }

    /**
     * Builds a collision-safe "<orkBase>_<simType>_<timestamp>.<ext>" file inside outDir
     * (created if it doesn't exist yet). If outDir is null, uses the ork file's own parent
     * directory (or "." if the ork file has no parent, e.g. a bare filename).
     * Never returns a path that already exists.
     */
    public static File uniqueFile(File orkFile, File outDir, String simType, String ext) {
        File dir = resolveDir(orkFile, outDir);
        String base = baseName(orkFile) + "_" + simType + "_" + timestamp();
        File out = new File(dir, base + "." + ext);
        int suffix = 2;
        while (out.exists()) {
            out = new File(dir, base + "_" + suffix + "." + ext);
            suffix++;
        }
        return out;
    }

    /**
     * Builds a collision-safe "<orkBase>_<simType>_<timestamp>" subfolder inside outDir (created
     * if it doesn't exist yet), for engines that emit many files at once (e.g. batch .ork
     * generation). The returned directory is created before being returned. If outDir is null,
     * uses the ork file's own parent directory.
     */
    public static File uniqueDir(File orkFile, File outDir, String simType) {
        File parent = resolveDir(orkFile, outDir);
        String base = baseName(orkFile) + "_" + simType + "_" + timestamp();
        File dir = new File(parent, base);
        int suffix = 2;
        while (dir.exists()) {
            dir = new File(parent, base + "_" + suffix);
            suffix++;
        }
        if (!dir.mkdirs()) {
            throw new IllegalStateException("Could not create output folder: " + dir.getAbsolutePath());
        }
        return dir;
    }

    /**
     * Resolves (creating if needed) a folder with a FIXED name, sitting next to orkFile -- e.g.
     * "Monte Carlo" or "OpenRocket Solves". This is the default output location for each engine
     * when the GUI's "Output folder" field is left blank; typing an explicit path bypasses this
     * entirely. If orkFile has no parent (a bare filename with no directory component), the
     * folder is created in the current working directory instead.
     */
    public static File namedSubfolder(File orkFile, String folderName) {
        File parent = orkFile.getParentFile();
        if (parent == null) parent = new File(".");
        File dir = new File(parent, folderName);
        if (!dir.exists() && !dir.mkdirs() && !dir.exists()) {
            throw new IllegalStateException("Could not create output folder: " + dir.getAbsolutePath());
        }
        return dir;
    }

    private static File resolveDir(File orkFile, File outDir) {
        File dir = outDir;
        if (dir == null) {
            dir = orkFile.getParentFile();
        }
        if (dir == null) {
            dir = new File(".");
        }
        if (!dir.exists() && !dir.mkdirs() && !dir.exists()) {
            throw new IllegalStateException("Could not create output folder: " + dir.getAbsolutePath());
        }
        return dir;
    }
}
