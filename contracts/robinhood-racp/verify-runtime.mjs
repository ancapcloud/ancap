import fs from 'node:fs';
import assert from 'node:assert/strict';
import { Contract, JsonRpcProvider, keccak256, toUtf8Bytes } from 'ethers';
import { compile } from './compile.mjs';
const plan = JSON.parse(fs.readFileSync('deployment-plan.json', 'utf8'));
const provider = new JsonRpcProvider(plan.rpcUrl);
assert.equal((await provider.getNetwork()).chainId, BigInt(plan.chainId));
const { input, artifact } = compile();
const actual = Buffer.from((await provider.getCode(plan.contractAddress)).slice(2), 'hex');
const expected = Buffer.from(artifact.evm.deployedBytecode.object, 'hex');
assert.equal(actual.length, expected.length);
for (const refs of Object.values(artifact.evm.deployedBytecode.immutableReferences)) {
  for (const { start, length } of refs) { actual.fill(0, start, start + length); expected.fill(0, start, start + length); }
}
assert.deepEqual(actual, expected);
const token = new Contract(plan.contractAddress, artifact.abi, provider);
assert.equal((await token.issuer()).toLowerCase(), plan.issuer.toLowerCase());
assert.equal((await token.recipient()).toLowerCase(), plan.recipient.toLowerCase());
assert.equal(await token.name(), 'Robinhood ACP');
assert.equal(await token.symbol(), 'rACP');
assert.equal(await token.MAX_ISSUANCE(), BigInt(plan.maxIssuance));
if (plan.reserveEvidence) {
  const proof = fs.readFileSync('prepared/reserve-funding.json', 'utf8').replace(/^\uFEFF/, '');
  assert.equal(keccak256(toUtf8Bytes(proof)), plan.reserveEvidence);
  assert.equal(await token.reserveEvidence(), plan.reserveEvidence);
}
const report = { chainId: plan.chainId, contractAddress: plan.contractAddress, runtimeMatchesLocalCompilation: true,
  totalSupply: (await token.totalSupply()).toString(), recipientBalance: (await token.balanceOf(plan.recipient)).toString(),
  issued: await token.issued(), reserveEvidence: await token.reserveEvidence(),
  explorerSourceVerification: JSON.parse(fs.readFileSync('prepared/source-verification.json', 'utf8')).blockscout.status };
fs.writeFileSync('prepared/runtime-verification.json', JSON.stringify(report, null, 2) + '\n');
fs.writeFileSync('prepared/standard-input.json', JSON.stringify(input, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
