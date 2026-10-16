"use client";

import Link from "next/link";
import { testProjects } from "@/lib/testProjects";
import { testProjectsByLang } from "@/locales/testProjects";
import { useLanguage } from "./LanguageProvider";
import { TestProjectFeedback } from "./ReviewTrustSection";
import s from "./WorkflowPresentation.module.css";

export function TestProjectsSection({ compact = false }: { compact?: boolean }) {
  const { lang } = useLanguage();
  const c = testProjectsByLang[lang];

  return <section id="test-projects" className={s.section} aria-labelledby="test-projects-heading">
    <p className={s.eyebrow}>{c.kicker}</p>
    <h2 id="test-projects-heading" className={s.heading}>{c.title}</h2>
    <p className={s.lead}>{c.lead}</p>
    <p className={s.note}>{c.disclosure}</p>
    <div className={compact ? s.grid : s.gridTwo}>
      {testProjects.map(project => {
        const copy = c.projects[project.id];
        return <article id={`test-project-${project.id}`} className={s.card} key={project.id} aria-labelledby={`test-project-${project.id}-heading`}>
          <span className={`${s.tag} ${s.core}`}>{c.badge}</span>
          <h3 id={`test-project-${project.id}-heading`}>{project.title}</h3>
          <p className={s.note}>{c.authorPrefix}: 3n3rgy</p>
          <div className={s.deliverable}><strong>{c.goal}</strong><p>{copy.goal}</p></div>
          {!compact && <>
            <div className={s.deliverable}><strong>{c.people}</strong><p>{copy.people}</p></div>
            <div className={s.deliverable}><strong>{c.ai}</strong><p>{copy.ai}</p></div>
          </>}
          <div className={s.deliverable}><strong>{c.deliverable}</strong><p>{copy.deliverable}</p></div>
          {!compact && <details className={s.deliverable}>
            <summary style={{ cursor: "pointer", color: "var(--accent)", fontSize: 13, lineHeight: 1.6 }}>{c.sample}</summary>
            <p style={{ marginTop: 12 }}>{copy.sample}</p>
          </details>}
          {!compact && <TestProjectFeedback projectId={project.id} />}
          <div className={s.projects}>
            <Link className={s.projectLink} href={`/economy/${project.economySlug}`}>{lang === "ru" ? "В каталоге People+Project" : "In People+Project catalog"} →</Link>
            <Link className={s.projectLink} href={project.href}>{c.open} →</Link>
          </div>
        </article>;
      })}
    </div>
    {compact && <div className={s.actions}><Link className={s.secondary} href="/projects#test-projects">{c.more} →</Link></div>}
  </section>;
}
