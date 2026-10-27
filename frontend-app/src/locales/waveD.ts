type Language = "en" | "ru" | "uk" | "de" | "zh-Hant";
type Tree = { [key: string]: string | Tree };

const accessEn: Tree = {
  title: "Access Grants",
  loading: "Loading access grants...",
  empty: "No access grants yet. When orders are fulfilled, execute/view/allocate permissions will appear here.",
  errLoad: "Failed to load access grants",
  strategy: "Strategy",
  grantee: "Grantee",
  created: "Created",
  expires: "Expires",
  never: "never",
  runStrategy: "Run strategy",
};

const bountiesEn: Tree = {
  title: "Bug Bounty",
  titlePlaceholder: "Title",
  descPlaceholder: "Describe reproduction steps",
  severityLow: "low",
  severityMedium: "medium",
  severityHigh: "high",
  severityCritical: "critical",
  submit: "Submit report",
  myReports: "My reports",
  refresh: "Refresh",
  errLoad: "Failed to load reports",
  errSubmit: "Failed to submit report",
};

const businessEn: Tree = {
  title: "Business & Treasury",
  lead: "Merchant invoicing is live in ANCAP Pay MVP. Treasury roles, approval limits, and batch payouts ship in the 61–90 day phase alongside embedded wallet business mode.",
  cardMerchant: "Merchant dashboard",
  cardMerchantDesc: "Payment links, CSV export, webhooks",
  cardOrgs: "Organizations",
  cardOrgsDesc: "Team roles and billing wallet",
  cardCompliance: "Compliance",
  cardComplianceDesc: "MiCA-safe utility asset messaging",
  cardEnterprise: "Enterprise",
  cardEnterpriseDesc: "Custom SLA and treasury",
};

const creatorsEn: Tree = {
  title: "Creator program",
  lead: "Publish workflows on ANCAP, earn ACP from successful runs, and export earnings with proof-backed receipts.",
  sellerDashboard: "Seller dashboard",
  earnings: "Earnings",
  payouts: "Payouts",
  pricing: "Creator plan pricing",
};

const claimEn: Tree = {
  title: "Claim codes",
  lead: "Lock ACP balance into a one-time redeemable voucher with proof receipt.",
  login: "Log in to create claim codes",
  amountLabel: "Amount (ACP)",
  campaignLabel: "Campaign label",
  creating: "Creating…",
  create: "Create claim code",
  redeemPage: "Redeem page",
  errCreate: "Failed to create claim code",
};

const claimRedeemEn: Tree = {
  title: "Redeem claim code",
  login: "Log in to redeem",
  pinLabel: "PIN (if required)",
  redeeming: "Redeeming…",
  redeem: "Redeem to wallet",
  redeemed: "Redeemed {amount} {currency}",
  viewProof: "View proof",
  errRedeem: "Redeem failed",
};

const sampleReportsEn: Tree = {
  back: "Back to workflow store",
  kicker: "Sample output",
  sampleScore: "Sample score",
  price: "Price",
  proof: "Proof",
  receiptReady: "Receipt-ready",
  includesTitle: "What the full report includes",
  sectionDesc: "Delivered as a structured artifact with request inputs, generated result, and receipt metadata.",
  ctaTitle: "Ready to generate your own?",
  ctaBody: "The live workflow creates a persistent run, pricing snapshot, payment intent, and proof bundle for the exact inputs you submit.",
  buyWorkflow: "Buy this workflow",
  freeSnapshot: "Start with free snapshot",
  sampleReady: "Sample-ready",
  sampleSummary: "{title} sample: {summary}",
};

const stakingEn: Tree = {
  title: "ACP Staking",
  lead: "Stake ACP from your agent accounts and release when needed.",
  rewardsTitle: "How staking rewards work",
  rewardsBody: "Rewards are funded from real platform cashflows (fees + slashing), with a capped bootstrap emission. APY is dynamic and constrained by floor/ceiling to keep tokenomics sustainable.",
  economics: "Source: {fees}% fees + {slash}% slashes; bootstrap {daily} {currency}/day (cap {cap}); APY range {floor}% - {ceiling}%; min stake {min} {currency}.",
  selectAgent: "Select owned agent",
  amountPlaceholder: "Amount ACP",
  processing: "Processing...",
  stake: "Stake ACP",
  yourStakes: "Your stakes",
  refresh: "Refresh",
  noStakes: "No stakes found.",
  status: "Status",
  release: "Release",
  errLoad: "Failed to load staking data",
  errStake: "Stake failed",
  errRelease: "Release failed",
};

const statusEn: Tree = {
  title: "Platform status",
  lead: "Public API and ACP node health.",
  errUnavailable: "Status unavailable",
  api: "API",
  operational: "Operational",
  checking: "Checking…",
  chain: "ACP chain",
  synced: "Synced",
  unavailable: "Unavailable",
  blockHeight: "Block height: {height}",
  openExplorer: "Open explorer",
};

const leaderboardsEn: Tree = {
  title: "Leaderboards",
  strategyFollowers: "Strategy followers",
  agentFollowers: "Agent followers",
  noData: "No data yet.",
  errLoad: "Failed to load leaderboard",
};

const onboardingEn: Tree = {
  title: "Onboarding",
  lead: "Claim starter assets (ACP), activate a starter pack, and run a quickstart workflow.",
  agentLabel: "Agent (optional)",
  agentNone: "(none)",
  claimFaucet: "Claim Faucet (10 ACP)",
  starterPack: "Activate Starter Pack",
  quickstart: "Quickstart Run",
  errLoadAgents: "Failed to load agents",
  errFaucet: "Faucet claim failed",
  errStarter: "Starter pack assign failed",
  errSelectAgent: "Select an agent first",
  errQuickstart: "Quickstart run failed",
};

const notificationsEn: Tree = {
  title: "Notifications",
  refresh: "Refresh",
  markRead: "Mark read",
  empty: "No notifications.",
  errLoad: "Failed to load notifications",
  errMarkRead: "Failed to mark read",
};

const listingsEn: Tree = {
  kicker: "Creator marketplace",
  title: "Paid AI-workflow listings",
  lead: "Human builders and AI agents can publish repeatable execution offers, price them in ACP, and earn from paid runs with proof-backed receipts.",
  creatorDashboard: "Creator dashboard",
  publishListing: "Publish listing",
  agentJson: "Agent JSON",
  loading: "Loading...",
  empty: "No active listings yet. Publish one from a strategy page.",
  active: "active",
  seller: "Seller",
  version: "Version",
  price: "Price",
  created: "Created",
  strategyFallback: "Strategy {id}",
};

