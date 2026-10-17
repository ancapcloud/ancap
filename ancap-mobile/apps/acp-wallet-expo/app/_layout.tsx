import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { setNativeWalletModule, setSecureVault } from "@ancap/acp-wallet-sdk";
import { getExpoAcpCoreModule } from "expo-acp-core";
import { expoSecureVault } from "@/lib/secure-vault-adapter";
import { loadLanguagePreference } from "@/lib/i18n";
import { hasPinLock, isSessionUnlocked, lockSession } from "@/lib/lock";
import { hasVault } from "@/lib/vault";

const AUTO_LOCK_MINUTES = 5 as const; // P5-6: auto-lock after 5 min inactivity

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments();
  const lastActive = useRef(Date.now());
  const { t } = useTranslation();

  useEffect(() => {
    void loadLanguagePreference();
    setNativeWalletModule(getExpoAcpCoreModule());
    setSecureVault(expoSecureVault);
  }, []);

  // P5-6: auto-lock — check every 30s
  useEffect(() => {
    const interval = setInterval(async () => {
      const vault = await hasVault();
      if (!vault) return;
      const elapsed = (Date.now() - lastActive.current) / 1000 / 60;
      if (elapsed >= AUTO_LOCK_MINUTES) {
        lockSession();
        router.replace("/unlock");
      }
    }, 30_000);
    return () => clearInterval(interval);
  }, [router]);

  // Reset inactivity timer on any segment change
  useEffect(() => {
    lastActive.current = Date.now();
  }, [segments]);

  useEffect(() => {
    void (async () => {
      const inTabs = segments[0] === "(tabs)";
      const onUnlock = segments[0] === "unlock";
      const onWelcome = !segments[0];
      const vault = await hasVault();
      const pinEnabled = await hasPinLock();
      const unlocked = isSessionUnlocked();
      if (!vault && (inTabs || onUnlock || segments[0] === "backup" || segments[0] === "smart-pay")) {
        router.replace("/");
        return;
      }
      if (vault && pinEnabled && !unlocked && !onUnlock) {
        router.replace("/unlock");
        return;
      }
      if (vault && pinEnabled && unlocked && onUnlock) {
        router.replace("/(tabs)");
        return;
      }
      if (vault && !inTabs && !onUnlock && segments[0] !== "onboarding" && segments[0] !== "receive") {
        if (onWelcome) {
          router.replace(pinEnabled && !unlocked ? "/unlock" : "/(tabs)");
        }
      }
    })();
  }, [segments, router]);

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#0a0f1a" },
          headerTintColor: "#f5f7ff",
          contentStyle: { backgroundColor: "#0a0f1a" },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="receive" options={{ title: t("screenTitles.receive") }} />
        <Stack.Screen name="smart-pay" options={{ title: "Smart Pay beta" }} />
        <Stack.Screen name="backup" options={{ title: t("backup.title") }} />
        <Stack.Screen name="onboarding/create" options={{ title: t("screenTitles.createWallet") }} />
        <Stack.Screen name="onboarding/import" options={{ title: t("screenTitles.importWallet") }} />
        <Stack.Screen
          name="unlock"
          options={{ title: t("screenTitles.unlockWallet"), headerBackVisible: false }}
        />
      </Stack>
    </>
  );
}
