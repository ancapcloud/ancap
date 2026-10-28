const assert = require('node:assert/strict');
const { test } = require('node:test');
const path = require('node:path');
const merge = require('deepmerge');
const attack = () => JSON.parse('{"__proto__":{"isAdmin":true}}');

function clean(value) {
  assert.equal(Object.getPrototypeOf(value), Object.prototype);
  assert.equal(value.isAdmin, undefined);
  assert.equal({}.isAdmin, undefined);
}

test('null-prototype target cannot poison the returned object', () => {
  clean(merge(Object.create(null), attack()));
});
test('nested null placeholders cannot acquire injected prototypes', () => {
  const result = merge({ session: null }, { session: attack() });
  clean(result); clean(result.session);
});
test('target own prototype keys are rejected before target copy', () => {
  clean(merge(attack(), { useful: true }));
  clean(merge(attack(), attack()));
});
test('constructor/prototype keys are blocked at every merged depth', () => {
  const result = merge({}, JSON.parse('{"constructor":{"prototype":{"isAdmin":true}},"safe":{"prototype":{"isAdmin":true},"value":1}}'));
  assert.equal(Object.hasOwn(result, 'constructor'), false);
  assert.equal(Object.hasOwn(result.safe, 'prototype'), false);
  assert.equal(result.safe.value, 1); clean(result); clean(result.safe);
});
test('throwing proxy safety checks fail closed', () => {
  const target = new Proxy({}, { has() { throw new Error('membership unavailable'); } });
  assert.throws(() => merge(target, { safe: true }), /membership unavailable/);
});
test('normal nested data, arrays, symbols and immutable inputs remain compatible', () => {
  const symbol = Symbol('metadata');
  const left = Object.freeze({ nested: { a: 1 }, list: [1], [symbol]: 'left' });
  const right = Object.freeze({ nested: { b: 2 }, list: [2], [symbol]: 'right' });
  const result = merge(left, right);
  assert.deepEqual(result.nested, { a: 1, b: 2 });
  assert.deepEqual(result.list, [1, 2]); assert.equal(result[symbol], 'right');
  assert.notEqual(result.nested, left.nested); assert.deepEqual(left.list, [1]);
});
test('custom arrayMerge, customMerge, clone=false and merge.all remain compatible', () => {
  assert.deepEqual(merge({ a: [1] }, { a: [2] }, { arrayMerge: (_a, b) => b }), { a: [2] });
  assert.deepEqual(merge({ a: { x: 1 } }, { a: { x: 2 } }, { customMerge: key => key === 'a' ? (_a, b) => b : undefined }), { a: { x: 2 } });
  const nested = { x: 1 }; assert.equal(merge({}, { nested }, { clone: false }).nested, nested);
  assert.deepEqual(merge.all([{ a: 1 }, { b: 2 }]), { a: 1, b: 2 });
  assert.throws(() => merge.all(null), /array/);
  clean(merge.all([Object.create(null), attack()]));
});
test('Expo resolves the reviewed local fork through the installed override', () => {
  const expoRoot = path.dirname(require.resolve('@expo/config/package.json'));
  assert.equal(require.resolve('deepmerge', { paths: [expoRoot] }), require.resolve('deepmerge'));
  assert.equal(require('deepmerge/package.json').name, '@ancap/deepmerge-safe');
});
