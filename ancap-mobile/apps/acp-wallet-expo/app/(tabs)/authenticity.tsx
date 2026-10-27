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
import type {
  NumismaticAuthResult,
  NumismaticCatalog,
  NumismaticFeatureDef,
  NumismaticValueResult,
} from "@ancap/acp-api-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { getApi } from "@/lib/api";

type Kind = "banknote" | "coin";
type FeatureState = "present" | "missing" | "unchecked";

export default function AuthenticityScreen() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [catalog, setCatalog] = useState<NumismaticCatalog | null>(null);
  const [kind, setKind] = useState<Kind>("banknote");
  const [currency, setCurrency] = useState("USD");
  const [series, setSeries] = useState("$100 Federal Reserve");
  const [year, setYear] = useState("1996");
  const [serial, setSerial] = useState("");
  const [face, setFace] = useState("100");
  const [grade, setGrade] = useState("VF");
  const [rarity, setRarity] = useState("common");
  const [featureState, setFeatureState] = useState<Record<string, FeatureState>>({});
  const [auth, setAuth] = useState<NumismaticAuthResult | null>(null);
  const [value, setValue] = useState<NumismaticValueResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const features = useMemo(() => {
    const all = catalog?.features ?? [];
    return all.filter((f) => f.applies_to.includes(kind));
  }, [catalog, kind]);

  const refresh = useCallback(async () => {
    setError("");
    try {
      const api = getApi();
      const cat = await api.getNumismaticCatalog();
      setCatalog(cat);
      setFeatureState((prev) => {
        const next = { ...prev };
        for (const f of cat.features) {
          if (!next[f.id]) next[f.id] = "unchecked";
        }
        return next;
      });
    } catch (e) {
      setError(safeErrorMessage(e, t("numismatic.loadFailed")));
      setCatalog(null);
    }
  }, [t]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      void refresh().finally(() => setLoading(false));
    }, [refresh])
  );

  const cycleFeature = (f: NumismaticFeatureDef) => {
    setFeatureState((prev) => {
      const cur = prev[f.id] || "unchecked";
      const order: FeatureState[] = ["unchecked", "present", "missing"];
      const next = order[(order.indexOf(cur) + 1) % order.length];
      return { ...prev, [f.id]: next };
    });
    setAuth(null);
    setValue(null);
  };

  const runAuth = async () => {
    setBusy(true);
    setError("");
    setValue(null);
    try {
      const present: string[] = [];
      const missing: string[] = [];
      const unchecked: string[] = [];
      for (const f of features) {
        const st = featureState[f.id] || "unchecked";
        if (st === "present") present.push(f.id);
        else if (st === "missing") missing.push(f.id);
        else unchecked.push(f.id);
      }
      const api = getApi();
      const res = await api.authenticateNumismatic({
        kind,
        currency_code: currency,
        series_or_denomination: series.trim(),
        year: year.trim() ? Number(year) : null,
        serial_or_mint_mark: serial.trim() || null,
        features_present: present,
        features_missing: missing,
        features_unchecked: unchecked,
      });
      setAuth(res);
    } catch (e) {
      setError(safeErrorMessage(e, t("numismatic.authFailed")));
    } finally {
      setBusy(false);
    }
  };

  const runValue = async () => {
    setBusy(true);
    setError("");
    try {
      const api = getApi();
      const res = await api.valueNumismatic({
        kind,
        currency_code: currency,
        series_or_denomination: series.trim(),
        year: year.trim() ? Number(year) : null,
        grade: grade as "VF",
        rarity: rarity as "common",
        face_value_hint: face.trim() || null,
        authenticity_score: auth?.authenticity_score ?? null,
        quantity: 1,
      });
      setValue(res);
    } catch (e) {
      setError(safeErrorMessage(e, t("numismatic.valueFailed")));
    } finally {
      setBusy(false);
    }
  };

  const verdictColor = (v?: string) => {
    if (v === "likely_genuine") return "#6ee7b7";
    if (v === "needs_review") return "#fbbf24";
    if (v === "suspect") return "#fca5a5";
    return "#94a3b8";
  };

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
      <Text style={styles.title}>{t("numismatic.title")}</Text>
      <Text style={styles.subtitle}>{t("numismatic.subtitle")}</Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.section}>{t("numismatic.kind")}</Text>
      <View style={styles.row}>
        {(["banknote", "coin"] as Kind[]).map((k) => (
          <Pressable
            key={k}
            onPress={() => {
              setKind(k);
              setAuth(null);
              setValue(null);
            }}
            style={[styles.chip, kind === k && styles.chipSelected]}
          >
            <Text style={[styles.chipText, kind === k && styles.chipTextSelected]}>
              {k === "banknote" ? t("numismatic.banknote") : t("numismatic.coin")}
            </Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.section}>{t("numismatic.currency")}</Text>
      <View style={styles.row}>
        {(catalog?.currencies ?? [{ code: "USD", label: "USD" }]).map((c) => (
          <Pressable
            key={c.code}
            onPress={() => setCurrency(c.code)}
            style={[styles.chip, currency === c.code && styles.chipSelected]}
          >
            <Text style={[styles.chipText, currency === c.code && styles.chipTextSelected]}>{c.code}</Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.section}>{t("numismatic.series")}</Text>
      <TextInput
        style={styles.input}
        value={series}
        onChangeText={setSeries}
        placeholderTextColor="#64748b"
        placeholder={t("numismatic.seriesPlaceholder")}
      />

      <View style={styles.grid2}>
        <View style={{ flex: 1 }}>
          <Text style={styles.section}>{t("numismatic.year")}</Text>
          <TextInput
            style={styles.input}
            value={year}
            onChangeText={setYear}
            keyboardType="number-pad"
            placeholderTextColor="#64748b"
          />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.section}>{t("numismatic.face")}</Text>
          <TextInput
            style={styles.input}
            value={face}
            onChangeText={setFace}
            keyboardType="decimal-pad"
            placeholderTextColor="#64748b"
          />
        </View>
      </View>

      <Text style={styles.section}>
        {kind === "banknote" ? t("numismatic.serial") : t("numismatic.mint")}
      </Text>
      <TextInput
        style={styles.input}
        value={serial}
        onChangeText={setSerial}
        placeholderTextColor="#64748b"
        autoCapitalize="characters"
      />

      <Text style={styles.section}>{t("numismatic.checks")}</Text>
      <Text style={styles.hint}>{t("numismatic.checksHint")}</Text>
      {features.map((f) => {
        const st = featureState[f.id] || "unchecked";
        return (
          <Pressable key={f.id} onPress={() => cycleFeature(f)} style={styles.featureRow}>
            <Text style={styles.featureLabel}>{f.label}</Text>
            <Text
              style={[
                styles.featureStatus,
                st === "present" && { color: "#6ee7b7" },
                st === "missing" && { color: "#fca5a5" },
              ]}
            >
              {st === "present"
                ? t("numismatic.present")
                : st === "missing"
                  ? t("numismatic.missing")
                  : t("numismatic.unchecked")}
            </Text>
          </Pressable>
        );
      })}

      <Pressable style={styles.primaryBtn} onPress={() => void runAuth()} disabled={busy}>
        {busy ? <ActivityIndicator color="#0a0f1a" /> : <Text style={styles.primaryBtnText}>{t("numismatic.runAuth")}</Text>}
      </Pressable>

      {auth ? (
        <View style={styles.resultBox}>
          <Text style={[styles.verdict, { color: verdictColor(auth.verdict) }]}>
            {auth.verdict.replace(/_/g, " ")} · {auth.authenticity_score}/100
          </Text>
          {auth.flags.map((f) => (
            <Text key={f} style={styles.flag}>
              • {f}
            </Text>
          ))}
          <Text style={styles.meta}>{auth.next_step}</Text>
        </View>
      ) : null}

      <Text style={styles.section}>{t("numismatic.grade")}</Text>
      <View style={styles.row}>
        {(catalog?.grades ?? [{ code: "VF", label: "VF" }]).map((g) => (
          <Pressable
            key={g.code}
            onPress={() => setGrade(g.code)}
            style={[styles.chip, grade === g.code && styles.chipSelected]}
          >
            <Text style={[styles.chipText, grade === g.code && styles.chipTextSelected]}>{g.code}</Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.section}>{t("numismatic.rarity")}</Text>
      <View style={styles.row}>
        {(catalog?.rarity_tiers ?? [{ code: "common", label: "Common" }]).map((r) => (
          <Pressable
            key={r.code}
            onPress={() => setRarity(r.code)}
            style={[styles.chip, rarity === r.code && styles.chipSelected]}
          >
            <Text style={[styles.chipText, rarity === r.code && styles.chipTextSelected]}>{r.code}</Text>
          </Pressable>
        ))}
      </View>

      <Pressable style={styles.secondaryBtn} onPress={() => void runValue()} disabled={busy}>
        <Text style={styles.secondaryBtnText}>{t("numismatic.runValue")}</Text>
      </Pressable>

      {value ? (
        <View style={styles.resultBox}>
          <Text style={styles.valueLine}>
            {value.indicative_acp_amount} ACP
          </Text>
          <Text style={styles.meta}>{value.rate_note}</Text>
          <Text style={styles.meta}>{value.authenticity_note}</Text>
          <Text style={styles.meta}>{value.next_step}</Text>
        </View>
      ) : null}

      {catalog ? <Text style={styles.compliance}>{catalog.disclaimer}</Text> : null}
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
  title: { color: "#f5f7ff", fontSize: 26, fontWeight: "800", marginBottom: 6 },
  subtitle: { color: "#94a3b8", fontSize: 14, lineHeight: 20, marginBottom: 16 },
  section: { color: "#cbd5e1", fontSize: 13, fontWeight: "600", marginTop: 12, marginBottom: 8 },
  hint: { color: "#64748b", fontSize: 12, marginBottom: 8 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  grid2: { flexDirection: "row", gap: 10 },
  chip: {
    backgroundColor: "#111827",
    borderColor: "#1e293b",
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  chipSelected: { borderColor: "#6ee7b7", backgroundColor: "#0f291e" },
  chipText: { color: "#e2e8f0", fontWeight: "700", fontSize: 12 },
  chipTextSelected: { color: "#6ee7b7" },
  input: {
    backgroundColor: "#111827",
    borderColor: "#1e293b",
    borderWidth: 1,
    borderRadius: 10,
    color: "#f5f7ff",
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    fontWeight: "600",
  },
  featureRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#1e293b",
  },
  featureLabel: { color: "#e2e8f0", flex: 1, fontSize: 13 },
  featureStatus: { color: "#64748b", fontWeight: "700", fontSize: 12 },
  primaryBtn: {
    marginTop: 18,
    backgroundColor: "#6ee7b7",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryBtnText: { color: "#0a0f1a", fontWeight: "800", fontSize: 16 },
  secondaryBtn: {
    marginTop: 14,
    backgroundColor: "#1e293b",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  secondaryBtnText: { color: "#6ee7b7", fontWeight: "800", fontSize: 15 },
  resultBox: {
    marginTop: 16,
    padding: 14,
    borderRadius: 12,
    backgroundColor: "#111827",
    borderColor: "#1e293b",
    borderWidth: 1,
    gap: 6,
  },
  verdict: { fontWeight: "800", fontSize: 16, textTransform: "capitalize" },
  valueLine: { color: "#6ee7b7", fontWeight: "800", fontSize: 22 },
  flag: { color: "#fbbf24", fontSize: 12 },
  meta: { color: "#94a3b8", fontSize: 12, lineHeight: 17 },
  compliance: { color: "#64748b", fontSize: 11, lineHeight: 16, marginTop: 24 },
  error: { color: "#fca5a5", marginBottom: 10 },
});