const listingDetailEn: Tree = {
  back: "← Back to listings",
  loading: "Loading…",
  notFound: "Listing not found.",
  purchaseSuccess: "Purchase successful",
  subscriptionStarted: "Subscription started ({period}) and access grant issued.",
  orderCreated: "Order created and access grant issued.",
  viewGrants: "View access grants",
  runStrategy: "Run this strategy",
  viewLedger: "View ledger",
  viewOrders: "View orders",
  orderGrant: "Order: {orderId}{grant}",
  grantSuffix: " · Grant: {grantId}",
  strategyFallback: "Strategy {id}",
  strategyId: "Strategy ID",
  version: "Version",
  price: "Price",
  scope: "Scope",
  execute: "execute",
  billingMonthly: "Monthly billing",
  billingQuarterly: "Quarterly billing",
  billingAnnual: "Annual billing",
  buyerAgent: "Buyer agent",
  noAgents: "No agents yet (create one)",
  createAgentHint: "Create a buyer agent on",
  billingPeriod: "Billing period",
  noteLabel: "Note (optional)",
  startingSubscription: "Starting subscription…",
  buying: "Buying…",
  startSubscription: "Start {period} subscription",
  buyAccess: "Buy access",
  errNoBuyer: "Create a buyer agent first (Agents → My).",
  periodMonthly: "Monthly",
  periodQuarterly: "Quarterly",
  periodAnnual: "Annual",
};

const docsWacpEn: Tree = {
  overviewTitle: "Wrapped ACP docs",
  overviewBadge: "Public docs",
  overviewLead: "wACP is the BNB Smart Chain representation of ACP. This documentation set is the public trust layer for bridge users: what the asset is, how reserve backing is supposed to work, what contracts are official, and what risks remain.",
  readNext: "Read next",
  bridgeFlow: "Bridge flow",
  reserveModel: "Reserve proof model",
  riskDisclosures: "Risk disclosures",
  contracts: "Contracts and official addresses",
  pancakeswap: "PancakeSwap listing playbook",
  markets: "Public markets & token list",
  currentState: "Current public state",
  bridgeTitle: "wACP bridge",
  bridgeBadge: "ACP ↔ BSC",
  bridgeLead: "The live direction today is ACP → BSC minting: user creates an ACP → wACP bridge intent, sends ACP to the reserve path, the backend waits for confirmations, then submits the BSC mint transaction for wACP. Reverse BSC → ACP redeem is live in runtime (burn detection, payout submission, ACP confirmation, reconciliation — all operational).",
  step1: "Create bridge intent",
  step2: "Send ACP deposit",
  step3: "Wait for ACP confirmations",
  step4: "Submit BSC mint",
  step5: "Confirm BSC mint",
  step6: "Track the ACP deposit tx and BSC mint tx in public explorers",
  reverseStatus: "Reverse rail status:",
  reverseBody: "BSC → ACP redeem is live. The backend detects ReleaseRequested burns, submits ACP payouts, and confirms on-chain. Reconciliation tracks outstanding liabilities. Admin endpoints require platform-admin auth + X-Bridge-Operator-Secret.",
  reserveTitle: "wACP reserve model",
  reserveBadge: "No reserve proof = no liquidity",
  reserveLead: "Canonical invariant: minted_wACP_on_BSC <= locked_or_custodied_ACP_reserve - operational_buffer. ACP has 8 decimals. wACP on BSC has 18 decimals. Conversion target: wacp_wei = acp_smallest_unit * 10^10.",
  healthy: "Healthy: backing ratio >= 1.0",
  degraded: "Degraded: ratio near threshold or telemetry stale",
  critical: "Critical: minted supply exceeds reserve-equivalent backing",
  reserveApi: "Public reserve proof should be exposed via /api/v1/wacp/reserve-proof and linked from wallet / bridge surfaces.",
  risksTitle: "wACP risks",
  risksBadge: "Disclosures",
  risk1: "wACP is a wrapped representation of ACP on BNB Smart Chain.",
  risk2: "Redemption depends on bridge availability, operator correctness, and reserve backing.",
  risk3: "Bridge operators may pause minting or redemption during incidents.",
  risk4: "Smart contract, custody, RPC, chain reorg, and liquidity risks exist.",
  risk5: "PancakeSwap market price may diverge from ACP reference value.",
  risk6: "Do not trust unofficial token contracts or unofficial pair links.",
  contractsTitle: "wACP contracts",
  contractsBadge: "Official addresses",
  contractsWarning: "Warning: pool is currently a technical liquidity bootstrap, not deep-liquidity market infrastructure.",
  pancakeswapTitle: "wACP → PancakeSwap",
  pancakeswapBadge: "Playbook",
  pancakeswapLead: "PancakeSwap V2 was used for the first public technical bootstrap. The current pair is wACP/USDT. This is live for smoke-testing, not yet positioned as a deep-liquidity market launch.",
  poolLink: "Pool link:",
  swapLink: "Swap link:",
  openPool: "open pool",
  openSwap: "open swap",
};

const docsSacpEn: Tree = {
  overviewTitle: "Stable ACP",
  overviewBadge: "Foundation",
  overviewLead: "sACP is ANCAP's commerce stablecoin: USD-targeted and ACP-collateralized on BNB Smart Chain. It is not the same as ACP (accounting unit) or wACP (1:1 ACP wrap), and it is not a guaranteed fiat redemption product.",
  readNext: "Read next",
  reserveLink: "Reserve / collateral model",
  risksLink: "Risk disclosures",
  compareWacp: "Compare with wACP",
  specLink: "Spec (STABLECOIN_SACP_SPEC.md)",
  publicApi: "Public API",
  reserveTitle: "Reserve / collateral model",
  overviewLink: "Overview",
  reserveLead1: "Target peg: 1 sACP ≈ 1 USD. Collateral is ACP held in a dedicated reserve with a minimum overcollateralization ratio (default 150%). Live proof endpoints report circulating supply vs collateral once the BSC contract and indexer are wired (S1–S2).",
  reserveLead2: "Canonical target invariant: collateral_value_usd(ACP_reserve) >= min_collateral_ratio × circulating_sACP.",
  liveProof: "Live reserve-proof JSON",
  risksTitle: "Risk disclosures",
  risk1Title: "Soft peg only.",
  risk1Body: "sACP targets USD for commerce pricing. There is no guarantee of 1:1 USD redemption or bank-deposit equivalence.",
  risk2Title: "ACP collateral risk.",
  risk2Body: "Reserve health depends on ACP market value, custody, and operator processes — similar honesty bar as the wACP bridge.",
  risk3Title: "Operator-mediated.",
  risk3Body: "Mint/redeem orchestration is custodial until further decentralization. Pause and gateway key risk apply.",
  risk4Title: "Not wACP.",
  risk4Body: "Confusing sACP with wACP (1:1 ACP wrap) or with partner USDC/USDT can cause wrong expectations about backing and redemption.",
  risk5Title: "Compliance.",
  risk5Body: "Public mint may require jurisdictional review (e.g. MiCA / e-money) before broad distribution.",
};

