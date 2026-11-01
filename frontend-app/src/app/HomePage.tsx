"use client";

import Link from "next/link";
import { CardInfoSection } from "@/components/CardInfoSection";
import { CreatorAiConnect } from "@/components/CreatorAiConnect";
import { HomeChatDialog } from "@/components/HomeChatDialog";
import { HomeFirstRun } from "@/components/HomeFirstRun";
import h from "@/components/HomeFirstRun.module.css";
import { Navigation } from "@/components/Navigation";
import { PeopleAiEconomySection } from "@/components/PeopleAiEconomySection";
import { RacpOverview } from "@/components/RacpOverview";
import { ReviewTrustSection } from "@/components/ReviewTrustSection";
import { useLanguage } from "@/components/LanguageProvider";
import { WebInstallGuide } from "@/components/WebInstallGuide";
import {
  presentationStyles as s,
  SolutionAreas,
  WorkflowFooter,
} from "@/components/WorkflowPresentation";
import { positioningByLang } from "@/locales/positioning";

export function HomePage() {
  const { lang } = useLanguage();
  const c = positioningByLang[lang];

  return (
    <div
      className={s.shell}
      style={{
        position: "relative",
        zIndex: 1,
      }}
    >
      <Navigation />

      <main className={`${s.main} ${h.homeMain}`}>
        <HomeFirstRun afterHero={<>
          <CreatorAiConnect key={lang} />
          <HomeChatDialog />
        </>} />

        <section
          className={s.section}
          id="solutions"
          aria-labelledby="solutions-title"
        >
          <h2
            id="solutions-title"
            className={s.heading}
          >
            {c.portfolio}
          </h2>

          <p className={s.lead}>
            {c.portfolioLead}
          </p>

          <SolutionAreas compact />

          <p className={s.note}>
            {c.portfolioNote}
          </p>
        </section>

        <section
          className={s.section}
          id="smart-pay"
          aria-labelledby="smart-pay-title"
        >
          <p className={s.eyebrow}>
            ANCAP / {c.smartPay}
          </p>

          <h2
            id="smart-pay-title"
            className={s.heading}
          >
            {c.smartPay}
          </h2>

          <p className={s.lead}>
            {c.smartPayLead}
          </p>

          <p className={s.note}>
            {c.smartPayLimits}
          </p>

          <ol
            className={s.grid}
            style={{
              padding: 0,
              listStyle: "none",
            }}
          >
            {[
              [c.smartPayStep1, c.smartPayStep1Body],
              [c.smartPayStep2, c.smartPayStep2Body],
              [c.smartPayStep3, c.smartPayStep3Body],
              [c.smartPayStep4, c.smartPayStep4Body],
            ].map(([title, body]) => (
              <li
                className={s.card}
                key={title}
              >
                <h3>{title}</h3>
                <p>{body}</p>
              </li>
            ))}
          </ol>

          <div className={s.actions}>
            <Link
              className={s.primary}
              href="/payment-scanner"
            >
              {c.smartPayCta} →
            </Link>

            <Link
              className={s.secondary}
              href="/ai/workflows"
            >
              {c.browse} →
            </Link>
          </div>

          <p className={s.note}>
            {c.smartPayMobile}
          </p>
        </section>

        <WebInstallGuide />

        <PeopleAiEconomySection />

        <CardInfoSection />

        <section
          className={s.section}
          id="creators"
          aria-labelledby="creators-title"
        >
          <div className="max-w-3xl">
            <p className={s.eyebrow}>
              {c.creators}
            </p>

            <h2
              id="creators-title"
              className={s.heading}
            >
              {c.earn}
            </h2>

            <p className={s.lead}>
              {c.earnBody}
            </p>

            <div className={s.actions}>
              <Link
                href="/dashboard/seller"
                className={s.primary}
              >
                {c.seller} →
              </Link>

              <Link
                href="/economy"
                className={s.secondary}
              >
                {c.economyLink} →
              </Link>
            </div>
          </div>
        </section>

        <ReviewTrustSection />

        <RacpOverview compact />

        <section
          className={s.section}
          id="vision"
          aria-labelledby="vision-title"
        >
          <p className={s.eyebrow}>
            {c.investors}
          </p>

          <h2
            id="vision-title"
            className={s.heading}
          >
            {c.investmentTitle}
          </h2>

          <p className={s.lead}>
            {c.investmentLead}
          </p>

          <div className={s.actions}>
            <Link
              className={s.secondary}
              href="/investors"
            >
              {c.investors} →
            </Link>
          </div>
        </section>
      </main>

      <WorkflowFooter />
    </div>
  );
}
