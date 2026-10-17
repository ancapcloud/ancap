/**
 * SecureVault adapter — wires expo SecureStore vault to acp-wallet-sdk interface.
 */
import type { SecureVault } from "@ancap/acp-wallet-sdk";
import { hasVault, loadVault, saveVaultMnemonic, wipeVault } from "@/lib/vault";

export const expoSecureVault: SecureVault = {
  async hasWallet(): Promise<boolean> {
    return hasVault();
  },
  async saveMnemonic(mnemonic: string): Promise<void> {
    await saveVaultMnemonic(mnemonic);
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
