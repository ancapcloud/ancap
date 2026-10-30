"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { safeGetItem, safeRemoveItem, safeSetItem } from "@/lib/safeStorage";
import { getPreferredEvmProvider, subscribeEvmProviderDiscovery, type Eip1193Provider } from "@/lib/evmProvider";
import { RACP_CHAIN_ID, RACP_CHAIN_HEX } from "@/lib/racpToken";

type EthereumRequestArgs = {
  method: string;
  params?: unknown[] | Record<string, unknown>;
};

type EthereumProvider = Eip1193Provider & {
  request: (args: EthereumRequestArgs) => Promise<unknown>;
};

type WalletSession = {
  address: string;
  chainId: number | null;
  provider: "metamask" | "injected";
};

type WalletContextType = {
  address: string | null;
  shortAddress: string | null;
  chainId: number | null;
  chainName: string;
  isConnected: boolean;
  isConnecting: boolean;
  providerAvailable: boolean;
  isMetaMask: boolean;
  error: string;
  connect: () => Promise<void>;
  disconnect: () => void;
  switchToRacp: () => Promise<void>;
  refresh: () => Promise<void>;
  clearError: () => void;
};

const WalletContext = createContext<WalletContextType | undefined>(undefined);
const STORAGE_KEY = "ancap_evm_wallet_session_v1";
const BNB_CHAIN_ID = 56;

function getProvider(): EthereumProvider | undefined {
  return getPreferredEvmProvider() as EthereumProvider | undefined;
}

