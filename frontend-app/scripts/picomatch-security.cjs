const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const fork = path.join(root, 'vendor/picomatch-safe');
const pico = require(fork);

test('single-branch repeated extglobs cannot stall matching or alternate compile APIs', () => {
  const program = `
    const assert = require('node:assert/strict');
    const pico = require(${JSON.stringify(fork)});
    const posix = require(${JSON.stringify(path.join(fork, 'posix.js'))});
    const utils = require(${JSON.stringify(path.join(fork, 'lib/utils.js'))});
    const slash = String.fromCharCode(92);
    assert.equal(utils.removeBackslashes((slash + '[').repeat(1000000)), '['.repeat(1000000));
    assert.equal(pico.scan((slash + '[').repeat(30000), { unescape: true }).base, '['.repeat(30000));
    const input = 'a'.repeat(40) + '!';
    for (const glob of ['+(*a)', '*(*a)', '+(*)b', 'prefix/+(*a).js']) {
      const sample = glob.startsWith('prefix/') ? 'prefix/' + input + '.js' : input;
      for (const options of [{}, { fastpaths: false }, { maxExtglobRecursion: false }]) {
        assert.equal(pico(glob, options)(sample), false);
        assert.equal(posix(glob, options)(sample), false);
        assert.equal(pico.makeRe(glob, options).test(sample), false);
        assert.equal(new RegExp('^(?:' + pico.parse(glob, options).output + ')$').test(sample), false);
      }
    }
  `;
  const result = spawnSync(process.execPath, ['-e', program], { timeout: 15000, encoding: 'utf8' });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
});

test('ordinary build globs, alternatives, options and scan API remain compatible', () => {
  assert.equal(pico('src/**/*.{ts,tsx}')('src/lib/file.ts'), true);
  assert.equal(pico('src/**/*.{ts,tsx}')('src/file.js'), false);
  assert.equal(pico('**/*.ts')('.hidden.ts'), false);
  assert.equal(pico('**/*.ts', { dot: true })('.hidden.ts'), true);
  assert.equal(pico('**/*.ts', { ignore: '**/generated/**' })('src/generated/x.ts'), false);
  assert.equal(pico('+(foo|bar)')('foobar'), true);
  assert.equal(pico('@(a|b)')('b'), true);
  assert.equal(pico('!(a)')('b'), true);
  assert.equal(pico('?(*.js)')('file.js'), true);
  assert.equal(pico('+(*(a)|*(b))')('abba'), true);
  assert.equal(pico('+(*a)')('+(*a)'), true);
  assert.equal(pico.scan('src/**/*.ts').isGlob, true);
});

test('linear unescaping preserves bracket groups, trailing escapes and line terminators', () => {
  const utils = require(path.join(fork, 'lib/utils.js'));
  const slash = String.fromCharCode(92);
  const cases = [
    ['', ''], ['abc', 'abc'],
    ['foo' + slash + 'bar', 'foobar'],
    [slash + '[ab]', '[ab]'],
    ['[a' + slash + 'b]', '[a' + slash + 'b]'],
    ['[a' + slash + ']b]', '[a' + slash + ']b]'],
    ['[' + slash + ']', '[]'],
    ['[]' + slash + 'q', '[]q'],
    ['[][]' + slash + 'q', '[][]q'],
    [slash + '[', '['],
    ['[a' + slash, '[a' + slash],
    [slash + slash, slash],
    [slash + slash + 'x', 'x'],
  ];
  for (const code of [10, 13, 0x2028, 0x2029]) {
    const line = String.fromCharCode(code);
    cases.push(['a' + slash + line + 'b', 'a' + slash + line + 'b']);
    cases.push(['[' + line + 'a' + slash + 'b]', '[' + line + 'ab]']);
    cases.push(['[a' + line + ']' + slash + 'x', '[a' + line + ']x']);
  }
  for (const [input, expected] of cases) assert.equal(utils.removeBackslashes(input), expected, JSON.stringify(input));
});

test('installed build consumers resolve the local security fork', () => {
  assert.equal(require('picomatch/package.json').name, '@ancap/picomatch-safe');
  for (const consumer of ['vite', 'micromatch', 'jest-util', '@expo/config', '@expo/cli']) {
    let entry;
    try { entry = require.resolve(consumer); } catch (error) {
      if (error.code === 'MODULE_NOT_FOUND') continue;
      throw error;
    }
    const resolved = require.resolve('picomatch', { paths: [path.dirname(entry)] });
    assert.equal(fs.realpathSync(resolved), fs.realpathSync(require.resolve('picomatch')), consumer);
  }
});

test('the two project security forks have identical runtime source', t => {
  const otherProject = path.basename(root) === 'frontend-app' ? 'ancap-mobile' : 'frontend-app';
  const other = path.resolve(root, '..', otherProject, 'vendor/picomatch-safe');
  if (!fs.existsSync(other)) {
    t.skip('Counterpart is absent in a standalone package checkout');
    return;
  }
  for (const file of ['index.js', 'posix.js', 'lib/constants.js', 'lib/parse.js', 'lib/picomatch.js', 'lib/scan.js', 'lib/utils.js']) {
    assert.equal(fs.readFileSync(path.join(fork, file), 'utf8'), fs.readFileSync(path.join(other, file), 'utf8'), file);
  }
});
