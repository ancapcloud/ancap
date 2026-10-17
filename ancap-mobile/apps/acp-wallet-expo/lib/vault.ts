import * as SecureStore from "expo-secure-store";
import { deleteKeystoreExportFile } from "./keystore-export";
import {
  clearPinLock,
  isBiometricUnlockEnabled,
  lockSession,
  markSessionUnlocked,
} from "./lock";
import { chunkSecret, joinSecretChunks } from "./vault-chunk";

/** Single pointer to the active vault generation. Flip only after a verified write. */
const KEY_ACTIVE_GEN = "acp_wallet_active_gen";

/**
 * Generations written but not yet active (or left behind after a failed cleanup).
 * wipeVault and commit retry delete these so mid-write orphans do not linger.
 */
const KEY_PENDING_GENS = "acp_wallet_pending_gens";

/**
 * Leftover keys from an older SecureStore "stash" backup feature (removed).
 * Cleared on wipe so upgrades do not keep a hidden keystore copy.
 */
const LEGACY_STASH = {
  parts: "acp_wallet_backup_ks_parts",
  part: (i: number) => `acp_wallet_backup_ks_p${i}`,
  address: "acp_wallet_backup_address",
} as const;

/** Legacy flat keys (pre-generation). Read for migration; wiped after successful gen save / wipe. */
const LEGACY = {
  address: "acp_wallet_address",
  keystore: "acp_wallet_keystore",
  keystoreParts: "acp_wallet_keystore_parts",
  keystorePartPrefix: "acp_wallet_keystore_p",
  mnemonic: "acp_wallet_mnemonic",
  keystoreAuth: "acp_wallet_keystore_auth",
  keystoreAuthParts: "acp_wallet_keystore_auth_parts",
  keystoreAuthPartPrefix: "acp_wallet_keystore_auth_p",
  mnemonicAuth: "acp_wallet_mnemonic_auth",
  vaultMode: "acp_wallet_vault_mode",
} as const;

const VAULT_AUTH_PROMPT = "Unlock ACP Wallet secrets";

const DEVICE_ONLY_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

const BIOMETRIC_SECRET_OPTIONS: SecureStore.SecureStoreOptions = {
  ...DEVICE_ONLY_OPTIONS,
  requireAuthentication: true,
  authenticationPrompt: VAULT_AUTH_PROMPT,
};

export type VaultPayload = {
  address: string;
  keystoreJson: string;
  /** Optional notes; full restore uses keystore only. */
  mnemonic?: string;
  protectedByBiometrics?: boolean;
};

type VaultMode = "plain" | "biometric";

type GenKeys = {
  address: string;
  mode: string;
  keystoreParts: string;
  keystorePart: (i: number) => string;
  mnemonic: string;
  keystoreAuthParts: string;
  keystoreAuthPart: (i: number) => string;
  mnemonicAuth: string;
};

function genKeys(gen: string): GenKeys {
  const prefix = `acp_wallet_${gen}`;
  return {
    address: `${prefix}_address`,
    mode: `${prefix}_mode`,
    keystoreParts: `${prefix}_ks_parts`,
    keystorePart: (i) => `${prefix}_ks_p${i}`,
    mnemonic: `${prefix}_mnemonic`,
    keystoreAuthParts: `${prefix}_ks_auth_parts`,
    keystoreAuthPart: (i) => `${prefix}_ks_auth_p${i}`,
    mnemonicAuth: `${prefix}_mnemonic_auth`,
  };
}

function normalizeMnemonic(mnemonic: string | undefined): string {
  return (mnemonic ?? "").trim();
}

function nextGenerationId(): string {
  return `g${Date.now().toString(36)}_${Math.floor(Math.random() * 1e6).toString(36)}`;
}

async function getActiveGen(): Promise<string | null> {
  const gen = await SecureStore.getItemAsync(KEY_ACTIVE_GEN, DEVICE_ONLY_OPTIONS);
  return gen && gen.trim() ? gen.trim() : null;
}

