# -*- coding: utf-8 -*-
"""Replace mostly-English de/zhHant maps with full translations, then rewrite exports."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "frontend-app" / "src" / "lib" / "projectOffersCopy.ts"
CURATED = Path(__file__).with_name("offer_locales_de_zh.json")


def parse_en() -> dict:
    t = TARGET.read_text(encoding="utf-8")
    block = t.split("const en: OfferCopyMap = {", 1)[1].split("\n};\n\nconst ru:", 1)[0]
    out = {}
    for m in re.finditer(r'"(/(?:[^"]+))"\s*:\s*\{(.*?)\n  \},?', block, re.S):
        href = m.group(1)
        body = m.group(2)
        fields = {}
        for fm in re.finditer(r'(\w+):\s*"((?:\\.|[^"\\])*)"', body):
            fields[fm.group(1)] = fm.group(2).replace('\\"', '"')
        out[href] = fields
    return out


# Full professional DE + zh-Hant maps (all portfolio routes).
DE = {
  "/markets": {"buyer":"Token-/Krypto-Team bei Markt- oder Rohstoffanalyse","task":"Strukturiertes Markt- oder Momentum-Briefing für die Planung erhalten","inputs":"Asset- oder Rohstofffokus, Horizont, Risikohinweise","aiResult":"Markt- oder Momentum-Briefing (Dokument)","constraints":"Keine Anlageberatung; kein Live-Handelsbot; öffentliche Listing-Widgets sind von bezahlten Briefings getrennt","payment":"ACP / wACP über Workflow-Store-Checkout","receipt":"Ausführungsbeleg mit Preis-Snapshot, Input-Hash und Status-Timeline"},
  "/business": {"buyer":"Gründer, der ein kommerzielles KI-Workflow-Angebot paketiert","task":"Geschäfts-/Angebotsbriefing vor dem Verkauf der Ausführung vorbereiten","inputs":"Angebotsbeschreibung, Zielgruppe, Preisabsicht","aiResult":"Memo zu Positionierung und Anforderungen","constraints":"Seite führt zu kommerziellen Tools; SKU vor Zahlung in /ai/workflows bestätigen","payment":"ACP bei Auswahl eines Katalog-SKU","receipt":"Proof-Beleg nach abgeschlossener Ausführung"},
  "/growth": {"buyer":"Krypto-Growth- oder Community-Lead","task":"Kampagnen- oder Telegram-Betriebsplan erstellen","inputs":"Zielgruppe, Kanäle, Launch-Fenster, Grenzen","aiResult":"Kampagnenplan, Post-Ideen, Ops-Checkliste","constraints":"Kauft keine Anzeigen und garantiert kein Follower-Wachstum","payment":"ACP / wACP","receipt":"Workflow-Ausführungsbeleg"},
  "/agency": {"buyer":"Team mit Bedarf an agency-ähnlichen Launch-Unterlagen","task":"Listing-, Risiko- und Kampagnenmaterialien in einem Paket bündeln","inputs":"Projektdaten, Token-Referenzen, Kanalziele","aiResult":"Gebündelte Launch-/Wachstumsdokumente","constraints":"Seite führt zu Katalogpaketen; Ergebnis sind Dokumente, keine Managed Services","payment":"ACP / wACP beim Paket-Checkout","receipt":"Bundle-Ausführungsbeleg"},
  "/startups": {"buyer":"Startup vor Token- oder Produktlaunch","task":"Listing-Texte und Launch-Readiness-Unterlagen erzeugen","inputs":"Projektname, Narrative, Chain, Checklistenantworten","aiResult":"Listing-Pack- / Launch-Audit-Dokumente","constraints":"Keine Börsenlisting-Garantie","payment":"ACP / wACP","receipt":"Proof-Beleg"},
  "/counsel": {"buyer":"Gründer bei Counsel-/Jurisdiktions-Intake","task":"Strukturiertes Intake für einen qualifizierten Berater erzeugen","inputs":"Jurisdiktionsabsicht, Entitätsdaten, Dokumenthinweise","aiResult":"Counsel-Matching- / Entity- / Vertrags-Intake-Briefing","constraints":"Keine Rechtsberatung; lizenzierter Counsel erforderlich","payment":"ACP für Briefing-Erzeugung","receipt":"Ausführungsbeleg; Beraterengagement separat"},
  "/insurance": {"buyer":"Betreiber zur Insurance-Desk-Literacy","task":"Framing von Insurance-Desk/Produkten verstehen","inputs":"Risikothema und Deckungsfragen","aiResult":"Planungshinweise / Desk-Übergabe (falls SKU gelistet)","constraints":"Keine Versicherungspolice; kein Maklerlizenzanspruch","payment":"Kein Fake-Checkout — Katalog nutzen, falls SKU erscheint","receipt":"N/A bis ein ausführbares SKU gewählt wird"},
  "/compliance": {"buyer":"Team für Governance-/Compliance-Readiness-Dokumente","task":"AI/ISO-Readiness- oder Compliance-Pack erstellen","inputs":"Prozessbeschreibung, Kontrollen, Evidenzinventar","aiResult":"Governance-/Compliance-Readiness-Dokumente","constraints":"Nur Readiness-Unterstützung — keine Zertifizierung","payment":"ACP / wACP","receipt":"Proof-Beleg mit Governance-Scope-Metadaten"},
  "/careers": {"buyer":"Bewerber oder Hiring Lead","task":"Offene Rollen und Bewerbungspfad prüfen","inputs":"Bewerbungsunterlagen (außerhalb oder Formular)","aiResult":"Keine — Stellenliste, kein bezahltes KI-Ergebnis","constraints":"Kein Workflow-SKU; keine ACP-Käufe von Beschäftigung","payment":"Keine","receipt":"N/A"},
  "/flora": {"buyer":"Käufer/Verkäufer zur Blumenauktions-Literacy","task":"FLORA-Auktions-/Katalogflächen nutzen","inputs":"Los- oder Anfragedetails bei geöffnetem Desk","aiResult":"Auktions-/Desk-Artefakte wenn aktiv — keine botanische Garantie","constraints":"Partner-/Auktionsschiene; Live-SKU vor Zahlung bestätigen","payment":"Desk-/Auktionsabrechnung wenn angeboten","receipt":"Auktions- oder Deskbeleg falls ausgestellt"},
  "/literary": {"buyer":"Autor oder Sammler am Literary-Auction-Desk","task":"Über Literary-Auktionsflächen listen oder bieten","inputs":"Werkmetadaten / Gebotsabsicht","aiResult":"Desk-Artefakte; standardmäßig kein Verlagsvertrag","constraints":"Auktionsdesk — keine automatische Buchdistribution","payment":"Auktion/Desk wenn angeboten","receipt":"Deskbeleg falls ausgestellt"},
  "/marketplace": {"buyer":"Käufer von Marketplace-Listings","task":"Gelistete Angebote durchsuchen und kaufen","inputs":"Listing-Auswahl und Zahlungsmethode","aiResult":"Abhängig vom Listing — ggf. nicht-KI-Waren/Dienste","constraints":"Marketplace-Aufträge sind von Workflow-Store-SKUs getrennt","payment":"Nach Listing-Bedingungen","receipt":"Auftragsbeleg falls ausgestellt"},
  "/field-services": {"buyer":"Kunde für IT-/CCTV-/Solar-Installationsvorbereitung vor Ort","task":"Installations-/Service-Intake für Technikpartner erzeugen","inputs":"Standortdetails, Servicetyp, Grenzen","aiResult":"Installations-/Service-Intake-Briefing","constraints":"Partner führt physische Arbeit aus; ANCAP verkauft das Intake-Dokument","payment":"ACP für Intake-SKU","receipt":"Ausführungsbeleg; Vor-Ort-Besuch partnerseitig"},
  "/starlink-install": {"buyer":"Kunde bei Starlink-Installationsplanung","task":"Install-Intake-/SKU-Briefing für Partner-Installer vorbereiten","inputs":"Standorttyp, Montagehinweise, Service-Stufe","aiResult":"Starlink-Install-Intake-Dokumente","constraints":"Kein Starlink-Hardwareverkauf durch ANCAP; kein SpaceX-Partnerschaftsanspruch","payment":"ACP für gelistete Install-SKUs","receipt":"Ausführungs-/Auftragsbeleg"},
  "/antique-fire-restore": {"buyer":"Eigentümer zur Konservierungs-Literacy nach Brand","task":"Konservierungsplan-Briefing erhalten (Artefaktanalogie)","inputs":"Artefaktbeschreibung, Schadenshinweise","aiResult":"Konservierungs-/Reverse-Combustion-Literacy-Briefing","constraints":"Keine medizinische Brandversorgung; kein garantiertes Restaurierungsergebnis","payment":"ACP bei SKU-Kauf","receipt":"Proof-Beleg"},
  "/humanitarian": {"buyer":"Spender oder Organisator für humanitären Desk-Handoff","task":"ACP-preisiges humanitäres Briefing / Channel-Handoff wählen","inputs":"Hilfsthema und Jurisdiktionshinweise","aiResult":"Desk-Briefing und Red-Cross-/Partnerlisting-Handoff","constraints":"Keine 135-FZ-Wohltätigkeit; keine ICRC/IFRC-Partnerschaft; standardmäßig nicht steuerlich absetzbar","payment":"ACP-Deskbeträge wenn auf /humanitarian angeboten","receipt":"Deskbeleg falls ausgestellt — kein Spendenbeleg"},
  "/aeterna": {"buyer":"Person bei Longevity-/Genomik-Partnerkonsultation","task":"Bildungs-/Consult-Prep-Briefing aus Vault- oder Panel-Eingaben kaufen","inputs":"Einwilligte Vault-Metadaten, Lifestyle-Hinweise, Intent-Art","aiResult":"Partnerreifes Consult-Briefing (Dokument)","constraints":"Keine Diagnose, Behandlung, Wet-Lab-Protokoll oder physische Medizinleistung","payment":"Hohe ACP-Preise im Katalog — vor Checkout bestätigen","receipt":"Proof-Beleg; klinische Versorgung bleibt bei lizenzierten Partnern"},
  "/dna-bank": {"buyer":"Nutzer zur DNA/RNA-Vault-Literacy","task":"Vault-Speicher-/Hash-Workflow verstehen","inputs":"Einwilligung und Vault-Metadaten wenn aktiv","aiResult":"Vault-/Bank-Literacy-Materialien; optionale AETERNA-Briefings","constraints":"Verschlüsselungs-Vault ist kein klinisches Labor","payment":"ACP für verknüpfte Briefings bei Auswahl","receipt":"Vault-/Ausführungsbeleg soweit zutreffend"},
  "/cryo": {"buyer":"Person am Kryokonservierungs-Partnerdesk","task":"Leistungen prüfen und Partner-Intake anfragen","inputs":"Serviceauswahl, Jurisdiktion","aiResult":"Desk-Katalog + Partner-Handoff-Materialien","constraints":"Nur lizenzierte Kryo-Partner; ANCAP betreibt keine Gefrieranlagen","payment":"Partner-/Deskpreise wenn angeboten","receipt":"Deskbeleg falls ausgestellt"},
  "/saliva-rx": {"buyer":"Research-Leser zur Speicheldiagnostik-Literacy","task":"Research-Briefing-Framing lesen","inputs":"Keine für Seiten-Literacy; Katalog-SKU falls später gelistet","aiResult":"Nur Research-Briefing-Framing auf dieser Seite","constraints":"Keine Apotheke und kein Rezeptdienst","payment":"Keine auf der Seite","receipt":"N/A"},
  "/fauna": {"buyer":"Leser zu veterinärer / Fauna-Research-Framing","task":"Research-/Partner-Literacy prüfen","inputs":"Optionale AETERNA-Vet-Briefing-Eingaben über Katalog","aiResult":"Research-Framing; Vet-Briefings über AETERNA-SKUs bei Auswahl","constraints":"Konzept-/Research-Framing — keine veterinäre Prozedur; lizenzierter Tierarzt nur für klinische Akte","payment":"ACP nur bei Kauf eines AETERNA-Vet-Briefing-SKU","receipt":"Briefing-Beleg — keine veterinäre Prozedur"},
  "/tech": {"buyer":"Betreiber zur Tech-/Wetter-Desk-Literacy","task":"Tech-Desk-Konzepte und Auktionsfloors prüfen","inputs":"Auktions- oder Briefing-Eingaben bei SKU-Wahl","aiResult":"Desk-/Auktionsplanungsdokumente","constraints":"Steuert kein Wetter und setzt keine physische Infrastruktur ein","payment":"Auktion oder SKU wenn angeboten — kein Wetterergebnis","receipt":"Auktions-/Ausführungsbeleg falls ausgestellt"},
  "/perimeter": {"buyer":"Sicherheitsplaner zu Perimeter-Konzepten","task":"Perimeter-/Security-Literacy lesen","inputs":"Keine, sofern kein Katalog-SKU ergänzt wird","aiResult":"Konzept-Framing","constraints":"Kein betriebenes Security Operations Center","payment":"Keine auf der Seite","receipt":"N/A"},
  "/galaxy": {"buyer":"Forscher zur Space-AI-Architektur-Literacy","task":"Space-/Orbit-Konzeptbriefing erhalten","inputs":"Missionsthema, Grenzen","aiResult":"Orbit-/Architektur-Literacy-Briefing","constraints":"Nur Konzeptbriefing — kein Satelliteneigentum und keine Flight Ops","payment":"ACP für gelistete Space-AI-Briefings","receipt":"Proof-Beleg der Dokumentausführung"},
  "/lunar": {"buyer":"Forscher zur Lunar-Land-Registry-Literacy","task":"Parcel-/Interest-Desk-Framing prüfen","inputs":"Parcel-Interest-Hinweise bei aktivem Desk","aiResult":"Registry-/Interest-Desk-Dokumente wenn angeboten","constraints":"Science-tagged Registry-Literacy — kein Titel auf Mondgebiet","payment":"Deskbeträge nur wenn ausdrücklich angeboten","receipt":"N/A sofern Desk keinen Beleg ausstellt"},
  "/stardust": {"buyer":"Forscher zu Wettermonitoring-Konzeptbriefings","task":"Weather-Monitor-/Early-Warning-Konzept-SKUs studieren","inputs":"Region und Monitoring-Absicht","aiResult":"Monitoring-/Warnkonzept-Dokumente","constraints":"Steuert kein Wetter; Auktionsfloors sind keine Ergebnisgarantien","payment":"ACP / Auktion wenn angeboten","receipt":"Dokument-/Auktionsbeleg — kein Weather-Control-Zertifikat"},
  "/quantum-sim": {"buyer":"Entwickler zu Quantum-SIM-Konzepten","task":"Quantum-SIM-Literacy lesen","inputs":"Keine, sofern kein SKU ergänzt wird","aiResult":"Konzept-Framing","constraints":"Simulations-Literacy — kein Carrier-SIM-Produktanspruch","payment":"Keine auf der Seite","receipt":"N/A"},
  "/nexus": {"buyer":"Community-Betreiber","task":"Social-/Nexus-Funktionen pilotieren","inputs":"Profil und Post-Inhalte","aiResult":"Pilot-App-Artefakte — keine garantierte Reichweite","constraints":"Pilotfläche","payment":"Keine, sofern kein Katalog-SKU verknüpft ist","receipt":"N/A"},
  "/dating": {"buyer":"Pilotnutzer","task":"Dating-Pilotflächen testen","inputs":"Profildaten","aiResult":"Pilot-Matching-UI — keine Matchmaking-Garantie","constraints":"Pilot","payment":"Standardmäßig keine","receipt":"N/A"},
  "/entertainment": {"buyer":"Eventplaner zur Entertainment-Literacy","task":"Entertainment-SKU-/Party-Briefing prüfen falls gelistet","inputs":"Eventhinweise beim SKU-Kauf","aiResult":"Entertainment-Planungsbriefing wenn SKU existiert","constraints":"Pilot-/Spezial-SKU — Katalog bestätigen","payment":"ACP bei SKU-Kauf","receipt":"Ausführungsbeleg"},
  "/arena": {"buyer":"Pilotteilnehmer","task":"Arena-Pilotflächen nutzen","inputs":"Teilnahmedaten","aiResult":"Pilot-Artefakte","constraints":"Pilot","payment":"Standardmäßig keine","receipt":"N/A"},
  "/feed": {"buyer":"Pilot-Leser/Creator","task":"Feed-Pilot nutzen","inputs":"Beiträge","aiResult":"Feed-Inhalte — standardmäßig kein bezahlter Workflow","constraints":"Pilot","payment":"Standardmäßig keine","receipt":"N/A"},
}

ZH = {
  "/markets": {"buyer":"準備市場或大宗商品分析的代幣／加密團隊","task":"取得結構化市場或動能簡報以供規劃","inputs":"資產或商品焦點、時間範圍、風險備註","aiResult":"市場方向或動能簡報（文件）","constraints":"非投資建議；非即時交易機器人；頁面公開上架元件與付費簡報分開","payment":"透過 workflow-store 結帳以 ACP／wACP 付款","receipt":"含價格快照、輸入雜湊與狀態時間軸的執行憑證"},
  "/business": {"buyer":"正在包裝商業 AI 工作流程方案的創辦人","task":"在販售執行前準備商業／方案簡報","inputs":"方案描述、受眾、定價意圖","aiResult":"定位與需求備忘","constraints":"頁面導向商業工具；付款前請在 /ai/workflows 確認 SKU","payment":"選擇目錄 SKU 時以 ACP 付款","receipt":"完成執行後的證明憑證"},
  "/growth": {"buyer":"加密成長或社群負責人","task":"建立活動或 Telegram 營運計畫","inputs":"受眾、通路、上線時窗、限制","aiResult":"活動計畫、貼文構想、營運清單","constraints":"不代買廣告，也不保證粉絲成長","payment":"ACP／wACP","receipt":"工作流程執行憑證"},
  "/agency": {"buyer":"需要代理風格上線資料的團隊","task":"將上架、風險與行銷資料打包","inputs":"專案事實、代幣參考、通路目標","aiResult":"打包的上線／成長文件","constraints":"頁面導向目錄套餐；交付是文件而非代管服務","payment":"套餐結帳時以 ACP／wACP 付款","receipt":"套餐執行憑證"},
  "/startups": {"buyer":"準備代幣或產品上線的新創","task":"產生上架文案與上線就緒資料","inputs":"專案名稱、敘事、鏈別、清單回答","aiResult":"上架套件／上線稽核文件","constraints":"不保證交易所上架","payment":"ACP／wACP","receipt":"證明憑證"},
  "/counsel": {"buyer":"準備法律顧問／管轄區收件的創辦人","task":"產出給合格顧問的結構化收件簡報","inputs":"管轄意圖、實體事實、文件備註","aiResult":"顧問媒合／實體／合約收件簡報","constraints":"非法律意見；需有合格顧問","payment":"以 ACP 產生簡報","receipt":"執行憑證；顧問服務另計"},
  "/insurance": {"buyer":"探索保險服務台識讀的營運者","task":"理解保險服務台／產品框架","inputs":"風險主題與保障問題","aiResult":"規劃備註／服務台交接（若有 SKU）","constraints":"非保單；非經紀牌照主張","payment":"本頁無假結帳——若出現 SKU 請用目錄","receipt":"在選擇可執行 SKU 前不適用"},
  "/compliance": {"buyer":"準備治理／合規就緒文件的團隊","task":"建立 AI／ISO 就緒或合規套件","inputs":"流程描述、控制措施、證據清冊","aiResult":"治理／合規就緒文件","constraints":"僅就緒支援——非認證","payment":"ACP／wACP","receipt":"含治理範圍中繼資料的證明憑證"},
  "/careers": {"buyer":"應徵者或招募負責人","task":"查看職缺與申請路徑","inputs":"申請資料（站外或表單）","aiResult":"無——職缺列表，非付費 AI 成果","constraints":"非工作流程 SKU；不能用 ACP 購買就業","payment":"無","receipt":"不適用"},
  "/flora": {"buyer":"探索花卉拍賣識讀的買賣方","task":"使用 FLORA 拍賣／目錄介面","inputs":"服務台開放時的拍品或請求細節","aiResult":"啟用時的拍賣／服務台產物——非植物學保證","constraints":"合作／拍賣軌道；付款前確認即時 SKU","payment":"有提供時以服務台／拍賣結算","receipt":"若開立則為拍賣或服務台憑證"},
  "/literary": {"buyer":"使用文學拍賣服務台的作者或收藏者","task":"透過文學拍賣介面上架或出價","inputs":"作品中繼資料／出價意圖","aiResult":"服務台產物；預設非出版合約","constraints":"拍賣服務台——非自動書籍發行","payment":"有提供時以拍賣／服務台付款","receipt":"若開立則為服務台憑證"},
  "/marketplace": {"buyer":"市集上架買家","task":"瀏覽並購買上架方案","inputs":"上架選擇與付款方式","aiResult":"視上架而定——可能是非 AI 商品／服務","constraints":"市集訂單與 workflow-store SKU 分開","payment":"依上架條款","receipt":"若開立則為訂單憑證"},
  "/field-services": {"buyer":"需要現場 IT／監視／太陽能安裝準備的客戶","task":"為技術合作夥伴產生安裝／服務收件簡報","inputs":"場地細節、服務類型、限制","aiResult":"安裝／服務收件簡報","constraints":"實體工作由合作夥伴執行；ANCAP 販售收件文件","payment":"以 ACP 購買收件 SKU","receipt":"執行憑證；現場造訪由合作夥伴負責"},
  "/starlink-install": {"buyer":"規劃 Starlink 安裝的客戶","task":"為合作安裝商準備安裝收件／SKU 簡報","inputs":"場地類型、安裝備註、服務層級","aiResult":"Starlink 安裝收件文件","constraints":"ANCAP 不販售 Starlink 硬體；非 SpaceX 合作主張","payment":"以 ACP 購買列出的安裝 SKU","receipt":"執行／訂單憑證"},
  "/antique-fire-restore": {"buyer":"火災後探索保存識讀的所有人","task":"取得保存規劃簡報（文物類比）","inputs":"文物描述、損害備註","aiResult":"保存／逆燃燒識讀簡報","constraints":"非醫療燒傷照護；非保證修復結果","payment":"購買 SKU 時以 ACP 付款","receipt":"證明憑證"},
  "/humanitarian": {"buyer":"尋求人道服務台交接的捐助者或組織者","task":"選擇以 ACP 計價的人道簡報／通路交接","inputs":"援助主題與管轄備註","aiResult":"服務台簡報與紅十字／合作上架交接","constraints":"非 135-FZ 慈善；非 ICRC／IFRC 合作；預設不可抵稅","payment":"若 /humanitarian 有提供則以 ACP 服務台金額付款","receipt":"若開立則為服務台憑證——非捐款憑證"},
  "/aeterna": {"buyer":"準備長壽／基因體合作諮詢的個人","task":"以保險庫或面板輸入購買教育／諮詢準備簡報","inputs":"經同意的保險庫中繼資料、生活型態備註、意圖類型","aiResult":"可供合作方使用的諮詢簡報（文件）","constraints":"非診斷、治療、濕式實驗流程或實體醫療服務","payment":"目錄 SKU 價格偏高——結帳前請確認","receipt":"證明憑證；臨床照護仍由合格合作方負責"},
  "/dna-bank": {"buyer":"探索 DNA／RNA 保險庫識讀的使用者","task":"理解保險庫儲存／雜湊流程","inputs":"啟用時的同意與保險庫中繼資料","aiResult":"保險庫／銀行識讀資料；可選 AETERNA 簡報","constraints":"加密保險庫工具不是臨床實驗室服務","payment":"選擇時以 ACP 購買連結簡報","receipt":"適用時的保險庫／執行憑證"},
  "/cryo": {"buyer":"探索冷凍保存合作服務台的個人","task":"查看服務並申請合作收件","inputs":"服務選擇、管轄區","aiResult":"服務台目錄＋合作交接資料","constraints":"僅限合格冷凍合作方；ANCAP 不營運冷凍設備","payment":"有提供時依合作／服務台定價","receipt":"若開立則為服務台憑證"},
  "/saliva-rx": {"buyer":"探索唾液診斷識讀的研究讀者","task":"閱讀研究簡報框架","inputs":"頁面識讀無需輸入；之後若有目錄 SKU 再使用","aiResult":"本頁僅研究簡報框架","constraints":"非藥局或處方服務","payment":"本頁無","receipt":"不適用"},
  "/fauna": {"buyer":"探索獸醫／動物研究框架的讀者","task":"查看研究／合作識讀","inputs":"可選透過目錄提供的 AETERNA 獸醫簡報輸入","aiResult":"研究框架；若選擇則透過 AETERNA SKU 提供獸醫簡報","constraints":"概念／研究框架——非獸醫處置；臨床行為僅限合格獸醫","payment":"僅在購買 AETERNA 獸醫簡報 SKU 時以 ACP 付款","receipt":"簡報憑證——非獸醫處置"},
  "/tech": {"buyer":"探索科技／天氣服務台識讀的營運者","task":"查看科技服務台概念與拍賣底價","inputs":"選擇 SKU 時的拍賣或簡報輸入","aiResult":"服務台／拍賣規劃文件","constraints":"不控制天氣，也不部署實體基礎設施","payment":"有提供時以拍賣或 SKU 付款——非天氣結果","receipt":"若開立則為拍賣／執行憑證"},
  "/perimeter": {"buyer":"探索周界概念的安全規劃者","task":"閱讀周界／安全識讀","inputs":"除非新增目錄 SKU，否則無","aiResult":"概念框架","constraints":"非已部署的資安營運中心","payment":"本頁無","receipt":"不適用"},
  "/galaxy": {"buyer":"探索太空 AI 架構識讀的研究者","task":"取得太空／軌道概念簡報","inputs":"任務主題、限制","aiResult":"軌道／架構識讀簡報","constraints":"僅概念簡報——非衛星所有權或飛行作業","payment":"以 ACP 購買列出的太空 AI 簡報","receipt":"文件執行的證明憑證"},
  "/lunar": {"buyer":"探索月球土地登記識讀的研究者","task":"查看地塊／意向服務台框架","inputs":"服務台啟用時的地塊意向備註","aiResult":"有提供時的登記／意向服務台文件","constraints":"科學標記登記識讀——非月球領土所有權","payment":"僅在明確提供時以服務台金額付款","receipt":"除非服務台開立，否則不適用"},
  "/stardust": {"buyer":"探索天氣監測概念簡報的研究者","task":"研讀天氣監測／預警概念 SKU","inputs":"區域與監測意圖","aiResult":"監測／預警概念文件","constraints":"不控制天氣；拍賣底價非結果保證","payment":"有提供時以 ACP／拍賣付款","receipt":"文件／拍賣憑證——非控天憑證"},
  "/quantum-sim": {"buyer":"探索量子 SIM 概念的開發者","task":"閱讀量子 SIM 識讀","inputs":"除非新增 SKU，否則無","aiResult":"概念框架","constraints":"模擬識讀——非電信 SIM 產品主張","payment":"本頁無","receipt":"不適用"},
  "/nexus": {"buyer":"社群營運者","task":"試點社群／Nexus 功能","inputs":"個人檔與貼文內容","aiResult":"試點應用產物——非保證受眾","constraints":"試點介面","payment":"除非連結目錄 SKU，否則無","receipt":"不適用"},
  "/dating": {"buyer":"試點使用者","task":"試用交友試點介面","inputs":"個人資料","aiResult":"試點配對介面——非配對保證","constraints":"試點","payment":"預設無","receipt":"不適用"},
  "/entertainment": {"buyer":"探索娛樂識讀的活動規劃者","task":"若有列出則查看娛樂 SKU／派對簡報","inputs":"購買 SKU 時的活動備註","aiResult":"若有 SKU 則為娛樂規劃簡報","constraints":"試點／特殊 SKU——請確認目錄","payment":"購買 SKU 時以 ACP 付款","receipt":"執行憑證"},
  "/arena": {"buyer":"試點參與者","task":"使用 Arena 試點介面","inputs":"參與資料","aiResult":"試點產物","constraints":"試點","payment":"預設無","receipt":"不適用"},
  "/feed": {"buyer":"試點讀者／創作者","task":"使用動態試點","inputs":"貼文","aiResult":"動態內容——預設非付費工作流程","constraints":"試點","payment":"預設無","receipt":"不適用"},
}


def main() -> None:
    en = parse_en()
    assert set(DE) == set(en) == set(ZH)
    CURATED.write_text(json.dumps({"de": DE, "zh-Hant": ZH}, ensure_ascii=False, indent=2), encoding="utf-8")
    # Re-run locale generator so de/zh come from curated JSON
    import subprocess
    import sys

    subprocess.check_call([sys.executable, str(Path(__file__).with_name("_gen_offer_locales.py"))])
    # Force rewrite de/zh sections from curated (generator may have already completed)
    text = TARGET.read_text(encoding="utf-8")
    # Replace de and zhHant object bodies
    def replace_map(src: str, const_name: str, data: dict) -> str:
        pattern = rf"const {const_name}: OfferCopyMap = \{{.*?\n\}};"
        lines = [f"const {const_name}: OfferCopyMap = {{"]
        for href, fields in data.items():
            lines.append(f'  "{href}": {{')
            for key in ("buyer", "task", "inputs", "aiResult", "constraints", "payment", "receipt"):
                val = fields[key].replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'    {key}: "{val}",')
            lines.append("  },")
        lines.append("};")
        repl = "\n".join(lines)
        new_src, n = re.subn(pattern, repl, src, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"failed replace {const_name}: {n}")
        return new_src

    text = replace_map(text, "de", DE)
    text = replace_map(text, "zhHant", ZH)
    TARGET.write_text(text, encoding="utf-8")
    print("filled_de_zh", len(DE))


if __name__ == "__main__":
    main()
