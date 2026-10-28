import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
} from "react-native";
import { assertAcpAddress, safeErrorMessage, signAndPrepareTransfer } from "@ancap/acp-wallet-sdk";
import { loadVault } from "@/lib/vault";
import { getApi } from "@/lib/api";

const RPC_URL =
  process.env.EXPO_PUBLIC_ACP_RPC_URL ?? "https://acp1.ancap.cloud/rpc";

export default function SendScreen() {
  const { t } = useTranslation();
  const [to, setTo] = useState("");
  const [amount, setAmount] = useState("");
  const [fee, setFee] = useState("");
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState("");

  const onEstimate = async () => {
    try {
      const vault = await loadVault();
      if (!vault) throw new Error(t("send.noWallet"));
      const from = assertAcpAddress(vault.address, "from");
      const toAddr = assertAcpAddress(to.trim(), "to");
      const est = await getApi().estimateFee({
        from,
        to: toAddr,
        amountAcp: amount.trim(),
      });
      setFee(est.feeAcp);
      setPreview(t("send.feePreview", { fee: est.feeAcp, minFee: est.minFeeAcp }));
    } catch (e) {
      Alert.alert(t("send.estimateFailedTitle"), safeErrorMessage(e, t("send.genericError")));
    }
  };

  const onSignLocal = async () => {
    setBusy(true);
    setPreview("");
    try {
      const vault = await loadVault();
      if (!vault) throw new Error(t("send.noWalletOnDevice"));

      const signed = await signAndPrepareTransfer(RPC_URL, vault.keystoreJson, {
        from: vault.address,
        to: to.trim(),
        amountAcp: amount.trim(),
        feeAcp: fee.trim() || undefined,
      });

      setPreview(t("send.signedLocalPreview", { txid: signed.txid }));
      Alert.alert(
        t("send.signedLocalTitle"),
        t("send.signedLocalBody", { txid: signed.txid })
      );
    } catch (e) {
      const msg = safeErrorMessage(e, t("send.signFailedTitle"));
      if (msg.includes("native module")) {
        Alert.alert(t("send.nativeSigningRequiredTitle"), t("send.nativeSigningRequiredBody"));
      } else {
        Alert.alert(t("send.signFailedTitle"), msg);
      }
    } finally {
      setBusy(false);
    }
  };

  const onSend = async () => {
    setBusy(true);
    setPreview("");
    try {
      const vault = await loadVault();
      if (!vault) throw new Error(t("send.noWalletOnDevice"));

      const signed = await signAndPrepareTransfer(RPC_URL, vault.keystoreJson, {
        from: vault.address,
        to: to.trim(),
        amountAcp: amount.trim(),
        feeAcp: fee.trim() || undefined,
      });

      const result = await getApi().broadcast(signed.rawTx);
      if (!result.accepted) {
        throw new Error(result.reason ?? t("send.broadcastRejected"));
      }
      Alert.alert(t("send.sentTitle"), t("send.sentBody", { txid: result.txid ?? signed.txid }));
      setTo("");
      setAmount("");
      setFee("");
    } catch (e) {
      const msg = safeErrorMessage(e, t("send.sendFailedTitle"));
      if (msg.includes("native module")) {
        Alert.alert(t("send.nativeSigningRequiredTitle"), t("send.nativeSigningRequiredBody"));
      } else {
        Alert.alert(t("send.sendFailedTitle"), msg);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.label}>{t("send.recipientLabel")}</Text>
      <TextInput
        style={styles.input}
        value={to}
        onChangeText={setTo}
        autoCapitalize="none"
        placeholder="acp1..."
        placeholderTextColor="#64748b"
      />

      <Text style={styles.label}>{t("send.amountLabel")}</Text>
      <TextInput
        style={styles.input}
        value={amount}
        onChangeText={setAmount}
        keyboardType="decimal-pad"
        placeholder="0.0"
        placeholderTextColor="#64748b"
      />

      <Text style={styles.label}>{t("send.feeLabel")}</Text>
      <TextInput
        style={styles.input}
        value={fee}
        onChangeText={setFee}
        keyboardType="decimal-pad"
        placeholder="auto"
        placeholderTextColor="#64748b"
      />

      {preview ? <Text style={styles.preview}>{preview}</Text> : null}

      <Pressable style={styles.secondary} onPress={onEstimate} disabled={busy}>
        <Text style={styles.secondaryText}>{t("send.estimateFee")}</Text>
      </Pressable>

      <Pressable style={styles.secondary} onPress={() => void onSignLocal()} disabled={busy}>
        <Text style={styles.secondaryText}>{t("send.signLocalOnly")}</Text>
      </Pressable>

      <Pressable style={styles.primary} onPress={() => void onSend()} disabled={busy}>
        {busy ? (
          <ActivityIndicator color="#042f1a" />
        ) : (
          <Text style={styles.primaryText}>{t("send.signAndSend")}</Text>
        )}
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1 },
  label: { color: "#94a3b8", marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: "#111827",
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    color: "#f5f7ff",
    padding: 12,
  },
  preview: { color: "#cbd5e1", marginTop: 16 },
  secondary: {
    borderColor: "#334155",
    borderWidth: 1,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 20,
  },
  secondaryText: { color: "#f5f7ff", textAlign: "center" },
  primary: {
    backgroundColor: "#10b981",
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 12,
  },
  primaryText: { color: "#042f1a", textAlign: "center", fontWeight: "600" },
});
