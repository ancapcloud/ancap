import { describe, expect, it } from "vitest";
import { claimTransaction, RACP_AIRDROP, type AirdropVoucher } from "../racpAirdrop";
import { RACP_CONTRACT } from "../racpToken";
const account = "0x0000000000000000000000000000000000001234";
const voucher: AirdropVoucher = { chain_id: 4663, airdrop_contract: RACP_AIRDROP, token_contract: RACP_CONTRACT, recipient: account, eligibility_id: "0x"+"ab".repeat(32), deadline: 2000000000, signature: "0x"+"12".repeat(65), grant: "500" };

describe("bounded rACP claim transaction", () => {
  it("encodes a zero-value fixed-function call with the correct ABI dynamic offset", () => {
    const tx = claimTransaction(voucher, account);
    expect(tx.to).toBe(RACP_AIRDROP); expect(tx.value).toBe("0x0"); expect(tx.chainId).toBe("0x1237");
    expect(tx.data.slice(0,10)).toBe("0xdd81e7be");
    expect(tx.data.slice(10,74)).toBe(account.slice(2).padStart(64,"0"));
    expect(tx.data.slice(202,266)).toBe("80".padStart(64,"0"));
    expect(tx.data.slice(266,330)).toBe("41".padStart(64,"0"));
    expect(tx.data.length).toBe(10+64*8);
  });
  it.each([{...voucher,chain_id:56},{...voucher,grant:"1001"},{...voucher,airdrop_contract:account},{...voucher,recipient:RACP_CONTRACT},{...voucher,signature:"0x12"}])("rejects altered destinations, limits and signatures", bad => {
    expect(() => claimTransaction(bad, account)).toThrow("Invalid airdrop voucher");
  });
});
