import { router } from "expo-router";
import * as Clipboard from "expo-clipboard";
import { useEffect, useState } from "react";
import { preventScreenCaptureAsync, allowScreenCaptureAsync } from "expo-screen-capture";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
} from "react-native";
import {
  addressFromKeystore,
  decryptKeystoreBackup,
  assertAcpAddress,
  safeErrorMessage,
  validateAcpAddress,
} from "@ancap/acp-wallet-sdk";
import { assertKeystoreExportJson, readKeystoreExportFile } from "@/lib/keystore-export";
import { saveVault } from "@/lib/vault";
import { pickKeystoreBackup } from "@/lib/keystore-backup";
import { assertEncryptedBackup } from "@/lib/keystore-backup-format";

export default function ImportWalletScreen() {
  const { t } = useTranslation();
  const [address, setAddress] = useState("");
  const [keystoreJson, setKeystoreJson] = useState("");
  const [mnemonic, setMnemonic] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [backupPassword, setBackupPassword] = useState("");
  useEffect(() => {
    void preventScreenCaptureAsync();
    return () => { allowScreenCaptureAsync().catch(() => {}); };
  }, []);

  const decodeInput = async (raw: string) => {
    if (raw.length > 512_000) throw new Error(t("importWallet.keystoreRequired"));
    let parsed;
    try { parsed = JSON.parse(raw); } catch { throw new Error(t("importWallet.keystoreRequired")); }
    if (parsed?.v === 2 && parsed?.crypto) {
      try {
        return assertKeystoreExportJson(await decryptKeystoreBackup(assertEncryptedBackup(raw), backupPassword));
      } catch { throw new Error(t("backup.decryptFailed")); }
    }
    try { return assertKeystoreExportJson(raw); }
    catch { throw new Error(t("importWallet.keystoreRequired")); }
  };

  const applyKeystore = async (raw: string) => {
    const trimmed = await decodeInput(raw);
    const derived = await addressFromKeystore(trimmed);
    setKeystoreJson(trimmed);
    setAddress(assertAcpAddress(derived, "address"));
  };

  const onPasteKeystore = async () => {
    setError("");
    setBusy(true);
    try {
      const clip = await Clipboard.getStringAsync();
      if (!clip?.trim()) {
        throw new Error(t("importWallet.clipboardEmpty"));
      }
      await applyKeystore(clip);
    } catch (e) {
      setError(safeErrorMessage(e, t("importWallet.importFailed")));
    } finally {
      setBusy(false);
    }
  };

  /** Load an explicit Copy-export file from the app documents directory (not a SecureStore stash). */
  const onLoadExportFile = async () => {
    setError("");
    setBusy(true);
    try {
      const raw = await readKeystoreExportFile();
      if (!raw) {
        throw new Error(t("importWallet.exportFileMissing"));
      }
      await applyKeystore(raw);
    } catch (e) {
      setError(safeErrorMessage(e, t("importWallet.importFailed")));
    } finally {
      setBusy(false);
    }
  };

  const onPickBackup = async () => {
    setError(""); setBusy(true);
    try {
      const raw = await pickKeystoreBackup();
      if (raw !== null) await applyKeystore(raw);
    } catch (error) {
      setError(safeErrorMessage(error, t("importWallet.importFailed")));
    } finally { setBusy(false); }
  };

  const onDeriveAddress = async () => {
    setError("");
    setBusy(true);
    try {
      await applyKeystore(keystoreJson);
    } catch (e) {
      setError(safeErrorMessage(e, t("importWallet.importFailed")));
    } finally {
      setBusy(false);
    }
  };

  const onSave = async () => {
    setError("");
    setBusy(true);
    try {
      const trimmed = await decodeInput(keystoreJson);
      const derived = await addressFromKeystore(trimmed);
      const addr = assertAcpAddress(derived, "address");
      const typed = address.trim();
      if (typed && typed !== addr) {
        throw new Error(t("importWallet.addressMismatch"));
      }
      setAddress(addr);
      setKeystoreJson(trimmed);
      await saveVault({
        address: addr,
        keystoreJson: trimmed,
        ...(mnemonic.trim() ? { mnemonic: mnemonic.trim() } : {}),
      });
      setBackupPassword("");
      router.replace("/(tabs)");
    } catch (e) {
      setError(safeErrorMessage(e, t("importWallet.importFailed")));
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{t("importWallet.title")}</Text>
      <Text style={styles.hint}>{t("importWallet.hint")}</Text>
      <TextInput accessibilityLabel="backup-password" style={styles.input}
        placeholder={t("backup.password")} placeholderTextColor="#64748b"
        value={backupPassword} onChangeText={setBackupPassword} secureTextEntry
        autoCapitalize="none" autoCorrect={false} editable={!busy} />
      <Pressable style={styles.secondary} onPress={() => void onPickBackup()} disabled={busy}>
        <Text style={styles.secondaryText}>{t("backup.import")}</Text>
      </Pressable>

      <Pressable style={styles.secondary} onPress={() => void onPasteKeystore()} disabled={busy}>
        <Text style={styles.secondaryText}>{t("importWallet.pasteKeystore")}</Text>
      </Pressable>

      <Pressable style={styles.secondary} onPress={() => void onLoadExportFile()} disabled={busy}>
        <Text style={styles.secondaryText}>{t("importWallet.loadExportFile")}</Text>
      </Pressable>

      <Text style={styles.label}>{t("importWallet.keystoreLabel")}</Text>
      {keystoreJson.trim() ? (
        <Text style={styles.loadedNote}>
          {t("importWallet.keystoreLoaded", {
            bytes: keystoreJson.trim().length,
            defaultValue: `Keystore loaded (${keystoreJson.trim().length} chars). Paste to replace.`,
          })}
        </Text>
      ) : null}
      <TextInput
        style={[styles.input, styles.multiline, styles.tall]}
        value={keystoreJson}
        onChangeText={setKeystoreJson}
        placeholder='{"version":3,...}'
        placeholderTextColor="#64748b"
        multiline
        scrollEnabled
        autoCapitalize="none"
      />

      <Pressable style={styles.secondary} onPress={() => void onDeriveAddress()} disabled={busy}>
        {busy ? (
          <ActivityIndicator color="#f5f7ff" />
        ) : (
          <Text style={styles.secondaryText}>{t("importWallet.deriveAddress")}</Text>
        )}
      </Pressable>

      <Text style={styles.label}>{t("importWallet.addressLabel")}</Text>
      <TextInput
        style={styles.input}
        value={address}
        onChangeText={setAddress}
        placeholder={t("importWallet.addressPlaceholder")}
        placeholderTextColor="#64748b"
        autoCapitalize="none"
      />

      <Text style={styles.label}>{t("importWallet.mnemonicLabel")}</Text>
      <Text style={styles.subHint}>{t("importWallet.mnemonicHint")}</Text>
      <TextInput
        style={[styles.input, styles.multiline]}
        value={mnemonic}
        onChangeText={setMnemonic}
        placeholder="word1 word2 ..."
        placeholderTextColor="#64748b"
        multiline
        autoCapitalize="none"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable style={styles.primary} onPress={() => void onSave()} disabled={busy}>
        {busy ? (
          <ActivityIndicator color="#042f1a" />
        ) : (
          <Text style={styles.primaryText}>{t("importWallet.saveOnDevice")}</Text>
        )}
      </Pressable>

      {address && !validateAcpAddress(address) ? (
        <Text style={styles.warn}>{t("importWallet.invalidAddressWarning")}</Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, backgroundColor: "#0a0f1a", flexGrow: 1 },
  title: { color: "#f5f7ff", fontSize: 24, fontWeight: "700", marginBottom: 8 },
  hint: { color: "#94a3b8", marginBottom: 20, lineHeight: 22 },
  subHint: { color: "#64748b", marginBottom: 6, fontSize: 13, lineHeight: 18 },
  label: { color: "#cbd5e1", marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: "#111827",
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    color: "#f5f7ff",
    padding: 12,
  },
  multiline: { minHeight: 80, textAlignVertical: "top" },
  /** Cap height so a full keystore JSON does not push Save off-screen. */
  tall: { minHeight: 120, maxHeight: 160 },
  loadedNote: { color: "#6ee7b7", marginBottom: 8, fontSize: 13 },
  error: { color: "#f87171", marginTop: 12 },
  warn: { color: "#fbbf24", marginTop: 8 },
  primary: {
    backgroundColor: "#10b981",
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  primaryText: { color: "#042f1a", textAlign: "center", fontWeight: "600" },
  secondary: {
    borderColor: "#334155",
    borderWidth: 1,
    paddingVertical: 12,
    borderRadius: 12,
    marginTop: 12,
  },
  secondaryText: { color: "#f5f7ff", textAlign: "center" },
});
