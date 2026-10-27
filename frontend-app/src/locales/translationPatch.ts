type PatchTree = { [key: string]: string | PatchTree };

/** Apply an intentional leaf override without replacing domain-module objects. */
export function applyTranslationPatch(root: PatchTree, path: string, value: string): void {
  const parts = path.split(".");
  for (const part of parts) {
    if (!part || part === "__proto__" || part === "constructor" || part === "prototype") {
      throw new Error("Unsafe translation path");
    }
  }
  let current = root;
  for (let index = 0; index < parts.length - 1; index++) {
    const part = parts[index]!;
    if (part === "__proto__" || part === "constructor" || part === "prototype") {
      throw new Error("Unsafe translation path");
    }
    if (typeof current[part] !== "object" || current[part] === null) current[part] = {};
    current = current[part] as PatchTree;
  }
  const leaf = parts[parts.length - 1]!;
  if (leaf === "__proto__" || leaf === "constructor" || leaf === "prototype") {
    throw new Error("Unsafe translation path");
  }
  current[leaf] = value;
}
