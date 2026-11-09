import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {evaluate} from './index.js';

const cwd=fs.mkdtempSync(path.join(os.tmpdir(),'ancap-scope-'));
try {
  fs.mkdirSync(path.join(cwd,'frontend-app/src'),{recursive:true});
  const spec={cwd,sources:['frontend-app/src/source.ts'],outputs:['frontend-app/src/output.ts']};
  const event=(toolName,p)=>({toolName,params:{path:p}});
  assert.equal(evaluate(event('write','src/output.ts'),spec),undefined);
  assert.equal(evaluate({toolName:'edit',params:{path:'src/output.ts',edits:[{oldText:'same',newText:'same'}]}},spec).block,true);
  assert.equal(evaluate({toolName:'edit',params:{path:'src/output.ts',edits:[{oldText:'before',newText:'after'}]}},spec),undefined);
  assert.deepEqual(evaluate(event('read','src/source.ts'),spec).params,{path:'src/source.ts',offset:1,limit:400});
  assert.equal(evaluate({toolName:'read',params:{path:'src/source.ts',offset:140,limit:5}},spec).params.offset,1);
  for (const e of [event('write','src/source.ts'),event('write','src/other.ts'),event('write','../../outside.ts'),event('edit','.env'),event('exec','src/output.ts')]) {
    assert.equal(evaluate(e,spec).block,true);
  }
  assert.equal(evaluate(event('write','src/output.ts'),null).block,true);
  assert.equal(evaluate(event('write','src/output.ts'),spec),undefined);
  assert.equal(fs.existsSync(path.join(cwd,'frontend-app/src/output.ts')),false);
  console.log('OpenClaw task scope: allowed operations delegate; forbidden operations blocked before writes.');
} finally {
  fs.rmSync(cwd,{recursive:true,force:true});
}
