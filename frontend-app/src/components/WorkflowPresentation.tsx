"use client";
import { webInstallByLang } from "@/locales/webInstall";
import Link from "next/link";
import { useLanguage } from "./LanguageProvider";
import { portfolioByLang, solutionPortfolio } from "@/lib/solutionPortfolio";
import { positioningByLang } from "@/locales/positioning";
import { isTestProjectRoute } from "@/lib/testProjects";
import { testProjectsByLang } from "@/locales/testProjects";
import s from "./WorkflowPresentation.module.css";
export { default as presentationStyles } from "./WorkflowPresentation.module.css";

export function SolutionAreas({ compact = false }: { compact?: boolean }) {
  const { lang } = useLanguage();
  const c = positioningByLang[lang];
  const p = portfolioByLang[lang];
  return <div className={compact ? s.grid : s.gridTwo}>
    {solutionPortfolio.map((area, i) => {
      const copy = p.areas[i];
      return <article key={area.id} id={area.id} className={s.card}>
        <svg className={s.areaIcon} viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={[
          "M20 4 34 11v13L20 36 6 24V11zM13 20l5 5 10-12",
          "M7 12h26v22H7zM14 12V6h12v6M7 20h26M18 18h4v6h-4z",
          "M6 9h5l4 19h16l4-14H13M17 34h1M28 34h1",
          "M20 35S3 25 7 14c3-8 11-6 13 0 2-6 10-8 13 0 4 11-13 21-13 21Z",
          "M20 4 36 13 20 22 4 13zM4 21l16 9 16-9M4 29l16 9 16-9",
          "M5 7h30v21H18L9 35v-7H5zM11 14h18M11 20h11",
        ][i % 6]}/></svg>
        <span className={`${s.tag} ${area.kind === "core" ? s.core : ""}`}>{p.kinds[area.kind]}</span>
        <h3>{copy.title}</h3><p>{copy.body}</p>
        <div className={s.deliverable}><strong>{c.output}</strong><p>{copy.deliverable}</p></div>
        {compact ? <Link className={s.projectLink} href={`/projects#${area.id}`}>{c.open} →</Link> : <>
          <strong className={s.eyebrow}>{c.projects}</strong>
          <div className={s.projects}>{area.routes.filter(([href]) => !isTestProjectRoute(href)).map(([href, name]) => <Link key={href} href={href} className={s.projectLink}>{name}</Link>)}</div>
          {area.routes.some(([href]) => isTestProjectRoute(href)) && <div className={s.projects}><Link href="/projects#test-projects" className={s.projectLink}>{testProjectsByLang[lang].title} →</Link></div>}
        </>}
      </article>;
    })}
  </div>;
}
export function WorkflowFooter() {
  const { lang, t } = useLanguage();
  const c = positioningByLang[lang];
  return <footer className={s.footer}><div className={s.footerBrand}><svg viewBox="0 0 40 38" aria-hidden="true"><path d="M4 32 19 6h6l13 26H28L20 17 11 32Z" fill="currentColor"/></svg><div><strong>ANCAP</strong><p>{c.kicker}</p></div></div><nav className={s.projects} aria-label={c.platform}>
    <Link href="/install">{webInstallByLang[lang].link}</Link><Link href="/investors">{c.investors}</Link><Link href="/legal/terms">{t("legal.termsLink")}</Link>
    <Link href="/legal/privacy">{t("legal.privacyLink")}</Link><Link href="/legal/refunds">{t("legal.refundsLink")}</Link>
    <Link href="/legal">{t("nav.legal")}</Link><a href="mailto:support@ancap.cloud">support@ancap.cloud</a>
  </nav></footer>;
}
