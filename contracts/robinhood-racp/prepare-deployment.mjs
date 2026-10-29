// Read-only. Writes unsigned deployment transaction and compiler input; never signs or broadcasts.
import fs from 'node:fs';
import { ContractFactory, JsonRpcProvider, getAddress, formatEther } from 'ethers';
import { compile } from './compile.mjs';

const plan = JSON.parse(fs.readFileSync('deployment-plan.json', 'utf8'));
const recipient = getAddress(plan.recipient.toLowerCase());
const provider = new JsonRpcProvider(plan.rpcUrl);
if ((await provider.getNetwork()).chainId !== BigInt(plan.chainId)) throw new Error('Wrong network');
const { input, artifact } = compile();
const issuer = recipient;
const factory = new ContractFactory(artifact.abi, artifact.evm.bytecode.object);
const tx = { ...(await factory.getDeployTransaction(issuer, recipient)), from: issuer, chainId: plan.chainId, value: '0x0' };
const gas = await provider.estimateGas(tx);
const fees = await provider.getFeeData();
const basePrice = fees.gasPrice;
const price = basePrice ? (basePrice * 110n + 99n) / 100n : null;
if (!price) throw new Error('Gas price unavailable');
const gasLimit = (gas * 120n + 99n) / 100n;
const balance = await provider.getBalance(issuer);
const report = {
  issuer, recipient, chainId: plan.chainId, gasEstimate: gas.toString(),
  gasPrice: price.toString(), maxEstimatedCostETH: formatEther(gasLimit * price),
  balanceETH: formatEther(balance), sufficientGasBalance: balance >= gasLimit * price,
  initialSupply: '0', reserveStatus: 'not-funded',
  transaction: { ...tx, type: 0, gasPrice: price.toString(), gasLimit: gasLimit.toString() },
};
fs.mkdirSync('prepared', { recursive: true });
fs.writeFileSync('prepared/deployment.json', JSON.stringify(report, null, 2) + '\n');
fs.writeFileSync('prepared/standard-input.json', JSON.stringify(input, null, 2) + '\n');
fs.writeFileSync('prepared/abi.json', JSON.stringify(artifact.abi, null, 2) + '\n');
console.log(JSON.stringify({ ...report, transaction: 'prepared/deployment.json' }, null, 2));
