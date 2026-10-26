/** Production defaults so Gradle/Android Studio builds work without a local .env */
process.env.NODE_ENV ??= "development";
process.env.EXPO_PUBLIC_ANCAP_API_BASE ??= "https://api.ancap.cloud/v1";
process.env.EXPO_PUBLIC_ACP_RPC_URL ??= "https://acp1.ancap.cloud/rpc";
// npm workspaces: keep Metro project root on the app, not the monorepo root.
process.env.EXPO_NO_METRO_WORKSPACE_ROOT ??= "1";

module.exports = ({ config: expo }) => {
  const androidPermissions = Array.from(
    new Set([
      ...(expo.android?.permissions ?? []),
      "android.permission.NFC",
      "android.permission.BLUETOOTH",
      "android.permission.BLUETOOTH_ADMIN",
      "android.permission.BLUETOOTH_SCAN",
      "android.permission.BLUETOOTH_CONNECT",
      "android.permission.BLUETOOTH_ADVERTISE",
      "android.permission.ACCESS_FINE_LOCATION",
      "android.permission.ACCESS_COARSE_LOCATION",
    ]),
  );

  /** @type {import('expo/config').ConfigContext} */
  return ({
    ...expo,
    android: {
      ...expo.android,
      permissions: androidPermissions,
    },
    ios: {
      ...expo.ios,
      infoPlist: {
        ...(expo.ios?.infoPlist ?? {}),
        NFCReaderUsageDescription:
          "Allow ANCAP ACP Wallet to read your enrolled Biohax NFC implant for wallet unlock.",
        NSBluetoothAlwaysUsageDescription:
          "ANCAP Dating uses Bluetooth to discover nearby ANCAP Dating peers and relay mesh messages without internet.",
        NSBluetoothPeripheralUsageDescription:
          "ANCAP Dating advertises this phone as an ANCAP Dating device for proximity discovery.",
        NSLocationWhenInUseUsageDescription:
          "ANCAP Dating uses location only when you create or view access-point pins on the map.",
      },
    },
    plugins: expo.plugins,
  });
};
