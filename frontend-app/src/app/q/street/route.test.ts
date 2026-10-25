import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { GET, HEAD } from "./route";

describe("street QR entry", () => {
  it("redirects to a fixed counter endpoint without caching", () => {
    const response = GET(new NextRequest("https://ancap.cloud/q/street?url=https://evil.example"));
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://api.ancap.cloud/v1/qr/street");
    expect(response.headers.get("cache-control")).toContain("no-store");
    expect(response.headers.get("x-robots-tag")).toContain("noindex");
  });
  it("preserves HEAD for non-counting link checks", () => {
    expect(HEAD(new NextRequest("https://ancap.cloud/q/street", {method:"HEAD"})).status).toBe(307);
  });
});