const docsMobileSecurityEn: Tree = {
  kicker: "Mobile security",
  title: "ACP Wallet security model",
  badge: "Public docs",
  lead: "This page is the public summary of the current non-custodial mobile-wallet security posture. Source-of-truth detail remains in docs/mobile/SECURITY_MODEL.md, but this route exists so mobile clients and public docs can link to a real web page instead of stale placeholders.",
  releaseTruth: "Release-status truth:",
  releaseBody: "the repo baseline for the main MASVS-L1-relevant controls is in place, but the wallet is not yet fully release-closed until real-device and native-build verification is finished.",
  baselineTitle: "Current baseline controls",
  remainingTitle: "Remaining release gates",
  readNext: "Read next",
  bridgeFlow: "Bridge flow",
  bridgeRisks: "Bridge and custody risks",
  terms: "Terms",
  privacy: "Privacy",
  cyberDefense: "Collective cyber defense",
  ctrl1Title: "Non-custodial by design",
  ctrl1Body: "The mobile wallet is device-local. ANCAP API read endpoints and the broadcast relay never hold the seed phrase or decrypted private keys.",
  ctrl2Title: "PIN handling",
  ctrl2Body: "The app stores only a salted SHA-256 verifier for the local PIN. Raw PIN digits are not persisted.",
  ctrl3Title: "Biometric gating",
  ctrl3Body: "When enabled, mnemonic and keystore secrets move into biometric-gated secure storage so reading signing secrets requires device authentication.",
  ctrl4Title: "Sensitive screen controls",
  ctrl4Body: "Seed-phrase screens block screenshots, receive-address clipboard copies auto-clear, and the app auto-locks after inactivity.",
  ctrl5Title: "Error/log redaction",
  ctrl5Body: "Wallet UI surfaces sanitize mnemonic, keystore, raw transaction, and bearer-token shaped values before rendering or forwarding errors.",
  gate1: "real device verification for PIN, biometrics, and secure-vault migration",
  gate2: "native create/send/sign verification once Android/iOS FFI artifacts are built",
  gate3: "stronger production-grade root/jailbreak or device-integrity checks",
  gate4: "TestFlight / Play Internal / store release validation",
};

function tr(en: Tree, ru: Tree, uk: Tree, de: Tree, zh: Tree): Record<Language, Tree> {
  return { en, ru, uk, de: de, "zh-Hant": zh };
}

export const accessPageByLang = tr(
  accessEn,
  { ...accessEn, title: "Гранты доступа", loading: "Загрузка грантов доступа...", empty: "Грантов доступа пока нет. После исполнения заказов здесь появятся права execute/view/allocate.", errLoad: "Не удалось загрузить гранты доступа", strategy: "Стратегия", grantee: "Получатель", created: "Создан", expires: "Истекает", never: "никогда", runStrategy: "Запустить стратегию" },
  { ...accessEn, title: "Гранти доступу", loading: "Завантаження грантів доступу...", empty: "Грантів доступу ще немає. Після виконання замовлень тут з’являться права execute/view/allocate.", errLoad: "Не вдалося завантажити гранти доступу", strategy: "Стратегія", grantee: "Отримувач", created: "Створено", expires: "Закінчується", never: "ніколи", runStrategy: "Запустити стратегію" },
  { ...accessEn, title: "Zugriffserteilungen", loading: "Zugriffserteilungen werden geladen...", empty: "Noch keine Zugriffserteilungen. Nach erfüllten Bestellungen erscheinen hier execute/view/allocate-Berechtigungen.", errLoad: "Zugriffserteilungen konnten nicht geladen werden", strategy: "Strategie", grantee: "Empfänger", created: "Erstellt", expires: "Läuft ab", never: "nie", runStrategy: "Strategie ausführen" },
  { ...accessEn, title: "存取授權", loading: "正在載入存取授權...", empty: "尚無存取授權。訂單完成後，execute/view/allocate 權限會顯示於此。", errLoad: "無法載入存取授權", strategy: "策略", grantee: "受權者", created: "建立", expires: "到期", never: "永不", runStrategy: "執行策略" }
);

export const bountiesPageByLang = tr(
  bountiesEn,
  { ...bountiesEn, title: "Bug Bounty", titlePlaceholder: "Заголовок", descPlaceholder: "Опишите шаги воспроизведения", submit: "Отправить отчёт", myReports: "Мои отчёты", refresh: "Обновить", errLoad: "Не удалось загрузить отчёты", errSubmit: "Не удалось отправить отчёт" },
  { ...bountiesEn, title: "Bug Bounty", titlePlaceholder: "Заголовок", descPlaceholder: "Опишіть кроки відтворення", submit: "Надіслати звіт", myReports: "Мої звіти", refresh: "Оновити", errLoad: "Не вдалося завантажити звіти", errSubmit: "Не вдалося надіслати звіт" },
  { ...bountiesEn, title: "Bug Bounty", titlePlaceholder: "Titel", descPlaceholder: "Reproduktionsschritte beschreiben", submit: "Bericht senden", myReports: "Meine Berichte", refresh: "Aktualisieren", errLoad: "Berichte konnten nicht geladen werden", errSubmit: "Bericht konnte nicht gesendet werden" },
  { ...bountiesEn, title: "漏洞賞金", titlePlaceholder: "標題", descPlaceholder: "描述重現步驟", submit: "提交報告", myReports: "我的報告", refresh: "重新整理", errLoad: "無法載入報告", errSubmit: "無法提交報告" }
);

export const businessPageByLang = tr(
  businessEn,
  { ...businessEn, title: "Бизнес и казначейство", lead: "Мерчант-инвойсинг доступен в ANCAP Pay MVP. Роли казначейства, лимиты одобрения и batch payouts — в фазе 61–90 дней вместе с embedded wallet business mode.", cardMerchant: "Мерчант-дашборд", cardMerchantDesc: "Платёжные ссылки, CSV, webhooks", cardOrgs: "Организации", cardOrgsDesc: "Роли команды и billing wallet", cardCompliance: "Комплаенс", cardComplianceDesc: "MiCA-safe utility messaging", cardEnterprise: "Enterprise", cardEnterpriseDesc: "Custom SLA и казначейство" },
  { ...businessEn, title: "Бізнес і казначейство", lead: "Мерчант-інвойсинг доступний у ANCAP Pay MVP. Ролі казначейства, ліміти схвалення та batch payouts — у фазі 61–90 днів разом із embedded wallet business mode.", cardMerchant: "Мерчант-дашборд", cardMerchantDesc: "Платіжні посилання, CSV, webhooks", cardOrgs: "Організації", cardOrgsDesc: "Ролі команди та billing wallet", cardCompliance: "Комплаєнс", cardComplianceDesc: "MiCA-safe utility messaging", cardEnterprise: "Enterprise", cardEnterpriseDesc: "Custom SLA та казначейство" },
  { ...businessEn, title: "Business & Treasury", lead: "Merchant-Invoicing ist im ANCAP Pay MVP live. Treasury-Rollen, Freigabelimits und Batch-Auszahlungen folgen in Phase 61–90 Tage mit embedded wallet business mode.", cardMerchant: "Merchant-Dashboard", cardMerchantDesc: "Zahlungslinks, CSV-Export, Webhooks", cardOrgs: "Organisationen", cardOrgsDesc: "Teamrollen und Billing-Wallet", cardCompliance: "Compliance", cardComplianceDesc: "MiCA-sichere Utility-Kommunikation", cardEnterprise: "Enterprise", cardEnterpriseDesc: "Custom SLA und Treasury" },
  { ...businessEn, title: "企業與資金庫", lead: "ANCAP Pay MVP 已上線商家發票。資金庫角色、核准限額與批次付款將在 61–90 天階段與嵌入式錢包企業模式一併推出。", cardMerchant: "商家儀表板", cardMerchantDesc: "付款連結、CSV 匯出、Webhooks", cardOrgs: "組織", cardOrgsDesc: "團隊角色與計費錢包", cardCompliance: "合規", cardComplianceDesc: "MiCA 安全的效用資產訊息", cardEnterprise: "企業", cardEnterpriseDesc: "自訂 SLA 與資金庫" }
);

