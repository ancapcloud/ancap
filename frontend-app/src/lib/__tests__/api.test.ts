import { describe, it, expect, vi } from 'vitest';
import { auth, api, bridgeRail, formatNetworkError, organizations, payments, subscriptions, walletAcp, webhooks } from '../api';

describe('API Client', () => {
  it('should have correct base URL', () => {
    expect(api).toBeDefined();
  });

  it('maps AbortSignal timeout to a readable chain-write message', () => {
    const err = new DOMException('signal timed out', 'TimeoutError');
    const mapped = formatNetworkError(err);
    expect(mapped.message.toLowerCase()).toContain('timed out');
    expect(mapped.message.toLowerCase()).toContain('acp');
  });

  it('should have agents methods', () => {
    expect(api.agents).toBeDefined();
    expect(api.agents.list).toBeDefined();
    expect(api.agents.get).toBeDefined();
  });

  it('should have strategies methods', () => {
    expect(api.strategies).toBeDefined();
    expect(api.strategies.list).toBeDefined();
    expect(api.strategies.get).toBeDefined();
  });

  it('should have runs methods', () => {
    expect(api.runs).toBeDefined();
    expect(api.runs.list).toBeDefined();
    expect(api.runs.get).toBeDefined();
  });

  it('should expose bridgeRail client', () => {
    expect(bridgeRail).toBeDefined();
    expect(bridgeRail.status).toBeDefined();
    expect(bridgeRail.reserveSummary).toBeDefined();
    expect(bridgeRail.createIntentAcpToBsc).toBeDefined();
    expect(bridgeRail.listMyIntents).toBeDefined();
  });

  it('should expose organization client helpers', () => {
    expect(organizations).toBeDefined();
    expect(organizations.list).toBeDefined();
    expect(organizations.get).toBeDefined();
    expect(organizations.create).toBeDefined();
    expect(organizations.updateMemberRole).toBeDefined();
    expect(organizations.removeMember).toBeDefined();
    expect(organizations.remove).toBeDefined();
  });

  it('should expose webhook client helpers', () => {
    expect(webhooks).toBeDefined();
    expect(webhooks.list).toBeDefined();
    expect(webhooks.create).toBeDefined();
    expect(webhooks.rotateSecret).toBeDefined();
    expect(webhooks.sendTest).toBeDefined();
    expect(webhooks.remove).toBeDefined();
  });

  it('should expose Stripe payment client helpers', () => {
    expect(payments).toBeDefined();
    expect(payments.createStripeIntent).toBeDefined();
    expect(payments.getStripeIntent).toBeDefined();
    expect(payments.getStripeStatus).toBeDefined();
    expect(payments.listMethods).toBeDefined();
    expect(payments.removeMethod).toBeDefined();
    expect(payments.createRefundRequest).toBeDefined();
    expect(payments.listMyRefundRequests).toBeDefined();
    expect(payments.listRefundRequests).toBeDefined();
    expect(payments.approveRefundRequest).toBeDefined();
    expect(payments.rejectRefundRequest).toBeDefined();
  });

  it('should expose subscriptions client helpers', () => {
    expect(subscriptions).toBeDefined();
    expect(subscriptions.list).toBeDefined();
    expect(subscriptions.create).toBeDefined();
  });

  it('should expose public ACP transaction lookup client', () => {
    expect(walletAcp).toBeDefined();
    expect(walletAcp.getTransaction).toBeDefined();
  });

  it('should aggregate organization, payment, subscription, and webhook APIs', () => {
    expect(api.organizations).toBe(organizations);
    expect(api.payments).toBe(payments);
    expect(api.subscriptions).toBe(subscriptions);
    expect(api.webhooks).toBe(webhooks);
  });
});


describe('optional Turnstile on local login', () => {
  it.each(['', 'verified-widget-token'])('submits optional token correctly: %s', async (token) => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ access_token: 'local-test-only' }), {
      status: 200, headers: { 'content-type': 'application/json' },
    }));
    vi.stubGlobal('fetch', fetchMock);
    try {
      await auth.login('local@example.com', 'local-test-password', token);
      const submitted = JSON.parse(fetchMock.mock.calls[0][1].body);
      expect(submitted.email).toBe('local@example.com');
      expect(submitted.turnstile_token).toBe(token || undefined);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
