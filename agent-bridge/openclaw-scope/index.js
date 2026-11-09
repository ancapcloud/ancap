import fs from 'node:fs';
import path from 'node:path';

function canonical(value) {
  let current = path.resolve(value);
  const suffix = [];
  while (!fs.existsSync(current)) {
    const parent = path.dirname(current);
    if (parent === current) throw new Error('Invalid path');
    suffix.unshift(path.basename(current));
    current = parent;
  }
  return path.join(fs.realpathSync.native(current), ...suffix).toLowerCase();
}

export function evaluate(event, spec) {
  try {
    if (!['read', 'write', 'edit'].includes(event.toolName)) {
      return {block:true,blockReason:'Task scope permits only read/write/edit tools'};
    }
    if (!spec || !Array.isArray(spec.outputs) || !Array.isArray(spec.sources)) throw new Error('Missing task policy');
    const root = path.join(spec.cwd, 'frontend-app');
    const value = event.params.path ?? event.params.file_path;
    if (typeof value !== 'string') throw new Error('One explicit file path is required');
    const target = canonical(path.resolve(root, value));
    const allowed = event.toolName === 'read' ? [...spec.sources, ...spec.outputs] : spec.outputs;
    if (!allowed.some(p => canonical(path.resolve(spec.cwd, p)) === target)) throw new Error('File is outside the task allowlist');
    if (event.toolName === 'edit' && Array.isArray(event.params.edits) && event.params.edits.length &&
        event.params.edits.every(e => typeof e.oldText === 'string' && e.oldText === e.newText)) {
      return {block:true,blockReason:'No-op edit: oldText and newText are identical. Supply an actual change. Match a short unique prefix and avoid unescaped double quotes in JSON; use single-quoted JSX expressions when appropriate. Do not reread the file.'};
    }
    if (event.toolName === 'read') {
      // These tickets contain small text files. Five-line pagination repeatedly
      // re-ran local inference and exhausted the entire task timeout.
      return {params:{...event.params,offset:1,limit:400}};
    }
    return undefined;
  } catch (error) {
    return {block:true,blockReason:'ANCAP scope denied: '+error.message};
  }
}

export default {
  id:'ancap-scope',
  name:'ANCAP task file scope',
  register(api) {
    api.on('before_tool_call', event => {
      let spec;
      try {spec = JSON.parse(process.env.ANCAP_FILE_POLICY ?? 'null');} catch {}
      return evaluate(event,spec);
    });
  },
};