export const creatorsPageByLang = tr(
  creatorsEn,
  { ...creatorsEn, title: "Программа для создателей", lead: "Публикуйте workflow на ANCAP, зарабатывайте ACP с успешных запусков и экспортируйте доход с proof-чеками.", sellerDashboard: "Дашборд продавца", earnings: "Доход", payouts: "Выплаты", pricing: "Тарифы для создателей" },
  { ...creatorsEn, title: "Програма для творців", lead: "Публікуйте workflow на ANCAP, заробляйте ACP з успішних запусків і експортуйте доходи з proof-чеками.", sellerDashboard: "Дашборд продавця", earnings: "Дохід", payouts: "Виплати", pricing: "Тарифи для творців" },
  { ...creatorsEn, title: "Creator-Programm", lead: "Veröffentlichen Sie Workflows auf ANCAP, verdienen Sie ACP aus erfolgreichen Runs und exportieren Sie Einnahmen mit Proof-Belegen.", sellerDashboard: "Seller-Dashboard", earnings: "Einnahmen", payouts: "Auszahlungen", pricing: "Creator-Tarife" },
  { ...creatorsEn, title: "創作者計畫", lead: "在 ANCAP 發布工作流程，從成功執行賺取 ACP，並以可證明收據匯出收益。", sellerDashboard: "賣家儀表板", earnings: "收益", payouts: "提領", pricing: "創作者方案定價" }
);

export const claimPageByLang = tr(
  claimEn,
  { ...claimEn, title: "Коды получения", lead: "Заблокируйте ACP в одноразовый ваучер с proof-чеком.", login: "Войдите, чтобы создавать коды", amountLabel: "Сумма (ACP)", campaignLabel: "Метка кампании", creating: "Создание…", create: "Создать код", redeemPage: "Страница погашения", errCreate: "Не удалось создать код" },
  { ...claimEn, title: "Коди отримання", lead: "Заблокуйте ACP у одноразовий ваучер із proof-чеком.", login: "Увійдіть, щоб створювати коди", amountLabel: "Сума (ACP)", campaignLabel: "Мітка кампанії", creating: "Створення…", create: "Створити код", redeemPage: "Сторінка погашення", errCreate: "Не вдалося створити код" },
  { ...claimEn, title: "Claim-Codes", lead: "Sperren Sie ACP-Guthaben in einen einmalig einlösbaren Gutschein mit Proof-Beleg.", login: "Anmelden, um Claim-Codes zu erstellen", amountLabel: "Betrag (ACP)", campaignLabel: "Kampagnenlabel", creating: "Wird erstellt…", create: "Claim-Code erstellen", redeemPage: "Einlöseseite", errCreate: "Claim-Code konnte nicht erstellt werden" },
  { ...claimEn, title: "領取代碼", lead: "將 ACP 餘額鎖定為一次性可兌換憑證，並附證明收據。", login: "登入以建立領取代碼", amountLabel: "金額 (ACP)", campaignLabel: "活動標籤", creating: "建立中…", create: "建立領取代碼", redeemPage: "兌換頁面", errCreate: "無法建立領取代碼" }
);

export const claimRedeemPageByLang = tr(
  claimRedeemEn,
  { ...claimRedeemEn, title: "Погашение кода", login: "Войдите для погашения", pinLabel: "PIN (если требуется)", redeeming: "Погашение…", redeem: "Зачислить в кошелёк", redeemed: "Погашено {amount} {currency}", viewProof: "Смотреть proof", errRedeem: "Погашение не удалось" },
  { ...claimRedeemEn, title: "Погашення коду", login: "Увійдіть для погашення", pinLabel: "PIN (за потреби)", redeeming: "Погашення…", redeem: "Зарахувати на гаманець", redeemed: "Погашено {amount} {currency}", viewProof: "Переглянути proof", errRedeem: "Погашення не вдалося" },
  { ...claimRedeemEn, title: "Claim-Code einlösen", login: "Anmelden zum Einlösen", pinLabel: "PIN (falls erforderlich)", redeeming: "Wird eingelöst…", redeem: "In Wallet gutschreiben", redeemed: "Eingelöst {amount} {currency}", viewProof: "Proof ansehen", errRedeem: "Einlösung fehlgeschlagen" },
  { ...claimRedeemEn, title: "兌換領取代碼", login: "登入以兌換", pinLabel: "PIN（如需要）", redeeming: "兌換中…", redeem: "兌換至錢包", redeemed: "已兌換 {amount} {currency}", viewProof: "查看證明", errRedeem: "兌換失敗" }
);

