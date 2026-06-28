import { ref, computed, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

const CRAFT_TIME_PROPS = ["craftTimeFactor", "manualTimeFactor", "autoTime"];

export const RecipesView = {
  name: "recipes-view",
  props: {
    recipes: { type: Array, required: true },
    aliases: { type: Object, required: true },
    tr: { type: Object, required: true },
    base: { type: String, required: true },
    categoryAliases: { type: Object, default: () => ({}) },
    workshopBuildings: { type: Object, default: () => ({}) },
  },
  setup(props) {
    const { iconSrc } = useIcons(props.base, toRef(props, "aliases"));
    function workshopIcon(where) {
      const building = props.workshopBuildings[where];
      return building ? iconSrc(building) : null;
    }
    const { iconSrc: categoryIcon } = useIcons(props.base, toRef(props, "categoryAliases"), "icons-categories");
    const { name, categoryLabel, workshopName } = useTranslations(toRef(props, "tr"));

    const search = ref("");
    const whereFilter = ref("all");
    const categoryFilter = ref("all");

    const workshops = computed(() => {
      const counts = {};
      for (const r of props.recipes) {
        const k = r.where || "(none)";
        counts[k] = (counts[k] || 0) + 1;
      }
      return Object.entries(counts)
        .map(([id, count]) => ({ id, count }))
        .sort((a, b) => workshopName(a.id).localeCompare(workshopName(b.id)));
    });

    // Recipe craft categories are flat itemType ids (e.g. Craft_Alloy); each has
    // an icon in the icons-categories set. Sorted by localized label.
    const categories = computed(() => {
      const counts = {};
      for (const r of props.recipes) {
        const k = r.category || "(none)";
        counts[k] = (counts[k] || 0) + 1;
      }
      return Object.entries(counts)
        .map(([id, count]) => ({ id, label: categoryLabel(id), count }))
        .sort((a, b) => a.label.localeCompare(b.label));
    });

    const filtered = computed(() => {
      let list = props.recipes;
      if (whereFilter.value !== "all")
        list = list.filter((r) => (r.where || "(none)") === whereFilter.value);
      if (categoryFilter.value !== "all")
        list = list.filter((r) => (r.category || "(none)") === categoryFilter.value);
      const q = search.value.trim().toLowerCase();
      if (q) {
        list = list.filter((r) => {
          if (r.id.toLowerCase().includes(q)) return true;
          const io = [...r.inputs, ...r.outputs];
          return io.some(
            (e) => e.item.toLowerCase().includes(q) || (name(e.item) || "").toLowerCase().includes(q)
          );
        });
      }
      return [...list].sort((a, b) =>
        sortName(a).localeCompare(sortName(b))
      );
    });

    function headerItem(r) {
      return r.outputs && r.outputs.length ? r.outputs[0].item : null;
    }
    function sortName(r) {
      const h = headerItem(r);
      return (h && name(h)) || h || r.id;
    }
    function itemHref(id) {
      return "#/items/" + encodeURIComponent(id);
    }
    function craftTime(r) {
      const p = r.props || {};
      const parts = [];
      if (p.craftTimeFactor !== undefined) parts.push("craft ×" + p.craftTimeFactor);
      if (p.manualTimeFactor !== undefined) parts.push("manual ×" + p.manualTimeFactor);
      if (p.autoTime !== undefined) parts.push("auto " + p.autoTime);
      return parts.join(" · ");
    }
    function fmtSeconds(s) {
      if (s === null || s === undefined) return null;
      if (s < 60) return s + "s";
      if (s < 3600) return (Math.round(s / 6) / 10) + "m";
      return (Math.round(s / 360) / 10) + "h";
    }
    function craftDuration(r) {
      const ct = r.craftTime;
      if (!ct) return null;
      const parts = [];
      if (ct.manual !== null && ct.manual !== undefined) parts.push("manual " + fmtSeconds(ct.manual));
      if (ct.auto !== null && ct.auto !== undefined) parts.push("auto " + fmtSeconds(ct.auto));
      return parts.join(" · ");
    }
    function otherAttrs(r) {
      const out = {};
      if (r.unlockType !== undefined) out.unlock = r.unlockType;
      if (r.lootLevel !== undefined) out.loot = r.lootLevel;
      for (const [k, v] of Object.entries(r.props || {})) {
        if (!CRAFT_TIME_PROPS.includes(k)) out[k] = v;
      }
      return out;
    }

    return {
      search, whereFilter, categoryFilter, workshops, categories, filtered,
      iconSrc, categoryIcon, workshopIcon, name, categoryLabel, workshopName,
      headerItem, itemHref, craftTime, fmtSeconds, craftDuration, otherAttrs,
    };
  },
  template: `
  <div class="flex gap-4 items-start">
    <aside class="w-52 shrink-0 text-sm">
      <div class="bg-white rounded-lg border border-slate-200 p-2 sticky top-20 max-h-[80vh] overflow-auto">
        <button @click="categoryFilter='all'" class="w-full text-left px-2 py-1 rounded font-medium"
                :class="categoryFilter==='all' ? 'bg-sky-600 text-white' : 'hover:bg-slate-100'">
          All categories <span class="text-xs opacity-60">({{ recipes.length }})</span>
        </button>
        <button v-for="c in categories" :key="c.id" @click="categoryFilter=c.id"
                class="w-full flex items-center gap-2 px-2 py-1 rounded mt-0.5"
                :class="categoryFilter===c.id ? 'bg-sky-600 text-white' : 'hover:bg-slate-100'">
          <span class="checker rounded w-5 h-5 shrink-0 flex items-center justify-center overflow-hidden">
            <img v-if="categoryIcon(c.id)" :src="categoryIcon(c.id)" :alt="c.id" loading="lazy" class="max-w-full max-h-full" />
          </span>
          <span class="truncate flex-1 text-left">{{ c.label }}</span>
          <span class="text-xs opacity-60">{{ c.count }}</span>
        </button>
      </div>
    </aside>

    <div class="flex-1 min-w-0">
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <span class="text-sm text-slate-500">showing {{ filtered.length }} / {{ recipes.length }}</span>
        <select v-model="whereFilter" class="ml-auto border border-slate-300 rounded px-2 py-1.5 text-sm">
          <option value="all">All workshops ({{ recipes.length }})</option>
          <option v-for="w in workshops" :key="w.id" :value="w.id">{{ workshopName(w.id) }} ({{ w.count }})</option>
        </select>
      </div>
      <div class="mb-4">
        <input v-model="search" type="search" placeholder="Search recipe, item id or name…" class="w-full border border-slate-300 rounded px-3 py-1.5 text-sm" />
      </div>

      <div class="grid gap-3 grid-cols-1 xl:grid-cols-2">
        <article v-for="r in filtered" :key="r.id" class="bg-white rounded-lg border border-slate-200 p-3 flex flex-col gap-2">
          <div class="flex items-center gap-2">
            <a v-if="headerItem(r)" :href="itemHref(headerItem(r))" class="flex items-center gap-2 min-w-0 hover:underline" :title="headerItem(r)">
              <span class="checker rounded w-9 h-9 shrink-0 flex items-center justify-center overflow-hidden">
                <img v-if="iconSrc(headerItem(r))" :src="iconSrc(headerItem(r))" :alt="headerItem(r)" loading="lazy" class="max-w-full max-h-full" />
                <span v-else class="text-[8px] text-slate-400 text-center px-0.5">{{ headerItem(r) }}</span>
              </span>
              <span class="font-medium truncate">{{ name(headerItem(r)) || headerItem(r) }}</span>
            </a>
            <span v-else class="font-medium truncate">{{ r.id }}</span>
          </div>
          <div class="text-xs text-slate-400 font-mono truncate" :title="r.id">ID: {{ r.id }}</div>
          <div v-if="r.where" class="flex flex-wrap items-center gap-1">
            <span class="inline-flex items-center gap-1 text-[11px] bg-slate-100 rounded px-1.5 py-0.5" :title="r.where">
              <img v-if="workshopIcon(r.where)" :src="workshopIcon(r.where)" :alt="r.where" loading="lazy" class="w-3.5 h-3.5" />
              {{ workshopName(r.where) }}
            </span>
            <span v-if="craftDuration(r)" class="inline-block text-[11px] text-slate-500">{{ craftDuration(r) }}</span>
          </div>

          <section v-if="r.outputs.length" class="border-t border-slate-100 pt-2">
            <div class="text-xs font-semibold text-slate-500 mb-1">Output</div>
            <dl v-if="r.outputs.length === 1" class="text-xs grid grid-cols-2 gap-x-3 gap-y-0.5">
              <dt class="text-slate-400">quantity</dt><dd class="text-right tabular-nums">{{ r.outputs[0].qty }}</dd>
            </dl>
            <div v-else class="flex flex-col gap-1 mb-1">
              <a v-for="(io,i) in r.outputs" :key="'o'+i" :href="itemHref(io.item)" :title="io.item" class="flex items-center gap-1 bg-emerald-50 rounded px-1.5 py-1 hover:bg-emerald-100">
                <span class="checker rounded w-8 h-8 flex items-center justify-center overflow-hidden">
                  <img v-if="iconSrc(io.item)" :src="iconSrc(io.item)" :alt="io.item" loading="lazy" class="max-w-full max-h-full" />
                  <span v-else class="text-[8px] text-slate-400 text-center px-0.5">{{ io.item }}</span>
                </span>
                <span class="text-xs whitespace-nowrap">{{ name(io.item) || io.item }} × {{ io.qty }}</span>
              </a>
            </div>
            <dl class="text-xs grid grid-cols-2 gap-x-3 gap-y-0.5">
              <template v-if="r.category">
                <dt class="text-slate-400">category</dt>
                <dd class="text-right">
                  <span class="inline-flex items-center gap-1" :title="r.category">
                    <img v-if="categoryIcon(r.category)" :src="categoryIcon(r.category)" :alt="r.category" loading="lazy" class="w-3 h-3" />
                    {{ categoryLabel(r.category) }}
                  </span>
                </dd>
              </template>
              <template v-if="craftTime(r)">
                <dt class="text-slate-400">craft time</dt><dd class="text-right">{{ craftTime(r) }}</dd>
              </template>
            </dl>
          </section>

          <section class="border-t border-slate-100 pt-2">
            <div class="text-xs font-semibold text-slate-500 mb-1">Inputs</div>
            <div class="flex flex-col gap-1">
              <a v-for="(io,i) in r.inputs" :key="'i'+i" :href="itemHref(io.item)" :title="io.item" class="flex items-center gap-1 bg-slate-50 rounded px-1.5 py-1 hover:bg-slate-100">
                <span class="checker rounded w-8 h-8 flex items-center justify-center overflow-hidden">
                  <img v-if="iconSrc(io.item)" :src="iconSrc(io.item)" :alt="io.item" loading="lazy" class="max-w-full max-h-full" />
                  <span v-else class="text-[8px] text-slate-400 text-center px-0.5">{{ io.item }}</span>
                </span>
                <span class="text-xs whitespace-nowrap">{{ name(io.item) || io.item }} × {{ io.qty }}</span>
              </a>
              <span v-if="!r.inputs.length" class="text-xs text-slate-400">no inputs</span>
            </div>
          </section>

          <section v-if="Object.keys(otherAttrs(r)).length" class="border-t border-slate-100 pt-2">
            <div class="text-xs font-semibold text-slate-500 mb-1">Other attributes</div>
            <div class="text-xs text-slate-600 flex flex-wrap gap-x-2 gap-y-0.5">
              <span v-for="(v,k) in otherAttrs(r)" :key="k"><span class="text-slate-400">{{ k }}</span> {{ v }}</span>
            </div>
          </section>
        </article>
      </div>
    </div>
  </div>
  `,
};
