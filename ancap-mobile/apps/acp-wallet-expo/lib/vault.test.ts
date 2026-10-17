import { beforeEach, describe, expect, it, vi } from "vitest";
import { SECURE_STORE_CHUNK_SIZE } from "./vault-chunk";

const { store, secureStore, lockApi, keystoreExport } = vi.hoisted(() => {
  const store = new Map<string, string>();
  return {
    store,
    secureStore: {
      WHEN_UNLOCKED_THIS_DEVICE_ONLY: "WHEN_UNLOCKED_THIS_DEVICE_ONLY",
      getItemAsync: vi.fn(async (key: string) => store.get(key) ?? null),
      setItemAsync: vi.fn(async (key: string, value: string) => {
        store.set(key, value);
      }),
      deleteItemAsync: vi.fn(async (key: string) => {
        store.delete(key);
      }),
    },
    lockApi: {
      clearPinLock: vi.fn(async () => undefined),
      isBiometricUnlockEnabled: vi.fn(async () => false),
      lockSession: vi.fn(),
      markSessionUnlocked: vi.fn(),
      requiresUnlock: vi.fn(async () => false),
    },
    keystoreExport: {
      deleteKeystoreExportFile: vi.fn(async () => undefined),
    },
  };
});

vi.mock("expo-secure-store", () => secureStore);
vi.mock("./lock", () => lockApi);
vi.mock("./keystore-export", () => keystoreExport);

import * as vault from "./vault";

const SMALL_KS = JSON.stringify({ version: 3, cipher: "abc" });
const LARGE_KS = JSON.stringify({ version: 3, cipher: "k".repeat(SECURE_STORE_CHUNK_SIZE * 2 + 100) });

const KEY_PENDING = "acp_wallet_pending_gens";
const KEY_STASH_PARTS = "acp_wallet_backup_ks_parts";
const KEY_STASH_ADDR = "acp_wallet_backup_address";

function activeGen(): string | null {
  return store.get("acp_wallet_active_gen") ?? null;
}

function pendingGens(): string[] {
  const raw = store.get(KEY_PENDING);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as string[];
  } catch {
    return [];
  }
}

function keysForGen(gen: string) {
  return {
    address: `acp_wallet_${gen}_address`,
    mode: `acp_wallet_${gen}_mode`,
    ksParts: `acp_wallet_${gen}_ks_parts`,
    ksPart: (i: number) => `acp_wallet_${gen}_ks_p${i}`,
    mnemonic: `acp_wallet_${gen}_mnemonic`,
  };
}

