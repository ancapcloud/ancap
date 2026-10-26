const { withAppBuildGradle, withMainApplication } = require("expo/config-plugins");

// Keep wallet build constraints reproducible when Expo regenerates Android.
module.exports = function withWalletAndroid(config) {
  config = withAppBuildGradle(config, (mod) => {
    // Remove the unsafe template assignment itself, as well as clearing the
    // effective configuration below, so generated sources are safe to inspect.
    mod.modResults.contents = mod.modResults.contents.replace(
      /(release\s*\{[\s\S]*?)signingConfig signingConfigs\.debug/,
      "$1// Release signing must be supplied by the operator.",
    );
    const marker = "// ANCAP wallet build constraints";
    if (!mod.modResults.contents.includes(marker)) {
      mod.modResults.contents += `
${marker}
// Debug APKs must remain usable without a running Metro server.
react { debuggableVariants = [] }
// Isolated emulator smoke must never replace the user's wallet installation.
android.buildTypes.debug.applicationIdSuffix = findProperty("ancap.testApplicationIdSuffix") ?: ""
// Never inherit the generated template's debug signing key for a release.
android.buildTypes.release.signingConfig = null

def verifyReleaseSigning = tasks.register("verifyReleaseSigning") {
    doLast {
        def selected = android.buildTypes.getByName("release").signingConfig
        def debugSigning = android.signingConfigs.getByName("debug")
        if (selected == null || selected == debugSigning || selected.storeFile == null ||
            selected.storeFile.canonicalFile == debugSigning.storeFile.canonicalFile) {
            throw new GradleException("Release signing is not configured with an operator upload key. Debug signing is forbidden for release artifacts.")
        }
    }
}
tasks.matching { it.name == "preReleaseBuild" }.configureEach {
    dependsOn(verifyReleaseSigning)
}
`;
    }
    return mod;
  });
  return withMainApplication(config, (mod) => {
    if (!mod.modResults.contents.includes("useDevSupport = false,")) {
      mod.modResults.contents = mod.modResults.contents.replace(
        "context = applicationContext,",
        "context = applicationContext,\n      useDevSupport = false,",
      );
    }
    return mod;
  });
};
