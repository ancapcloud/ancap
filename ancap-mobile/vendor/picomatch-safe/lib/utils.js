/*global navigator*/
'use strict';

const {
  REGEX_BACKSLASH,
  REGEX_SPECIAL_CHARS,
  REGEX_SPECIAL_CHARS_GLOBAL
} = require('./constants');

exports.isObject = val => val !== null && typeof val === 'object' && !Array.isArray(val);
exports.hasRegexChars = str => REGEX_SPECIAL_CHARS.test(str);
exports.isRegexChar = str => str.length === 1 && exports.hasRegexChars(str);
exports.escapeRegex = str => str.replace(REGEX_SPECIAL_CHARS_GLOBAL, '\\$1');
exports.toPosixSlashes = str => str.replace(REGEX_BACKSLASH, '/');

exports.isWindows = () => {
  if (typeof navigator !== 'undefined' && navigator.platform) {
    const platform = navigator.platform.toLowerCase();
    return platform === 'win32' || platform === 'windows';
  }

  if (typeof process !== 'undefined' && process.platform) {
    return process.platform === 'win32';
  }

  return false;
};

const isLineTerminator = code => code === 10 || code === 13 || code === 0x2028 || code === 0x2029;

exports.removeBackslashes = str => {
  // Preserve the original bracket/line-terminator rules without restarting
  // a lazy bracket regexp at every unmatched '[' (quadratic on hostile input).
  const closeAt = new Int32Array(str.length);
  let nearest = -1;
  let second = -1;
  let nextLine = str.length;
  for (let i = str.length - 1; i >= 0; i--) {
    if (str[i] === ']' && str[i - 1] !== '\\') {
      second = nearest;
      nearest = i;
    }
    if (isLineTerminator(str.charCodeAt(i))) nextLine = i;
    if (str[i] === '[') {
      const close = nearest === i + 1 ? second : nearest;
      if (close >= i + 2 && nextLine >= close - 1) closeAt[i] = close;
    }
  }
  const parts = [];
  let start = 0;
  for (let i = 0; i < str.length; i++) {
    if (str[i] === '[' && closeAt[i] !== 0) {
      i = closeAt[i];
    } else if (str[i] === '\\' && i + 1 < str.length && !isLineTerminator(str.charCodeAt(i + 1))) {
      parts.push(str.slice(start, i));
      start = i + 1;
    }
  }
  parts.push(str.slice(start));
  return parts.join('');
};

exports.escapeLast = (input, char, lastIdx) => {
  const idx = input.lastIndexOf(char, lastIdx);
  if (idx === -1) return input;
  if (input[idx - 1] === '\\') return exports.escapeLast(input, char, idx - 1);
  return `${input.slice(0, idx)}\\${input.slice(idx)}`;
};

exports.removePrefix = (input, state = {}) => {
  let output = input;
  if (output.startsWith('./')) {
    output = output.slice(2);
    state.prefix = './';
  }
  return output;
};

exports.wrapOutput = (input, state = {}, options = {}) => {
  const prepend = options.contains ? '' : '^';
  const append = options.contains ? '' : '$';

  let output = `${prepend}(?:${input})${append}`;
  if (state.negated === true) {
    output = `(?:^(?!${output}).*$)`;
  }
  return output;
};

exports.basename = (path, { windows } = {}) => {
  const segs = path.split(windows ? /[\\/]/ : '/');
  const last = segs[segs.length - 1];

  if (last === '') {
    return segs[segs.length - 2];
  }

  return last;
};
