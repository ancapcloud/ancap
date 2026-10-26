import { Link } from "expo-router";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import { fetchWacpBalanceWei, formatWacp } from "@ancap/acp-bsc-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { loadVaultAddress } from "@/lib/vault";
import { getApi } from "@/lib/api";

export default function WalletHomeScreen() {
  const { t } = useTranslation();
  const [address, setAddress] = useState("");
  const [acp, setAcp] = useState("—");
  const [wacp, setWacp] = useState("—");
  const [utxos, setUtxos] = useState(0);
  const [bridgeStatus, setBridgeStatus] = useState("—");
  const [wacpEnabled, setWacpEnabled] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setError("");
    const walletAddress = await loadVaultAddress();
    if (!walletAddress) {
      setError(t("walletHome.noWallet"));
      return;
    }
    setAddress(walletAddress);
    try {
      const api = getApi();
      const [bal, cfg] = await Promise.all([api.getBalance(walletAddress), api.getConfig()]);
      setAcp(bal.acp);
      setUtxos(bal.utxo_count);
      setBridgeStatus(cfg.bridgeStatus);

      // Fetch wACP balance from BSC
      if (cfg.bscRpcUrl && cfg.wacpContract) {
        setWacpEnabled(true);
        try {
          const wei = await fetchWacpBalanceWei({
            rpcUrl: cfg.bscRpcUrl,
            contract: cfg.wacpContract,
            holder: walletAddress,
          });
          setWacp(formatWacp(wei));
        } catch {
          setWacp("—");
        }
      } else {
        setWacpEnabled(false);
        setWacp("—");
      }
    } catch (e) {
      setError(safeErrorMessage(e, t("walletHome.failedLoadBalance")));
    }
  }, [t]);

  useFocusEffect(
    useCallback(() => {
      void refresh();
    }, [refresh])
  );

  const onPull = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onPull} tintColor="#6ee7b7" />
      }
    >
      <Text style={styles.label}>{t("walletHome.addressLabel")}</Text>
      <Text style={styles.address} selectable>
        {address || "…"}
      </Text>

      <View style={styles.actions}>
        <Link href="/receive" asChild>
          <Pressable style={styles.actionBtn}>
            <Text style={styles.actionText}>{t("walletHome.receive")}</Text>
          </Pressable>
        </Link>
        <Link href="/(tabs)/send" asChild>
          <Pressable style={styles.actionBtn}>
            <Text style={styles.actionText}>{t("walletHome.send")}</Text>
          </Pressable>
        </Link>
      </View>

      <Link href="/smart-pay" asChild>
        <Pressable style={styles.smartPayBtn}>
          <Text style={styles.smartPayTitle}>Smart Pay beta</Text>
          <Text style={styles.smartPayText}>Paste/import payment payload → parse → quote → execute</Text>
        </Pressable>
      </Link>

      <View style={styles.card}>
        <Text style={styles.cardLabel}>{t("walletHome.acpLabel")}</Text>
        <Text style={styles.balance}>{acp}</Text>
        <Text style={styles.meta}>{t("walletHome.utxos", { count: utxos })}</Text>
      </View>

      {wacpEnabled ? (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>{t("walletHome.wacpLabel")}</Text>
          <Text style={styles.balanceWacp}>{wacp}</Text>
          <Text style={styles.meta}>{t("walletHome.wacpMeta")}</Text>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.cardLabel}>{t("walletHome.bridgeLabel")}</Text>
        <Text style={styles.meta}>{t("walletHome.bridgeStatus", { status: bridgeStatus })}</Text>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!address && !error ? <ActivityIndicator color="#6ee7b7" /> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1 },
  label: { color: "#94a3b8", fontSize: 13, marginBottom: 4 },
  address: { color: "#f5f7ff", fontSize: 14, marginBottom: 16 },
  actions: { flexDirection: "row", gap: 12, marginBottom: 20 },
  actionBtn: {
    flex: 1,
    backgroundColor: "#10b981",
    paddingVertical: 14,
    borderRadius: 12,
  },
  actionText: { color: "#042f1a", textAlign: "center", fontWeight: "600" },
  smartPayBtn: {
    backgroundColor: "#0f172a",
    borderColor: "#10b981",
    borderWidth: 1,
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
  },
  smartPayTitle: { color: "#6ee7b7", fontSize: 16, fontWeight: "700", marginBottom: 6 },
  smartPayText: { color: "#cbd5e1", lineHeight: 20 },
  card: {
    backgroundColor: "#111827",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderColor: "#1e293b",
    borderWidth: 1,
  },
  cardLabel: { color: "#94a3b8", marginBottom: 8 },
  balance: { color: "#6ee7b7", fontSize: 36, fontWeight: "700" },
  balanceWacp: { color: "#a78bfa", fontSize: 36, fontWeight: "700" },
  meta: { color: "#cbd5e1", marginTop: 8 },
  error: { color: "#f87171", marginTop: 12 },
});
