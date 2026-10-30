/** Display conversion only. Native balances and API transfer amounts stay in ACP. */
export function acpToRacpEquivalent(raw: string): string {
  if (!/^-?\d+(\.\d{1,8})?$/.test(raw)) throw new Error("Invalid ACP display amount");
  const negative = raw.startsWith("-");
  const [whole, fraction = ""] = raw.replace(/^-/, "").split(".");
  const units = (BigInt(whole) * 100_000_000n + BigInt(fraction.padEnd(8, "0"))) * 10n;
  const decimals = (units % 100_000_000n).toString().padStart(8, "0").replace(/0+$/, "");
  return `${negative && units ? "-" : ""}${units / 100_000_000n}${decimals ? "." + decimals : ""}`;
}

export function formatRacpEquivalent(raw: string, lang = "en"): string {
  return new Intl.NumberFormat(lang, { maximumFractionDigits: 7 }).format(Number(acpToRacpEquivalent(raw)));
}
