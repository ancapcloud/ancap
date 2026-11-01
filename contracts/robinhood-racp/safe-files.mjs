// Descriptor-based local files: reject symlinks and non-regular files.
import fs from 'node:fs';

export function readText(path) {
  const fd = fs.openSync(path, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0) | (fs.constants.O_NONBLOCK ?? 0));
  try {
    const opened = fs.fstatSync(fd);
    const named = fs.lstatSync(path);
    if (!opened.isFile() || named.isSymbolicLink() || opened.ino !== named.ino || opened.dev !== named.dev) {
      throw new Error('Expected the same regular file');
    }
    return fs.readFileSync(fd, 'utf8');
  } finally { fs.closeSync(fd); }
}

export function readOptionalJson(path) {
  try { return JSON.parse(readText(path)); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

export function writeJson(path, value, { exclusive = false } = {}) {
  const flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | (fs.constants.O_NOFOLLOW ?? 0)
    | (fs.constants.O_NONBLOCK ?? 0) | (exclusive ? fs.constants.O_EXCL : 0);
  const fd = fs.openSync(path, flags, 0o600);
  try {
    const opened = fs.fstatSync(fd);
    const named = fs.lstatSync(path);
    if (!opened.isFile() || named.isSymbolicLink() || opened.ino !== named.ino || opened.dev !== named.dev) {
      throw new Error('Expected the same regular file');
    }
    fs.ftruncateSync(fd, 0);
    fs.writeFileSync(fd, JSON.stringify(value, null, 2) + '\n');
    fs.fsyncSync(fd);
  } finally { fs.closeSync(fd); }
}

export function getOrCreateSecret(path, create) {
  try { return readText(path).trim(); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  try { fs.writeFileSync(path, create() + '\n', { flag: 'wx', mode: 0o600 }); }
  catch (error) { if (error.code !== 'EEXIST') throw error; }
  return readText(path).trim();
}