function normalizeChainId(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith("0x") || trimmed.startsWith("0X")) {
      const parsed = Number.parseInt(trimmed, 16);
      return Number.isFinite(parsed) ? parsed : null;
    }
    const parsed = Number.parseInt(trimmed, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function shortAddress(address: string | null): string | null {
  if (!address) return null;
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

function chainName(chainId: number | null): string {
  switch (chainId) {
    case 1:
      return "Ethereum";
    case BNB_CHAIN_ID:
      return "BNB Chain";
    case RACP_CHAIN_ID:
      return "Robinhood Chain";
    case 8453:
      return "Base";
    case 42161:
      return "Arbitrum";
    case 10:
      return "Optimism";
    case 137:
      return "Polygon";
    default:
      return chainId ? `Chain ${chainId}` : "Not connected";
  }
}

function readStoredSession(): WalletSession | null {
  const raw = safeGetItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<WalletSession>;
    if (!parsed || typeof parsed.address !== "string") return null;
    return {
      address: parsed.address,
      chainId: normalizeChainId(parsed.chainId),
      provider: parsed.provider === "metamask" ? "metamask" : "injected",
    };
  } catch {
    return null;
  }
}

function persistSession(address: string, chainId: number | null, isMetaMask: boolean) {
  const session: WalletSession = {
    address,
    chainId,
    provider: isMetaMask ? "metamask" : "injected",
  };
  safeSetItem(STORAGE_KEY, JSON.stringify(session));
}

function clearSession() {
  safeRemoveItem(STORAGE_KEY);
}

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [currentChainId, setCurrentChainId] = useState<number | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState("");
  const [providerAvailable, setProviderAvailable] = useState(false);
  const [isMetaMask, setIsMetaMask] = useState(false);

  const clearError = useCallback(() => setError(""), []);

  const applyWalletState = useCallback((nextAddress: string | null, nextChainId: number | null, metaMaskFlag: boolean) => {
    setAddress(nextAddress);
    setCurrentChainId(nextChainId);
    setIsMetaMask(metaMaskFlag);
    if (nextAddress) {
      persistSession(nextAddress, nextChainId, metaMaskFlag);
    } else {
      clearSession();
    }
  }, []);

  const syncFromProvider = useCallback(async () => {
    const provider = getProvider();
    setProviderAvailable(!!provider);
    setIsMetaMask(!!provider?.isMetaMask);

    if (!provider) {
      applyWalletState(null, null, false);
      return;
    }

    try {
      const [accountsRaw, chainIdRaw] = await Promise.all([
        provider.request({ method: "eth_accounts" }),
        provider.request({ method: "eth_chainId" }),
      ]);
      const accounts = Array.isArray(accountsRaw) ? accountsRaw : [];
      const nextAddress = typeof accounts[0] === "string" ? accounts[0] : null;
      const nextChainId = normalizeChainId(chainIdRaw);
      applyWalletState(nextAddress, nextChainId, !!provider.isMetaMask);
    } catch {
      applyWalletState(null, null, !!provider.isMetaMask);
    }
  }, [applyWalletState]);

  useEffect(() => {
    const provider = getProvider();
    setProviderAvailable(!!provider);
    setIsMetaMask(!!provider?.isMetaMask);
    void syncFromProvider();

    const unsubscribeDiscovery = subscribeEvmProviderDiscovery(() => {
      void syncFromProvider();
    });

    const handleWindowFocus = () => {
      void syncFromProvider();
    };

    const handleVisibilityChange = () => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        void syncFromProvider();
      }
    };

    if (typeof window !== "undefined") {
      window.addEventListener("focus", handleWindowFocus);
      document.addEventListener("visibilitychange", handleVisibilityChange);
    }

    if (!provider?.on) {
      return () => {
        if (typeof window !== "undefined") {
          window.removeEventListener("focus", handleWindowFocus);
          document.removeEventListener("visibilitychange", handleVisibilityChange);
        }
        unsubscribeDiscovery();
      };
    }

    const handleAccountsChanged = (...args: unknown[]) => {
      const accountsMaybe = args[0];
      const accounts = Array.isArray(accountsMaybe) ? accountsMaybe : [];
      const nextAddress = typeof accounts[0] === "string" ? accounts[0] : null;
      applyWalletState(nextAddress, readStoredSession()?.chainId ?? null, !!provider.isMetaMask);
      void syncFromProvider();
    };

    const handleChainChanged = (...args: unknown[]) => {
      const nextChainId = normalizeChainId(args[0]);
      setCurrentChainId(nextChainId);
      const activeAddress = typeof window !== "undefined" ? readStoredSession()?.address : null;
      if (activeAddress) {
        persistSession(activeAddress, nextChainId, !!provider.isMetaMask);
      }
      void syncFromProvider();
    };

    provider.on("accountsChanged", handleAccountsChanged);
    provider.on("chainChanged", handleChainChanged);

    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("focus", handleWindowFocus);
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      }
      provider.removeListener?.("accountsChanged", handleAccountsChanged);
      provider.removeListener?.("chainChanged", handleChainChanged);
      unsubscribeDiscovery();
    };
  }, [applyWalletState, syncFromProvider]);

  const connect = useCallback(async () => {
    setError("");
    setIsConnecting(true);
    try {
      let provider = getProvider();
      if (!provider) {
        // Chrome/iOS and other mobile browsers: MetaMask Connect deeplinks to the app, then returns a provider.
        const { resolveEvmProvider } = await import("@/lib/metamaskConnect");
        provider = (await resolveEvmProvider([RACP_CHAIN_HEX])) as EthereumProvider;
      }
      await provider.request({ method: "eth_requestAccounts" });
      await syncFromProvider();
      const accountsRaw = await provider.request({ method: "eth_accounts" });
      const accounts = Array.isArray(accountsRaw) ? accountsRaw : [];
      const activeAddress = typeof accounts[0] === "string" ? accounts[0] : "";
      if (!activeAddress) {
        throw new Error("MetaMask connected but no account was returned.");
      }
      applyWalletState(activeAddress, readStoredSession()?.chainId ?? null, true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to connect wallet.";
      setError(message);
    } finally {
      setIsConnecting(false);
    }
  }, [applyWalletState, syncFromProvider]);

  const disconnect = useCallback(() => {
    clearError();
    applyWalletState(null, null, false);
  }, [applyWalletState, clearError]);

  const switchToRacp = useCallback(async () => {
    const provider = getProvider();
    if (!provider) {
      setError("MetaMask is not available in this browser. Disable Rainbow for ancap.cloud or use MetaMask directly.");
      return;
    }

    setError("");
    try {
      const { ensureRobinhoodChain } = await import("@/lib/racpToken");
      await ensureRobinhoodChain(provider);
      await syncFromProvider();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to switch wallet to Robinhood Chain.";
      setError(message);
    }
  }, [syncFromProvider]);

  const value = useMemo<WalletContextType>(() => ({
    address,
    shortAddress: shortAddress(address),
    chainId: currentChainId,
    chainName: chainName(currentChainId),
    isConnected: !!address,
    isConnecting,
    providerAvailable,
    isMetaMask,
    error,
    connect,
    disconnect,
    switchToRacp,
    refresh: syncFromProvider,
    clearError,
  }), [address, clearError, connect, currentChainId, disconnect, error, isConnecting, isMetaMask, providerAvailable, switchToRacp, syncFromProvider]);

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error("useWallet must be used within WalletProvider");
  }
  return context;
}

export const walletConstants = {
  racpChainId: RACP_CHAIN_ID,
};
