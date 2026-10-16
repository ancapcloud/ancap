"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navigation } from "@/components/Navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { WorkflowFooter, presentationStyles as s } from "@/components/WorkflowPresentation";
import { economy, type EconomyProjectList } from "@/lib/api";
import { economyByLang } from "@/locales/economy";
import { testProjectsByLang } from "@/locales/testProjects";
import type { TestProjectId } from "@/lib/testProjects";

export default function EconomyCatalogPage() {
  const { lang } = useLanguage();
  const t = testProjectsByLang[lang];
  const e = economyByLang[lang];
  const [data, setData] = useState<EconomyProjectList | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    economy.listProjects({ limit: 50 })
      .then(result => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load projects");
          setData(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className={s.shell}>
      <Navigation />
      <main className={s.main}>
        <section className={s.section} style={{ borderTop: 0, paddingTop: 60 }}>
          <p className={s.eyebrow}>People + AI Project Economy</p>
          <h1 className={s.title}>
            {lang === "ru" ? "Первые проекты в системе" : "First projects in the catalog"}
          </h1>
          <p className={s.lead}>
            {lang === "ru"
              ? "Пять AI-составленных демо-проектов пользователя 3n3rgy — первые записи People + Project. Каталог community-заказов и выплаты ещё не открыты."
              : "Five AI-authored demo projects by 3n3rgy are the first People + Project catalog entries. Community orders and payouts are not open yet."}
          </p>
          {data?.preview_only && (
            <p className={s.note}>
              {lang === "ru"
                ? "Режим предпросмотра: видны только платформенные демо. Создание проектов и заявки закрыты (FF_PROJECT_ECONOMY=false)."
                : "Preview mode: only platform demos are visible. Create/apply are closed (FF_PROJECT_ECONOMY=false)."}
            </p>
          )}
          {error && <p className={s.note} role="alert">{error}</p>}
          <div className={s.gridTwo}>
            {(data?.items ?? []).map((project, index) => {
              const seed = project.seed_key as TestProjectId | null;
              const local = seed && t.projects[seed] ? t.projects[seed] : null;
              const author = project.owner_display_name || (project.is_platform_seed ? "3n3rgy" : null);
              return (
                <article className={s.card} key={project.id}>
                  <span className={`${s.tag} ${s.core}`}>
                    {project.is_platform_seed ? t.badge : project.kind} · #{index + 1}
                  </span>
                  <h3>{project.title}</h3>
                  {author && (
                    <p className={s.note}>{e.authorPrefix}: {author}</p>
                  )}
                  <p>{local?.goal ?? project.summary}</p>
                  <div className={s.deliverable}>
                    <strong>{t.deliverable}</strong>
                    <p>{local?.deliverable ?? project.result_promise}</p>
                  </div>
                  <div className={s.projects}>
                    <Link className={s.projectLink} href={`/economy/${project.slug}`}>
                      {lang === "ru" ? "Открыть в каталоге" : "Open in catalog"} →
                    </Link>
                    {project.background_href && (
                      <Link className={s.projectLink} href={project.background_href}>
                        {t.open} →
                      </Link>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
          {!error && data && data.items.length === 0 && (
            <p className={s.note}>
              {lang === "ru" ? "Каталог пока пуст." : "Catalog is empty."}
            </p>
          )}
          <div className={s.actions}>
            <Link className={s.secondary} href="/">{e.home} →</Link>
            <Link className={s.secondary} href="/projects#test-projects">
              {t.more} →
            </Link>
          </div>
        </section>
      </main>
      <WorkflowFooter />
    </div>
  );
}
