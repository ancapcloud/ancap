// Explicit mainnet broadcast; no issuance. Key file is read in memory and never logged.
import { readText, readOptionalJson, writeJson } from './safe-files.mjs';
import { Wallet, JsonRpcProvider, getCreateAddress, keccak256, Contract } from 'ethers';
import { compile } from './compile.mjs';

if (!process.argv.includes('--broadcast')) throw new Error('Explicit --broadcast required');
const keyFile = process.env.RACP_DEPLOYER_ENV_FILE;
if (!keyFile) throw new Error('Set RACP_DEPLOYER_ENV_FILE to the existing signer env file');
const line = readText(keyFile).split(/\r?\n/).find(l => l.startsWith('BRIDGE_BSC_PRIVATE_KEY='));
if (!line) throw new Error('Signer key missing');
const key = line.slice(line.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '');
const report = JSON.parse(readText('prepared/deployment.json'));
const plan = JSON.parse(readText('deployment-plan.json'));
const provider = new JsonRpcProvider(plan.rpcUrl);
const wallet = new Wallet(key, provider);
if (wallet.address.toLowerCase() !== plan.recipient.toLowerCase()) throw new Error('Signer mismatch');
if ((await provider.getNetwork()).chainId !== 4663n) throw new Error('Wrong chain');
const journalPath = 'prepared/broadcast-journal.json';
let journal = readOptionalJson(journalPath);
if (!journal) {
  if (plan.contractAddress) throw new Error('Already deployed');
  const { from, ...tx } = report.transaction;
  if (from.toLowerCase() !== wallet.address.toLowerCase() || tx.to || BigInt(tx.value) !== 0n) throw new Error('Invalid deployment');
  const cost = BigInt(tx.gasLimit) * BigInt(tx.gasPrice);
  if (cost > 50_000_000_000_000n) throw new Error('Deployment exceeds 0.00005 ETH budget');
  if ((await provider.getBalance(wallet.address)) < cost) throw new Error('Insufficient ETH');
  tx.nonce = await provider.getTransactionCount(wallet.address, 'pending');
  const signed = await wallet.signTransaction(tx);
  journal = { transactionHash: keccak256(signed), contractAddress: getCreateAddress({from: wallet.address, nonce: tx.nonce}), nonce: tx.nonce, status: 'broadcast-intent' };
  writeJson(journalPath, journal, { exclusive: true });
  // Persist intent before sending: never create a second contract on an ambiguous response.
  const sent = await provider.broadcastTransaction(signed);
  console.log('BROADCAST', sent.hash);
}
const receipt = await provider.waitForTransaction(journal.transactionHash, 1, 120_000);
if (!receipt || receipt.status !== 1) throw new Error('Deployment not confirmed successfully; inspect journal');
const { artifact } = compile();
const token = new Contract(journal.contractAddress, artifact.abi, provider);
if ((await token.totalSupply()) !== 0n) throw new Error('Unexpected nonzero initial supply');
if ((await token.recipient()).toLowerCase() !== plan.recipient.toLowerCase()) throw new Error('Recipient mismatch');
Object.assign(plan, { status: 'deployed_unfunded', issuer: wallet.address, contractAddress: journal.contractAddress, deploymentTransaction: journal.transactionHash });
writeJson('deployment-plan.json', plan);
Object.assign(journal, {status: 'confirmed', blockNumber: receipt.blockNumber, gasUsed: receipt.gasUsed.toString(), feeWei: receipt.fee.toString()});
writeJson(journalPath, journal);
console.log(JSON.stringify(journal, null, 2));