export const sampleReportsPageByLang = tr(
  sampleReportsEn,
  { ...sampleReportsEn, back: "Назад в магазин workflow", kicker: "Пример результата", sampleScore: "Примерная оценка", price: "Цена", proof: "Proof", receiptReady: "Готов к чеку", includesTitle: "Что входит в полный отчёт", sectionDesc: "Структурированный артефакт с входными данными, результатом и метаданными чека.", ctaTitle: "Готовы создать свой?", ctaBody: "Живой workflow создаёт run, снимок цены, payment intent и proof bundle для ваших входных данных.", buyWorkflow: "Купить workflow", freeSnapshot: "Начать с бесплатного снимка", sampleReady: "Пример готов", sampleSummary: "Пример {title}: {summary}" },
  { ...sampleReportsEn, back: "Назад до магазину workflow", kicker: "Зразок результату", sampleScore: "Зразкова оцінка", price: "Ціна", proof: "Proof", receiptReady: "Готовий до чека", includesTitle: "Що входить у повний звіт", sectionDesc: "Структурований артефакт із вхідними даними, результатом і метаданими чека.", ctaTitle: "Готові створити свій?", ctaBody: "Живий workflow створює run, знімок ціни, payment intent і proof bundle для ваших вхідних даних.", buyWorkflow: "Купити workflow", freeSnapshot: "Почати з безкоштовного знімка", sampleReady: "Зразок готовий", sampleSummary: "Зразок {title}: {summary}" },
  { ...sampleReportsEn, back: "Zurück zum Workflow-Store", kicker: "Beispielausgabe", sampleScore: "Beispiel-Score", price: "Preis", proof: "Proof", receiptReady: "Belegbereit", includesTitle: "Was der vollständige Bericht enthält", sectionDesc: "Strukturiertes Artefakt mit Eingaben, Ergebnis und Beleg-Metadaten.", ctaTitle: "Eigenen Bericht erzeugen?", ctaBody: "Der Live-Workflow erstellt einen Run, Preissnapshot, Payment Intent und Proof-Bundle für Ihre Eingaben.", buyWorkflow: "Workflow kaufen", freeSnapshot: "Mit kostenlosem Snapshot starten", sampleReady: "Beispiel bereit", sampleSummary: "Beispiel {title}: {summary}" },
  { ...sampleReportsEn, back: "返回工作流程商店", kicker: "範例輸出", sampleScore: "範例分數", price: "價格", proof: "證明", receiptReady: "可開立收據", includesTitle: "完整報告包含內容", sectionDesc: "結構化產出，含請求輸入、生成結果與收據中繼資料。", ctaTitle: "準備生成您自己的？", ctaBody: "即時工作流程會為您提交的輸入建立持久 run、定價快照、付款意圖與證明包。", buyWorkflow: "購買此工作流程", freeSnapshot: "從免費快照開始", sampleReady: "範例就緒", sampleSummary: "{title} 範例：{summary}" }
);

export const stakingPageByLang = tr(
  stakingEn,
  { ...stakingEn, title: "ACP Staking", lead: "Стейкайте ACP с агентских аккаунтов и снимайте при необходимости.", rewardsTitle: "Как работают награды", rewardsBody: "Награды финансируются из реальных денежных потоков платформы (комиссии + slashing) с ограниченной bootstrap-эмиссией. APY динамический и ограничен floor/ceiling.", selectAgent: "Выберите своего агента", amountPlaceholder: "Сумма ACP", processing: "Обработка...", stake: "Застейкать ACP", yourStakes: "Ваши стейки", refresh: "Обновить", noStakes: "Стейков не найдено.", status: "Статус", release: "Снять", errLoad: "Не удалось загрузить данные стейкинга", errStake: "Стейк не удался", errRelease: "Снятие не удалось" },
  { ...stakingEn, title: "ACP Staking", lead: "Стейкуйте ACP з агентських акаунтів і знімайте за потреби.", rewardsTitle: "Як працюють винагороди", rewardsBody: "Винагороди фінансуються з реальних грошових потоків платформи (комісії + slashing) з обмеженою bootstrap-емісією. APY динамічний і обмежений floor/ceiling.", selectAgent: "Оберіть свого агента", amountPlaceholder: "Сума ACP", processing: "Обробка...", stake: "Застейкати ACP", yourStakes: "Ваші стейки", refresh: "Оновити", noStakes: "Стейків не знайдено.", status: "Статус", release: "Зняти", errLoad: "Не вдалося завантажити дані стейкінгу", errStake: "Стейк не вдався", errRelease: "Зняття не вдалося" },
  { ...stakingEn, title: "ACP Staking", lead: "Staken Sie ACP von Ihren Agent-Konten und geben Sie bei Bedarf frei.", rewardsTitle: "So funktionieren Staking-Belohnungen", rewardsBody: "Belohnungen werden aus echten Plattform-Cashflows (Gebühren + Slashing) mit begrenzter Bootstrap-Emission finanziert. APY ist dynamisch und durch Floor/Ceiling begrenzt.", selectAgent: "Eigenen Agenten wählen", amountPlaceholder: "Betrag ACP", processing: "Wird verarbeitet...", stake: "ACP staken", yourStakes: "Ihre Stakes", refresh: "Aktualisieren", noStakes: "Keine Stakes gefunden.", status: "Status", release: "Freigeben", errLoad: "Staking-Daten konnten nicht geladen werden", errStake: "Stake fehlgeschlagen", errRelease: "Freigabe fehlgeschlagen" },
  { ...stakingEn, title: "ACP 質押", lead: "從代理帳戶質押 ACP，需要時可解除。", rewardsTitle: "質押獎勵如何運作", rewardsBody: "獎勵來自平台真實現金流（手續費 + 懲罰），並有上限的 bootstrap 發行。APY 動態且受 floor/ceiling 限制。", selectAgent: "選擇自有代理", amountPlaceholder: "ACP 金額", processing: "處理中...", stake: "質押 ACP", yourStakes: "您的質押", refresh: "重新整理", noStakes: "找不到質押。", status: "狀態", release: "解除", errLoad: "無法載入質押資料", errStake: "質押失敗", errRelease: "解除失敗" }
);

export const statusPageByLang = tr(
  statusEn,
  { ...statusEn, title: "Статус платформы", lead: "Публичное здоровье API и ACP-узла.", errUnavailable: "Статус недоступен", operational: "Работает", checking: "Проверка…", synced: "Синхронизирован", unavailable: "Недоступен", blockHeight: "Высота блока: {height}", openExplorer: "Открыть explorer" },
  { ...statusEn, title: "Статус платформи", lead: "Публічне здоров’я API та ACP-вузла.", errUnavailable: "Статус недоступний", operational: "Працює", checking: "Перевірка…", synced: "Синхронізовано", unavailable: "Недоступно", blockHeight: "Висота блоку: {height}", openExplorer: "Відкрити explorer" },
  { ...statusEn, title: "Plattformstatus", lead: "Öffentliche API- und ACP-Knoten-Gesundheit.", errUnavailable: "Status nicht verfügbar", operational: "Betriebsbereit", checking: "Wird geprüft…", synced: "Synchronisiert", unavailable: "Nicht verfügbar", blockHeight: "Blockhöhe: {height}", openExplorer: "Explorer öffnen" },
  { ...statusEn, title: "平台狀態", lead: "公開 API 與 ACP 節點健康狀態。", errUnavailable: "狀態不可用", operational: "正常運作", checking: "檢查中…", synced: "已同步", unavailable: "不可用", blockHeight: "區塊高度：{height}", openExplorer: "開啟瀏覽器" }
);

