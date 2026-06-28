import { ref, computed, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

export const WorkshopsView = {
  name: "workshops-view",
  props: {
    workshops: { type: Array, required: true },
    recipes: { type: Array, required: true },
    tr: { type: Object, required: true },
    aliases: { type: Object, default: () => ({}) },
    base: { type: String, default: "" },
  },
  setup(props) {
    const { iconSrc } = useIcons(props.base, toRef(props, "aliases"));
    const { workshopName } = useTranslations(toRef(props, "tr"));
    const search = ref("");
    const recipeCounts = computed(() => {
      const counts = {};
      for (const r of props.recipes) {
        if (!r.where) continue;
        counts[r.where] = (counts[r.where] || 0) + 1;
      }
      return counts;
    });
    const filtered = computed(() => {
      const q = search.value.trim().toLowerCase();
      let list = props.workshops;
      if (q) list = list.filter((w) =>
        w.id.toLowerCase().includes(q) || workshopName(w.id).toLowerCase().includes(q));
      return [...list].sort((a, b) => workshopName(a.id).localeCompare(workshopName(b.id)));
    });
    return { search, filtered, recipeCounts, workshopName, iconSrc };
  },
  template: `
  <div>
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <span class="text-sm text-slate-500">{{ filtered.length }} / {{ workshops.length }} workshops</span>
      <input v-model="search" type="search" placeholder="Search workshop…" class="ml-auto min-w-[12rem] border border-slate-300 rounded px-3 py-1.5 text-sm" />
    </div>
    <div class="grid gap-3 grid-cols-[repeat(auto-fill,minmax(16rem,1fr))]">
      <article v-for="w in filtered" :key="w.id" class="bg-white rounded-lg border border-slate-200 p-3 flex flex-col gap-2">
        <div class="flex items-center gap-2">
          <span class="checker rounded w-9 h-9 shrink-0 flex items-center justify-center overflow-hidden">
            <img v-if="w.building && iconSrc(w.building)" :src="iconSrc(w.building)" :alt="w.building" loading="lazy" class="max-w-full max-h-full" />
          </span>
          <span class="font-medium">{{ workshopName(w.id) }}</span>
        </div>
        <div class="text-xs text-slate-400 font-mono truncate" :title="w.id">{{ w.id }}</div>
        <dl class="text-xs grid grid-cols-2 gap-x-3 gap-y-0.5">
          <template v-if="w.craftAction"><dt class="text-slate-400">action</dt><dd class="text-right">{{ w.craftAction }}</dd></template>
          <template v-if="w.autoCraftTime !== undefined"><dt class="text-slate-400">auto base</dt><dd class="text-right tabular-nums">{{ w.autoCraftTime }}s</dd></template>
          <template v-if="w.manualCraftTime !== undefined"><dt class="text-slate-400">manual base</dt><dd class="text-right tabular-nums">{{ w.manualCraftTime }}s</dd></template>
          <dt class="text-slate-400">recipes</dt><dd class="text-right tabular-nums">{{ recipeCounts[w.id] || 0 }}</dd>
        </dl>
      </article>
    </div>
  </div>
  `,
};
