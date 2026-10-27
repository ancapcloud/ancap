const { test } = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const forge = require('node-forge');
const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const verifier = forge.pki.publicKeyFromPem(publicKey.export({ type: 'spki', format: 'pem' }));
const message = Buffer.from('ANCAP defensive RSA DigestAlgorithm regression');
const digest = crypto.createHash('sha256').update(message).digest();
const { asn1 } = forge;
const value = (type, constructed, data) => asn1.create(asn1.Class.UNIVERSAL, type, constructed, data);

function signature({ nullParameter = true, extra = false } = {}) {
  const algorithm = [value(asn1.Type.OID, false, asn1.oidToDer('2.16.840.1.101.3.4.2.1').getBytes())];
  if (nullParameter) algorithm.push(value(asn1.Type.NULL, false, ''));
  if (extra) algorithm.push(value(asn1.Type.OCTETSTRING, false, 'unconsumed nested child'));
  const der = Buffer.from(asn1.toDer(value(asn1.Type.SEQUENCE, true, [
    value(asn1.Type.SEQUENCE, true, algorithm),
    value(asn1.Type.OCTETSTRING, false, digest.toString('binary')),
  ])).getBytes(), 'binary');
  const block = Buffer.concat([Buffer.from([0, 1]), Buffer.alloc(256 - der.length - 3, 255), Buffer.from([0]), der]);
  return crypto.privateEncrypt({ key: privateKey, padding: crypto.constants.RSA_NO_PADDING }, block);
}

test('valid SHA-256 signatures still verify', () => {
  const signed = crypto.sign('sha256', message, privateKey);
  assert.equal(verifier.verify(digest.toString('binary'), signed.toString('binary')), true);
});
test('permitted absent SHA-256 NULL parameter still verifies', () => {
  assert.equal(verifier.verify(digest.toString('binary'), signature({ nullParameter: false }).toString('binary')), true);
});
for (const nullParameter of [true, false]) {
  test(`rejects nested DigestAlgorithm garbage (NULL=${nullParameter})`, () => {
    const signed = signature({ nullParameter, extra: true });
    assert.equal(crypto.verify('sha256', message, publicKey, signed), false);
    assert.throws(() => verifier.verify(digest.toString('binary'), signed.toString('binary')), /DigestInfo/);
  });
}
const path = require('node:path');
const cliRoot = path.dirname(require.resolve('@expo/cli/package.json', { paths: [path.dirname(require.resolve('expo/package.json'))] }));
const { PluginSchema, DevToolsPluginOutputSchema } = require(path.join(cliRoot, 'build/src/start/server/DevToolsPlugin.schema.js'));
const { createMCPDevToolsExtensionSchema } = require(path.join(cliRoot, 'build/src/start/server/createMCPDevToolsExtensionSchema.js'));

test('Expo CLI plugin schemas remain compatible with patched Zod 4', () => {
  const plugin = PluginSchema.parse({ packageName: 'ancap-test', packageRoot: '/tmp/ancap', cliExtensions: {
    description: 'local test', entryPoint: './test.js', commands: [{ name: 'status', title: 'Status', environments: ['cli', 'mcp'],
      parameters: [{ name: 'verbose', type: 'confirm' }] }],
  } });
  const schema = createMCPDevToolsExtensionSchema(plugin);
  assert.equal(schema.safeParse({ command: 'status', verbose: true }).success, true);
  assert.equal(schema.safeParse({ command: 'other' }).success, false);
  assert.equal(schema.safeParse({ command: 'status', verbose: 'yes' }).success, false);
  assert.equal(schema.safeParse({ command: 'status', unexpected: true }).success, false);
  assert.equal(DevToolsPluginOutputSchema.safeParse([{ type: 'text', text: 'ok', level: 'info' }]).success, true);
  assert.equal(DevToolsPluginOutputSchema.safeParse([{ type: 'image', url: 'not-a-url', text: 'bad' }]).success, false);
});
