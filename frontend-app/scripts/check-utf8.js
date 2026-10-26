const fs = require("fs");
const s = fs.readFileSync("src/locales/translations.ts", "utf8");
const m = s.match(/ru:\s*\{[\s\S]*?product:\s*"([^"]+)"/);
console.log("ru product:", m && m[1]);
const m2 = s.match(/"zh-Hant":\s*\{[\s\S]*?product:\s*"([^"]+)"/);
console.log("zh product:", m2 && m2[1]);
console.log("has cyrillic", /[А-Яа-яЁё]/.test(s));
console.log("has cjk", /[\u4e00-\u9fff]/.test(s));
console.log("len", s.length);