describe("generation vault", () => {
  beforeEach(() => {
    store.clear();
    secureStore.getItemAsync.mockClear();
    secureStore.setItemAsync.mockClear();
    secureStore.deleteItemAsync.mockClear();
    lockApi.clearPinLock.mockClear();
    lockApi.isBiometricUnlockEnabled.mockReset();
    lockApi.isBiometricUnlockEnabled.mockResolvedValue(false);
    lockApi.lockSession.mockClear();
    lockApi.markSessionUnlocked.mockClear();
    lockApi.requiresUnlock.mockResolvedValue(false);
    keystoreExport.deleteKeystoreExportFile.mockClear();

    secureStore.getItemAsync.mockImplementation(async (key: string) => store.get(key) ?? null);
    secureStore.setItemAsync.mockImplementation(async (key: string, value: string) => {
      store.set(key, value);
    });
    secureStore.deleteItemAsync.mockImplementation(async (key: string) => {
      store.delete(key);
    });
  });

  it("blocks secret reads and replacement of an existing locked wallet", async () => {
    await vault.saveVault({ address: "original", keystoreJson: SMALL_KS });
    lockApi.requiresUnlock.mockResolvedValue(true);
    await expect(vault.loadVault()).rejects.toThrow(/locked/);
    await expect(vault.saveVault({ address: "replacement", keystoreJson: LARGE_KS })).rejects.toThrow(/locked/);
    expect(await vault.hasVault()).toBe(true);
    lockApi.requiresUnlock.mockResolvedValue(false);
    expect((await vault.loadVault())?.address).toBe("original");
  });

  it("preserves the committed wallet when pending-list cleanup fails after the flip", async () => {
    await vault.saveVault({ address: "old", keystoreJson: SMALL_KS });
    let flipped = false;
    secureStore.setItemAsync.mockImplementation(async (key, value) => {
      if (key === "acp_wallet_active_gen") flipped = true;
      if (flipped && key === KEY_PENDING) throw new Error("metadata cleanup unavailable");
      store.set(key, value);
    });
    secureStore.deleteItemAsync.mockImplementation(async (key) => {
      if (flipped && key === KEY_PENDING) throw new Error("metadata cleanup unavailable");
      store.delete(key);
    });
    await vault.saveVault({ address: "new", keystoreJson: LARGE_KS });
    expect((await vault.loadVault())?.address).toBe("new");
    expect((await vault.loadVault())?.keystoreJson).toBe(LARGE_KS);
  });

  it("retains an active generation if the pointer promise rejects after persisting", async () => {
    await vault.saveVault({ address: "old", keystoreJson: SMALL_KS });
    secureStore.setItemAsync.mockImplementation(async (key, value) => {
      store.set(key, value);
      if (key === "acp_wallet_active_gen") throw new Error("acknowledgement lost");
    });
    await vault.saveVault({ address: "new", keystoreJson: LARGE_KS });
    expect((await vault.loadVault())?.address).toBe("new");
  });

  it("does not silently remove existing biometric protection on an ordinary save", async () => {
    await vault.saveVault({ address: "wallet", keystoreJson: SMALL_KS, protectedByBiometrics: true });
    await vault.saveVault({ address: "wallet", keystoreJson: LARGE_KS });
    expect((await vault.loadVault())?.protectedByBiometrics).toBe(true);
  });

  it("never overwrites an active allocation if a generation id repeats", async () => {
    const clock = vi.spyOn(Date, "now").mockReturnValue(123456);
    const random = vi.spyOn(Math, "random").mockReturnValue(0);
    try {
      await vault.saveVault({ address: "original", keystoreJson: SMALL_KS });
      await expect(vault.saveVault({ address: "replacement", keystoreJson: LARGE_KS })).rejects.toThrow(/collision/);
      expect((await vault.loadVault())?.address).toBe("original");
    } finally { clock.mockRestore(); random.mockRestore(); }
  });

  it("serializes concurrent saves and a later wipe without resurrecting a wallet", async () => {
    await Promise.all([
      vault.saveVault({ address: "one", keystoreJson: SMALL_KS }),
      vault.saveVault({ address: "two", keystoreJson: LARGE_KS }),
      vault.wipeVault(),
    ]);
    expect(await vault.hasVault()).toBe(false);
    expect([...store.keys()].filter((key) => /_ks_p\d+$/.test(key))).toEqual([]);
  });

  it("retains failed wipe metadata for retry and reports incomplete removal", async () => {
    await vault.saveVault({ address: "one", keystoreJson: LARGE_KS });
    const gen = activeGen()!;
    secureStore.deleteItemAsync.mockImplementation(async (key) => {
      if (key === `acp_wallet_${gen}_ks_p1`) throw new Error("delete refused");
      store.delete(key);
    });
    await expect(vault.wipeVault()).rejects.toThrow(/removal incomplete/);
    expect(pendingGens()).toContain(gen);
    expect(store.has(`acp_wallet_${gen}_ks_parts`)).toBe(true);
    expect(lockApi.lockSession).toHaveBeenCalled();
    secureStore.deleteItemAsync.mockImplementation(async (key) => { store.delete(key); });
    await vault.wipeVault();
    expect(pendingGens()).toEqual([]);
    expect(store.has(`acp_wallet_${gen}_ks_p1`)).toBe(false);
  });

  it("does not interpret corrupt chunk metadata as an empty wallet", async () => {
    await vault.saveVault({ address: "one", keystoreJson: SMALL_KS });
    store.set(`acp_wallet_${activeGen()}_ks_parts`, "1garbage");
    expect(await vault.hasVault()).toBe(true);
    await expect(vault.loadVault()).rejects.toThrow(/metadata/);
  });

  it("cleans an interrupted allocation beyond the old 32-chunk fallback", async () => {
    const gen = "ginterrupted";
    store.set(KEY_PENDING, JSON.stringify([gen]));
    store.set(`acp_wallet_${gen}_ks_parts`, "45");
    store.set(`acp_wallet_${gen}_ks_p40`, "secret");
    await vault.cleanupIncompleteGenerations();
    expect(store.has(`acp_wallet_${gen}_ks_p40`)).toBe(false);
  });

  it("imports keystore without mnemonic and still loads for signing", async () => {
    await vault.saveVault({
      address: "acp1qqimportonly000000000000000000000000000",
      keystoreJson: SMALL_KS,
    });

    const loaded = await vault.loadVault();
    expect(loaded?.address).toBe("acp1qqimportonly000000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(SMALL_KS);
    expect(loaded?.mnemonic).toBeUndefined();
    expect(await vault.hasVault()).toBe(true);
    expect(lockApi.markSessionUnlocked).toHaveBeenCalled();
  });

  it("fails mid-chunk write without flipping the active pointer", async () => {
    await vault.saveVault({
      address: "acp1qqfirstwallet00000000000000000000000000",
      keystoreJson: SMALL_KS,
      mnemonic: "one two three four five six seven eight nine ten eleven twelve",
    });
    const firstGen = activeGen();
    expect(firstGen).toBeTruthy();

    let failArmed = false;
    secureStore.setItemAsync.mockImplementation(async (key: string, value: string) => {
      if (failArmed && /_ks_p1$/.test(key)) {
        throw new Error("simulated chunk write failure");
      }
      store.set(key, value);
    });
    failArmed = true;

    await expect(
      vault.saveVault({
        address: "acp1qqsecondwallet0000000000000000000000000",
        keystoreJson: LARGE_KS,
      })
    ).rejects.toThrow(/simulated chunk write failure/);

    expect(activeGen()).toBe(firstGen);
    const loaded = await vault.loadVault();
    expect(loaded?.address).toBe("acp1qqfirstwallet00000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(SMALL_KS);
  });

  it("overwrites an existing wallet only after the new generation verifies", async () => {
    await vault.saveVault({
      address: "acp1qqoldwallet000000000000000000000000000",
      keystoreJson: SMALL_KS,
      mnemonic: "alpha beta gamma",
    });
    const oldGen = activeGen()!;
    const oldKeys = keysForGen(oldGen);

    await vault.saveVault({
      address: "acp1qqnewwallet000000000000000000000000000",
      keystoreJson: LARGE_KS,
    });
    const newGen = activeGen()!;
    expect(newGen).not.toBe(oldGen);

    const loaded = await vault.loadVault();
    expect(loaded?.address).toBe("acp1qqnewwallet000000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(LARGE_KS);
    expect(loaded?.mnemonic).toBeUndefined();

    expect(store.has(oldKeys.address)).toBe(false);
    expect(store.has(oldKeys.ksParts)).toBe(false);
  });

  it("keeps the plain generation if biometric migration write fails mid-way", async () => {
    await vault.saveVault({
      address: "acp1qqplainwallet0000000000000000000000000",
      keystoreJson: LARGE_KS,
      mnemonic: "plain seed words here for notes only",
    });
    const plainGen = activeGen()!;

    let failArmed = false;
    secureStore.setItemAsync.mockImplementation(async (key: string, value: string) => {
      if (failArmed && /_ks_auth_p1$/.test(key)) {
        throw new Error("biometric migration interrupted");
      }
      store.set(key, value);
    });
    failArmed = true;

    await expect(vault.enableVaultBiometricProtection()).rejects.toThrow(
      /biometric migration interrupted/
    );

    expect(activeGen()).toBe(plainGen);
    const loaded = await vault.loadVault();
    expect(loaded?.protectedByBiometrics).toBe(false);
    expect(loaded?.address).toBe("acp1qqplainwallet0000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(LARGE_KS);
  });

  it("surfaces a missing chunk after the pointer is active", async () => {
    await vault.saveVault({
      address: "acp1qqchunkwallet0000000000000000000000000",
      keystoreJson: LARGE_KS,
    });
    const gen = activeGen()!;
    const part1 = `acp_wallet_${gen}_ks_p1`;
    expect(store.has(part1)).toBe(true);
    store.delete(part1);

    await expect(vault.loadVault()).rejects.toThrow(/chunk 1/);
  });

  it("wipeVault clears leftover stash keys and incomplete generations", async () => {
    await vault.saveVault({
      address: "acp1qqlivewallet00000000000000000000000000",
      keystoreJson: SMALL_KS,
    });
    const liveGen = activeGen()!;

    // Simulate leftover production stash from an older build.
    store.set(KEY_STASH_ADDR, "acp1qqstashaddr000000000000000000000000000");
    store.set(KEY_STASH_PARTS, "1");
    store.set("acp_wallet_backup_ks_p0", LARGE_KS);

    // Simulate an orphan incomplete generation left after a failed write.
    const orphan = "gorphan_test1";
    store.set(`acp_wallet_${orphan}_address`, "acp1qqorphan00000000000000000000000000000");
    store.set(`acp_wallet_${orphan}_mode`, "plain");
    store.set(`acp_wallet_${orphan}_ks_parts`, "1");
    store.set(`acp_wallet_${orphan}_ks_p0`, SMALL_KS);
    store.set(KEY_PENDING, JSON.stringify([orphan]));

    // Legacy flat keys.
    store.set("acp_wallet_address", "acp1qqlegacy000000000000000000000000000000");
    store.set("acp_wallet_vault_mode", "plain");

    await vault.wipeVault();

    expect(await vault.hasVault()).toBe(false);
    expect(activeGen()).toBeNull();
    expect(pendingGens()).toEqual([]);
    expect(store.has(KEY_STASH_ADDR)).toBe(false);
    expect(store.has(KEY_STASH_PARTS)).toBe(false);
    expect(store.has("acp_wallet_backup_ks_p0")).toBe(false);
    expect(store.has(`acp_wallet_${orphan}_address`)).toBe(false);
    expect(store.has(`acp_wallet_${liveGen}_address`)).toBe(false);
    expect(store.has("acp_wallet_address")).toBe(false);
    expect(lockApi.clearPinLock).toHaveBeenCalled();
    expect(lockApi.lockSession).toHaveBeenCalled();
    expect(keystoreExport.deleteKeystoreExportFile).toHaveBeenCalled();
  });

  it("preserves the previous wallet when the active-gen flip fails", async () => {
    await vault.saveVault({
      address: "acp1qqkeepwallet00000000000000000000000000",
      keystoreJson: SMALL_KS,
      mnemonic: "keep me",
    });
    const firstGen = activeGen()!;

    let flipArmed = false;
    secureStore.setItemAsync.mockImplementation(async (key: string, value: string) => {
      if (flipArmed && key === "acp_wallet_active_gen") {
        throw new Error("simulated flip failure");
      }
      store.set(key, value);
    });
    flipArmed = true;

    await expect(
      vault.saveVault({
        address: "acp1qqshouldnotwin00000000000000000000000",
        keystoreJson: LARGE_KS,
      })
    ).rejects.toThrow(/simulated flip failure/);

    expect(activeGen()).toBe(firstGen);
    const loaded = await vault.loadVault();
    expect(loaded?.address).toBe("acp1qqkeepwallet00000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(SMALL_KS);
    expect(loaded?.mnemonic).toBe("keep me");
  });

  it("keeps a failed cleanup on the pending list so a later wipe can finish it", async () => {
    await vault.saveVault({
      address: "acp1qqbasewallet00000000000000000000000000",
      keystoreJson: SMALL_KS,
    });
    const baseGen = activeGen()!;

    // First overwrite: after flip, deleting the previous generation fails → tracked as pending.
    let blockDeleteOf = baseGen;
    secureStore.deleteItemAsync.mockImplementation(async (key: string) => {
      if (blockDeleteOf && key.includes(blockDeleteOf)) {
        throw new Error("simulated cleanup refusal");
      }
      store.delete(key);
    });

    await vault.saveVault({
      address: "acp1qqnextwallet00000000000000000000000000",
      keystoreJson: LARGE_KS,
    });
    const nextGen = activeGen()!;
    expect(nextGen).not.toBe(baseGen);
    expect(pendingGens()).toContain(baseGen);
    expect(store.has(keysForGen(baseGen).address)).toBe(true);

    // Cleanup still refused → pending remains.
    await vault.cleanupIncompleteGenerations();
    expect(pendingGens()).toContain(baseGen);

    // Subsequent wipe clears everything once deletes succeed again.
    blockDeleteOf = "";
    secureStore.deleteItemAsync.mockImplementation(async (key: string) => {
      store.delete(key);
    });
    await vault.wipeVault();
    expect(pendingGens()).toEqual([]);
    expect(store.has(keysForGen(baseGen).address)).toBe(false);
    expect(store.has(keysForGen(nextGen).address)).toBe(false);
    expect(await vault.hasVault()).toBe(false);
  });

  it("enables and disables biometric vault protection successfully", async () => {
    await vault.saveVault({
      address: "acp1qqbiowallet000000000000000000000000000",
      keystoreJson: LARGE_KS,
      mnemonic: "bio notes",
    });
    expect(await vault.isVaultBiometricProtected()).toBe(false);

    await expect(vault.enableVaultBiometricProtection()).resolves.toBe(true);
    expect(await vault.isVaultBiometricProtected()).toBe(true);
    let loaded = await vault.loadVault();
    expect(loaded?.protectedByBiometrics).toBe(true);
    expect(loaded?.address).toBe("acp1qqbiowallet000000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(LARGE_KS);
    expect(loaded?.mnemonic).toBe("bio notes");

    await expect(vault.disableVaultBiometricProtection()).resolves.toBe(true);
    expect(await vault.isVaultBiometricProtected()).toBe(false);
    loaded = await vault.loadVault();
    expect(loaded?.protectedByBiometrics).toBe(false);
    expect(loaded?.address).toBe("acp1qqbiowallet000000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(LARGE_KS);
  });

  it("does not mix address from one generation with secrets from another", async () => {
    await vault.saveVault({
      address: "acp1qqwalletA00000000000000000000000000000",
      keystoreJson: SMALL_KS,
    });
    const genA = activeGen()!;

    await vault.saveVault({
      address: "acp1qqwalletB00000000000000000000000000000",
      keystoreJson: LARGE_KS,
      mnemonic: "only b",
    });
    const genB = activeGen()!;
    expect(genB).not.toBe(genA);

    const loaded = await vault.loadVault();
    expect(loaded?.address).toBe("acp1qqwalletB00000000000000000000000000000");
    expect(loaded?.keystoreJson).toBe(LARGE_KS);
    expect(loaded?.mnemonic).toBe("only b");
  });
});
