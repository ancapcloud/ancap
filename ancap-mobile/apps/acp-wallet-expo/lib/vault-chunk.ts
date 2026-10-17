/** Conservative UTF-8 byte budget for each SecureStore value. */
export const SECURE_STORE_CHUNK_SIZE = 1800;

export function chunkSecret(value: string, size = SECURE_STORE_CHUNK_SIZE): string[] {
  if (!Number.isSafeInteger(size) || size <= 0) throw new Error("Invalid chunk byte budget.");
  const parts: string[] = [];
  let part = "";
  let bytes = 0;
  // Iterate code points so surrogate pairs cannot be split across stored values.
  for (const char of value) {
    const point = char.codePointAt(0)!;
    const width = point <= 0x7f ? 1 : point <= 0x7ff ? 2 : point <= 0xffff ? 3 : 4;
    if (width > size) throw new Error("Chunk byte budget cannot fit a code point.");
    if (bytes + width > size) {
      parts.push(part);
      part = "";
      bytes = 0;
    }
    part += char;
    bytes += width;
  }
  if (part) parts.push(part);
  return parts;
}

export function joinSecretChunks(parts: string[]): string {
  return parts.join("");
}
