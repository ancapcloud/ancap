export function safeAuthReturn(raw: string | null | undefined): string {
  const path = raw?.trim();
  if (!path || !path.startsWith("/") || path.startsWith("//") || /[\\\u0000-\u001f\u007f]/.test(path)) return "/dashboard";
  return path;
}
