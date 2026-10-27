import { runInNewContext } from "node:vm";
import ts from "typescript";
import { describe, expect, it } from "vitest";
import { generateTranslationSource, setPath } from "./i18n-apply-fixes";
import { positioningByLang } from "../src/locales/positioning";
import { SUPPORTED_LANGUAGES, t } from "../src/locales/translations";

describe("translation regeneration", () => {
  it("preserves external positioning translations and the English fallback", () => {
    const source = generateTranslationSource();
    const js = ts.transpileModule(source, {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
    }).outputText;
    const output: { t?: typeof t; translations?: Record<string, Record<string, unknown>> } = {};
    runInNewContext(js, {
      exports: output,
      require: (name: string) => {
        if (name === "./positioning") return { positioningByLang };
        throw new Error(`Unexpected generated dependency: ${name}`);
      },
    });
    for (const lang of SUPPORTED_LANGUAGES) {
      expect(output.t!(lang, "positioning.investors")).toBe(t(lang, "positioning.investors"));
      expect(output.t!(lang, "positioning.investors")).not.toBe("positioning.investors");
    }
    output.translations!.en.regenerationFallback = "English fallback";
    expect(output.t!("ru", "regenerationFallback")).toBe("English fallback");
    expect(output.t!("en", "missing.key")).toBe("missing.key");
  });

  it.each(["__proto__.polluted", "constructor.prototype.polluted", "nav.__proto__.polluted", ".empty", "nav."])(
    "rejects unsafe path %s before mutating the tree", (path) => {
      const tree = {};
      expect(() => setPath(tree, path, "yes")).toThrow("Unsafe translation path");
      expect(tree).toEqual({});
      expect(Object.prototype).not.toHaveProperty("polluted");
    },
  );
});
