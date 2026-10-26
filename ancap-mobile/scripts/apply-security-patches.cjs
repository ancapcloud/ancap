const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

// Backport digitalbazaar/forge#1152 while GHSA-86w9-cpqp-85rv has no npm release.
// Never change the package version or suppress the registry advisory.
const root = path.dirname(require.resolve('node-forge/package.json'));
const metadata = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const file = path.join(root, 'lib/rsa.js');
const before = '            obj.value.length !== 2) {';
const after = "            obj.value.length !== 2 ||\n            obj.value[0].value.length !==\n              (('parameters' in capture) ? 2 : 1)) {";
let source = fs.readFileSync(file, 'utf8');
const hash = (text) => crypto.createHash('sha256').update(text).digest('hex');
const originalHash = 'fd4740238145ec26470eb3f06a627c72039538ce1307dbdce40521f94dfd0a50';
const patchedHash = 'c9b1e3799e230528b6d6815c1f6cd3c6058b9d45975264b55d995abb976589af';
if (![originalHash, patchedHash].includes(hash(source))) {
  throw new Error('Unexpected Forge source hash; review the backport instead of patching unknown code.');
}
if (metadata.version !== '1.4.0') {
  throw new Error('Review and remove the Forge backport before changing node-forge version.');
}
if (!source.includes(after)) {
  if (source.split(before).length !== 2) throw new Error('Unexpected Forge source; security patch was not applied.');
  source = source.replace(before, after);
  fs.writeFileSync(file, source);
}
if (hash(source) !== patchedHash) throw new Error('Forge security backport integrity check failed.');
console.log(`Forge CVE-2026-85393 backport verified (${patchedHash}).`);
