"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import { presentationStyles as s } from "@/components/WorkflowPresentation";
import { webInstallByLang } from "@/locales/webInstall";

export function WebInstallGuide({ standalone = false }: { standalone?: boolean }) {
  const { lang } = useLanguage();
  const c = webInstallByLang[lang];
  return (
    <section className={s.section} id="install-app" aria-labelledby="install-app-title">
      {standalone ? <h1 id="install-app-title" className={s.heading}>{c.title}</h1> : <h2 id="install-app-title" className={s.heading}>{c.title}</h2>}
      <p className={s.lead}>{c.lead}</p>
      <div className={s.gridTwo}>
        {[["iPhone · Safari", c.iphone], ["Android · Chrome", c.android]].map(([title, steps]) => (
          <article className={s.card} key={title as string}>
            {standalone ? <h2>{title}</h2> : <h3>{title}</h3>}
            <ol className="list-decimal space-y-3 pl-5 mt-4 text-[var(--text-secondary)]">
              {(steps as string[]).map(step => <li key={step}>{step}</li>)}
            </ol>
          </article>
        ))}
      </div>
      <p className={s.note}>{c.result}</p>
      <p className={s.note}>{c.help}</p>
      <div className={s.actions}>
        <Link href="/wallet" className={s.primary}>{c.open} →</Link>
        {!standalone && <Link href="/install" className={s.secondary}>{c.link} →</Link>}
      </div>
    </section>
  );
}
