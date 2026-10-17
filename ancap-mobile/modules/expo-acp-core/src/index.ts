import { requireOptionalNativeModule } from "expo-modules-core";

export type CreatedWalletNative = {
  address: string;
  mnemonic: string;
  keystoreJson: string;
};

export type SignedTransferNative = {
  rawTx: string;
  txid: string;
};

type ExpoAcpCoreNative = {
  encryptKeystore(keystoreJson: string, password: string): Promise<string>;
  decryptKeystore(backupJson: string, password: string): Promise<string>;
  createWallet(): Promise<CreatedWalletNative>;
  validateAddress(address: string): boolean;
  addressFromKeystore(keystoreJson: string): Promise<string>;
  estimateFeeDefault(): Promise<{ feeAcp: string; feeUnits: number }>;
  signTransfer(
    rpcUrl: string,
    keystoreJson: string,
    toAddress: string,
    amountAcp: string,
    feeAcp: string | null
  ): Promise<SignedTransferNative>;
};

const Native = requireOptionalNativeModule<ExpoAcpCoreNative>("ExpoAcpCore");

export type NativeWalletBridge = {
  encryptKeystore(keystoreJson: string, password: string): Promise<string>;
  decryptKeystore(backupJson: string, password: string): Promise<string>;
  createWallet(): Promise<CreatedWalletNative>;
  validateAddress(address: string): Promise<boolean>;
  addressFromKeystore(keystoreJson: string): Promise<string>;
  estimateFeeDefault(): Promise<{ feeAcp: string; feeUnits: number }>;
  signTransfer(params: {
    rpcUrl: string;
    keystoreJson: string;
    to: string;
    amountAcp: string;
    feeAcp?: string;
  }): Promise<SignedTransferNative>;
};

export function getExpoAcpCoreModule(): NativeWalletBridge | null {
  if (!Native) {
    return null;
  }
  return {
    async encryptKeystore(keystoreJson, password) {
      if (!Native.encryptKeystore) throw new Error("Encrypted backup requires a rebuilt native wallet.");
      return Native.encryptKeystore(keystoreJson, password);
    },
    async decryptKeystore(backupJson, password) {
      if (!Native.decryptKeystore) throw new Error("Encrypted backup requires a rebuilt native wallet.");
      return Native.decryptKeystore(backupJson, password);
    },
    async createWallet() {
      return Native.createWallet();
    },
    async validateAddress(address: string) {
      return Native.validateAddress(address);
    },
    async addressFromKeystore(keystoreJson: string) {
      return Native.addressFromKeystore(keystoreJson);
    },
    async estimateFeeDefault() {
      return Native.estimateFeeDefault();
    },
    async signTransfer(params) {
      return Native.signTransfer(
        params.rpcUrl,
        params.keystoreJson,
        params.to,
        params.amountAcp,
        params.feeAcp ?? null
      );
    },
  };
}
