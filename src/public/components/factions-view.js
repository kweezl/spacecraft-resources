import { ref, computed, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

export const FactionsView = {
  name: "factions-view",
  props: {
    factions: { type: Array, required: true },
    contracts: { type: Array, required: true },
    factionAliases: { type: Object, required: true },
    tr: { type: Object, required: true },
    base: { type: String, required: true },
  },
  setup(props) {
    const { iconSrc } = useIcons(props.base, toRef(props, "factionAliases"), "icons-factions");
    const { factionName } = useTranslations(toRef(props, "tr"));
    const search = ref("");
    const contractCounts = computed(() => {
      const counts = {};
      for (const c of props.contracts) {
        if (!c.client) continue;
        counts[c.client] = (counts[c.client] || 0) + 1;
      }
      return counts;
    });
    const filtered = computed(() => {
      const q = search.value.trim().toLowerCase();
      let list = props.factions;
      if (q) list = list.filter((f) =>
        f.id.toLowerCase().includes(q) || factionName(f.id).toLowerCase().includes(q));
      return [...list].sort((a, b) => factionName(a.id).localeCompare(factionName(b.id)));
    });
    return { search, filtered, contractCounts, iconSrc, factionName };
  },
  template: `
  <div>
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <span class="text-sm text-slate-500">{{ filtered.length }} / {{ factions.length }} factions</span>
      <input v-model="search" type="search" placeholder="Search faction…" class="ml-auto min-w-[12rem] border border-slate-300 rounded px-3 py-1.5 text-sm" />
    </div>
    <div class="grid gap-3 grid-cols-[repeat(auto-fill,minmax(15rem,1fr))]">
      <article v-for="f in filtered" :key="f.id" class="bg-white rounded-lg border border-slate-200 p-3 flex items-center gap-3">
        <span class="checker rounded w-12 h-12 flex items-center justify-center overflow-hidden shrink-0">
          <img v-if="iconSrc(f.id)" :src="iconSrc(f.id)" :alt="f.id" loading="lazy" class="max-w-full max-h-full" />
          <span v-else class="text-[10px] text-slate-400">no logo</span>
        </span>
        <div class="min-w-0">
          <div class="font-medium truncate">{{ factionName(f.id) }}</div>
          <div class="text-xs text-slate-400 font-mono truncate" :title="f.id">{{ f.id }}</div>
          <div class="text-xs text-slate-500 mt-0.5">{{ contractCounts[f.id] || 0 }} contracts</div>
        </div>
      </article>
    </div>
  </div>
  `,
};
