import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { AcpTransaction } from "@ancap/acp-api-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { loadVaultAddress } from "@/lib/vault";
import { getApi } from "@/lib/api";

export default function ActivityScreen() {
  const { t } = useTranslation();
  const [items, setItems] = useState<AcpTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    const address = await loadVaultAddress();
    if (!address) {
      setError(t("activity.noWallet"));
      setItems([]);
      return;
    }
    try {
      const txs = await getApi().getTransactions(address, 50);
      setItems(txs);
    } catch (e) {
      setError(safeErrorMessage(e, t("activity.failedLoadHistory")));
    }
  }, [t]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      void load().finally(() => setLoading(false));
    }, [load])
  );

  if (loading && items.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#6ee7b7" />
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => item.txid}
      contentContainerStyle={styles.list}
      refreshControl={
        <RefreshControl
          refreshing={loading}
          onRefresh={() => {
            setLoading(true);
            void load().finally(() => setLoading(false));
          }}
          tintColor="#6ee7b7"
        />
      }
      ListEmptyComponent={<Text style={styles.empty}>{error || t("activity.noTransactions")}</Text>}
      renderItem={({ item }) => (
        <View style={styles.row}>
          <View>
            <Text style={styles.dir}>{t(`activity.direction.${item.direction}`)}</Text>
            <Text style={styles.time}>{item.block_time}</Text>
          </View>
          <View style={styles.right}>
            <Text style={styles.amount}>{item.net_acp} ACP</Text>
            <Text style={styles.conf}>{t("activity.confirmations", { count: item.confirmations })}</Text>
          </View>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  list: { padding: 16, flexGrow: 1 },
  empty: { color: "#94a3b8", textAlign: "center", marginTop: 40 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    marginBottom: 10,
    borderColor: "#1e293b",
    borderWidth: 1,
  },
  dir: { color: "#f5f7ff", fontWeight: "600" },
  time: { color: "#64748b", fontSize: 12, marginTop: 4 },
  right: { alignItems: "flex-end" },
  amount: { color: "#6ee7b7", fontWeight: "600" },
  conf: { color: "#94a3b8", fontSize: 12, marginTop: 4 },
});
