import { describe, expect, it } from "vitest";
import { chunkSecret, joinSecretChunks, SECURE_STORE_CHUNK_SIZE } from "./vault-chunk";

describe("vault-chunk", () => {
  it("bounds UTF-8 bytes without splitting Unicode code points", () => {
    const value = "кошелёк🔑漢字".repeat(1000);
    const parts = chunkSecret(value, 11);
    expect(parts.every((p) => new TextEncoder().encode(p).length <= 11)).toBe(true);
    expect(joinSecretChunks(parts)).toBe(value);
  });

  it("rejects invalid budgets instead of looping forever", () => {
    for (const size of [0, -1, NaN, Infinity, 1.5]) {
      expect(() => chunkSecret("secret", size)).toThrow();
    }
    expect(() => chunkSecret("🔑", 3)).toThrow();
  });
  it("keeps small secrets as a single chunk", () => {
    expect(chunkSecret("abc")).toEqual(["abc"]);
  });

  it("splits oversized secrets under the SecureStore limit", () => {
    const value = "x".repeat(SECURE_STORE_CHUNK_SIZE * 2 + 50);
    const parts = chunkSecret(value);
    expect(parts.length).toBe(3);
    expect(parts.every((p) => p.length <= SECURE_STORE_CHUNK_SIZE)).toBe(true);
    expect(joinSecretChunks(parts)).toBe(value);
  });

  it("roundtrips a keystore-sized payload", () => {
    const value = JSON.stringify({ version: 3, crypto: "y".repeat(40_000) });
    expect(joinSecretChunks(chunkSecret(value))).toBe(value);
  });
});
