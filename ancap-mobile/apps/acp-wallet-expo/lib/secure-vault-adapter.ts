/**
 * SecureVault adapter — wires expo SecureStore vault to acp-wallet-sdk interface.
 */
import type { SecureVault } from "@ancap/acp-wallet-sdk";
import { hasVault, loadVault, saveVault, wipeVault, type VaultPayload } from "@/lib/vault";

export const expoSecureVault: SecureVault = {
  async hasWallet(): Promise<boolean> {
    return hasVault();
  },
  async saveMnemonic(mnemonic: string): Promise<void> {
    const existing = await loadVault();
    if (!existing?.address || !existing.keystoreJson) {
      throw new Error("Vault address/keystore must be saved before storing mnemonic via SecureVault.");
    }
    const payload: VaultPayload = {
      address: existing.address,
      keystoreJson: existing.keystoreJson,
      mnemonic,
      protectedByBiometrics: existing.protectedByBiometrics,
    };
    await saveVault(payload);
  },
  async loadMnemonic(): Promise<string> {
    const vault = await loadVault();
    const mnemonic = vault?.mnemonic?.trim();
    if (!mnemonic) {
      throw new Error(
        "No wallet mnemonic in secure vault. Restore used keystore-only import; seed notes were not stored."
      );
    }
    return mnemonic;
  },
  async wipe(): Promise<void> {
    // wipeVault also deletes the document-dir keystore export file.
    await wipeVault();
  },
};
