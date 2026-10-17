export const MAX_BACKUP_BYTES = 64 * 1024;
export const BACKUP_FILENAME = "acp-wallet-backup.json";

/** Only the existing Rust encrypted envelope may leave the sandbox as a backup. */
export function assertEncryptedBackup(raw: string): string {
  if (raw.length > MAX_BACKUP_BYTES) throw new Error("Encrypted backup is too large.");
  let parsed;
  try { parsed = JSON.parse(raw); } catch { throw new Error("Invalid encrypted backup JSON."); }
  if (!parsed || parsed.v !== 2 || typeof parsed.crypto !== "object" || !parsed.crypto ||
      Object.keys(parsed).some((key) => !["v", "crypto"].includes(key))) {
    throw new Error("Expected a password-encrypted ACP backup.");
  }
  const c = parsed.crypto;
  const fields = ["kdf", "mem_kib", "time", "parallelism", "salt_b64", "nonce_b64", "ciphertext_b64"];
  if (Object.keys(c).some((key) => !fields.includes(key)) ||
      c.kdf !== "argon2id" || c.mem_kib !== 65536 || c.time !== 3 || c.parallelism !== 1 ||
      !["salt_b64", "nonce_b64", "ciphertext_b64"].every((key) =>
        typeof c[key] === "string" && c[key].length > 0 && /^[A-Za-z0-9+/]+={0,2}$/.test(c[key]))) {
    throw new Error("Unsupported encrypted backup format.");
  }
  return raw.trim();
}

