"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { auth, users } from "@/lib/api";
import { safeGetItem, safeRemoveItem, safeSetItem } from "@/lib/safeStorage";

interface User {
  id: string;
  email: string;
  display_name: string;
  wallet_address?: string | null;
  wallet_chain_id?: number | null;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isWalletOnlyAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, turnstileToken?: string) => Promise<string | null>;
  register: (email: string, password: string, displayName: string, referralCode?: string, turnstileToken?: string) => Promise<string | null>;
  loginWithWallet: (walletAddress: string, chainId?: number | null, turnstileToken?: string) => Promise<void>;
  linkWallet: (walletAddress: string, chainId?: number | null, turnstileToken?: string) => Promise<void>;
  requestPasswordReset: (email: string, turnstileToken?: string) => Promise<void>;
  resetPassword: (token: string, password: string, turnstileToken?: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  recoverPasswordWithWallet: (walletAddress: string, newPassword: string, chainId?: number | null, turnstileToken?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const WALLET_ONLY_USER_KEY = "ancap_wallet_only_user";

function userFromApiPayload(u: { id?: string; email?: string; display_name?: string | null; wallet_address?: string | null; wallet_chain_id?: number | null }): User {
  const email = typeof u.email === "string" ? u.email : "";
  const display =
    (u.display_name && String(u.display_name)) ||
    (email.includes("@") ? email.split("@")[0] : "") ||
    "User";
  return {
    id: String(u.id ?? ""),
    email,
    display_name: display,
    wallet_address: typeof u.wallet_address === "string" ? u.wallet_address : null,
    wallet_chain_id: typeof u.wallet_chain_id === "number" ? u.wallet_chain_id : null,
  };
}

async function signWalletChallenge(walletAddress: string, chainId?: number | null, turnstileToken?: string) {
  const compact = walletAddress.trim().toLowerCase();
  if (!compact) {
    throw new Error("Wallet address is required");
  }
  const { resolveEvmProvider } = await import("@/lib/metamaskConnect");
  const provider = await resolveEvmProvider(["0x1237"]);
  if (!provider) {
    throw new Error("No MetaMask provider found. Install MetaMask and reconnect from Chrome.");
  }

  const accountsRaw = await provider.request({ method: "eth_accounts" });
  const accounts = Array.isArray(accountsRaw) ? accountsRaw : [];
  const providerAddress = typeof accounts[0] === "string" ? accounts[0].trim().toLowerCase() : "";

  if (!providerAddress) {
    throw new Error("No connected wallet account found. Reconnect MetaMask and try again.");
  }

  if (providerAddress !== compact) {
    throw new Error(
      `Connected wallet account changed. ANCAP expected ${compact}, but MetaMask is exposing ${providerAddress}. Reconnect the wallet and try again.`
    );
  }

  const chainIdRaw = await provider.request({ method: "eth_chainId" });
  const activeChainId =
    typeof chainIdRaw === "string"
      ? Number.parseInt(chainIdRaw, chainIdRaw.startsWith("0x") || chainIdRaw.startsWith("0X") ? 16 : 10)
      : typeof chainIdRaw === "number"
        ? chainIdRaw
        : undefined;

  const domain = window.location.host;
  const uri = `${window.location.origin}/login`;
  const nonceRes = await auth.walletNonce(providerAddress, activeChainId ?? chainId ?? undefined, domain, uri, turnstileToken);
  const signatureRaw = await provider.request({
    method: "personal_sign",
    params: [nonceRes.message, providerAddress],
  });
  const signature = typeof signatureRaw === "string" ? signatureRaw : "";
  if (!signature) {
    throw new Error("Wallet signature was not returned");
  }

  return {
    challengeId: nonceRes.challenge_id as string,
    providerAddress,
    signature,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isWalletOnlyAuthenticated, setIsWalletOnlyAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = safeGetItem("ancap_user");
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser) as Partial<User>;
        if (parsed && typeof parsed === "object" && "email" in parsed) {
          setUser(userFromApiPayload(parsed));
        } else {
          safeRemoveItem("ancap_user");
        }
      } catch {
        safeRemoveItem("ancap_user");
      }
    }

    let cancelled = false;

    users
      .me()
      .then((u) => {
        if (cancelled) return;
        const userData = userFromApiPayload(u);
        setUser(userData);
        setIsWalletOnlyAuthenticated(false);
        safeSetItem("ancap_user", JSON.stringify(userData));
        safeRemoveItem(WALLET_ONLY_USER_KEY);
      })
      .catch(() => {
        if (cancelled) return;
        // Never keep a ghost UI session when the HttpOnly cookie/JWT is gone —
        // otherwise /wallet/acp shows "-" for address/balance while nav looks logged-in.
        safeRemoveItem("ancap_user");
        safeRemoveItem(WALLET_ONLY_USER_KEY);
        setIsWalletOnlyAuthenticated(false);
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const refreshUser = async () => {
    const me = await users.me();
    const userData = userFromApiPayload(me);
    setUser(userData);
    setIsWalletOnlyAuthenticated(false);
    safeSetItem("ancap_user", JSON.stringify(userData));
    safeRemoveItem(WALLET_ONLY_USER_KEY);
  };

  const login = async (email: string, password: string, turnstileToken?: string) => {
    const loginRes = await auth.login(email, password, turnstileToken);
    await refreshUser();
    const walletBackupMnemonic =
      loginRes && typeof loginRes === "object" && "wallet_backup_mnemonic" in loginRes
        ? String((loginRes as any).wallet_backup_mnemonic || "")
        : "";
    return walletBackupMnemonic || null;
  };

  const register = async (email: string, password: string, displayName: string, referralCode?: string, turnstileToken?: string) => {
    const created = await auth.register(email, password, displayName, referralCode, turnstileToken);
    const walletBackupMnemonic =
      created && typeof created === "object" && "wallet_backup_mnemonic" in created
        ? String((created as any).wallet_backup_mnemonic || "")
        : "";
    await refreshUser();
    return walletBackupMnemonic || null;
  };

  const loginWithWallet = async (walletAddress: string, chainId?: number | null, turnstileToken?: string) => {
    const signed = await signWalletChallenge(walletAddress, chainId, turnstileToken);
    await auth.walletVerify(signed.challengeId, signed.providerAddress, signed.signature);
    await refreshUser();
  };

  const linkWallet = async (walletAddress: string, chainId?: number | null, turnstileToken?: string) => {
    const signed = await signWalletChallenge(walletAddress, chainId, turnstileToken);
    await auth.walletLink(signed.challengeId, signed.providerAddress, signed.signature);
    await refreshUser();
  };

  const requestPasswordReset = async (email: string, turnstileToken?: string) => {
    await auth.forgotPassword(email, turnstileToken);
  };

  const resetPassword = async (token: string, password: string, turnstileToken?: string) => {
    await auth.resetPassword(token, password, turnstileToken);
  };

  const changePassword = async (currentPassword: string, newPassword: string) => {
    await auth.changePassword(currentPassword, newPassword);
  };

  const recoverPasswordWithWallet = async (walletAddress: string, newPassword: string, chainId?: number | null, turnstileToken?: string) => {
    const signed = await signWalletChallenge(walletAddress, chainId, turnstileToken);
    await auth.recoverPasswordWithWallet(signed.challengeId, signed.providerAddress, signed.signature, newPassword);
  };

  const logout = () => {
    auth.logout();
    setUser(null);
    setIsWalletOnlyAuthenticated(false);
    safeRemoveItem("ancap_user");
    safeRemoveItem(WALLET_ONLY_USER_KEY);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isWalletOnlyAuthenticated,
        isLoading,
        login,
        register,
        loginWithWallet,
        linkWallet,
        requestPasswordReset,
        resetPassword,
        changePassword,
        recoverPasswordWithWallet,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
