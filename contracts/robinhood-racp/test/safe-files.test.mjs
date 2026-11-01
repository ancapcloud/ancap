import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { readText, readOptionalJson, writeJson, getOrCreateSecret } from '../safe-files.mjs';

test('exclusive journals preserve existing transaction intent and update on descriptor', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ancap-journal-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'journal.json');
  assert.equal(readOptionalJson(file), null);
  writeJson(file, { transaction: 'first' }, { exclusive: true });
  assert.throws(() => writeJson(file, { transaction: 'second' }, { exclusive: true }), { code: 'EEXIST' });
  assert.deepEqual(readOptionalJson(file), { transaction: 'first' });
  writeJson(file, { status: 'confirmed' });
  assert.deepEqual(readOptionalJson(file), { status: 'confirmed' });
});

test('secret generation preserves existing key', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ancap-secret-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'key');
  assert.equal(getOrCreateSecret(file, () => 'first'), 'first');
  assert.equal(getOrCreateSecret(file, () => { throw new Error('must not rotate'); }), 'first');
});

test('symbolic links cannot read or overwrite journal targets', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ancap-link-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const target = path.join(dir, 'target');
  const link = path.join(dir, 'link');
  fs.writeFileSync(target, 'preserve');
  try { fs.symlinkSync(target, link); }
  catch (error) { if (error.code === 'EPERM') return t.skip('Windows symlink privilege unavailable'); throw error; }
  assert.throws(() => readText(link));
  assert.throws(() => writeJson(link, { overwrite: true }));
  assert.equal(fs.readFileSync(target, 'utf8'), 'preserve');
});
