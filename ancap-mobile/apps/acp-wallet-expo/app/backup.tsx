import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput } from "react-native";
import { allowScreenCaptureAsync, preventScreenCaptureAsync } from "expo-screen-capture";
import { encryptKeystoreBackup, safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { loadVault } from "@/lib/vault";
import { exportEncryptedBackup } from "@/lib/keystore-backup";

/** Export an existing wallet without retaining plaintext secrets in screen state. */
export default function WalletBackupScreen() {
  const { t } = useTranslation();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    void preventScreenCaptureAsync();
    return () => { allowScreenCaptureAsync().catch(() => {}); };
  }, []);
  const onExport = async () => {
    if ([...password].length < 12 || password !== confirmation) {
      Alert.alert(t("backup.title"), t("backup.passwordMismatch")); return;
    }
    setBusy(true);
    try {
      const vault = await loadVault();
      if (!vault) throw new Error(t("backup.failed"));
      const encrypted = await encryptKeystoreBackup(vault.keystoreJson, password);
      const result = await exportEncryptedBackup(encrypted);
      if (result !== "cancelled") {
        setPassword(""); setConfirmation("");
        Alert.alert(t("backup.title"), result === "saved" ? t("backup.saved") : t("backup.verifyShared"));
      }
    } catch (error) {
      Alert.alert(t("backup.title"), safeErrorMessage(error, t("backup.failed")));
    } finally { setBusy(false); }
  };
  return <ScrollView contentContainerStyle={styles.container}>
    <Text style={styles.title}>{t("backup.title")}</Text>
    <Text style={styles.hint}>{t("backup.hint")}</Text>
    <TextInput accessibilityLabel="backup-password" style={styles.input} secureTextEntry
      value={password} onChangeText={setPassword} placeholder={t("backup.password")}
      placeholderTextColor="#94a3b8" autoCapitalize="none" autoCorrect={false} editable={!busy} />
    <TextInput accessibilityLabel="backup-password-confirm" style={styles.input} secureTextEntry
      value={confirmation} onChangeText={setConfirmation} placeholder={t("backup.confirm")}
      placeholderTextColor="#94a3b8" autoCapitalize="none" autoCorrect={false} editable={!busy} />
    <Pressable style={styles.button} onPress={() => void onExport()} disabled={busy}>
      {busy ? <ActivityIndicator color="#f5f7ff" /> : <Text style={styles.label}>{t("backup.export")}</Text>}
    </Pressable>
  </ScrollView>;
}
const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1, backgroundColor: "#0a0f1a" },
  title: { color: "#f5f7ff", fontSize: 24, marginBottom: 16 },
  hint: { color: "#94a3b8", lineHeight: 22, marginBottom: 16 },
  input: { color: "#f5f7ff", borderColor: "#334155", borderWidth: 1, padding: 14, borderRadius: 10, marginBottom: 12 },
  button: { borderColor: "#334155", borderWidth: 1, padding: 16, borderRadius: 12 },
  label: { color: "#f5f7ff", textAlign: "center" },
});
