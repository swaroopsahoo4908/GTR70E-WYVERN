package com.arc.sim;

public class Main {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            printUsage();
            return;
        }
        String mode = args[0];
        String[] rest = java.util.Arrays.copyOfRange(args, 1, args.length);
        switch (mode) {
            case "sweep":
                EnvironmentSweep.main(rest);
                break;
            case "fullsweep":
                FullFactorialSweep.main(rest);
                break;
            case "design":
                DesignSolver.main(rest);
                break;
            case "batch":
                OrkBatchGenerator.main(rest);
                break;
            default:
                printUsage();
        }
    }

    private static void printUsage() {
        System.out.println("Usage:");
        System.out.println("  Engine 1  (Monte Carlo environment sample, rocket held fixed):");
        System.out.println("    java -jar arc-sim.jar sweep <input.ork> <site> <numSamples> [outputDir]");
        System.out.println();
        System.out.println("  Engine 2 (TRUE full-factorial sweep, every combination, rocket held fixed):");
        System.out.println("    java -jar arc-sim.jar fullsweep <input.ork> <sweep_grid.properties> [outputDir] [--force]");
        System.out.println();
        System.out.println("  Engine 3  (solve ballast + fin height + fin sweep for one fixed atmosphere):");
        System.out.println("    java -jar arc-sim.jar design <input.ork> <targetApogeeM> <targetTimeMinS> <targetTimeMaxS> \\");
        System.out.println("        <site> <windAvgMs> <windStdDevMs> <turbulencePct> <windDirDeg> <tempC> <pressureMbar>");
        System.out.println();
        System.out.println("  Engine 4  (batch-generate .ork design variants + a linking manifest.csv; optionally");
        System.out.println("            also simulates + checks each variant against a target, via the grid config's");
        System.out.println("            optional simCheck.* properties -- see batch_grid.properties):");
        System.out.println("    java -jar arc-sim.jar batch <input.ork> <batch_grid.properties> [outputParentDir] [--force]");
        System.out.println();
        System.out.println("  site = MDRA_SOD_FARM | SPAAR_LANCASTER");
        System.out.println();
        System.out.println("  outputDir / outputParentDir are optional -- default to the input .ork's own folder.");
        System.out.println("  All output filenames/foldernames are auto-generated as <orkName>_<simType>_<timestamp>");
        System.out.println("  so repeated runs never overwrite a previous result. Engine 2 writes .parquet (not");
        System.out.println("  .xlsx) plus a companion _summary.csv; both engines 2 and 4 output are readable in this");
        System.out.println("  toolkit's GUI \"Data Viewer\" tab (also opens plain .xlsx/.csv).");
    }
}
