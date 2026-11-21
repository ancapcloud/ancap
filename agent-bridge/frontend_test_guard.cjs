// Compare syntax, not diff lines: preserve old test bodies while allowing additions.
const fs = require('node:fs');
const path = require('node:path');
const input = require.main===module ? JSON.parse(fs.readFileSync(0,'utf8')) : null;
const ts = require(input?.typescript ?? path.resolve(__dirname, '../frontend-app/node_modules/typescript'));

function parse(text) {
  const file = ts.createSourceFile('tests.tsx', text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  if (file.parseDiagnostics.length) throw new Error('Frontend regression has invalid syntax');
  return file;
}
function children(node) { const result=[]; ts.forEachChild(node, n => {result.push(n);}); return result; }
function exact(a,b) {
  if (a.kind !== b.kind) return false;
  const left=children(a), right=children(b);
  if (!left.length && !right.length) return (a.text ?? a.getText()) === (b.text ?? b.getText());
  return left.length === right.length && left.every((n,i) => exact(n,right[i]));
}
function subsequence(oldNodes,newNodes,compare) {
  let cursor=0;
  for (const old of oldNodes) {
    while (cursor<newNodes.length && !compare(old,newNodes[cursor])) cursor++;
    if (cursor===newNodes.length) return false;
    cursor++;
  }
  return true;
}
function testRoot(node) {
  if (ts.isIdentifier(node)) return ['describe','it','test'].includes(node.text);
  if (ts.isPropertyAccessExpression(node)) return testRoot(node.expression);
  if (ts.isCallExpression(node)) return testRoot(node.expression);
  return false;
}
function matchExpression(a,b) {
  if (!ts.isCallExpression(a) || !ts.isCallExpression(b) || !testRoot(a.expression) || !testRoot(b.expression)) return exact(a,b);
  // Runner modifiers must remain unchanged: never accept .skip/.todo/.only.
  if (!matchRunner(a.expression,b.expression) || a.arguments.length!==b.arguments.length) return false;
  return a.arguments.every((arg,i) => {
    const other=b.arguments[i];
    if (i===0 && ts.isStringLiteral(arg) && ts.isStringLiteral(other)) return true; // descriptive title
    if (ts.isArrowFunction(arg) || ts.isFunctionExpression(arg)) {
      if (arg.kind!==other.kind) return false;
      const left=children(arg), right=children(other);
      return left.length===right.length && left.every((n,j) => ts.isBlock(n) && ts.isBlock(right[j])
        ? subsequence(n.statements,right[j].statements,matchStatement) : exact(n,right[j]));
    }
    return exact(arg,other);
  });
}
function matchRunner(a,b) {
  if (ts.isCallExpression(a) && ts.isCallExpression(b) && ts.isPropertyAccessExpression(a.expression)
      && a.expression.name.text==='each' && exact(a.expression,b.expression) && a.arguments.length===1 && b.arguments.length===1
      && ts.isArrayLiteralExpression(a.arguments[0]) && ts.isArrayLiteralExpression(b.arguments[0])) {
    return subsequence(a.arguments[0].elements,b.arguments[0].elements,exact);
  }
  return exact(a,b);
}
function matchStatement(a,b) {
  if (ts.isExpressionStatement(a) && ts.isExpressionStatement(b)) return matchExpression(a.expression,b.expression);
  return exact(a,b);
}
function preserved(before,after) {
  return subsequence(parse(before).statements,parse(after).statements,matchStatement);
}
module.exports={preserved};
if (require.main===module) {
  try {process.stdout.write(JSON.stringify({preserved:preserved(input.before,input.after)}));}
  catch (error) {process.stderr.write(error.message);process.exitCode=1;}
}
