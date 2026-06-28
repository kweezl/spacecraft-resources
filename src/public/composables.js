import { ref } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";

// Known languages produced by parse-translations (English base first).
export const LANGS = ["en", "de", "es", "fr", "pl", "pt-BR", "ru", "zh"];
const LANG_KEY = "sc-lang";

// Resolve where generated/ lives from the mount element. index.html sets
// data-data-base="./generated" (served at /generated locally and on Pages).
export function resolveDataBase(mountEl) {
  const base = mountEl && mountEl.dataset ? mountEl.dataset.dataBase : "";
  return (base && base.replace(/\/+$/, "")) || "./generated";
}

// no-store: always read freshly generated data, never a stale cache.
export async function loadJson(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(path + " → HTTP " + res.status);
  return res.json();
}

// Selected language, persisted across views via localStorage.
export function useLang() {
  function read() {
    try {
      const v = localStorage.getItem(LANG_KEY);
      return LANGS.includes(v) ? v : "en";
    } catch (e) {
      return "en";
    }
  }
  const lang = ref(read());
  function persistLang() {
    try {
      localStorage.setItem(LANG_KEY, lang.value);
    } catch (e) {
      /* ignore storage failures */
    }
  }
  return { lang, langs: LANGS, persistLang };
}

// id -> icon URL, resolved through aliases (dedup-safe); null when no icon.
// `dir` selects the icon set folder (icons | icons-categories | icons-factions).
export function useIcons(base, aliasesRef, dir = "icons") {
  function iconSrc(id) {
    const f = aliasesRef.value[id];
    return f ? base + "/" + dir + "/" + f : null;
  }
  return { iconSrc };
}

// Localized lookups over a translation map ({ item, attribute, itemType, ... }).
export function useTranslations(trRef) {
  const name = (id) => trRef.value.item?.[id]?.name || null;
  const desc = (id) => trRef.value.item?.[id]?.desc || null;
  const attrName = (code) => trRef.value.attribute?.[code]?.name || code;
  const categoryLabel = (id) => trRef.value.itemType?.[id]?.name || id;
  const workshopName = (id) => trRef.value.workshop?.[id]?.name || id;
  const contractTitle = (id) => trRef.value.contract?.[id]?.name || id;
  const spaceObjectName = (id) => trRef.value.spaceObject?.[id]?.name || id;
  const factionName = (id) => trRef.value.faction?.[id]?.name || id;
  const instanceName = (id) => trRef.value.instance?.[id]?.name || id;
  return {
    name, desc, attrName, categoryLabel,
    workshopName, contractTitle, spaceObjectName, factionName, instanceName,
  };
}

// Path-style hash routing: #/items, #/items/<id>, #/recipes, plus the new
// single-segment views (legacy #item-<id> still supported).
export function useHashRoute() {
  const VIEWS = ["items", "recipes", "workshops", "contracts", "categories", "space-objects", "factions"];
  function parse() {
    const h = location.hash || "";
    let m = h.match(/^#item-(.+)$/); // legacy deep link
    if (m) return { view: "items", itemId: decodeURIComponent(m[1]) };
    m = h.match(/^#\/items\/(.+)$/);
    if (m) return { view: "items", itemId: decodeURIComponent(m[1]) };
    m = h.match(/^#\/([a-z-]+)$/);
    if (m && VIEWS.includes(m[1])) return { view: m[1], itemId: null };
    return { view: "items", itemId: null };
  }
  const route = ref(parse());
  window.addEventListener("hashchange", () => {
    route.value = parse();
  });
  return { route };
}
