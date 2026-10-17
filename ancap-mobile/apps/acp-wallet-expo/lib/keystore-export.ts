import * as FileSystem from "expo-file-system";

/**
 * Explicit user-initiated keystore export filename under the app document directory.
 * Written only when the user taps Copy — not a hidden SecureStore stash.
 */
export const KEYSTORE_EXPORT_FILENAME = "acp-keystore-export.json";

function exportUri(): string | null {
  const base = FileSystem.documentDirectory;
  if (!base) {
    return null;
  }
  return `${base}${KEYSTORE_EXPORT_FILENAME}`;
}

/**
 * Lightweight shape check for ACP keystore JSON before import/export.
 * Accepts both `"v":3` (native KeystoreV3) and legacy `"version":3` fixtures.
 */
export function assertKeystoreExportJson(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) {
    throw new Error("Keystore JSON is empty.");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error("Keystore JSON is not valid JSON.");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Keystore JSON must be an object.");
  }
  const obj = parsed as Record<string, unknown>;
  const version = obj.v ?? obj.version;
  if (version !== 3 && version !== "3") {
    throw new Error('Keystore JSON must declare version 3 ("v":3).');
  }
  if (trimmed.length > 512_000) {
    throw new Error("Keystore JSON is too large.");
  }
  return trimmed;
}

/**
 * Write an external keystore backup file (user Copy action only).
 * @returns true when a durable file was written; false when documentDirectory is unavailable.
 */
export async function writeKeystoreExportFile(keystoreJson: string): Promise<boolean> {
  const uri = exportUri();
  if (!uri) {
    return false;
  }
  const validated = assertKeystoreExportJson(keystoreJson);
  await FileSystem.writeAsStringAsync(uri, validated);
  return true;
}

/** Read a previously exported keystore file, if present. */
export async function readKeystoreExportFile(): Promise<string | null> {
  const uri = exportUri();
  if (!uri) {
    return null;
  }
  const info = await FileSystem.getInfoAsync(uri);
  if (!info.exists) {
    return null;
  }
  const raw = await FileSystem.readAsStringAsync(uri);
  if (!raw?.trim()) {
    return null;
  }
  return assertKeystoreExportJson(raw);
}

/** Remove the export file (called on wallet wipe so secrets do not linger after remove). */
export async function deleteKeystoreExportFile(): Promise<void> {
  const uri = exportUri();
  if (!uri) {
    return;
  }
  try {
    const info = await FileSystem.getInfoAsync(uri);
    if (info.exists) {
      await FileSystem.deleteAsync(uri, { idempotent: true });
    }
  } catch {
    // Best-effort — wipe must still clear SecureStore.
  }
}
