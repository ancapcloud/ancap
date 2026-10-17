import { beforeEach, describe, expect, it, vi } from "vitest";
const { fs, picker, sharing, platform } = vi.hoisted(() => ({
  fs: { cacheDirectory: "file:///cache/", writeAsStringAsync: vi.fn(), deleteAsync: vi.fn(),
    getInfoAsync: vi.fn(), readAsStringAsync: vi.fn(), StorageAccessFramework: {
      requestDirectoryPermissionsAsync: vi.fn(), createFileAsync: vi.fn(),
    } },
  picker: { getDocumentAsync: vi.fn() },
  sharing: { isAvailableAsync: vi.fn(), shareAsync: vi.fn() },
  platform: { OS: "android" },
}));
vi.mock("expo-file-system", () => fs);
vi.mock("expo-document-picker", () => picker);
vi.mock("expo-sharing", () => sharing);
vi.mock("react-native", () => ({ Platform: platform }));
import { exportEncryptedBackup, pickKeystoreBackup } from "./keystore-backup";
import { assertEncryptedBackup, MAX_BACKUP_BYTES } from "./keystore-backup-format";
const encrypted = JSON.stringify({ v: 2, crypto: { kdf: "argon2id", mem_kib: 65536, time: 3,
  parallelism: 1, salt_b64: "AAAA", nonce_b64: "AAAA", ciphertext_b64: "AAAA" } });
describe("encrypted external wallet backup", () => {
  beforeEach(() => {
    vi.resetAllMocks(); platform.OS = "android";
    fs.StorageAccessFramework.requestDirectoryPermissionsAsync.mockResolvedValue({ granted: true, directoryUri: "content://folder" });
    fs.StorageAccessFramework.createFileAsync.mockResolvedValue("content://folder/backup");
    sharing.isAvailableAsync.mockResolvedValue(true);
    fs.getInfoAsync.mockResolvedValue({ exists: true, size: encrypted.length });
    fs.readAsStringAsync.mockResolvedValue(encrypted);
  });
  it("refuses plaintext or appended private material before opening export UI", async () => {
    for (const raw of [JSON.stringify({ v: 3, seed: [1] }),
      JSON.stringify({ ...JSON.parse(encrypted), spend_dilithium_sk: [1] })]) {
      await expect(exportEncryptedBackup(raw)).rejects.toThrow();
    }
    expect(fs.StorageAccessFramework.requestDirectoryPermissionsAsync).not.toHaveBeenCalled();
  });
  it("writes only encrypted content to the user-selected Android folder", async () => {
    expect(await exportEncryptedBackup(encrypted)).toBe("saved");
    expect(fs.writeAsStringAsync).toHaveBeenCalledWith("content://folder/backup", encrypted);
  });
  it("treats Android cancel as cancel and propagates write failure", async () => {
    fs.StorageAccessFramework.requestDirectoryPermissionsAsync.mockResolvedValueOnce({ granted: false });
    expect(await exportEncryptedBackup(encrypted)).toBe("cancelled");
    expect(fs.writeAsStringAsync).not.toHaveBeenCalled();
    fs.writeAsStringAsync.mockRejectedValueOnce(new Error("disk full"));
    await expect(exportEncryptedBackup(encrypted)).rejects.toThrow("disk full");
  });
  it("does not claim a durable iOS export from a closed share sheet and removes cache", async () => {
    platform.OS = "ios";
    expect(await exportEncryptedBackup(encrypted)).toBe("share_sheet_closed");
    expect(fs.deleteAsync).toHaveBeenCalledWith(expect.stringMatching(/^file:\/\/\/cache\/acp-wallet-backup-.*\.json$/), { idempotent: true });
  });
  it("cleans the share cache on error", async () => {
    platform.OS = "ios"; sharing.shareAsync.mockRejectedValueOnce(new Error("share failed"));
    await expect(exportEncryptedBackup(encrypted)).rejects.toThrow("share failed");
    expect(fs.deleteAsync).toHaveBeenCalled();
  });
  it("imports a picker cache copy and never deletes the external source", async () => {
    picker.getDocumentAsync.mockResolvedValue({ canceled: false, assets: [{ uri: "file:///cache/picked", size: 200 }] });
    expect(await pickKeystoreBackup()).toBe(encrypted);
    expect(fs.deleteAsync).toHaveBeenCalledWith("file:///cache/picked", { idempotent: true });
    fs.deleteAsync.mockClear();
    picker.getDocumentAsync.mockResolvedValue({ canceled: false, assets: [{ uri: "content://original", size: 200 }] });
    await pickKeystoreBackup();
    expect(fs.deleteAsync).not.toHaveBeenCalled();
  });
  it("rejects oversized files before reading and cleans picker cache", async () => {
    picker.getDocumentAsync.mockResolvedValue({ canceled: false, assets: [{ uri: "file:///cache/picked", size: MAX_BACKUP_BYTES + 1 }] });
    await expect(pickKeystoreBackup()).rejects.toThrow(/large/);
    expect(fs.readAsStringAsync).not.toHaveBeenCalled();
    expect(fs.deleteAsync).toHaveBeenCalled();
  });
  it("does not import on picker cancellation", async () => {
    picker.getDocumentAsync.mockResolvedValue({ canceled: true, assets: null });
    expect(await pickKeystoreBackup()).toBeNull();
    expect(fs.readAsStringAsync).not.toHaveBeenCalled();
  });
  it("rejects unsupported KDF parameters before native decryption", () => {
    const backup = JSON.parse(encrypted); backup.crypto.mem_kib = 999999999;
    expect(() => assertEncryptedBackup(JSON.stringify(backup))).toThrow(/Unsupported/);
  });
});
