"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { WorkflowFooter, presentationStyles as s } from "@/components/WorkflowPresentation";
import { economy, type EconomyProject } from "@/lib/api";
import { economyByLang } from "@/locales/economy";
import { testProjectsByLang } from "@/locales/testProjects";
import type { TestProjectId } from "@/lib/testProjects";

export default function EconomyProjectPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug ?? "";
  const { lang } = useLanguage();
  const t = testProjectsByLang[lang];
  const e = economyByLang[lang];
  const [project, setProject] = useState<EconomyProject | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    economy.getProject(slug)
      .then(result => {
        if (!cancelled) {
          setProject(result);
          setError(null);
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load project");
          setProject(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  const seed = project?.seed_key as TestProjectId | null | undefined;
  const local = seed && t.projects[seed] ? t.projects[seed] : null;
  const author = project?.owner_display_name || (project?.is_platform_seed ? "3n3rgy" : null);

  return (
    <div className={s.shell}>
      <Navigation />
      <main className={s.main}>
        <section className={s.section} style={{ borderTop: 0, paddingTop: 60 }}>
          <p className={s.eyebrow}>People + AI · /economy</p>
          {error && <p className={s.note} role="alert">{error}</p>}
          {project && (
            <>
              <span className={`${s.tag} ${s.core}`}>
                {project.is_platform_seed ? t.badge : project.kind} · {project.status}
              </span>
              <h1 className={s.title}>{project.title}</h1>
              {author && <p className={s.note}>{e.authorPrefix}: {author}</p>}
              <p className={s.lead}>{local?.goal ?? project.summary}</p>
              <p className={s.note}>
                {lang === "ru"
                  ? "Это запись каталога People + Project. Оплата, приёмка и split ещё не запущены (Wave 2)."
                  : "This is a People + Project catalog entry. Payment, acceptance and payout split are not live (Wave 2)."}
              </p>
              <div className={s.gridTwo}>
                <article className={s.card}>
                  <h3>{t.deliverable}</h3>
                  <p>{local?.deliverable ?? project.result_promise}</p>
                  {project.earning_model && (
                    <div className={s.deliverable}>
                      <strong>{lang === "ru" ? "Ограничения" : "Limits"}</strong>
                      <p>{project.earning_model}</p>
                    </div>
                  )}
                </article>
                <article className={s.card}>
                  <h3>{lang === "ru" ? "Задачи" : "Tasks"}</h3>
                  {(project.tasks ?? []).map(task => (
                    <div className={s.deliverable} key={task.id}>
                      <strong>{task.title}</strong>
                      <p>{task.acceptance_criteria}</p>
                      <p>
                        {task.assignee_type}
                        {task.price_acp != null ? ` · ${task.price_acp} ACP` : ""}
                      </p>
                    </div>
                  ))}
                  {(project.tasks ?? []).length === 0 && (
                    <p>{lang === "ru" ? "Задач пока нет." : "No tasks yet."}</p>
                  )}
                </article>
              </div>
              {local && (
                <details className={s.note}>
                  <summary style={{ cursor: "pointer" }}>{t.sample}</summary>
                  <p style={{ marginTop: 12 }}>{local.sample}</p>
                </details>
              )}
              <div className={s.actions}>
                <Link className={s.secondary} href="/">{e.home} →</Link>
                <Link className={s.secondary} href="/economy">
                  {lang === "ru" ? "К каталогу" : "Back to catalog"} →
                </Link>
                {project.background_href && (
                  <Link className={s.secondary} href={project.background_href}>
                    {t.open} →
                  </Link>
                )}
                <Link className={s.secondary} href="/projects#test-projects">
                  {t.more} →
                </Link>
              </div>
            </>
          )}
        </section>
      </main>
      <WorkflowFooter />
    </div>
  );
}