async function setActiveGen(gen: string): Promise<void> {
  await SecureStore.setItemAsync(KEY_ACTIVE_GEN, gen, DEVICE_ONLY_OPTIONS);
}

async function readPendingGens(): Promise<string[]> {
  const raw = await SecureStore.getItemAsync(KEY_PENDING_GENS, DEVICE_ONLY_OPTIONS);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  } catch {
    return [];
  }
}

async function writePendingGens(gens: string[]): Promise<void> {
  const unique = [...new Set(gens.map((g) => g.trim()).filter(Boolean))];
  if (unique.length === 0) {
    await SecureStore.deleteItemAsync(KEY_PENDING_GENS);
    return;
  }
  await SecureStore.setItemAsync(KEY_PENDING_GENS, JSON.stringify(unique), DEVICE_ONLY_OPTIONS);
}

async function trackPendingGen(gen: string): Promise<void> {
  const list = await readPendingGens();
  if (!list.includes(gen)) {
    list.push(gen);
    await writePendingGens(list);
  }
}

async function untrackPendingGen(gen: string): Promise<void> {
  const list = await readPendingGens();
  await writePendingGens(list.filter((item) => item !== gen));
}

async function writeChunked(
  partsKey: string,
  partKey: (i: number) => string,
  value: string,
  options: SecureStore.SecureStoreOptions
): Promise<number> {
  const parts = chunkSecret(value);
  if (parts.length === 0) {
    throw new Error("Cannot store empty keystore in vault.");
  }
  // Write payload chunks first; commit count last so a mid-write crash has no valid parts meta.
  for (let i = 0; i < parts.length; i += 1) {
    await SecureStore.setItemAsync(partKey(i), parts[i], options);
  }
  await SecureStore.setItemAsync(partsKey, String(parts.length), options);
  return parts.length;
}

async function readChunked(
  partsKey: string,
  partKey: (i: number) => string,
  options: SecureStore.SecureStoreOptions
): Promise<string> {
  const partsRaw = await SecureStore.getItemAsync(partsKey, options);
  if (!partsRaw) {
    throw new Error("Vault keystore metadata is missing.");
  }
  const count = Number.parseInt(partsRaw, 10);
  if (!Number.isFinite(count) || count <= 0) {
    throw new Error("Vault keystore metadata is invalid.");
  }
  const parts: string[] = [];
  for (let i = 0; i < count; i += 1) {
    const part = await SecureStore.getItemAsync(partKey(i), options);
    if (part == null) {
      throw new Error(`Vault keystore chunk ${i} of ${count} is missing.`);
    }
    parts.push(part);
  }
  return joinSecretChunks(parts);
}

async function deleteChunked(
  partsKey: string,
  partKey: (i: number) => string,
  options: SecureStore.SecureStoreOptions,
  knownCount?: number
): Promise<void> {
  let count = knownCount;
  if (count == null) {
    const partsRaw = await SecureStore.getItemAsync(partsKey, options);
    count = partsRaw ? Number.parseInt(partsRaw, 10) : 0;
  }
  const toDelete = Number.isFinite(count) && (count as number) > 0 ? (count as number) : 32;
  const deletions: Promise<void>[] = [SecureStore.deleteItemAsync(partsKey)];
  for (let i = 0; i < toDelete; i += 1) {
    deletions.push(SecureStore.deleteItemAsync(partKey(i)));
  }
  await Promise.all(deletions);
}

async function deleteGeneration(gen: string): Promise<void> {
  const keys = genKeys(gen);
  await Promise.all([
    SecureStore.deleteItemAsync(keys.address),
    SecureStore.deleteItemAsync(keys.mode),
    SecureStore.deleteItemAsync(keys.mnemonic),
    SecureStore.deleteItemAsync(keys.mnemonicAuth),
    deleteChunked(keys.keystoreParts, keys.keystorePart, DEVICE_ONLY_OPTIONS),
    deleteChunked(keys.keystoreAuthParts, keys.keystoreAuthPart, BIOMETRIC_SECRET_OPTIONS),
  ]);
}

