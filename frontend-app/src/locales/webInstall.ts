import type { Language } from "./translations";

type InstallCopy = { title: string; lead: string; link: string; iphone: string[]; android: string[]; help: string; result: string; open: string };

export const webInstallByLang: Record<Language, InstallCopy> = {
  "en": {
    "title": "Install ANCAP on your phone",
    "lead": "Add the ANCAP web app directly from your browser. No App Store or Google Play download is needed.",
    "link": "Installation guide",
    "iphone": [
      "Open ancap.cloud in Safari.",
      "Tap Share (or open the page menu, then Share).",
      "Choose “Add to Home Screen”.",
      "If shown, enable “Open as Web App”, then tap “Add”."
    ],
    "android": [
      "Open ancap.cloud in Chrome.",
      "Tap the three-dot menu ⋮.",
      "Choose “Add to Home screen”, then “Install” if offered. Some versions show “Install app” directly.",
      "Confirm with “Install” or “Add”."
    ],
    "help": "If the option is missing, open this page directly in Safari or Chrome instead of the browser inside a messenger. In Safari, check “Edit Actions” in the Share menu. Menu labels may vary by system language and version.",
    "result": "The ANCAP icon will appear on your home screen. Tap it to open the website. An internet connection is required.",
    "open": "Open ANCAP"
  },
  "de": {
    "title": "ANCAP auf dem Smartphone installieren",
    "lead": "Füge die ANCAP-Web-App direkt über deinen Browser zum Home-Bildschirm hinzu. Ein Download im App Store oder bei Google Play ist nicht erforderlich.",
    "link": "Installationsanleitung",
    "iphone": [
      "Öffne ancap.cloud in Safari.",
      "Tippe auf „Teilen“. Je nach Safari-Layout öffnest du dafür zuerst das Seitenmenü.",
      "Scrolle nach unten und wähle „Zum Home-Bildschirm“ bzw. „Zu Home-Bildschirm hinzufügen“.",
      "Aktiviere „Als Web-App öffnen“, falls angezeigt, und tippe auf „Hinzufügen“."
    ],
    "android": [
      "Öffne ancap.cloud in Chrome.",
      "Tippe auf das Dreipunkt-Menü ⋮.",
      "Wähle „Zum Startbildschirm hinzufügen“ bzw. „Zum Home-Bildschirm hinzufügen“ und dann „Installieren“, falls angeboten. Manche Versionen zeigen direkt „App installieren“.",
      "Bestätige mit „Installieren“ oder „Hinzufügen“."
    ],
    "help": "Fehlt die Option? Öffne die Seite direkt in Safari oder Chrome statt im integrierten Browser eines Messengers. Prüfe in Safari auch „Aktionen bearbeiten“ im Teilen-Menü. Die Bezeichnungen können je nach Systemsprache und Version abweichen.",
    "result": "Das ANCAP-Symbol erscheint auf deinem Home-Bildschirm. Tippe darauf, um die Website zu öffnen. Eine Internetverbindung ist erforderlich.",
    "open": "ANCAP öffnen"
  },
  "ru": {
    "title": "Установите ANCAP на телефон",
    "lead": "Добавьте веб-приложение ANCAP из браузера на главный экран. Загрузка из App Store или Google Play не нужна.",
    "link": "Как установить",
    "iphone": [
      "Откройте ancap.cloud в Safari.",
      "Нажмите «Поделиться» (при необходимости сначала откройте меню страницы).",
      "Выберите «На экран Домой».",
      "Если доступно, включите «Открывать как веб-приложение» и нажмите «Добавить»."
    ],
    "android": [
      "Откройте ancap.cloud в Chrome.",
      "Нажмите меню с тремя точками ⋮.",
      "Выберите «Добавить на главный экран», затем «Установить», если доступно. В некоторых версиях сразу отображается «Установить приложение».",
      "Подтвердите: «Установить» или «Добавить»."
    ],
    "help": "Нет нужного пункта? Откройте страницу напрямую в Safari или Chrome, а не во встроенном браузере мессенджера. В Safari проверьте «Править действия» в меню «Поделиться». Названия зависят от языка и версии системы.",
    "result": "Значок ANCAP появится на главном экране. Нажмите его, чтобы открыть сайт. Для работы нужен интернет.",
    "open": "Открыть ANCAP"
  },
  "uk": {
    "title": "Установіть ANCAP на телефон",
    "lead": "Додайте вебзастосунок ANCAP із браузера на початковий екран. Завантаження з App Store чи Google Play не потрібне.",
    "link": "Як установити",
    "iphone": [
      "Відкрийте ancap.cloud у Safari.",
      "Натисніть «Поширити» (за потреби спочатку відкрийте меню сторінки).",
      "Виберіть «На початковий екран».",
      "Якщо доступно, увімкніть «Відкривати як вебзастосунок» і натисніть «Додати»."
    ],
    "android": [
      "Відкрийте ancap.cloud у Chrome.",
      "Натисніть меню з трьома крапками ⋮.",
      "Виберіть «Додати на головний екран», потім «Установити», якщо доступно. Деякі версії одразу показують «Установити застосунок».",
      "Підтвердьте: «Установити» або «Додати»."
    ],
    "help": "Немає потрібного пункту? Відкрийте сторінку безпосередньо в Safari або Chrome, а не у браузері месенджера. У Safari перевірте «Редагувати дії» в меню поширення. Назви залежать від мови та версії системи.",
    "result": "Значок ANCAP з’явиться на початковому екрані. Натисніть його, щоб відкрити сайт. Потрібне підключення до інтернету.",
    "open": "Відкрити ANCAP"
  },
  "zh-Hant": {
    "title": "在手機上安裝 ANCAP",
    "lead": "直接從瀏覽器將 ANCAP 網頁應用程式加入主畫面，無需從 App Store 或 Google Play 下載。",
    "link": "安裝指南",
    "iphone": [
      "在 Safari 中開啟 ancap.cloud。",
      "點選「分享」（必要時先開啟頁面選單）。",
      "選擇「加入主畫面」。",
      "若顯示「以網頁 App 打開」，請啟用，然後點選「新增」。"
    ],
    "android": [
      "在 Chrome 中開啟 ancap.cloud。",
      "點選右上角的三點選單 ⋮。",
      "選擇「加到主畫面」，如有提供，再選擇「安裝」。部分版本會直接顯示「安裝應用程式」。",
      "點選「安裝」或「新增」以確認。"
    ],
    "help": "找不到選項？請直接使用 Safari 或 Chrome 開啟網頁，不要使用通訊軟體內建瀏覽器。在 Safari 的分享選單中也可查看「編輯動作」。選單名稱可能因系統語言和版本而異。",
    "result": "ANCAP 圖示會出現在主畫面。點選圖示即可開啟網站。使用時需要網路連線。",
    "open": "開啟 ANCAP"
  }
};
