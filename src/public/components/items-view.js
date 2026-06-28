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
    const typeFilter = ref("all");
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

    // The game groups items by their display category (the itemType the parser
    // resolved into `displayCategory`), not by the leaf `type`. Items the parser
    // left unresolved fall into one "(uncategorized)" bucket.
    const UNCATEGORIZED = "(uncategorized)";
    function itemCategory(it) {
      return it.displayCategory || UNCATEGORIZED;
    }
    function catLabel(id) {
      return id === UNCATEGORIZED ? "(uncategorized)" : categoryLabel(id);
    }

    const displayCategories = computed(() => {
      const counts = {};
      for (const it of props.items) {
        const c = itemCategory(it);
        counts[c] = (counts[c] || 0) + 1;
      }
      return Object.entries(counts)
        .map(([id, count]) => ({ id, label: catLabel(id), count }))
        .sort((a, b) => a.label.localeCompare(b.label));
    });

    const missingIconCount = computed(() =>
      props.items.reduce((n, it) => n + (iconSrc(it.id) ? 0 : 1), 0)
    );

    const filtered = computed(() => {
      let list = props.items;
      if (typeFilter.value !== "all")
        list = list.filter((i) => itemCategory(i) === typeFilter.value);
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
      typeFilter.value = "all";
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
      search, typeFilter, missingOnly, view, imgFailed, flashId,
      chipFields, tableColumns, displayCategories, missingIconCount, filtered,
      iconSrc, categoryIcon, name, desc, attrName, categoryLabel, scalars,
      itemCategory, catLabel,
    };
  },
  template: `
  <div>
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
      <select v-model="typeFilter" class="border border-slate-300 rounded px-2 py-1.5 text-sm">
        <option value="all">All categories ({{ items.length }})</option>
        <option v-for="c in displayCategories" :key="c.id" :value="c.id">{{ c.label }} ({{ c.count }})</option>
      </select>
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
            <span v-if="it.type" class="inline-flex items-center gap-1 mt-1 text-[11px] bg-slate-100 rounded px-1.5 py-0.5" :title="'category: ' + itemCategory(it) + ' · type: ' + it.type">
              <img v-if="it.displayCategory && categoryIcon(it.displayCategory)" :src="categoryIcon(it.displayCategory)" :alt="it.displayCategory" loading="lazy" class="w-3 h-3" />
              {{ catLabel(itemCategory(it)) }}
            </span>
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
  `,
};
