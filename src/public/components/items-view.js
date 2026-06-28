import { ref, computed, watch, nextTick, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

export const ItemsView = {
  name: "items-view",
  props: {
    items: { type: Array, required: true },
    aliases: { type: Object, required: true },
    tr: { type: Object, required: true },
    base: { type: String, required: true },
    focusId: { type: String, default: null },
    categoriesById: { type: Object, default: () => ({}) },
    categoryAliases: { type: Object, default: () => ({}) },
  },
  emits: ["notify"],
  setup(props, { emit }) {
    const { iconSrc } = useIcons(props.base, toRef(props, "aliases"));
    const { iconSrc: categoryIcon } = useIcons(props.base, toRef(props, "categoryAliases"), "icons-categories");
    const { name, desc, attrName, categoryLabel } = useTranslations(toRef(props, "tr"));

    const search = ref("");
    // Category selection is a token: "all" | "main:<id>" | "sub:<id>".
    const catSel = ref("all");
    const missingOnly = ref(false);
    const view = ref("cards");
    const imgFailed = ref({});
    const flashId = ref(null);

    const chipFields = ["tags", "skills", "compatibleSkills", "lootMaterial"];
    const tableColumns = [
      { key: "name", label: "name" },
      { key: "id", label: "id" },
      { key: "type", label: "type" },
      { key: "price", label: "price" },
      { key: "lootLevel", label: "loot" },
      { key: "storage", label: "storage" },
      { key: "attrs", label: "#attr" },
    ];

    // The game groups items under a main display category (the itemType the parser
    // resolved into `displayCategory`) and a subcategory below it (`subcategory`),
    // not by the leaf `type`. Items the parser left unresolved fall into one
    // "(uncategorized)" main bucket.
    const UNCATEGORIZED = "(uncategorized)";
    function itemCategory(it) {
      return it.displayCategory || UNCATEGORIZED;
    }
    function catLabel(id) {
      return id === UNCATEGORIZED ? "(uncategorized)" : categoryLabel(id);
    }
    // Order categories by the game's categoryIndex when available, else by name.
    function catOrder(id) {
      const ci = props.categoriesById[id] && props.categoriesById[id].props
        ? props.categoriesById[id].props.categoryIndex : undefined;
      return ci === undefined || ci === null ? Infinity : ci;
    }

    // main -> { id, label, count, subs: [{id,label,count}] }, both levels sorted.
    const categoryTree = computed(() => {
      const mains = {};
      for (const it of props.items) {
        const m = itemCategory(it);
        const entry = mains[m] || (mains[m] = { id: m, count: 0, subs: {} });
        entry.count++;
        if (it.subcategory) entry.subs[it.subcategory] = (entry.subs[it.subcategory] || 0) + 1;
      }
      const bySort = (a, b) => (catOrder(a.id) - catOrder(b.id)) || a.label.localeCompare(b.label);
      return Object.values(mains)
        .map((m) => ({
          id: m.id,
          label: catLabel(m.id),
          count: m.count,
          subs: Object.entries(m.subs)
            .map(([id, count]) => ({ id, label: categoryLabel(id), count }))
            .sort(bySort),
        }))
        .sort(bySort);
    });

    const missingIconCount = computed(() =>
      props.items.reduce((n, it) => n + (iconSrc(it.id) ? 0 : 1), 0)
    );

    const filtered = computed(() => {
      let list = props.items;
      const sel = catSel.value;
      if (sel.startsWith("main:")) {
        const id = sel.slice(5);
        list = list.filter((i) => itemCategory(i) === id);
      } else if (sel.startsWith("sub:")) {
        const id = sel.slice(4);
        list = list.filter((i) => i.subcategory === id);
      }
      if (missingOnly.value) list = list.filter((i) => !iconSrc(i.id));
      const q = search.value.trim().toLowerCase();
      if (q) {
        list = list.filter(
          (i) =>
            i.id.toLowerCase().includes(q) ||
            (name(i.id) || "").toLowerCase().includes(q) ||
            (i.type || "").toLowerCase().includes(q)
        );
      }
      return [...list].sort((a, b) =>
        (name(a.id) || a.id).localeCompare(name(b.id) || b.id)
      );
    });

    function scalars(it) {
      const out = {};
      for (const k of ["price", "lootLevel", "storage", "refDesc"]) {
        if (it[k] !== undefined && it[k] !== null) out[k] = it[k];
      }
      return out;
    }

    function focusItem(id) {
      const exists = props.items.some((it) => it.id === id);
      if (!exists) { emit("notify", "No item card for '" + id + "'."); return; }
      search.value = "";
      catSel.value = "all";
      missingOnly.value = false;
      view.value = "cards";
      nextTick(() => {
        const el = document.getElementById("item-" + id);
        if (!el) return;
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        flashId.value = id;
        setTimeout(() => { if (flashId.value === id) flashId.value = null; }, 1200);
      });
    }

    watch(() => props.focusId, (id) => { if (id) focusItem(id); }, { immediate: true });

    return {
      search, catSel, missingOnly, view, imgFailed, flashId,
      chipFields, tableColumns, categoryTree, missingIconCount, filtered,
      iconSrc, categoryIcon, name, desc, attrName, categoryLabel, scalars,
    };
  },
  template: `
  <div class="flex gap-4 items-start">
    <aside class="w-56 shrink-0 text-sm">
      <div class="bg-white rounded-lg border border-slate-200 p-2 sticky top-20 max-h-[80vh] overflow-auto">
        <button @click="catSel='all'" class="w-full text-left px-2 py-1 rounded font-medium"
                :class="catSel==='all' ? 'bg-slate-800 text-white' : 'hover:bg-slate-100'">
          All items <span class="text-xs opacity-60">({{ items.length }})</span>
        </button>
        <div v-for="m in categoryTree" :key="m.id" class="mt-1">
          <button @click="catSel='main:'+m.id"
                  class="w-full flex items-center gap-2 px-2 py-1 rounded font-medium"
                  :class="catSel==='main:'+m.id ? 'bg-slate-800 text-white' : 'hover:bg-slate-100'">
            <span class="checker rounded w-5 h-5 shrink-0 flex items-center justify-center overflow-hidden">
              <img v-if="categoryIcon(m.id)" :src="categoryIcon(m.id)" :alt="m.id" loading="lazy" class="max-w-full max-h-full" />
            </span>
            <span class="truncate flex-1 text-left">{{ m.label }}</span>
            <span class="text-xs opacity-60">{{ m.count }}</span>
          </button>
          <button v-for="s in m.subs" :key="s.id" @click="catSel='sub:'+s.id"
                  class="w-full flex items-center gap-2 pl-7 pr-2 py-0.5 rounded text-xs"
                  :class="catSel==='sub:'+s.id ? 'bg-slate-700 text-white' : 'text-slate-600 hover:bg-slate-100'">
            <span class="checker rounded w-4 h-4 shrink-0 flex items-center justify-center overflow-hidden">
              <img v-if="categoryIcon(s.id)" :src="categoryIcon(s.id)" :alt="s.id" loading="lazy" class="max-w-full max-h-full" />
            </span>
            <span class="truncate flex-1 text-left">{{ s.label }}</span>
            <span class="opacity-60">{{ s.count }}</span>
          </button>
        </div>
      </div>
    </aside>

    <div class="flex-1 min-w-0">
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <span class="text-sm text-slate-500">
          showing {{ filtered.length }} / {{ items.length }}
          <span v-if="missingIconCount" class="text-amber-600">· {{ missingIconCount }} without icon</span>
        </span>
        <div class="ml-auto inline-flex rounded border border-slate-300 overflow-hidden text-sm">
          <button @click="view='cards'" :class="view==='cards' ? 'bg-slate-800 text-white' : 'bg-white'" class="px-3 py-1">Cards</button>
          <button @click="view='table'" :class="view==='table' ? 'bg-slate-800 text-white' : 'bg-white'" class="px-3 py-1 border-l border-slate-300">Table</button>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-3 mb-4">
        <input v-model="search" type="search" placeholder="Search id, name or type…" class="flex-1 min-w-[12rem] border border-slate-300 rounded px-3 py-1.5 text-sm" />
        <label class="flex items-center gap-1.5 text-sm text-slate-600 select-none">
          <input type="checkbox" v-model="missingOnly" /> missing icon only
        </label>
      </div>

      <div v-if="view==='cards'" class="grid gap-3 grid-cols-[repeat(auto-fill,minmax(15rem,1fr))]">
        <article v-for="it in filtered" :key="it.id" :id="'item-' + it.id"
                 class="bg-white rounded-lg border border-slate-200 p-3 flex flex-col gap-2"
                 :class="{ 'ring-1 ring-amber-300': !iconSrc(it.id), 'flash-green': flashId === it.id }">
          <div class="flex items-center gap-3">
            <div class="checker rounded w-16 h-16 shrink-0 flex items-center justify-center overflow-hidden">
              <img v-if="iconSrc(it.id) && !imgFailed[it.id]" :src="iconSrc(it.id)" :alt="it.id" loading="lazy" class="max-w-full max-h-full" @error="imgFailed[it.id]=true" />
              <span v-else class="text-[10px] text-slate-400 text-center px-1">no icon</span>
            </div>
            <div class="min-w-0">
              <div class="font-medium truncate" :title="name(it.id) || it.id">{{ name(it.id) || it.id }}</div>
              <div class="text-xs text-slate-400 font-mono truncate" :title="it.id">{{ it.id }}</div>
              <div class="mt-1 flex flex-wrap items-center gap-1 text-[11px]">
                <span v-if="it.displayCategory" class="inline-flex items-center gap-1 bg-slate-100 rounded px-1.5 py-0.5" :title="it.displayCategory">
                  <img v-if="categoryIcon(it.displayCategory)" :src="categoryIcon(it.displayCategory)" :alt="it.displayCategory" loading="lazy" class="w-3 h-3" />
                  {{ categoryLabel(it.displayCategory) }}
                </span>
                <span v-if="it.subcategory" class="inline-flex items-center gap-1 bg-slate-50 rounded px-1.5 py-0.5 text-slate-500" :title="it.subcategory">
                  <img v-if="categoryIcon(it.subcategory)" :src="categoryIcon(it.subcategory)" :alt="it.subcategory" loading="lazy" class="w-3 h-3" />
                  {{ categoryLabel(it.subcategory) }}
                </span>
                <span v-if="!it.displayCategory && it.type" class="text-slate-400" :title="it.type">{{ it.type }}</span>
              </div>
            </div>
          </div>
          <p v-if="desc(it.id)" class="text-xs text-slate-600 line-clamp-3">{{ desc(it.id) }}</p>
          <dl class="text-xs grid grid-cols-2 gap-x-3 gap-y-0.5">
            <template v-for="(v,k) in scalars(it)" :key="k">
              <dt class="text-slate-400">{{ k }}</dt><dd class="text-right tabular-nums">{{ v }}</dd>
            </template>
          </dl>
          <div v-if="it.attributes && it.attributes.length" class="text-xs">
            <div class="text-slate-400">attributes</div>
            <ul class="mt-0.5 space-y-0.5">
              <li v-for="(a,i) in it.attributes" :key="i" class="flex justify-between gap-2">
                <span class="truncate" :title="a.attr">{{ attrName(a.attr) }}</span>
                <span class="tabular-nums text-slate-600">{{ a.value }}</span>
              </li>
            </ul>
          </div>
          <template v-for="key in chipFields" :key="key">
            <div v-if="it[key] && it[key].length" class="text-xs">
              <span class="text-slate-400">{{ key }}:</span>
              <span v-for="c in it[key]" :key="c" class="inline-block ml-1 mb-1 bg-slate-100 rounded px-1.5 py-0.5">{{ c }}</span>
            </div>
          </template>
        </article>
      </div>

      <div v-else class="overflow-x-auto bg-white rounded-lg border border-slate-200">
        <table class="min-w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-2 py-2">icon</th>
              <th v-for="col in tableColumns" :key="col.key" class="px-2 py-2 whitespace-nowrap">
                {{ col.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in filtered" :key="it.id" class="border-t border-slate-100 hover:bg-slate-50" :class="{ 'bg-amber-50': !iconSrc(it.id) }">
              <td class="px-2 py-1">
                <div class="checker rounded w-9 h-9 flex items-center justify-center overflow-hidden">
                  <img v-if="iconSrc(it.id) && !imgFailed[it.id]" :src="iconSrc(it.id)" :alt="it.id" loading="lazy" class="max-w-full max-h-full" @error="imgFailed[it.id]=true" />
                </div>
              </td>
              <td class="px-2 py-1">{{ name(it.id) || '—' }}</td>
              <td class="px-2 py-1 font-mono text-xs text-slate-500">{{ it.id }}</td>
              <td class="px-2 py-1">{{ it.type || '' }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ it.price ?? '' }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ it.lootLevel ?? '' }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ it.storage ?? '' }}</td>
              <td class="px-2 py-1 text-right tabular-nums">{{ (it.attributes && it.attributes.length) || '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
  `,
};