export const leaderboardsPageByLang = tr(
  leaderboardsEn,
  { ...leaderboardsEn, title: "Рейтинги", strategyFollowers: "Подписчики стратегий", agentFollowers: "Подписчики агентов", noData: "Данных пока нет.", errLoad: "Не удалось загрузить рейтинг" },
  { ...leaderboardsEn, title: "Рейтинги", strategyFollowers: "Підписники стратегій", agentFollowers: "Підписники агентів", noData: "Даних поки немає.", errLoad: "Не вдалося завантажити рейтинг" },
  { ...leaderboardsEn, title: "Bestenlisten", strategyFollowers: "Strategie-Follower", agentFollowers: "Agent-Follower", noData: "Noch keine Daten.", errLoad: "Bestenliste konnte nicht geladen werden" },
  { ...leaderboardsEn, title: "排行榜", strategyFollowers: "策略追蹤者", agentFollowers: "代理追蹤者", noData: "尚無資料。", errLoad: "無法載入排行榜" }
);

export const onboardingPageByLang = tr(
  onboardingEn,
  { ...onboardingEn, title: "Онбординг", lead: "Получите стартовые ACP, активируйте starter pack и запустите quickstart workflow.", agentLabel: "Агент (необязательно)", agentNone: "(нет)", claimFaucet: "Claim Faucet (10 ACP)", starterPack: "Активировать Starter Pack", quickstart: "Quickstart Run", errLoadAgents: "Не удалось загрузить агентов", errFaucet: "Faucet claim не удался", errStarter: "Starter pack assign не удался", errSelectAgent: "Сначала выберите агента", errQuickstart: "Quickstart run не удался" },
  { ...onboardingEn, title: "Онбординг", lead: "Отримайте стартові ACP, активуйте starter pack і запустіть quickstart workflow.", agentLabel: "Агент (необов’язково)", agentNone: "(немає)", claimFaucet: "Claim Faucet (10 ACP)", starterPack: "Активувати Starter Pack", quickstart: "Quickstart Run", errLoadAgents: "Не вдалося завантажити агентів", errFaucet: "Faucet claim не вдався", errStarter: "Starter pack assign не вдався", errSelectAgent: "Спочатку оберіть агента", errQuickstart: "Quickstart run не вдався" },
  { ...onboardingEn, title: "Onboarding", lead: "Starter-ACP abholen, Starter Pack aktivieren und Quickstart-Workflow ausführen.", agentLabel: "Agent (optional)", agentNone: "(keiner)", claimFaucet: "Faucet abholen (10 ACP)", starterPack: "Starter Pack aktivieren", quickstart: "Quickstart-Run", errLoadAgents: "Agenten konnten nicht geladen werden", errFaucet: "Faucet-Claim fehlgeschlagen", errStarter: "Starter-Pack-Zuweisung fehlgeschlagen", errSelectAgent: "Zuerst einen Agenten wählen", errQuickstart: "Quickstart-Run fehlgeschlagen" },
  { ...onboardingEn, title: "入門引導", lead: "領取入門 ACP、啟用入門包並執行快速開始工作流程。", agentLabel: "代理（選填）", agentNone: "（無）", claimFaucet: "領取水龍頭 (10 ACP)", starterPack: "啟用入門包", quickstart: "快速開始執行", errLoadAgents: "無法載入代理", errFaucet: "水龍頭領取失敗", errStarter: "入門包指派失敗", errSelectAgent: "請先選擇代理", errQuickstart: "快速開始執行失敗" }
);

export const notificationsPageByLang = tr(
  notificationsEn,
  { ...notificationsEn, title: "Уведомления", refresh: "Обновить", markRead: "Отметить прочитанным", empty: "Уведомлений нет.", errLoad: "Не удалось загрузить уведомления", errMarkRead: "Не удалось отметить прочитанным" },
  { ...notificationsEn, title: "Сповіщення", refresh: "Оновити", markRead: "Позначити прочитаним", empty: "Сповіщень немає.", errLoad: "Не вдалося завантажити сповіщення", errMarkRead: "Не вдалося позначити прочитаним" },
  { ...notificationsEn, title: "Benachrichtigungen", refresh: "Aktualisieren", markRead: "Als gelesen markieren", empty: "Keine Benachrichtigungen.", errLoad: "Benachrichtigungen konnten nicht geladen werden", errMarkRead: "Als gelesen markieren fehlgeschlagen" },
  { ...notificationsEn, title: "通知", refresh: "重新整理", markRead: "標為已讀", empty: "尚無通知。", errLoad: "無法載入通知", errMarkRead: "無法標為已讀" }
);

export const listingsPageByLang = tr(
  listingsEn,
  { ...listingsEn, kicker: "Маркетплейс создателей", title: "Платные AI-workflow листинги", lead: "Люди и AI-агенты публикуют повторяемые офферы, ценят в ACP и зарабатывают с paid runs с proof-чеками.", creatorDashboard: "Дашборд создателя", publishListing: "Опубликовать листинг", agentJson: "Agent JSON", loading: "Загрузка...", empty: "Активных листингов пока нет. Опубликуйте со страницы стратегии.", active: "active", seller: "Продавец", version: "Версия", price: "Цена", created: "Создан", strategyFallback: "Стратегия {id}" },
  { ...listingsEn, kicker: "Маркетплейс творців", title: "Платні AI-workflow лістинги", lead: "Люди та AI-агенти публікують повторювані офери, ціноутворюють у ACP і заробляють з paid runs із proof-чеками.", creatorDashboard: "Дашборд творця", publishListing: "Опублікувати лістинг", agentJson: "Agent JSON", loading: "Завантаження...", empty: "Активних лістингів ще немає. Опублікуйте зі сторінки стратегії.", active: "active", seller: "Продавець", version: "Версія", price: "Ціна", created: "Створено", strategyFallback: "Стратегія {id}" },
  { ...listingsEn, kicker: "Creator-Marktplatz", title: "Bezahlte AI-Workflow-Listings", lead: "Menschen und AI-Agenten veröffentlichen wiederholbare Ausführungsangebote, preisen in ACP und verdienen aus bezahlten Runs mit Proof-Belegen.", creatorDashboard: "Creator-Dashboard", publishListing: "Listing veröffentlichen", agentJson: "Agent JSON", loading: "Wird geladen...", empty: "Noch keine aktiven Listings. Veröffentlichen Sie eine Strategie.", active: "active", seller: "Verkäufer", version: "Version", price: "Preis", created: "Erstellt", strategyFallback: "Strategie {id}" },
  { ...listingsEn, kicker: "創作者市集", title: "付費 AI 工作流程上架", lead: "人類建置者與 AI 代理可發布可重複執行方案，以 ACP 定價，並從付費執行賺取可證明收據。", creatorDashboard: "創作者儀表板", publishListing: "發布上架", agentJson: "Agent JSON", loading: "載入中...", empty: "尚無有效上架。請從策略頁發布。", active: "active", seller: "賣家", version: "版本", price: "價格", created: "建立", strategyFallback: "策略 {id}" }
);

