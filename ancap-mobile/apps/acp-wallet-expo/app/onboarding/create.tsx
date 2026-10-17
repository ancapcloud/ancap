import { router } from "expo-router";
import * as Clipboard from "expo-clipboard";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { createWallet, safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { deleteKeystoreExportFile, writeKeystoreExportFile } from "@/lib/keystore-export";
import { saveVault } from "@/lib/vault";

// P5-2: block screenshots while seed phrase is visible
import {
  allowScreenCaptureAsync,
  preventScreenCaptureAsync,
} from "expo-screen-capture";

export default function CreateWalletScreen() {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [words, setWords] = useState<string[]>([]);
  const [address, setAddress] = useState("");
  const [keystoreJson, setKeystoreJson] = useState("");

  useEffect(() => {
    void preventScreenCaptureAsync();
    return () => {
      allowScreenCaptureAsync().catch(() => {});
    };
  }, []);

  const onGenerate = async () => {
    setBusy(true);
    try {
      // Drop any prior Copy export so regenerate cannot leave a stale backup file.
      await deleteKeystoreExportFile();
      const w = await createWallet();
      const wordsList = w.mnemonic.split(/\s+/).filter(Boolean);
      setWords(wordsList);
      setAddress(w.address);
      setKeystoreJson(w.keystoreJson);
    } catch (e) {
      const msg = safeErrorMessage(e, t("createWallet.couldNotCreate"));
      if (msg.includes("not linked") || msg.includes("Native ACP")) {
        const nativeSteps = Platform.select({
          ios: t("createWallet.nativeStepsIos"),
          android: t("createWallet.nativeStepsAndroid"),
          default: t("createWallet.nativeStepsDefault"),
        });
        Alert.alert(
          t("createWallet.nativeBuildRequiredTitle"),
          t("createWallet.nativeBuildRequiredBody", { nativeSteps }),
          [{ text: t("createWallet.useImport"), onPress: () => router.push("/onboarding/import") }]
        );
      } else {
        Alert.alert(t("createWallet.couldNotCreate"), msg);
      }
    } finally {
      setBusy(false);
    }
  };

  const onBackupConfirm = () => {
    Alert.alert(
      t("createWallet.backupTitle"),
      t("createWallet.backupBody"),
      [
        { text: t("createWallet.backupDone"), style: "cancel" },
        { text: t("createWallet.backupReview"), style: "destructive" },
      ]
    );
  };

  const onCopyKeystore = async () => {
    if (!keystoreJson) {
      Alert.alert(t("createWallet.generateFirst"));
      return;
    }
    // Explicit external export only: clipboard + optional document-dir file for the user to pull.
    // Never write a hidden SecureStore stash copy.
    await Clipboard.setStringAsync(keystoreJson);
    let fileWritten = false;
    try {
      fileWritten = await writeKeystoreExportFile(keystoreJson);
    } catch {
      fileWritten = false;
    }
    Alert.alert(
      t("createWallet.keystoreCopiedTitle"),
      fileWritten
        ? t("createWallet.keystoreCopiedBody")
        : t("createWallet.keystoreCopiedClipboardOnlyBody")
    );
  };

  const onSaveAndContinue = async () => {
    if (!address || !keystoreJson || words.length === 0) {
      Alert.alert(t("createWallet.generateFirst"));
      return;
    }
    await saveVault({ address, keystoreJson, mnemonic: words.join(" ") });
    Alert.alert(
      t("createWallet.savedTitle"),
      t("createWallet.savedBody"),
      [{ text: t("createWallet.continue"), onPress: () => router.replace("/(tabs)") }]
    );
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{t("createWallet.title")}</Text>
      <Text style={styles.body}>{t("createWallet.body")}</Text>

      {words.length > 0 ? (
        <View style={styles.seedBox}>
          {words.map((w, i) => (
            <Text key={`${w}-${i}`} style={styles.word}>
              {i + 1}. {w}
            </Text>
          ))}
        </View>
      ) : null}

      {address ? (
        <Text style={styles.addr} selectable>
          {address}
        </Text>
      ) : null}

      <Pressable style={styles.primary} onPress={onGenerate} disabled={busy}>
        {busy ? (
          <ActivityIndicator color="#042f1a" />
        ) : (
          <Text style={styles.primaryText}>
            {words.length ? t("createWallet.regenerate") : t("createWallet.generate")}
          </Text>
        )}
      </Pressable>

      {words.length > 0 ? (
        <>
          <Text style={styles.keystoreNote}>{t("createWallet.keystoreNote")}</Text>
          <Pressable style={styles.secondary} onPress={() => void onCopyKeystore()}>
            <Text style={styles.secondaryText}>{t("createWallet.copyKeystore")}</Text>
          </Pressable>

          <Pressable style={styles.warning} onPress={onBackupConfirm}>
            <Text style={styles.warningText}>{t("createWallet.readBeforeContinuing")}</Text>
          </Pressable>

          <Pressable style={styles.secondary} onPress={onSaveAndContinue}>
            <Text style={styles.secondaryText}>{t("createWallet.saveWallet")}</Text>
          </Pressable>
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1 },
  title: { color: "#f5f7ff", fontSize: 24, fontWeight: "700", marginBottom: 12 },
  body: { color: "#94a3b8", fontSize: 16, lineHeight: 24, marginBottom: 20 },
  seedBox: {
    backgroundColor: "#111827",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderColor: "#334155",
    borderWidth: 1,
  },
  word: { color: "#f5f7ff", marginBottom: 6, fontSize: 16 },
  addr: { color: "#6ee7b7", marginBottom: 20, fontSize: 13 },
  keystoreNote: { color: "#fbbf24", marginBottom: 12, lineHeight: 20, fontSize: 13 },
  primary: {
    backgroundColor: "#10b981",
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  primaryText: { color: "#042f1a", textAlign: "center", fontWeight: "600" },
  warning: {
    backgroundColor: "#450a0a",
    borderColor: "#b91c1c",
    borderWidth: 1,
    padding: 14,
    borderRadius: 12,
    marginBottom: 12,
    marginTop: 12,
  },
  warningText: { color: "#fecaca", textAlign: "center", fontWeight: "600" },
  secondary: {
    borderColor: "#334155",
    borderWidth: 1,
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 12,
  },
  secondaryText: { color: "#f5f7ff", textAlign: "center" },
});
