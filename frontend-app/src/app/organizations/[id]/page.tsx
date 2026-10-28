"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useAuth } from "@/components/AuthProvider";
import { organizations } from "@/lib/api";

type Org = {
  id: string;
  name: string;
  slug: string;
  description?: string;
  billing_wallet_address?: string;
  member_count: number;
  user_role?: string;
  created_at?: string;
};

type Member = {
  user_id: string;
  role: string;
  joined_at?: string;
  user_email?: string;
};

export default function OrganizationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orgId = params?.id as string;
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [org, setOrg] = useState<Org | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [memberRoleDrafts, setMemberRoleDrafts] = useState<Record<string, string>>({});
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [billingWallet, setBillingWallet] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [addingMember, setAddingMember] = useState(false);
  const [savingWallet, setSavingWallet] = useState(false);
  const [deletingOrg, setDeletingOrg] = useState(false);
  const [memberActionKey, setMemberActionKey] = useState<string | null>(null);

  const canManageMembers = org?.user_role === "admin" || org?.user_role === "owner";
  const canEditWallet = canManageMembers;
  const canDeleteOrganization = org?.user_role === "owner";

  const load = useCallback(async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const [orgData, memberData] = await Promise.all([
        organizations.get(orgId),
        organizations.listMembers(orgId),
      ]);
      const memberList = memberData || [];
      setOrg(orgData);
      setMembers(memberList);
      setMemberRoleDrafts(
        Object.fromEntries(memberList.map((member: Member) => [member.user_id, member.role]))
      );
      setBillingWallet(orgData?.billing_wallet_address || "");
      setError("");
    } catch (e: any) {
      setError(e?.message || "Failed to load organization");
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated || !orgId) return;
    void load();
  }, [isAuthenticated, orgId, load]);

  async function addMember(e: React.FormEvent) {
    e.preventDefault();
    setAddingMember(true);
    setError("");
    setNotice("");
    try {
      await organizations.addMember(orgId, { email, role });
      setEmail("");
      setRole("member");
      setNotice("Member added.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Failed to add member");
    } finally {
      setAddingMember(false);
    }
  }

  async function saveWallet() {
    setSavingWallet(true);
    setError("");
    setNotice("");
    try {
      await organizations.update(orgId, { billing_wallet_address: billingWallet || null });
      setNotice("Billing wallet updated.");
      await load();
    } catch (e: any) {
      setError(e?.message || "Failed to update billing wallet");
    } finally {
      setSavingWallet(false);
    }
  }

  async function saveMemberRole(member: Member) {
    const nextRole = memberRoleDrafts[member.user_id] || member.role;
    if (nextRole === member.role) return;
    setMemberActionKey(`role:${member.user_id}`);
    setError("");
    setNotice("");
    try {
      await organizations.updateMemberRole(orgId, member.user_id, { role: nextRole });
      setNotice(`Updated role for ${member.user_email || member.user_id}.`);
      await load();
    } catch (e: any) {
      setError(e?.message || "Failed to update member role");
    } finally {
      setMemberActionKey(null);
    }
  }

  async function removeMember(member: Member) {
    const selfRemove = member.user_id === user?.id;
    const label = selfRemove ? "leave this organization" : `remove ${member.user_email || member.user_id}`;
    if (!window.confirm(`Are you sure you want to ${label}?`)) {
      return;
    }

    setMemberActionKey(`remove:${member.user_id}`);
    setError("");
    setNotice("");
    try {
      await organizations.removeMember(orgId, member.user_id);
      if (selfRemove) {
        router.push("/organizations");
        return;
      }
      setNotice(`Removed ${member.user_email || member.user_id}.`);
      await load();
    } catch (e: any) {
      setError(e?.message || "Failed to remove member");
    } finally {
      setMemberActionKey(null);
    }
  }

  async function deleteOrganization() {
    if (!canDeleteOrganization || !org) return;
    if (!window.confirm(`Delete organization ${org.name}? This cannot be undone.`)) {
      return;
    }

    setDeletingOrg(true);
    setError("");
    setNotice("");
    try {
      await organizations.remove(org.id);
      router.push("/organizations");
    } catch (e: any) {
      setError(e?.message || "Failed to delete organization");
    } finally {
      setDeletingOrg(false);
    }
  }

  if (authLoading || !isAuthenticated) return null;

  return (
    <>
      <Navigation />
      <main className="relative z-10 mx-auto max-w-6xl space-y-6 px-4 py-8">
        {error && <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>}
        {notice && <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">{notice}</div>}
        {loading ? (
          <div className="py-20 text-center opacity-60">Loading…</div>
        ) : org ? (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold">{org.name}</h1>
                <p className="mt-1 text-sm opacity-60">{org.slug} · role: {org.user_role || "member"}</p>
                {org.description && <p className="mt-3 max-w-3xl text-sm opacity-75">{org.description}</p>}
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => void load()}
                  disabled={deletingOrg}
                  className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Refresh
                </button>
                {canDeleteOrganization && (
                  <button
                    onClick={deleteOrganization}
                    disabled={deletingOrg}
                    className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {deletingOrg ? "Deleting…" : "Delete organization"}
                  </button>
                )}
              </div>
            </div>

            <section className="grid gap-6 lg:grid-cols-[420px_1fr]">
              <div className="space-y-6">
                <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 space-y-4">
                  <div>
                    <h2 className="text-lg font-semibold">Billing wallet</h2>
                    <p className="mt-1 text-xs opacity-60">Route organization-level billing and payouts to a shared ACP-compatible wallet.</p>
                  </div>
                  <input
                    value={billingWallet}
                    onChange={(e) => setBillingWallet(e.target.value)}
                    placeholder="0x... or billing wallet address"
                    disabled={!canEditWallet || savingWallet}
                    className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  {canEditWallet ? (
                    <button
                      onClick={saveWallet}
                      disabled={savingWallet}
                      className="rounded-lg border border-[var(--accent)] bg-[var(--accent)]/10 px-4 py-2 text-sm font-medium text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {savingWallet ? "Saving…" : "Save wallet"}
                    </button>
                  ) : (
                    <div className="text-xs opacity-50">Only organization admins and owners can edit the billing wallet.</div>
                  )}
                </div>

                <form onSubmit={addMember} className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5 space-y-4">
                  <div>
                    <h2 className="text-lg font-semibold">Add member</h2>
                    <p className="mt-1 text-xs opacity-60">Invite existing ANCAP users into this organization with scoped roles.</p>
                  </div>
                  <input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="member@email"
                    disabled={!canManageMembers || addingMember}
                    className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    disabled={!canManageMembers || addingMember}
                    className="w-full rounded-lg border border-[var(--border)] bg-transparent px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="viewer">viewer</option>
                    <option value="member">member</option>
                    <option value="admin">admin</option>
                  </select>
                  {canManageMembers ? (
                    <button
                      disabled={addingMember}
                      className="rounded-lg border border-[var(--accent)] bg-[var(--accent)]/10 px-4 py-2 text-sm font-medium text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {addingMember ? "Adding…" : "Invite/add member"}
                    </button>
                  ) : (
                    <div className="text-xs opacity-50">Only organization admins and owners can add members.</div>
                  )}
                </form>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-5">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">Members</h2>
                    <p className="mt-1 text-xs opacity-50">{members.length} total · roles and membership are enforced server-side.</p>
                  </div>
                  <button onClick={() => void load()} className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs">
                    Refresh
                  </button>
                </div>
                {members.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-[var(--border)] px-4 py-10 text-center text-sm opacity-50">No members found.</div>
                ) : (
                  <div className="space-y-3">
                    {members.map((member) => {
                      const draftRole = memberRoleDrafts[member.user_id] || member.role;
                      const roleChanged = draftRole !== member.role;
                      const canEditRole = canManageMembers && member.role !== "owner";
                      const canRemoveMember = member.role !== "owner" && (canManageMembers || member.user_id === user?.id);
                      const isBusy = memberActionKey === `role:${member.user_id}` || memberActionKey === `remove:${member.user_id}`;

                      return (
                        <div key={member.user_id} className="rounded-xl border border-[var(--border)] p-4">
                          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                            <div className="min-w-0">
                              <div className="font-medium">{member.user_email || member.user_id}</div>
                              <div className="text-xs opacity-50">
                                joined {member.joined_at ? new Date(member.joined_at).toLocaleString() : "unknown"}
                                {member.user_id === user?.id ? " · you" : ""}
                              </div>
                            </div>

                            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                              {canEditRole ? (
                                <>
                                  <select
                                    value={draftRole}
                                    onChange={(e) =>
                                      setMemberRoleDrafts((current) => ({
                                        ...current,
                                        [member.user_id]: e.target.value,
                                      }))
                                    }
                                    disabled={isBusy}
                                    className="rounded-lg border border-[var(--border)] bg-transparent px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    <option value="viewer">viewer</option>
                                    <option value="member">member</option>
                                    <option value="admin">admin</option>
                                  </select>
                                  <button
                                    onClick={() => void saveMemberRole(member)}
                                    disabled={!roleChanged || isBusy}
                                    className="rounded-lg border border-[var(--accent)] bg-[var(--accent)]/10 px-3 py-2 text-sm font-medium text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    {memberActionKey === `role:${member.user_id}` ? "Saving…" : "Save role"}
                                  </button>
                                </>
                              ) : (
                                <div className="rounded-full bg-white/5 px-3 py-1 text-xs opacity-70">{member.role}</div>
                              )}

                              {canRemoveMember && (
                                <button
                                  onClick={() => void removeMember(member)}
                                  disabled={isBusy}
                                  className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  {memberActionKey === `remove:${member.user_id}`
                                    ? "Removing…"
                                    : member.user_id === user?.id
                                      ? "Leave"
                                      : "Remove"}
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </section>
          </>
        ) : null}
      </main>
    </>
  );
}