export const listingDetailPageByLang = tr(
  listingDetailEn,
  { ...listingDetailEn, back: "← Назад к листингам", loading: "Загрузка…", notFound: "Листинг не найден.", purchaseSuccess: "Покупка успешна", subscriptionStarted: "Подписка начата ({period}), выдан grant доступа.", orderCreated: "Заказ создан, выдан grant доступа.", viewGrants: "Смотреть grants", runStrategy: "Запустить стратегию", viewLedger: "Реестр", viewOrders: "Заказы", buyerAgent: "Агент-покупатель", noAgents: "Агентов пока нет (создайте)", createAgentHint: "Создайте агента-покупателя на", billingPeriod: "Период оплаты", noteLabel: "Заметка (необязательно)", startingSubscription: "Запуск подписки…", buying: "Покупка…", startSubscription: "Начать подписку ({period})", buyAccess: "Купить доступ", errNoBuyer: "Сначала создайте агента-покупателя (Agents → My).", periodMonthly: "Ежемесячно", periodQuarterly: "Ежеквартально", periodAnnual: "Ежегодно", billingMonthly: "Ежемесячная оплата", billingQuarterly: "Ежеквартальная оплата", billingAnnual: "Ежегодная оплата" },
  { ...listingDetailEn, back: "← Назад до лістингів", loading: "Завантаження…", notFound: "Лістинг не знайдено.", purchaseSuccess: "Покупка успішна", subscriptionStarted: "Підписку розпочато ({period}), видано grant доступу.", orderCreated: "Замовлення створено, видано grant доступу.", viewGrants: "Переглянути grants", runStrategy: "Запустити стратегію", viewLedger: "Реєстр", viewOrders: "Замовлення", buyerAgent: "Агент-покупець", noAgents: "Агентів ще немає (створіть)", createAgentHint: "Створіть агента-покупця на", billingPeriod: "Період оплати", noteLabel: "Примітка (необов’язково)", startingSubscription: "Запуск підписки…", buying: "Покупка…", startSubscription: "Розпочати підписку ({period})", buyAccess: "Купити доступ", errNoBuyer: "Спочатку створіть агента-покупця (Agents → My).", periodMonthly: "Щомісяця", periodQuarterly: "Щокварталу", periodAnnual: "Щорічно", billingMonthly: "Щомісячна оплата", billingQuarterly: "Щоквартальна оплата", billingAnnual: "Щорічна оплата" },
  { ...listingDetailEn, back: "← Zurück zu Listings", loading: "Wird geladen…", notFound: "Listing nicht gefunden.", purchaseSuccess: "Kauf erfolgreich", subscriptionStarted: "Abonnement gestartet ({period}), Zugriffsgrant ausgestellt.", orderCreated: "Bestellung erstellt, Zugriffsgrant ausgestellt.", viewGrants: "Zugriffsgrants ansehen", runStrategy: "Strategie ausführen", viewLedger: "Ledger ansehen", viewOrders: "Bestellungen ansehen", buyerAgent: "Käufer-Agent", noAgents: "Noch keine Agenten (einen erstellen)", createAgentHint: "Käufer-Agent erstellen unter", billingPeriod: "Abrechnungszeitraum", noteLabel: "Notiz (optional)", startingSubscription: "Abonnement wird gestartet…", buying: "Wird gekauft…", startSubscription: "{period}-Abonnement starten", buyAccess: "Zugang kaufen", errNoBuyer: "Zuerst einen Käufer-Agenten erstellen (Agents → My).", periodMonthly: "Monatlich", periodQuarterly: "Vierteljährlich", periodAnnual: "Jährlich", billingMonthly: "Monatliche Abrechnung", billingQuarterly: "Vierteljährliche Abrechnung", billingAnnual: "Jährliche Abrechnung" },
  { ...listingDetailEn, back: "← 返回上架列表", loading: "載入中…", notFound: "找不到上架項目。", purchaseSuccess: "購買成功", subscriptionStarted: "已開始訂閱（{period}）並核發存取授權。", orderCreated: "已建立訂單並核發存取授權。", viewGrants: "查看存取授權", runStrategy: "執行此策略", viewLedger: "查看帳本", viewOrders: "查看訂單", buyerAgent: "買方代理", noAgents: "尚無代理（請建立）", createAgentHint: "請在以下路徑建立買方代理", billingPeriod: "計費週期", noteLabel: "備註（選填）", startingSubscription: "正在開始訂閱…", buying: "購買中…", startSubscription: "開始{period}訂閱", buyAccess: "購買存取", errNoBuyer: "請先建立買方代理（Agents → My）。", periodMonthly: "每月", periodQuarterly: "每季", periodAnnual: "每年", billingMonthly: "每月計費", billingQuarterly: "每季計費", billingAnnual: "每年計費" }
);

const docsWacpRu: Tree = {
  ...docsWacpEn,
  overviewTitle: "Документация wACP",
  overviewBadge: "Публичная документация",
  overviewLead: "wACP — представление ACP в BNB Smart Chain. Этот набор документов — публичный trust layer для пользователей моста: что за актив, как должно работать резервное обеспечение, какие контракты официальны и какие риски остаются.",
  readNext: "Читать далее",
  bridgeFlow: "Поток моста",
  reserveModel: "Модель reserve proof",
  riskDisclosures: "Раскрытие рисков",
  contracts: "Контракты и официальные адреса",
  pancakeswap: "Playbook листинга PancakeSwap",
  markets: "Публичные рынки и token list",
  currentState: "Текущее публичное состояние",
  bridgeTitle: "Мост wACP",
  reserveTitle: "Модель резерва wACP",
  risksTitle: "Риски wACP",
  contractsTitle: "Контракты wACP",
  pancakeswapTitle: "wACP → PancakeSwap",
};
const docsWacpUk: Tree = {
  ...docsWacpEn,
  overviewTitle: "Документація wACP",
  overviewBadge: "Публічна документація",
  overviewLead: "wACP — представлення ACP у BNB Smart Chain. Цей набір документів — публічний trust layer для користувачів мосту.",
  readNext: "Читати далі",
  bridgeFlow: "Потік мосту",
  reserveModel: "Модель reserve proof",
  riskDisclosures: "Розкриття ризиків",
  contracts: "Контракти та офіційні адреси",
  pancakeswap: "Playbook лістингу PancakeSwap",
  markets: "Публічні ринки та token list",
  currentState: "Поточний публічний стан",
  bridgeTitle: "Міст wACP",
  reserveTitle: "Модель резерву wACP",
  risksTitle: "Ризики wACP",
  contractsTitle: "Контракти wACP",
  pancakeswapTitle: "wACP → PancakeSwap",
};
const docsWacpDe: Tree = {
  ...docsWacpEn,
  overviewTitle: "wACP-Dokumentation",
  overviewBadge: "Öffentliche Docs",
  overviewLead: "wACP ist die BNB Smart Chain-Repräsentation von ACP. Diese Dokumentation ist die öffentliche Vertrauensschicht für Bridge-Nutzer.",
  readNext: "Weiterlesen",
  bridgeFlow: "Bridge-Ablauf",
  reserveModel: "Reserve-Proof-Modell",
  riskDisclosures: "Risikohinweise",
  contracts: "Verträge und offizielle Adressen",
  pancakeswap: "PancakeSwap-Listing-Playbook",
  markets: "Öffentliche Märkte & Token-Liste",
  currentState: "Aktueller öffentlicher Stand",
  bridgeTitle: "wACP-Bridge",
  reserveTitle: "wACP-Reservemodell",
  risksTitle: "wACP-Risiken",
  contractsTitle: "wACP-Verträge",
  pancakeswapTitle: "wACP → PancakeSwap",
};
const docsWacpZh: Tree = {
  ...docsWacpEn,
  overviewTitle: "wACP 文件",
  overviewBadge: "公開文件",
  overviewLead: "wACP 是 ACP 在 BNB Smart Chain 上的代表。此文件集是橋接使用者的公開信任層。",
  readNext: "繼續閱讀",
  bridgeFlow: "橋接流程",
  reserveModel: "儲備證明模型",
  riskDisclosures: "風險揭露",
  contracts: "合約與官方地址",
  pancakeswap: "PancakeSwap 上架手冊",
  markets: "公開市場與代幣列表",
  currentState: "目前公開狀態",
  bridgeTitle: "wACP 橋接",
  reserveTitle: "wACP 儲備模型",
  risksTitle: "wACP 風險",
  contractsTitle: "wACP 合約",
  pancakeswapTitle: "wACP → PancakeSwap",
};

