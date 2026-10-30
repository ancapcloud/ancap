import { RACP_CONTRACT } from "./racpToken";
export const RACP_AIRDROP = "0x2867D10560b35616370cF5C7A21Ab1532698FD0F";
export type AirdropVoucher = { chain_id: number; airdrop_contract: string; token_contract: string; recipient: string; eligibility_id: string; deadline: number; signature: string; grant: string };

/** Encode only claim(address,bytes32,uint256,bytes), never server-provided arbitrary calldata. */
export function claimTransaction(voucher: AirdropVoucher, account: string) {
  if (voucher.chain_id !== 4663 || voucher.airdrop_contract.toLowerCase() !== RACP_AIRDROP.toLowerCase() || voucher.token_contract.toLowerCase() !== RACP_CONTRACT.toLowerCase()
    || !/^0x[0-9a-f]{40}$/i.test(account) || voucher.recipient.toLowerCase() !== account.toLowerCase() || voucher.grant !== "500"
    || !/^0x[0-9a-f]{64}$/i.test(voucher.eligibility_id) || !/^0x[0-9a-f]{130}$/i.test(voucher.signature)
    || !Number.isSafeInteger(voucher.deadline) || voucher.deadline <= 0) throw new Error("Invalid airdrop voucher");
  const word = (value: bigint) => value.toString(16).padStart(64, "0");
  const data = "0xdd81e7be" + account.slice(2).toLowerCase().padStart(64, "0") + voucher.eligibility_id.slice(2)
    + word(BigInt(voucher.deadline)) + word(BigInt(128)) + word(BigInt(65)) + voucher.signature.slice(2).padEnd(192, "0");
  return { from: account, to: RACP_AIRDROP, data, value: "0x0", chainId: "0x1237" };
}