/** Best-effort delete of residual SecureStore stash keys from older app builds. */
async function clearLeftoverStashKeys(): Promise<void> {
  await SecureStore.deleteItemAsync(LEGACY_STASH.address);
  await deleteChunked(LEGACY_STASH.parts, LEGACY_STASH.part, DEVICE_ONLY_OPTIONS);
}

/**
 * Delete tracked incomplete generations (except the active pointer).
 * Failed deletions stay on the pending list for a later retry / wipeVault.
 */
export async function cleanupIncompleteGenerations(): Promise<void> {
  const active = await getActiveGen();
  const pending = await readPendingGens();
  const remaining: string[] = [];
  for (const gen of pending) {
    if (active && gen === active) {
      continue;
    }
    try {
      await deleteGeneration(gen);
    } catch {
      remaining.push(gen);
    }
  }
  await writePendingGens(remaining);
}

async function writeGeneration(
  gen: string,
  payload: { address: string; keystoreJson: string; mnemonic: string },
  mode: VaultMode
): Promise<void> {
  const keys = genKeys(gen);
  const secretOpts = mode === "biometric" ? BIOMETRIC_SECRET_OPTIONS : DEVICE_ONLY_OPTIONS;
  const partsKey = mode === "biometric" ? keys.keystoreAuthParts : keys.keystoreParts;
  const partKey = mode === "biometric" ? keys.keystoreAuthPart : keys.keystorePart;
  const mnemonicKey = mode === "biometric" ? keys.mnemonicAuth : keys.mnemonic;

  await writeChunked(partsKey, partKey, payload.keystoreJson, secretOpts);
  if (payload.mnemonic) {
    await SecureStore.setItemAsync(mnemonicKey, payload.mnemonic, secretOpts);
  } else {
    await SecureStore.deleteItemAsync(mnemonicKey);
  }
  await SecureStore.setItemAsync(keys.address, payload.address, DEVICE_ONLY_OPTIONS);
  await SecureStore.setItemAsync(keys.mode, mode, DEVICE_ONLY_OPTIONS);
}

async function readGeneration(gen: string): Promise<VaultPayload> {
  const keys = genKeys(gen);
  const [address, modeRaw] = await Promise.all([
    SecureStore.getItemAsync(keys.address, DEVICE_ONLY_OPTIONS),
    SecureStore.getItemAsync(keys.mode, DEVICE_ONLY_OPTIONS),
  ]);
  if (!address) {
    throw new Error("Vault generation address is missing.");
  }
  const mode: VaultMode = modeRaw === "biometric" ? "biometric" : "plain";
  const secretOpts = mode === "biometric" ? BIOMETRIC_SECRET_OPTIONS : DEVICE_ONLY_OPTIONS;
  const partsKey = mode === "biometric" ? keys.keystoreAuthParts : keys.keystoreParts;
  const partKey = mode === "biometric" ? keys.keystoreAuthPart : keys.keystorePart;
  const mnemonicKey = mode === "biometric" ? keys.mnemonicAuth : keys.mnemonic;

  const keystoreJson = await readChunked(partsKey, partKey, secretOpts);
  const mnemonic = (await SecureStore.getItemAsync(mnemonicKey, secretOpts)) ?? undefined;
  return {
    address,
    keystoreJson,
    mnemonic: mnemonic || undefined,
    protectedByBiometrics: mode === "biometric",
  };
}

