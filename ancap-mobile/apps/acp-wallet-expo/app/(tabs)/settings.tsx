import { Linking } from "react-native";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import {
  canUseBiometricUnlock,
  canUseNfcFactor,
  clearPinLock,
  disableBiometricUnlock,
  disableNfcFactor,
  enableBiometricUnlock,
  enableNfcUnlock,
  hasPinLock,
  isBiometricUnlockEnabled,
  isNfcFactorEnabled,
  isValidPin,
  lockSession,
  setPinLock,
} from "@/lib/lock";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { LANGUAGE_OPTIONS, loadLanguagePreference, setLanguagePreference, type AppLanguage } from "@/lib/i18n";
import {
  disableVaultBiometricProtection,
  enableVaultBiometricProtection,
  isVaultBiometricProtected,
  wipeVault,
} from "@/lib/vault";
import { syncNfcCredentialToBackend } from "@/lib/identity";

const BASE = "https://ancap.cloud";

function checkInsecureEnvironment(message: string): string | null {
  if (typeof __DEV__ !== "undefined" && __DEV__) {
    return message;
  }
  return null;
}

export default function SettingsScreen() {
  const { t } = useTranslation();
  const [envWarning, setEnvWarning] = useState<string | null>(null);
  const [pinEnabled, setPinEnabled] = useState(false);
  const [biometricEnabled, setBiometricEnabled] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [nfcEnabled, setNfcEnabled] = useState(false);
  const [nfcAvailable, setNfcAvailable] = useState(false);
  const [vaultBiometricProtected, setVaultBiometricProtected] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<AppLanguage>("en");
  const [pin, setPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");

  const links = [
    { label: t("settings.terms"), url: `${BASE}/legal/terms` },
    { label: t("settings.privacy"), url: `${BASE}/legal/privacy` },
    { label: t("settings.bridgeRiskDisclosure"), url: `${BASE}/docs/wacp/risks` },
    { label: t("settings.bridgeDocumentation"), url: `${BASE}/docs/wacp/bridge` },
    { label: t("settings.reserveProof"), url: `${BASE}/docs/wacp/reserve` },
    { label: t("settings.support"), url: `${BASE}/support` },
  ];

  useEffect(() => {
    const warning = checkInsecureEnvironment(t("settings.envWarning"));
    if (warning) setEnvWarning(warning);
    void refreshState();
  }, [t]);

  const refreshState = async () => {
    const [pinOn, biometricOn, biometricCapable, nfcOn, nfcCapable, vaultProtected, language] =
      await Promise.all([
        hasPinLock(),
        isBiometricUnlockEnabled(),
        canUseBiometricUnlock(),
        isNfcFactorEnabled(),
        canUseNfcFactor(),
        isVaultBiometricProtected(),
        loadLanguagePreference(),
      ]);
    setPinEnabled(pinOn);
    setBiometricEnabled(biometricOn);
    setBiometricAvailable(biometricCapable);
    setNfcEnabled(nfcOn);
    setNfcAvailable(nfcCapable);
    setVaultBiometricProtected(vaultProtected);
    setSelectedLanguage(language);
  };

  const onWipe = () => {
    Alert.alert(t("settings.removeWalletTitle"), t("settings.removeWalletBody"), [
      { text: t("settings.cancel"), style: "cancel" },
      {
        text: t("settings.remove"),
        style: "destructive",
        onPress: async () => {
            try {
              await wipeVault();
              router.replace("/");
            } catch (error) {
              Alert.alert(t("settings.removeWalletTitle"), safeErrorMessage(error, "Wallet removal incomplete. Retry removal."));
            }
        },
      },
    ]);
  };

  const onOpen = (url: string) => {
    void Linking.openURL(url);
  };

  const onSavePin = async () => {
    if (!isValidPin(pin)) {
      Alert.alert(t("settings.invalidPinTitle"), t("settings.invalidPinBody"));
      return;
    }
    if (pin !== confirmPin) {
      Alert.alert(t("settings.pinMismatchTitle"), t("settings.pinMismatchBody"));
      return;
    }
    await setPinLock(pin);
    setPin("");
    setConfirmPin("");
    await refreshState();
    Alert.alert(t("settings.pinEnabledTitle"), t("settings.pinEnabledBody"));
  };

  const onDisablePin = () => {
    Alert.alert(t("settings.disableLockTitle"), t("settings.disableLockBody"), [
      { text: t("settings.cancel"), style: "cancel" },
      {
        text: t("settings.disableTitle"),
        style: "destructive",
        onPress: async () => {
          await disableVaultBiometricProtection();
          await clearPinLock();
          await refreshState();
        },
      },
    ]);
  };

  const onEnableBiometrics = async () => {
    try {
      await enableBiometricUnlock();
      await enableVaultBiometricProtection();
      await refreshState();
      Alert.alert(t("settings.biometricsEnabledTitle"), t("settings.biometricsEnabledBody"));
    } catch (e) {
      Alert.alert(t("settings.biometricsErrorTitle"), safeErrorMessage(e, "Unknown error"));
    }
  };

  const onDisableBiometrics = () => {
    Alert.alert(t("settings.disableBiometricTitle"), t("settings.disableBiometricBody"), [
      { text: t("settings.cancel"), style: "cancel" },
      {
        text: t("settings.disableTitle"),
        style: "destructive",
        onPress: async () => {
          await disableVaultBiometricProtection();
          await disableBiometricUnlock();
          await refreshState();
        },
      },
    ]);
  };

  const onEnableNfc = async () => {
    try {
      await enableNfcUnlock();
      const synced = await syncNfcCredentialToBackend();
      await refreshState();
      Alert.alert(
        t("settings.nfcEnabledTitle"),
        synced ? t("settings.nfcEnabledBodySynced") : t("settings.nfcEnabledBody")
      );
    } catch (e) {
      Alert.alert(t("settings.nfcErrorTitle"), safeErrorMessage(e, "Unknown error"));
    }
  };

  const onDisableNfc = () => {
    Alert.alert(t("settings.disableNfcTitle"), t("settings.disableNfcBody"), [
      { text: t("settings.cancel"), style: "cancel" },
      {
        text: t("settings.disableTitle"),
        style: "destructive",
        onPress: async () => {
          await disableNfcFactor();
          await refreshState();
        },
      },
    ]);
  };

  const onLockNow = () => {
    lockSession();
    router.replace("/unlock");
  };

  const onLanguageChange = async (language: AppLanguage) => {
    await setLanguagePreference(language);
    setSelectedLanguage(language);
  };

  const statusParts = [pinEnabled ? t("settings.pinEnabled") : t("settings.pinDisabled")];
  if (biometricEnabled) statusParts.push(t("settings.biometricsEnabled"));
  if (nfcEnabled) statusParts.push(t("settings.nfcEnabled"));
  if (vaultBiometricProtected) statusParts.push(t("settings.secureVaultGated"));

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{t("settings.title")}</Text>

      {envWarning ? (
        <View style={styles.warnCard}>
          <Text style={styles.warnText}>{envWarning}</Text>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.cardLabel}>{t("settings.appTitle")}</Text>
        <Text style={styles.meta}>{t("settings.version")}</Text>
        <Text style={styles.meta}>{t("settings.nonCustodial")}</Text>
      </View>

      <Text style={styles.section}>{t("settings.language")}</Text>
      <View style={styles.card}>
        <Text style={styles.meta}>{t("settings.languageHelp")}</Text>
        <View style={styles.languageGrid}>
          {LANGUAGE_OPTIONS.map((option) => {
            const active = selectedLanguage === option.code;
            return (
              <Pressable
                key={option.code}
                style={[styles.languageButton, active ? styles.languageButtonActive : null]}
                onPress={() => void onLanguageChange(option.code)}
              >
                <Text style={[styles.languageButtonText, active ? styles.languageButtonTextActive : null]}>
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Text style={styles.section}>{t("settings.legalDocs")}</Text>
      {links.map((link) => (
        <Pressable key={link.url} style={styles.linkRow} onPress={() => onOpen(link.url)}>
          <Text style={styles.linkText}>{link.label}</Text>
          <Text style={styles.arrow}>›</Text>
        </Pressable>
      ))}

      <Text style={styles.section}>{t("settings.security")}</Text>
      <View style={styles.card}>
        <Text style={styles.cardLabel}>{t("settings.keyStorageTitle")}</Text>
        <Text style={styles.meta}>{t("settings.keyStorageBody")}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardLabel}>{t("settings.bridgeRiskTitle")}</Text>
        <Text style={styles.meta}>{t("settings.bridgeRiskBody")}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardLabel}>{t("settings.appLockTitle")}</Text>
        <Text style={styles.meta}>{t("settings.statusLine", { status: statusParts.join(" · ") })}</Text>
        <Text style={styles.meta}>{t("settings.nfcHelp")}</Text>
        <TextInput
          style={styles.input}
          value={pin}
          onChangeText={setPin}
          placeholder={t("settings.setPin")}
          placeholderTextColor="#64748b"
          keyboardType="number-pad"
          secureTextEntry
          maxLength={8}
        />
        <TextInput
          style={styles.input}
          value={confirmPin}
          onChangeText={setConfirmPin}
          placeholder={t("settings.confirmPin")}
          placeholderTextColor="#64748b"
          keyboardType="number-pad"
          secureTextEntry
          maxLength={8}
        />
        <Pressable style={styles.primary} onPress={() => void onSavePin()}>
          <Text style={styles.primaryText}>{pinEnabled ? t("settings.updatePin") : t("settings.enablePin")}</Text>
        </Pressable>
        {pinEnabled ? (
          <Pressable style={styles.secondary} onPress={onDisablePin}>
            <Text style={styles.secondaryText}>{t("settings.disablePinLock")}</Text>
          </Pressable>
        ) : null}
        {pinEnabled && biometricAvailable && !biometricEnabled ? (
          <Pressable style={styles.secondary} onPress={() => void onEnableBiometrics()}>
            <Text style={styles.secondaryText}>{t("settings.enableBiometricUnlock")}</Text>
          </Pressable>
        ) : null}
        {pinEnabled && biometricEnabled ? (
          <Pressable style={styles.secondary} onPress={onDisableBiometrics}>
            <Text style={styles.secondaryText}>{t("settings.disableBiometricUnlock")}</Text>
          </Pressable>
        ) : null}
        {pinEnabled && nfcAvailable && !nfcEnabled ? (
          <Pressable style={styles.secondary} onPress={() => void onEnableNfc()}>
            <Text style={styles.secondaryText}>{t("settings.enableNfcUnlock")}</Text>
          </Pressable>
        ) : null}
        {pinEnabled && nfcEnabled ? (
          <Pressable style={styles.secondary} onPress={onDisableNfc}>
            <Text style={styles.secondaryText}>{t("settings.disableNfcUnlock")}</Text>
          </Pressable>
        ) : null}
        {pinEnabled && !nfcAvailable ? (
          <Text style={styles.meta}>{t("settings.nfcUnavailable")}</Text>
        ) : null}
        {pinEnabled ? (
          <Pressable style={styles.secondary} onPress={onLockNow}>
            <Text style={styles.secondaryText}>{t("settings.lockNow")}</Text>
          </Pressable>
        ) : null}
      </View>

      <Pressable style={styles.secondary} onPress={() => router.push("/backup")}>
        <Text style={styles.secondaryText}>{t("backup.title")}</Text>
      </Pressable>
      <Pressable style={styles.danger} onPress={onWipe}>
        <Text style={styles.dangerText}>{t("settings.removeWallet")}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1 },
  title: { color: "#f5f7ff", fontSize: 20, fontWeight: "700", marginBottom: 16 },
  section: {
    color: "#94a3b8",
    fontSize: 13,
    fontWeight: "600",
    marginTop: 20,
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  card: {
    backgroundColor: "#111827",
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderColor: "#1e293b",
    borderWidth: 1,
  },
  cardLabel: { color: "#f5f7ff", fontWeight: "600", marginBottom: 6 },
  warnCard: {
    backgroundColor: "#450a0a",
    borderColor: "#b91c1c",
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
  },
  warnText: { color: "#fecaca", fontSize: 13, lineHeight: 20 },
  meta: { color: "#94a3b8", fontSize: 13, lineHeight: 20, marginTop: 6 },
  languageGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 14,
  },
  languageButton: {
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    backgroundColor: "#0f172a",
  },
  languageButtonActive: {
    backgroundColor: "#10b981",
    borderColor: "#10b981",
  },
  languageButtonText: { color: "#f5f7ff", fontWeight: "600" },
  languageButtonTextActive: { color: "#042f1a" },
  linkRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#111827",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 10,
    marginBottom: 6,
    borderColor: "#1e293b",
    borderWidth: 1,
  },
  linkText: { color: "#f5f7ff", fontSize: 15 },
  arrow: { color: "#64748b", fontSize: 20 },
  input: {
    backgroundColor: "#0f172a",
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    color: "#f5f7ff",
    padding: 12,
    marginTop: 12,
  },
  primary: {
    backgroundColor: "#10b981",
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 12,
  },
  primaryText: { color: "#042f1a", textAlign: "center", fontWeight: "600" },
  secondary: {
    borderColor: "#334155",
    borderWidth: 1,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 10,
  },
  secondaryText: { color: "#f5f7ff", textAlign: "center", fontWeight: "600" },
  danger: {
    backgroundColor: "#450a0a",
    borderColor: "#b91c1c",
    borderWidth: 1,
    padding: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  dangerText: { color: "#fecaca", textAlign: "center", fontWeight: "600" },
});
