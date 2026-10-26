const r = require("./tmp-i18n-audit.json");
for (const [loc, v] of Object.entries(r.locales)) {
  console.log(loc, v.sameAsEn.join(", "));
}