async function readLegacyVault(): Promise<VaultPayload | null> {
  const address = await SecureStore.getItemAsync(LEGACY.address, DEVICE_ONLY_OPTIONS);
  if (!address) {
    return null;
  }
  const modeRaw = await SecureStore.getItemAsync(LEGACY.vaultMode, DEVICE_ONLY_OPTIONS);
  const mode: VaultMode = modeRaw === "biometric" ? "biometric" : "plain";
  const secretOpts = mode === "biometric" ? BIOMETRIC_SECRET_OPTIONS : DEVICE_ONLY_OPTIONS;

  let keystoreJson: string | null = null;
  try {
    if (mode === "biometric") {
      const parts = await SecureStore.getItemAsync(LEGACY.keystoreAuthParts, secretOpts);
      if (parts) {
        keystoreJson = await readChunked(
          LEGACY.keystoreAuthParts,
          (i) => `${LEGACY.keystoreAuthPartPrefix}${i}`,
          secretOpts
        );
      } else {
        keystoreJson = await SecureStore.getItemAsync(LEGACY.keystoreAuth, secretOpts);
      }
    } else {
      const parts = await SecureStore.getItemAsync(LEGACY.keystoreParts, secretOpts);
      if (parts) {
        keystoreJson = await readChunked(
          LEGACY.keystoreParts,
          (i) => `${LEGACY.keystorePartPrefix}${i}`,
          secretOpts
        );
      } else {
        keystoreJson = await SecureStore.getItemAsync(LEGACY.keystore, secretOpts);
      }
    }
  } catch {
    return null;
  }
  if (!keystoreJson) {
    return null;
  }
  const mnemonicKey = mode === "biometric" ? LEGACY.mnemonicAuth : LEGACY.mnemonic;
  const mnemonic = (await SecureStore.getItemAsync(mnemonicKey, secretOpts)) ?? undefined;
  return {
    address,
    keystoreJson,
    mnemonic: mnemonic || undefined,
    protectedByBiometrics: mode === "biometric",
  };
}

async function deleteLegacyVault(): Promise<void> {
  await Promise.all([
    SecureStore.deleteItemAsync(LEGACY.address),
    SecureStore.deleteItemAsync(LEGACY.vaultMode),
    SecureStore.deleteItemAsync(LEGACY.mnemonic),
    SecureStore.deleteItemAsync(LEGACY.mnemonicAuth),
    SecureStore.deleteItemAsync(LEGACY.keystore),
    SecureStore.deleteItemAsync(LEGACY.keystoreAuth),
    deleteChunked(LEGACY.keystoreParts, (i) => `${LEGACY.keystorePartPrefix}${i}`, DEVICE_ONLY_OPTIONS),
    deleteChunked(
      LEGACY.keystoreAuthParts,
      (i) => `${LEGACY.keystoreAuthPartPrefix}${i}`,
      BIOMETRIC_SECRET_OPTIONS
    ),
  ]);
}

/**
 * Persist a full vault generation, verify by reading it back, then flip the active pointer.
 * Previous generation (and legacy flat keys) are removed only after the pointer switch succeeds.
 * Incomplete writes are tracked for wipeVault / cleanupIncompleteGenerations.
 */
async function commitVault(
  payload: { address: string; keystoreJson: string; mnemonic: string },
  mode: VaultMode
): Promise<VaultPayload> {
  await cleanupIncompleteGenerations();

  const previous = await getActiveGen();
  const gen = nextGenerationId();
  await trackPendingGen(gen);

  try {
    await writeGeneration(gen, payload, mode);
    const verified = await readGeneration(gen);
    if (verified.address !== payload.address || verified.keystoreJson !== payload.keystoreJson) {
      throw new Error("Vault write verification failed.");
    }
    if (normalizeMnemonic(verified.mnemonic) !== payload.mnemonic) {
      throw new Error("Vault mnemonic verification failed.");
    }
    if (Boolean(verified.protectedByBiometrics) !== (mode === "biometric")) {
      throw new Error("Vault mode verification failed.");
    }

    await setActiveGen(gen);
    await untrackPendingGen(gen);

    if (previous && previous !== gen) {
      try {
        await deleteGeneration(previous);
      } catch {
        await trackPendingGen(previous);
      }
    }

    await cleanupIncompleteGenerations();
    try {
      await deleteLegacyVault();
    } catch {
      // Best-effort.
    }
    return verified;
  } catch (error) {
    try {
      await deleteGeneration(gen);
      await untrackPendingGen(gen);
    } catch {
      // Leave gen on the pending list for wipeVault / later cleanup.
    }
    throw error;
  }
}

