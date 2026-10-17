import * as FileSystem from "expo-file-system";
import * as DocumentPicker from "expo-document-picker";
import * as Sharing from "expo-sharing";
import { Platform } from "react-native";

import { assertEncryptedBackup, BACKUP_FILENAME, MAX_BACKUP_BYTES } from "./keystore-backup-format";

export async function exportEncryptedBackup(raw: string): Promise<"saved" | "cancelled" | "share_sheet_closed"> {
  const encrypted = assertEncryptedBackup(raw);
  const filename = BACKUP_FILENAME.replace(".json", `-${Date.now()}-${Math.random().toString(36).slice(2, 10)}.json`);
  if (Platform.OS === "android") {
    const saf = FileSystem.StorageAccessFramework;
    const permission = await saf.requestDirectoryPermissionsAsync();
    if (!permission.granted) return "cancelled";
    const uri = await saf.createFileAsync(permission.directoryUri, filename, "application/json");
    await FileSystem.writeAsStringAsync(uri, encrypted);
    return "saved";
  }
  if (!FileSystem.cacheDirectory || !(await Sharing.isAvailableAsync())) {
    throw new Error("File sharing is unavailable on this device.");
  }
  const uri = `${FileSystem.cacheDirectory}${filename}`;
  try {
    await FileSystem.writeAsStringAsync(uri, encrypted);
    await Sharing.shareAsync(uri, { mimeType: "application/json", UTI: "public.json" });
    // Sharing does not prove the destination saved the file, or distinguish cancel.
    return "share_sheet_closed";
  } finally {
    await FileSystem.deleteAsync(uri, { idempotent: true });
  }
}

export async function pickKeystoreBackup(): Promise<string | null> {
  const result = await DocumentPicker.getDocumentAsync({ type: ["application/json", "text/plain"],
    copyToCacheDirectory: true, multiple: false });
  if (result.canceled) return null;
  const asset = result.assets[0];
  try {
    const info = await FileSystem.getInfoAsync(asset.uri);
    if (!info.exists || info.size > MAX_BACKUP_BYTES || (asset.size ?? 0) > MAX_BACKUP_BYTES) {
      throw new Error("Backup file is unavailable or too large.");
    }
    const raw = await FileSystem.readAsStringAsync(asset.uri);
    if (raw.length > MAX_BACKUP_BYTES) throw new Error("Backup file is too large.");
    return raw;
  } finally {
    // Only the picker-created cache copy belongs to this app.
    if (FileSystem.cacheDirectory && asset.uri.startsWith(FileSystem.cacheDirectory)) {
      await FileSystem.deleteAsync(asset.uri, { idempotent: true });
    }
  }
}