const docsSacpRu: Tree = {
  ...docsSacpEn,
  overviewTitle: "Stable ACP",
  overviewBadge: "Foundation",
  overviewLead: "sACP — коммерческий стейблкоин ANCAP: ориентир на USD и обеспечение ACP в BNB Smart Chain. Это не ACP (учётная единица) и не wACP (1:1 wrap).",
  readNext: "Читать далее",
  reserveLink: "Модель резерва / обеспечения",
  risksLink: "Раскрытие рисков",
  compareWacp: "Сравнить с wACP",
  publicApi: "Публичный API",
  reserveTitle: "Модель резерва / обеспечения",
  overviewLink: "Обзор",
  risksTitle: "Раскрытие рисков",
};
const docsSacpUk: Tree = {
  ...docsSacpEn,
  overviewTitle: "Stable ACP",
  overviewBadge: "Foundation",
  overviewLead: "sACP — комерційний стейблкоін ANCAP: орієнтир на USD і забезпечення ACP у BNB Smart Chain.",
  readNext: "Читати далі",
  reserveLink: "Модель резерву / забезпечення",
  risksLink: "Розкриття ризиків",
  compareWacp: "Порівняти з wACP",
  publicApi: "Публічний API",
  reserveTitle: "Модель резерву / забезпечення",
  overviewLink: "Огляд",
  risksTitle: "Розкриття ризиків",
};
const docsSacpDe: Tree = {
  ...docsSacpEn,
  overviewTitle: "Stable ACP",
  overviewBadge: "Foundation",
  overviewLead: "sACP ist ANCAPs Commerce-Stablecoin: USD-orientiert und ACP-besichert auf BNB Smart Chain.",
  readNext: "Weiterlesen",
  reserveLink: "Reserve-/Collateral-Modell",
  risksLink: "Risikohinweise",
  compareWacp: "Mit wACP vergleichen",
  publicApi: "Öffentliche API",
  reserveTitle: "Reserve-/Collateral-Modell",
  overviewLink: "Übersicht",
  risksTitle: "Risikohinweise",
};
const docsSacpZh: Tree = {
  ...docsSacpEn,
  overviewTitle: "Stable ACP",
  overviewBadge: "Foundation",
  overviewLead: "sACP 是 ANCAP 的商務穩定幣：以 USD 為目標、以 ACP 作為 BNB Smart Chain 上的抵押。",
  readNext: "繼續閱讀",
  reserveLink: "儲備／抵押模型",
  risksLink: "風險揭露",
  compareWacp: "與 wACP 比較",
  publicApi: "公開 API",
  reserveTitle: "儲備／抵押模型",
  overviewLink: "概覽",
  risksTitle: "風險揭露",
};

const docsMobileRu: Tree = {
  ...docsMobileSecurityEn,
  kicker: "Мобильная безопасность",
  title: "Модель безопасности ACP Wallet",
  badge: "Публичная документация",
  baselineTitle: "Текущие базовые контроли",
  remainingTitle: "Оставшиеся release gates",
  readNext: "Читать далее",
  bridgeFlow: "Поток моста",
  bridgeRisks: "Риски моста и custody",
  terms: "Условия",
  privacy: "Конфиденциальность",
  cyberDefense: "Коллективная киберзащита",
};
const docsMobileUk: Tree = {
  ...docsMobileSecurityEn,
  kicker: "Мобільна безпека",
  title: "Модель безпеки ACP Wallet",
  badge: "Публічна документація",
  baselineTitle: "Поточні базові контролі",
  remainingTitle: "Залишкові release gates",
  readNext: "Читати далі",
  bridgeFlow: "Потік мосту",
  bridgeRisks: "Ризики мосту та custody",
  terms: "Умови",
  privacy: "Конфіденційність",
  cyberDefense: "Колективна кіберзахист",
};
const docsMobileDe: Tree = {
  ...docsMobileSecurityEn,
  kicker: "Mobile Sicherheit",
  title: "ACP-Wallet-Sicherheitsmodell",
  badge: "Öffentliche Docs",
  baselineTitle: "Aktuelle Baseline-Kontrollen",
  remainingTitle: "Verbleibende Release-Gates",
  readNext: "Weiterlesen",
  bridgeFlow: "Bridge-Ablauf",
  bridgeRisks: "Bridge- und Custody-Risiken",
  terms: "AGB",
  privacy: "Datenschutz",
  cyberDefense: "Kollektive Cyber-Abwehr",
};
const docsMobileZh: Tree = {
  ...docsMobileSecurityEn,
  kicker: "行動安全",
  title: "ACP 錢包安全模型",
  badge: "公開文件",
  baselineTitle: "目前基線控制",
  remainingTitle: "剩餘發布關卡",
  readNext: "繼續閱讀",
  bridgeFlow: "橋接流程",
  bridgeRisks: "橋接與託管風險",
  terms: "條款",
  privacy: "隱私",
  cyberDefense: "集體網路防禦",
};

export const docsWacpByLang = tr(docsWacpEn, docsWacpRu, docsWacpUk, docsWacpDe, docsWacpZh);
export const docsSacpByLang = tr(docsSacpEn, docsSacpRu, docsSacpUk, docsSacpDe, docsSacpZh);
export const docsMobileSecurityByLang = tr(docsMobileSecurityEn, docsMobileRu, docsMobileUk, docsMobileDe, docsMobileZh);
