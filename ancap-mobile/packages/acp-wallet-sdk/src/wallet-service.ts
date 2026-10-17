import { assertAcpAddress } from "./address.js";
import type { SecureVault, SignedTransaction, TransferRequest } from "./types.js";

export type CreatedWalletResult = {
  address: string;
  mnemonic: string;
  keystoreJson: string;
};

export type FeeEstimateResult = {
  feeAcp: string;
  feeUnits: number;
};

export type NativeWalletModule = {
  encryptKeystore?(keystoreJson: string, password: string): Promise<string>;
  decryptKeystore?(backupJson: string, password: string): Promise<string>;
  createWallet(): Promise<CreatedWalletResult>;
  validateAddress(address: string): Promise<boolean>;
  addressFromKeystore(keystoreJson: string): Promise<string>;
  estimateFeeDefault(): Promise<FeeEstimateResult>;
  signTransfer(params: {
    rpcUrl: string;
    keystoreJson: string;
    to: string;
    amountAcp: string;
    feeAcp?: string;
  }): Promise<SignedTransaction>;
};

export async function encryptKeystoreBackup(keystoreJson: string, password: string): Promise<string> {
  const native = requireNative();
  if (!native.encryptKeystore) throw new Error("Encrypted backup requires a rebuilt native wallet.");
  return native.encryptKeystore(keystoreJson, password);
}

export async function decryptKeystoreBackup(backupJson: string, password: string): Promise<string> {
  const native = requireNative();
  if (!native.decryptKeystore) throw new Error("Encrypted backup requires a rebuilt native wallet.");
  return native.decryptKeystore(backupJson, password);
}

let nativeModule: NativeWalletModule | null | undefined;
let secureVault: SecureVault | null = null;

export function setNativeWalletModule(mod: NativeWalletModule | null): void {
  nativeModule = mod;
}

export function setSecureVault(vault: SecureVault | null): void {
  secureVault = vault;
}

export function getSecureVault(): SecureVault | null {
  return secureVault;
}

function requireNative(): NativeWalletModule {
  if (!nativeModule) {
    throw new Error(
      "ACP native module is not linked. Use a native Expo dev build with expo-acp-core (Android: build-android-native.ps1, iOS/macOS: build-ios-native.ps1) or import via walletd."
    );
  }
  return nativeModule;
}

export async function createWallet(): Promise<CreatedWalletResult> {
  const w = await requireNative().createWallet();
  return {
    address: w.address,
    mnemonic: w.mnemonic,
    keystoreJson: w.keystoreJson,
  };
}

export async function validateAddressWithNative(address: string): Promise<boolean> {
  return requireNative().validateAddress(address.trim());
}

export async function addressFromKeystore(keystoreJson: string): Promise<string> {
  return requireNative().addressFromKeystore(keystoreJson);
}

export async function estimateFeeDefault(): Promise<FeeEstimateResult> {
  const fee = await requireNative().estimateFeeDefault();
  return {
    feeAcp: fee.feeAcp,
    feeUnits: fee.feeUnits,
  };
}

export async function signAndPrepareTransfer(
  rpcUrl: string,
  keystoreJson: string,
  req: TransferRequest
): Promise<SignedTransaction> {
  assertAcpAddress(req.from, "from");
  assertAcpAddress(req.to, "to");
  const native = requireNative();
  const signer = await native.addressFromKeystore(keystoreJson);
  if (signer !== req.from.trim()) {
    throw new Error("Signing wallet does not match the confirmed sender.");
  }
  return native.signTransfer({
    rpcUrl,
    keystoreJson,
    to: req.to,
    amountAcp: req.amountAcp,
    feeAcp: req.feeAcp,
  });
}
