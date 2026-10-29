import fs from 'node:fs';
import path from 'node:path';
import solc from 'solc';

export function compile() {
  const input = {
    language: 'Solidity',
    sources: { 'src/RobinhoodACP.sol': { content: fs.readFileSync('src/RobinhoodACP.sol', 'utf8') } },
    settings: {
      optimizer: { enabled: true, runs: 200 }, evmVersion: 'paris',
      outputSelection: { '*': { '*': ['abi', 'evm.bytecode', 'evm.deployedBytecode'] } },
    },
  };
  const output = JSON.parse(solc.compile(JSON.stringify(input), {
    import: file => {
      const target = path.resolve('node_modules', file);
      if (!target.startsWith(path.resolve('node_modules') + path.sep)) return { error: 'Invalid import' };
      try {
        const contents = fs.readFileSync(target, 'utf8');
        input.sources[file] = { content: contents };
        return { contents };
      }
      catch { return { error: `Missing import: ${file}` }; }
    },
  }));
  const errors = (output.errors ?? []).filter(e => e.severity === 'error');
  if (errors.length) throw new Error(errors.map(e => e.formattedMessage).join('\n'));
  return { input, artifact: output.contracts['src/RobinhoodACP.sol'].RobinhoodACP };
}
