import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { fileSystem } = vi.hoisted(() => {
  const files = new Map<string, string>();
  return {
    fileSystem: {
      documentDirectory: "file:///mock-docs/",
      files,
      writeAsStringAsync: vi.fn(async (uri: string, contents: string) => {
        files.set(uri, contents);
      }),
      readAsStringAsync: vi.fn(async (uri: string) => {
        if (!files.has(uri)) {
          throw new Error(`missing ${uri}`);
        }
        return files.get(uri)!;
      }),
      getInfoAsync: vi.fn(async (uri: string) => ({ exists: files.has(uri) })),
      deleteAsync: vi.fn(async (uri: string) => {
        files.delete(uri);
      }),
    },
  };
});

vi.mock("expo-file-system", () => fileSystem);

import {
  KEYSTORE_EXPORT_FILENAME,
  assertKeystoreExportJson,
  deleteKeystoreExportFile,
  readKeystoreExportFile,
  writeKeystoreExportFile,
} from "./keystore-export";

const VALID_V = JSON.stringify({ v: 3, seed: [1, 2, 3] });
const ENCRYPTED = JSON.stringify({ v: 2, crypto: { kdf: "argon2id", mem_kib: 65536, time: 3, parallelism: 1, salt_b64: "AAAA", nonce_b64: "AAAA", ciphertext_b64: "AAAA" } });
const VALID_VERSION = JSON.stringify({ version: 3, cipher: "x" });

describe("assertKeystoreExportJson", () => {
  it("accepts native v:3 and legacy version:3", () => {
    expect(assertKeystoreExportJson(VALID_V)).toBe(VALID_V);
    expect(assertKeystoreExportJson(`  ${VALID_VERSION}  `)).toBe(VALID_VERSION);
  });

  it("rejects empty, non-object, and wrong version", () => {
    expect(() => assertKeystoreExportJson("")).toThrow(/empty/i);
    expect(() => assertKeystoreExportJson("[]")).toThrow(/object/i);
    expect(() => assertKeystoreExportJson(JSON.stringify({ v: 2 }))).toThrow(/version 3/i);
    expect(() => assertKeystoreExportJson("{not-json")).toThrow(/valid JSON/i);
  });
});

describe("keystore export file helpers", () => {
  afterEach(() => vi.unstubAllGlobals());
  beforeEach(() => {
    vi.stubGlobal("__DEV__", true);
    fileSystem.files.clear();
    fileSystem.documentDirectory = "file:///mock-docs/";
    fileSystem.writeAsStringAsync.mockClear();
    fileSystem.readAsStringAsync.mockClear();
    fileSystem.getInfoAsync.mockClear();
    fileSystem.deleteAsync.mockClear();
  });

  it("writes, reads, and deletes the export file", async () => {
    expect(await writeKeystoreExportFile(ENCRYPTED)).toBe(true);
    const uri = `file:///mock-docs/${KEYSTORE_EXPORT_FILENAME}`;
    expect(fileSystem.files.get(uri)).toBe(ENCRYPTED);
    expect(await readKeystoreExportFile()).toBe(ENCRYPTED);
    await deleteKeystoreExportFile();
    expect(fileSystem.files.has(uri)).toBe(false);
    expect(await readKeystoreExportFile()).toBeNull();
  });

  it("returns false when documentDirectory is unavailable", async () => {
    fileSystem.documentDirectory = null as unknown as string;
    expect(await writeKeystoreExportFile(ENCRYPTED)).toBe(false);
    expect(fileSystem.writeAsStringAsync).not.toHaveBeenCalled();
  });

  it("never writes plaintext private keys to the release app documents directory", async () => {
    vi.stubGlobal("__DEV__", false);
    await expect(writeKeystoreExportFile(VALID_V)).rejects.toThrow(/encrypted ACP backup/);
    expect(fileSystem.writeAsStringAsync).not.toHaveBeenCalled();
  });

  it("surfaces deletion failure for wipe retry", async () => {
    await writeKeystoreExportFile(ENCRYPTED);
    fileSystem.deleteAsync.mockRejectedValueOnce(new Error("delete failed"));
    await expect(deleteKeystoreExportFile()).rejects.toThrow("delete failed");
  });
});
