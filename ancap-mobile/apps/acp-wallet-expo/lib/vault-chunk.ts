/** Android SecureStore rejects values > 2048 bytes; keep chunks under that. */
export const SECURE_STORE_CHUNK_SIZE = 1800;

export function chunkSecret(value: string, size = SECURE_STORE_CHUNK_SIZE): string[] {
  if (!value) {
    return [];
  }
  if (value.length <= size) {
    return [value];
  }
  const parts: string[] = [];
  for (let i = 0; i < value.length; i += size) {
    parts.push(value.slice(i, i + size));
  }
  return parts;
}

export function joinSecretChunks(parts: string[]): string {
  return parts.join("");
}
