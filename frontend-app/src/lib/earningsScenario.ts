export type EarningsInputs = {
  price: string;
  orders: string;
  feePercent: string;
  variableCost: string;
  fixedCost: string;
};

export const exampleEarningsInputs: EarningsInputs = {
  price: "100", orders: "10", feePercent: "10", variableCost: "15", fixedCost: "50",
};

const SCALE = 100_000_000n;
function units(value: string): bigint | null {
  if (!/^\d{1,9}(?:\.\d{1,8})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole) * SCALE + BigInt(fraction.padEnd(8, "0"));
}
function amount(value: bigint): string {
  const absolute = value < 0n ? -value : value;
  return `${value < 0n ? "-" : ""}${absolute / SCALE}.${String(absolute % SCALE).padStart(8, "0")}`;
}

/** Hypothetical ACP accounting only. Integer arithmetic preserves eight-decimal precision. */
export function calculateEarningsScenario(input: EarningsInputs) {
  const price = units(input.price);
  const variableCost = units(input.variableCost);
  const fixedCost = units(input.fixedCost);
  if (price === null || variableCost === null || fixedCost === null || !/^\d{1,6}$/.test(input.orders)) return null;
  if (!/^\d{1,3}(?:\.\d{1,2})?$/.test(input.feePercent)) return null;
  const [whole, fraction = ""] = input.feePercent.split(".");
  const feeBasisPoints = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  if (feeBasisPoints > 10_000n) return null;
  const orders = BigInt(input.orders);
  const gross = price * orders;
  // Round the illustrative fee to the nearest 0.00000001 ACP, half up.
  const fee = (gross * feeBasisPoints + 5_000n) / 10_000n;
  const costs = variableCost * orders + fixedCost;
  const net = gross - fee - costs;
  return { gross: amount(gross), fee: amount(fee), costs: amount(costs), net: amount(net), loss: net < 0n };
}

export function formatScenarioAmount(value: string, locale: string): string {
  const negative = value.startsWith("-");
  const [whole, fraction = ""] = value.replace(/^-/, "").split(".");
  const decimal = new Intl.NumberFormat(locale).formatToParts(1.1).find(part => part.type === "decimal")?.value ?? ".";
  const tail = fraction.replace(/0+$/, "");
  return `${negative ? "−" : ""}${new Intl.NumberFormat(locale).format(BigInt(whole))}${tail ? decimal + tail : ""}`;
}
