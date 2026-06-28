import { createApp, ref, computed, onMounted } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { resolveDataBase, loadJson, useLang, useHashRoute } from "./composables.js";
import { ItemsView } from "./components/items-view.js";
import { RecipesView } from "./components/recipes-view.js";

const mountEl = document.getElementById("app");
const DATA = resolveDataBase(mountEl);

createApp({
  components: { ItemsView, RecipesView },
  setup() {
    const loading = ref(true);
    const error = ref("");
    const notice = ref("");
    const items = ref([]);
    const recipes = ref([]);
    const aliases = ref({});
    const tr = ref({ item: {}, attribute: {}, itemType: {} });
    const { lang, langs, persistLang } = useLang();
    const { route } = useHashRoute();
    const dataBase = DATA;

    async function loadLang(l) {
      try {
        tr.value = await loadJson(DATA + "/i18n/translation." + l + ".json");
      } catch (e) {
        tr.value = { item: {}, attribute: {}, itemType: {} };
      }
    }
    function changeLang() {
      loadLang(lang.value);
      persistLang();
    }
    function notify(msg) {
      notice.value = msg;
      setTimeout(() => { if (notice.value === msg) notice.value = ""; }, 4000);
    }

    const focusId = computed(() =>
      route.value.view === "items" ? route.value.itemId : null
    );

    onMounted(async () => {
      try {
        const [it, cr, al] = await Promise.all([
          loadJson(DATA + "/items.json"),
          loadJson(DATA + "/craft.json"),
          loadJson(DATA + "/aliases.json"),
        ]);
        items.value = Object.values(it.items || {});
        recipes.value = Object.values(cr.recipes || {});
        aliases.value = (al && al.icons) || {};
        await loadLang(lang.value);
      } catch (e) {
        error.value = e.message || String(e);
      } finally {
        loading.value = false;
      }
    });

    return {
      loading, error, notice, items, recipes, aliases, tr,
      lang, langs, route, dataBase, focusId, changeLang, notify,
    };
  },
  template: `
  <div>
    <div v-if="notice" class="fixed top-3 right-3 z-20 max-w-xs rounded border border-red-300 bg-red-50 text-red-700 text-sm px-3 py-2 shadow">{{ notice }}</div>
    <header class="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-3">
        <div class="flex flex-wrap items-center gap-3">
          <h1 class="text-lg font-semibold">SpaceCraft resources</h1>
          <nav class="flex items-center gap-2 text-sm">
            <a href="#/items" :class="route.view==='items' ? 'font-semibold text-slate-900' : 'text-sky-600 hover:underline'">Items</a>
            <span class="text-slate-300">·</span>
            <a href="#/recipes" :class="route.view==='recipes' ? 'font-semibold text-slate-900' : 'text-sky-600 hover:underline'">Recipes</a>
          </nav>
          <div class="ml-auto flex items-center gap-2">
            <label class="text-sm text-slate-500">Lang</label>
            <select v-model="lang" @change="changeLang" class="border border-slate-300 rounded px-2 py-1 text-sm">
              <option v-for="l in langs" :key="l" :value="l">{{ l }}</option>
            </select>
          </div>
        </div>
      </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-5">
      <div v-if="loading" class="text-slate-500">Loading…</div>
      <div v-else-if="error" class="rounded border border-red-300 bg-red-50 p-4 text-red-700">
        <p class="font-medium">Could not load data: {{ error }}</p>
        <p class="text-sm mt-1">
          This page must be served over HTTP (browsers block <code>file://</code> fetches).
          Run <code class="bg-red-100 px-1 rounded">python sc.py serve</code> from the repo root,
          or <code class="bg-red-100 px-1 rounded">python -m http.server</code> in the repo root,
          then open <code class="bg-red-100 px-1 rounded">http://localhost:8000/</code>.
        </p>
      </div>
      <items-view v-else-if="route.view==='items'" :items="items" :aliases="aliases" :tr="tr" :base="dataBase" :focus-id="focusId" @notify="notify"></items-view>
      <recipes-view v-else :recipes="recipes" :aliases="aliases" :tr="tr" :base="dataBase"></recipes-view>
    </main>
  </div>
  `,
}).mount("#app");
