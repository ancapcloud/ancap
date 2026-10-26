const { withAppBuildGradle, withMainApplication, withProjectBuildGradle } = require("expo/config-plugins");

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
  config = withProjectBuildGradle(config, (mod) => {
    const marker = "// ANCAP Windows native object paths";
    const endMarker = "// End ANCAP Windows native object paths";
    const start = mod.modResults.contents.indexOf(marker);
    if (start >= 0) {
      const end = mod.modResults.contents.indexOf(endMarker, start);
      const before = mod.modResults.contents.slice(0, start).trimEnd();
      const after = end >= 0 ? mod.modResults.contents.slice(end + endMarker.length).trimStart() : "";
      mod.modResults.contents = before + "\n\n" + after;
    }
    const block = `${marker}
// Keep Ninja object paths under Windows MAX_PATH, including deep npm workspaces.
if (System.getProperty("os.name").toLowerCase().contains("windows")) {
    def nativeCacheRoot = rootProject.findProperty("ancap.nativeBuildRoot") ?:
        new File(System.getenv("SystemDrive") + File.separator, ".ancap-cxx")
    def nativeProjectKey = java.security.MessageDigest.getInstance("SHA-256")
        .digest(rootProject.projectDir.canonicalPath.getBytes("UTF-8")).encodeHex().toString().substring(0, 12)
    subprojects { nativeProject ->
        ["com.android.library", "com.android.application"].each { pluginId ->
            nativeProject.plugins.withId(pluginId) {
                def nativeAndroid = nativeProject.extensions.getByName("android")
                nativeAndroid.externalNativeBuild.cmake.buildStagingDirectory =
                    new File(new File(nativeCacheRoot.toString(), nativeProjectKey), nativeProject.name)
                nativeAndroid.defaultConfig.externalNativeBuild.cmake.arguments.add("-DCMAKE_OBJECT_PATH_MAX=240")
            }
        }
    }
}
${endMarker}
`;
    const entry = 'apply plugin: "expo-root-project"';
    if (!mod.modResults.contents.includes(entry)) throw new Error("Review Windows native staging for this Expo template.");
    // React's root plugin evaluates the app early. Register these callbacks first.
    mod.modResults.contents = mod.modResults.contents.replace(entry, block + "\n" + entry).trimEnd() + "\n";
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
