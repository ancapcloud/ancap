import { redirect } from "next/navigation";

/** rACP is the primary external token; legacy wACP remains at its explicit route. */
export default function BridgeIndexPage() {
  redirect("/tokens/racp/redeem");
}
