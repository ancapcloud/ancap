import { beforeEach, describe, expect, it, vi } from "vitest";

const connect = vi.fn();
const getProvider = vi.fn();
const createEVMClient = vi.fn(async () => ({ connect, getProvider }));
const getPreferredEvmProvider = vi.fn();

vi.mock("@metamask/connect-evm", () => ({
  createEVMClient,
}));

vi.mock("@/lib/evmProvider", () => ({
  getPreferredEvmProvider,
}));

describe("resolveEvmProvider", () => {
  beforeEach(() => {
    vi.resetModules();
    connect.mockReset();
    getProvider.mockReset();
    createEVMClient.mockClear();
    getPreferredEvmProvider.mockReset();
    Object.defineProperty(globalThis, "window", {
      value: { location: { origin: "https://ancap.cloud" } },
      configurable: true,
      writable: true,
    });
  });

  it("returns an injected provider without opening MetaMask Connect", async () => {
    const injected = { request: vi.fn() };
    getPreferredEvmProvider.mockReturnValue(injected);
    const { resolveEvmProvider } = await import("../metamaskConnect");
    await expect(resolveEvmProvider(["0x1237"])).resolves.toBe(injected);
    expect(createEVMClient).not.toHaveBeenCalled();
  });

  it("deeplinks MetaMask Connect when Chrome has no injected ethereum", async () => {
    getPreferredEvmProvider.mockReturnValue(undefined);
    const connected = { request: vi.fn() };
    getProvider.mockReturnValue(connected);
    connect.mockResolvedValue({ accounts: ["0x1"], chainId: "0x1237" });
    const { resolveEvmProvider } = await import("../metamaskConnect");
    await expect(resolveEvmProvider(["0x1237"])).resolves.toBe(connected);
    expect(createEVMClient).toHaveBeenCalled();
    expect(connect).toHaveBeenCalledWith({ chainIds: ["0x1237"] });
  });
});