export async function hasVault(): Promise<boolean> {
  const gen = await getActiveGen();
  if (gen) {
    try {
      const vault = await readGeneration(gen);
      return Boolean(vault.address && vault.keystoreJson);
    } catch {
      return false;
    }
  }
  const legacy = await readLegacyVault();
  return Boolean(legacy?.address && legacy.keystoreJson);
}

export async function loadVaultAddress(): Promise<string | null> {
  const gen = await getActiveGen();
  if (gen) {
    return SecureStore.getItemAsync(genKeys(gen).address, DEVICE_ONLY_OPTIONS);
  }
  return SecureStore.getItemAsync(LEGACY.address, DEVICE_ONLY_OPTIONS);
}

export async function isVaultBiometricProtected(): Promise<boolean> {
  const gen = await getActiveGen();
  if (gen) {
    const mode = await SecureStore.getItemAsync(genKeys(gen).mode, DEVICE_ONLY_OPTIONS);
    return mode === "biometric";
  }
  const mode = await SecureStore.getItemAsync(LEGACY.vaultMode, DEVICE_ONLY_OPTIONS);
  return mode === "biometric";
}

export async function saveVault(payload: VaultPayload): Promise<void> {
  if (!payload.address?.trim() || !payload.keystoreJson?.trim()) {
    throw new Error("Vault requires address and keystore JSON.");
  }
  const protectSecrets = payload.protectedByBiometrics ?? (await isBiometricUnlockEnabled());
  await commitVault(
    {
      address: payload.address.trim(),
      keystoreJson: payload.keystoreJson.trim(),
      mnemonic: normalizeMnemonic(payload.mnemonic),
    },
    protectSecrets ? "biometric" : "plain"
  );
  markSessionUnlocked();
}

export async function enableVaultBiometricProtection(): Promise<boolean> {
  const current = await loadVault();
  if (!current) {
    return false;
  }
  if (current.protectedByBiometrics) {
    return true;
  }
  await commitVault(
    {
      address: current.address,
      keystoreJson: current.keystoreJson,
      mnemonic: normalizeMnemonic(current.mnemonic),
    },
    "biometric"
  );
  return true;
}

export async function disableVaultBiometricProtection(): Promise<boolean> {
  const current = await loadVault();
  if (!current) {
    return false;
  }
  if (!current.protectedByBiometrics) {
    return true;
  }
  await commitVault(
    {
      address: current.address,
      keystoreJson: current.keystoreJson,
      mnemonic: normalizeMnemonic(current.mnemonic),
    },
    "plain"
  );
  return true;
}

export async function loadVault(): Promise<VaultPayload | null> {
  const gen = await getActiveGen();
  if (gen) {
    try {
      return await readGeneration(gen);
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      if (message.includes("chunk") || message.includes("missing") || message.includes("metadata")) {
        throw e;
      }
      throw new Error(
        "Secure vault secrets are unavailable. Device biometrics may have changed. Re-import the wallet from your backup on this device."
      );
    }
  }
  return readLegacyVault();
}

/**
 * Remove wallet secrets from this device: active generation, incomplete generations,
 * legacy flat keys, leftover stash keys from older builds, and any document-dir
 * keystore export file left by an explicit Copy action.
 */
export async function wipeVault(): Promise<void> {
  const active = await getActiveGen();
  const pending = await readPendingGens();
  await SecureStore.deleteItemAsync(KEY_ACTIVE_GEN);

  const toDelete = new Set<string>([...pending, ...(active ? [active] : [])]);
  for (const gen of toDelete) {
    try {
      await deleteGeneration(gen);
    } catch {
      // continue — still clear metadata below
    }
  }
  await writePendingGens([]);

  try {
    await deleteLegacyVault();
  } catch {
    // continue
  }
  try {
    await clearLeftoverStashKeys();
  } catch {
    // continue
  }
  try {
    await deleteKeystoreExportFile();
  } catch {
    // continue
  }

  await clearPinLock();
  lockSession();
}
