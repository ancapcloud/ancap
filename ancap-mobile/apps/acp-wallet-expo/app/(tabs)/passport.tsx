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
  TextInput,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { DigitalPassportRecord } from "@ancap/acp-api-client";
import { safeErrorMessage } from "@ancap/acp-wallet-sdk";
import { getApi, hasApiAuthHeader } from "@/lib/api";
import { getOrgIdForPassport, syncNfcCredentialToBackend } from "@/lib/identity";
import { loadVaultAddress } from "@/lib/vault";

export default function PassportScreen() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [passports, setPassports] = useState<DigitalPassportRecord[]>([]);
  const [walletAddress, setWalletAddress] = useState("");
  const orgId = getOrgIdForPassport();

  const refresh = useCallback(async () => {
    setError("");
    if (!hasApiAuthHeader()) {
      setPassports([]);
      setLoading(false);
      return;
    }
    try {
      const api = getApi();
      const listed = await api.listMyPassports();
      setPassports(listed.items);
      const address = await loadVaultAddress();
      if (address && !walletAddress) {
        setWalletAddress(address);
      }
    } catch (e) {
      setError(safeErrorMessage(e, t("passport.loadFailed")));
    } finally {
      setLoading(false);
    }
  }, [t, walletAddress]);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      void refresh();
    }, [refresh])
  );

  const onIssue = async () => {
    if (!orgId) {
      setError(t("passport.orgMissing"));
      return;
    }
    if (!walletAddress.startsWith("0x") || walletAddress.length !== 42) {
      setError(t("passport.invalidWallet"));
      return;
    }
    setBusy(true);
    setError("");
    try {
      await syncNfcCredentialToBackend();
      const api = getApi();
      await api.issueOrgPassport(orgId, { wallet_address: walletAddress });
      await refresh();
    } catch (e) {
      setError(safeErrorMessage(e, t("passport.issueFailed")));
    } finally {
      setBusy(false);
    }
  };

  const onOpenExplorer = (url?: string | null) => {
    if (!url) return;
    void Linking.openURL(url);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#6ee7b7" />
      </View>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={busy} onRefresh={() => void refresh()} tintColor="#6ee7b7" />}
    >
      <Text style={styles.title}>{t("passport.title")}</Text>
      <Text style={styles.subtitle}>{t("passport.subtitle")}</Text>

      {!hasApiAuthHeader() ? (
        <View style={styles.card}>
          <Text style={styles.meta}>{t("passport.authRequired")}</Text>
        </View>
      ) : null}

      {orgId ? (
        <View style={styles.card}>
          <Text style={styles.label}>{t("passport.walletAddress")}</Text>
          <TextInput
            style={styles.input}
            value={walletAddress}
            onChangeText={setWalletAddress}
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="0x..."
            placeholderTextColor="#64748b"
          />
          <Pressable style={[styles.button, busy ? styles.buttonDisabled : null]} disabled={busy} onPress={() => void onIssue()}>
            <Text style={styles.buttonText}>{busy ? t("passport.issuing") : t("passport.requestIssue")}</Text>
          </Pressable>
          <Text style={styles.hint}>{t("passport.issueHint")}</Text>
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.meta}>{t("passport.orgMissing")}</Text>
        </View>
      )}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.section}>{t("passport.yourPassports")}</Text>
      {passports.length === 0 ? (
        <Text style={styles.meta}>{t("passport.none")}</Text>
      ) : (
        passports.map((p) => (
          <View key={p.id} style={styles.card}>
            <Text style={styles.cardTitle}>
              {t("passport.tokenLabel", { id: p.token_id })} · {p.status}
            </Text>
            <Text style={styles.meta}>{p.wallet_address}</Text>
            <Text style={styles.meta}>{p.claim_hash}</Text>
            {p.explorer_url ? (
              <Pressable onPress={() => onOpenExplorer(p.explorer_url)}>
                <Text style={styles.link}>{t("passport.viewOnChain")}</Text>
              </Pressable>
            ) : null}
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#0a0f1a" },
  container: { padding: 16, gap: 12, backgroundColor: "#0a0f1a", flexGrow: 1 },
  title: { color: "#f5f7ff", fontSize: 22, fontWeight: "700" },
  subtitle: { color: "#94a3b8", fontSize: 14, lineHeight: 20 },
  section: { color: "#cbd5e1", fontSize: 16, fontWeight: "600", marginTop: 8 },
  card: { backgroundColor: "#111827", borderRadius: 12, padding: 14, gap: 8 },
  cardTitle: { color: "#f5f7ff", fontSize: 16, fontWeight: "600" },
  label: { color: "#cbd5e1", fontSize: 14 },
  meta: { color: "#94a3b8", fontSize: 13, lineHeight: 18 },
  hint: { color: "#64748b", fontSize: 12, lineHeight: 17 },
  input: {
    backgroundColor: "#0f172a",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: "#f5f7ff",
    fontSize: 14,
  },
  button: { backgroundColor: "#059669", borderRadius: 8, paddingVertical: 12, alignItems: "center" },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#ecfdf5", fontWeight: "600" },
  link: { color: "#6ee7b7", fontSize: 13, marginTop: 4 },
  error: { color: "#fca5a5", fontSize: 13 },
});
