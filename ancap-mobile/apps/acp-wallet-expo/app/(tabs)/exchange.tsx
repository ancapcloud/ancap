import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { ExchangeAsset, ExchangeCatalog, ExchangeQuote, ExchangeTicket } from "@ancap/acp-api-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { getApi } from "@/lib/api";
import { loadVaultAddress } from "@/lib/vault";

const HUB = "acp";

export default function ExchangeScreen() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [catalog, setCatalog] = useState<ExchangeCatalog | null>(null);
  const [fromAsset, setFromAsset] = useState("usdt_trc20");
  const [toAsset, setToAsset] = useState(HUB);
  const [amount, setAmount] = useState("100");
  const [purity, setPurity] = useState("999");
  const [goodsEstimate, setGoodsEstimate] = useState("");
  const [quote, setQuote] = useState<ExchangeQuote | null>(null);
  const [ticket, setTicket] = useState<ExchangeTicket | null>(null);
  const [error, setError] = useState("");
  const [quoting, setQuoting] = useState(false);
  const [settling, setSettling] = useState(false);

  const assets = catalog?.assets ?? [];
  const fromMeta = useMemo(
    () => assets.find((a) => a.id === fromAsset) ?? null,
    [assets, fromAsset]
  );
  const liveAssets = useMemo(
    () => assets.filter((a) => a.availability !== "planned" || a.id === HUB),
    [assets]
  );

  const refresh = useCallback(async () => {
    setError("");
    try {
      const api = getApi();
      const cat = await api.getExchangeCatalog();
      setCatalog(cat);
      if (!cat.assets.some((a) => a.id === fromAsset)) {
        const first = cat.assets.find((a) => a.id !== HUB) ?? cat.assets[0];
        if (first) setFromAsset(first.id);
      }
    } catch (e) {
      setError(safeErrorMessage(e, t("exchange.loadFailed")));
      setCatalog(null);
    }
  }, [fromAsset, t]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      void refresh().finally(() => setLoading(false));
    }, [refresh])
  );

  const swapDirection = () => {
    setFromAsset(toAsset);
    setToAsset(fromAsset);
    setQuote(null);
    setTicket(null);
  };

  const onQuote = async () => {
    setQuoting(true);
    setError("");
    setQuote(null);
    setTicket(null);
    try {
      const api = getApi();
      const body: {
        from_asset: string;
        to_asset: string;
        from_amount: string;
        purity_ppt?: number;
        goods_estimate_acp?: string;
      } = {
        from_asset: fromAsset,
        to_asset: toAsset,
        from_amount: amount.trim(),
      };
      if (fromMeta?.kind === "metal") {
        const ppt = Number(purity);
        if (Number.isFinite(ppt)) body.purity_ppt = ppt;
      }
      if (fromMeta?.kind === "goods" && goodsEstimate.trim()) {
        body.goods_estimate_acp = goodsEstimate.trim();
      }
      const q = await api.quoteExchange(body);
      setQuote(q);
    } catch (e) {
      setError(safeErrorMessage(e, t("exchange.quoteFailed")));
    } finally {
      setQuoting(false);
    }
  };

  const onOpenAndSettle = async () => {
    if (!quote) return;
    setSettling(true);
    setError("");
    try {
      const address = await loadVaultAddress();
      if (!address) {
        setError(t("exchange.needAddress"));
        return;
      }
      const api = getApi();
      const opened = await api.createExchangeTicket(
        {
          quote_id: quote.quote_id,
          payout_acp_address: address,
        },
        `xo-${quote.quote_id}`
      );
      const settled = await api.authSettleExchangeTicket(opened.id);
      setTicket(settled);
    } catch (e) {
      setError(safeErrorMessage(e, t("exchange.ticketFailed")));
    } finally {
      setSettling(false);
    }
  };

  const onSyncTicket = async () => {
    if (!ticket) return;
    setSettling(true);
    setError("");
    try {
      const api = getApi();
      const synced = await api.syncExchangeTicket(ticket.id);
      setTicket(synced);
    } catch (e) {
      setError(safeErrorMessage(e, t("exchange.ticketFailed")));
    } finally {
      setSettling(false);
    }
  };

  const pickAsset = (side: "from" | "to", asset: ExchangeAsset) => {
    if (side === "from") {
      setFromAsset(asset.id);
      if (asset.id === toAsset) setToAsset(asset.id === HUB ? "usdt_trc20" : HUB);
    } else {
      setToAsset(asset.id);
      if (asset.id === fromAsset) setFromAsset(asset.id === HUB ? "usdt_trc20" : HUB);
    }
    setQuote(null);
    setTicket(null);
  };

  const AssetChip = ({
    asset,
    selected,
    onPress,
  }: {
    asset: ExchangeAsset;
    selected: boolean;
    onPress: () => void;
  }) => (
    <Pressable
      onPress={onPress}
      style={[styles.chip, selected && styles.chipSelected, asset.availability === "planned" && styles.chipPlanned]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
        {asset.symbol}
        {asset.availability === "planned" ? " ·" : ""}
      </Text>
      <Text style={styles.chipSub}>{asset.label}</Text>
    </Pressable>
  );

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
      <Text style={styles.title}>{t("exchange.title")}</Text>
      <Text style={styles.subtitle}>{t("exchange.subtitle")}</Text>

      {loading && !catalog ? (
        <ActivityIndicator color="#6ee7b7" style={{ marginTop: 24 }} />
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.section}>{t("exchange.from")}</Text>
      <View style={styles.chipRow}>
        {liveAssets.map((a) => (
          <AssetChip key={`from-${a.id}`} asset={a} selected={a.id === fromAsset} onPress={() => pickAsset("from", a)} />
        ))}
      </View>

      <Pressable style={styles.swapBtn} onPress={swapDirection}>
        <Text style={styles.swapBtnText}>{t("exchange.swapSides")}</Text>
      </Pressable>

      <Text style={styles.section}>{t("exchange.to")}</Text>
      <View style={styles.chipRow}>
        {liveAssets.map((a) => (
          <AssetChip key={`to-${a.id}`} asset={a} selected={a.id === toAsset} onPress={() => pickAsset("to", a)} />
        ))}
      </View>

      <Text style={styles.section}>{t("exchange.amount")}</Text>
      <TextInput
        style={styles.input}
        value={amount}
        onChangeText={setAmount}
        keyboardType="decimal-pad"
        placeholderTextColor="#64748b"
        placeholder={fromMeta?.unit ? `0 ${fromMeta.unit}` : "0"}
      />

      {fromMeta?.kind === "metal" ? (
        <>
          <Text style={styles.section}>{t("exchange.purity")}</Text>
          <TextInput
            style={styles.input}
            value={purity}
            onChangeText={setPurity}
            keyboardType="number-pad"
            placeholderTextColor="#64748b"
            placeholder="999"
          />
        </>
      ) : null}

      {fromMeta?.kind === "goods" ? (
        <>
          <Text style={styles.section}>{t("exchange.goodsEstimate")}</Text>
          <TextInput
            style={styles.input}
            value={goodsEstimate}
            onChangeText={setGoodsEstimate}
            keyboardType="decimal-pad"
            placeholderTextColor="#64748b"
            placeholder="ACP"
          />
        </>
      ) : null}

      <Pressable style={styles.primaryBtn} onPress={() => void onQuote()} disabled={quoting}>
        {quoting ? (
          <ActivityIndicator color="#0a0f1a" />
        ) : (
          <Text style={styles.primaryBtnText}>{t("exchange.getQuote")}</Text>
        )}
      </Pressable>

      {quote ? (
        <View style={styles.quoteBox}>
          <Text style={styles.quoteTitle}>{t("exchange.quote")}</Text>
          <Text style={styles.quoteLine}>
            {quote.from_amount} {quote.from_asset} → {quote.to_amount} {quote.to_asset}
          </Text>
          <Text style={styles.quoteMeta}>
            {t("exchange.hub")}: {quote.acp_hub_amount} ACP · {quote.legs.length}{" "}
            {quote.legs.length === 1 ? t("exchange.leg") : t("exchange.legs")}
          </Text>
          <Text style={styles.quoteMeta}>
            {t("exchange.rail")}: {quote.rail}
            {quote.indicative ? ` · ${t("exchange.indicative")}` : ""}
          </Text>
          <Text style={styles.quoteNote}>{quote.rate_note}</Text>
          <Text style={styles.quoteNext}>{quote.next_step}</Text>
          <Text style={styles.quoteHint}>{t("exchange.ticketHint")}</Text>
          <Pressable style={styles.secondaryBtn} onPress={() => void onOpenAndSettle()} disabled={settling}>
            {settling ? (
              <ActivityIndicator color="#6ee7b7" />
            ) : (
              <Text style={styles.secondaryBtnText}>{t("exchange.openTicket")}</Text>
            )}
          </Pressable>
        </View>
      ) : null}

      {ticket ? (
        <View style={styles.quoteBox}>
          <Text style={styles.quoteTitle}>
            {t("exchange.ticketOpened")}: {ticket.status}
          </Text>
          <Text style={styles.quoteMeta}>
            {ticket.id.slice(0, 8)}… · {ticket.rail}
            {ticket.rail_ref_id ? ` · ref ${ticket.rail_ref_id.slice(0, 8)}…` : ""}
          </Text>
          <Text style={styles.quoteNext}>{ticket.next_step}</Text>
          <Pressable style={styles.secondaryBtn} onPress={() => void onSyncTicket()} disabled={settling}>
            <Text style={styles.secondaryBtnText}>{t("exchange.syncTicket")}</Text>
          </Pressable>
        </View>
      ) : null}

      {catalog ? (
        <Text style={styles.compliance}>{catalog.compliance_note}</Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
    paddingBottom: 48,
    backgroundColor: "#0a0f1a",
    flexGrow: 1,
  },
  title: {
    color: "#f5f7ff",
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 6,
  },
  subtitle: {
    color: "#94a3b8",
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 18,
  },
  section: {
    color: "#cbd5e1",
    fontSize: 13,
    fontWeight: "600",
    marginTop: 12,
    marginBottom: 8,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    backgroundColor: "#111827",
    borderColor: "#1e293b",
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
    minWidth: 88,
  },
  chipSelected: {
    borderColor: "#6ee7b7",
    backgroundColor: "#0f291e",
  },
  chipPlanned: {
    opacity: 0.55,
  },
  chipText: {
    color: "#e2e8f0",
    fontWeight: "700",
    fontSize: 13,
  },
  chipTextSelected: {
    color: "#6ee7b7",
  },
  chipSub: {
    color: "#64748b",
    fontSize: 10,
    marginTop: 2,
  },
  swapBtn: {
    alignSelf: "center",
    marginVertical: 10,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: "#1e293b",
  },
  swapBtnText: {
    color: "#6ee7b7",
    fontWeight: "700",
    fontSize: 13,
  },
  input: {
    backgroundColor: "#111827",
    borderColor: "#1e293b",
    borderWidth: 1,
    borderRadius: 10,
    color: "#f5f7ff",
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 18,
    fontWeight: "600",
  },
  primaryBtn: {
    marginTop: 18,
    backgroundColor: "#6ee7b7",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryBtnText: {
    color: "#0a0f1a",
    fontWeight: "800",
    fontSize: 16,
  },
  secondaryBtn: {
    marginTop: 14,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#6ee7b7",
  },
  secondaryBtnText: {
    color: "#6ee7b7",
    fontWeight: "800",
    fontSize: 15,
  },
  quoteBox: {
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#111827",
    borderColor: "#1e293b",
    borderWidth: 1,
    gap: 6,
  },
  quoteTitle: {
    color: "#6ee7b7",
    fontWeight: "800",
    fontSize: 15,
    marginBottom: 4,
  },
  quoteLine: {
    color: "#f5f7ff",
    fontSize: 17,
    fontWeight: "700",
  },
  quoteMeta: {
    color: "#94a3b8",
    fontSize: 13,
  },
  quoteNote: {
    color: "#cbd5e1",
    fontSize: 12,
    marginTop: 4,
  },
  quoteNext: {
    color: "#e2e8f0",
    fontSize: 13,
    marginTop: 8,
    lineHeight: 18,
  },
  quoteHint: {
    color: "#64748b",
    fontSize: 12,
    marginTop: 8,
  },
  compliance: {
    color: "#64748b",
    fontSize: 11,
    lineHeight: 16,
    marginTop: 24,
  },
  error: {
    color: "#fca5a5",
    marginBottom: 10,
  },
});
