import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { BridgeIntent, RedeemQuote, ReserveProof, WacpStatus } from "@ancap/acp-bridge-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { loadVaultAddress } from "@/lib/vault";
import { getBridgeClient } from "@/lib/bridge";

export default function BridgeScreen() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [bridgeStatus, setBridgeStatus] = useState("—");
  const [bridgeEnabled, setBridgeEnabled] = useState(false);
  const [reverseEnabled, setReverseEnabled] = useState(false);
  const [wacpContract, setWacpContract] = useState("");
  const [reserveProof, setReserveProof] = useState<ReserveProof | null>(null);
  const [wacpStatus, setWacpStatus] = useState<WacpStatus | null>(null);
  const [sampleRedeemQuote, setSampleRedeemQuote] = useState<RedeemQuote | null>(null);
  const [recentIntents, setRecentIntents] = useState<BridgeIntent[]>([]);
  const [docs, setDocs] = useState<{ bridge: string; risks: string; reserve: string } | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setError("");
    const bridge = getBridgeClient();
    try {
      const [status, reserve, publicStatus, quote] = await Promise.all([
        bridge.getStatus(),
        bridge.getReserveProof(),
        bridge.getWacpStatus(),
        bridge.quoteBscToAcp("1"),
      ]);
      setBridgeStatus(publicStatus.status || reserve.status || "offline");
      setBridgeEnabled(status.bridge_rail_enabled);
      setReverseEnabled(publicStatus.redeem_available);
      setWacpContract(publicStatus.wacp_contract || "—");
      setReserveProof(reserve);
      setWacpStatus(publicStatus);
      setSampleRedeemQuote(quote);
      setDocs({
        bridge: publicStatus.docs.bridge,
        risks: publicStatus.docs.risks,
        reserve: publicStatus.docs.reserve,
      });
    } catch (e) {
      setBridgeStatus("offline");
      setError(safeErrorMessage(e, t("bridge.statusUnavailable")));
      setReserveProof(null);
      setWacpStatus(null);
      setSampleRedeemQuote(null);
      setRecentIntents([]);
      return;
    }

    try {
      const address = await loadVaultAddress();
      if (!address) {
        setRecentIntents([]);
        return;
      }
      setRecentIntents([]);
    } catch {
      setRecentIntents([]);
    }
  }, [t]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      void refresh().finally(() => setLoading(false));
    }, [refresh])
  );

  const enabledLabel = t("common.enabled");
  const disabledLabel = t("common.disabled");
  const yesLabel = t("common.yes");
  const noLabel = t("common.no");
  const unknownLabel = t("common.unknown");

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={loading}
          onRefresh={() => {
            setLoading(true);
            void refresh().finally(() => setLoading(false));
          }}
          tintColor="#6ee7b7"
        />
      }
    >
      <Text style={styles.title}>{t("bridge.title")}</Text>
      <Text style={styles.disclaimer}>{t("bridge.disclaimer")}</Text>

      <View style={styles.card}>
        <Text style={styles.label}>{t("bridge.railStatus")}</Text>
        <Text style={styles.value}>{bridgeStatus}</Text>
        <Text style={styles.meta}>{t("bridge.mint", { status: bridgeEnabled ? enabledLabel : disabledLabel })}</Text>
        <Text style={styles.meta}>
          {t("bridge.redeem", {
            status: reverseEnabled ? enabledLabel : t("bridge.redeemPendingDisabled"),
          })}
        </Text>
        <Text style={styles.meta}>{t("bridge.contract", { value: wacpContract })}</Text>
      </View>

      {reserveProof ? (
        <View style={styles.card}>
          <Text style={styles.label}>{t("bridge.reserveProof")}</Text>
          <Text style={styles.meta}>{t("bridge.health", { value: reserveProof.reserve_health })}</Text>
          <Text style={styles.meta}>{t("bridge.backingRatio", { value: reserveProof.backing_ratio ?? unknownLabel })}</Text>
          <Text style={styles.meta}>{t("bridge.reserveAddress", { value: reserveProof.acp_reserve_address || unknownLabel })}</Text>
          <Text style={styles.meta}>{t("bridge.reserveBalance", { value: reserveProof.acp_reserve_balance_smallest })}</Text>
        </View>
      ) : null}

      {sampleRedeemQuote ? (
        <View style={styles.card}>
          <Text style={styles.label}>{t("bridge.redeemExample")}</Text>
          <Text style={styles.meta}>{t("bridge.redeemExampleLine", { amount: sampleRedeemQuote.acp_amount_floor })}</Text>
          <Text style={styles.meta}>{t("bridge.remainder", { value: sampleRedeemQuote.remainder_wacp })}</Text>
          <Text style={styles.meta}>{sampleRedeemQuote.policy}</Text>
        </View>
      ) : null}

      {wacpStatus ? (
        <View style={styles.card}>
          <Text style={styles.label}>{t("bridge.publicMarketStatus")}</Text>
          <Text style={styles.meta}>{t("bridge.pairLive", { value: wacpStatus.pair_live ? yesLabel : noLabel })}</Text>
          <Text style={styles.meta}>{t("bridge.dex", { value: wacpStatus.pair_dex ?? unknownLabel })}</Text>
          <Text style={styles.meta}>{t("bridge.contractVerified", { value: wacpStatus.bsc_contract_verified ? yesLabel : noLabel })}</Text>
          <Text style={styles.meta}>{t("bridge.tokenMetadataLive", { value: wacpStatus.token_metadata_live ? yesLabel : noLabel })}</Text>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.label}>{t("bridge.yourIntents")}</Text>
        {recentIntents.length > 0 ? (
          recentIntents.slice(0, 3).map((item) => (
            <View key={item.id} style={styles.intentRow}>
              <Text style={styles.intentPrimary}>{item.direction} · {item.status}</Text>
              <Text style={styles.intentMeta}>{t("bridge.intentAmount", { value: item.amount_acp_smallest })}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.meta}>{t("bridge.intentsUnavailable")}</Text>
        )}
      </View>

      <Text style={styles.note}>{t("bridge.note")}</Text>

      {docs ? (
        <View style={styles.links}>
          <Pressable onPress={() => Linking.openURL(docs.bridge)}>
            <Text style={styles.link}>{t("bridge.docs")}</Text>
          </Pressable>
          <Pressable onPress={() => Linking.openURL(docs.risks)}>
            <Text style={styles.link}>{t("bridge.risks")}</Text>
          </Pressable>
          <Pressable onPress={() => Linking.openURL(docs.reserve)}>
            <Text style={styles.link}>{t("bridge.reserveDocs")}</Text>
          </Pressable>
          {wacpStatus?.swap_url ? (
            <Pressable onPress={() => Linking.openURL(wacpStatus.swap_url!)}>
              <Text style={styles.link}>{t("bridge.openSwap")}</Text>
            </Pressable>
          ) : null}
        </View>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {loading ? <ActivityIndicator color="#6ee7b7" style={{ marginTop: 24 }} /> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, flexGrow: 1 },
  title: { color: "#f5f7ff", fontSize: 22, fontWeight: "700", marginBottom: 8 },
  disclaimer: { color: "#fbbf24", lineHeight: 20, marginBottom: 20, fontSize: 13 },
  card: {
    backgroundColor: "#111827",
    borderRadius: 16,
    padding: 20,
    borderColor: "#1e293b",
    borderWidth: 1,
    marginBottom: 16,
  },
  label: { color: "#94a3b8", marginBottom: 8 },
  value: { color: "#6ee7b7", fontSize: 20, fontWeight: "600", marginBottom: 8 },
  meta: { color: "#cbd5e1", marginTop: 4, fontSize: 13 },
  intentRow: {
    paddingVertical: 8,
    borderTopColor: "#1e293b",
    borderTopWidth: 1,
  },
  intentPrimary: { color: "#f5f7ff", fontSize: 14, fontWeight: "600" },
  intentMeta: { color: "#94a3b8", marginTop: 4, fontSize: 12 },
  note: { color: "#94a3b8", lineHeight: 22, marginBottom: 16 },
  links: { gap: 12 },
  link: { color: "#6ee7b7", fontSize: 16 },
  error: { color: "#f87171", marginTop: 12 },
});
