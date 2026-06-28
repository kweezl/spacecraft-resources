import { ref, computed, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

export const CategoriesView = {
  name: "categories-view",
  props: {
    categories: { type: Array, required: true },
    items: { type: Array, required: true },
    tr: { type: Object, required: true },
    base: { type: String, required: true },
    categoryAliases: { type: Object, required: true },
  },
  setup(props) {
    const { iconSrc } = useIcons(props.base, toRef(props, "categoryAliases"), "icons-categories");
    const { categoryLabel } = useTranslations(toRef(props, "tr"));
    const search = ref("");

    const itemCounts = computed(() => {
      const counts = {};
      for (const it of props.items) {
        const t = it.type;
        if (!t) continue;
        counts[t] = (counts[t] || 0) + 1;
      }
      return counts;
    });
    const childrenOf = computed(() => {
      const map = {};
      for (const c of props.categories) {
        const p = c.parent || "";
        (map[p] = map[p] || []).push(c);
      }
      for (const k in map) map[k].sort((a, b) => categoryLabel(a.id).localeCompare(categoryLabel(b.id)));
      return map;
    });
    const roots = computed(() => (childrenOf.value[""] || []));
    const q = computed(() => search.value.trim().toLowerCase());
    function matches(c) {
      if (!q.value) return true;
      return c.id.toLowerCase().includes(q.value) || categoryLabel(c.id).toLowerCase().includes(q.value);
    }
    return { search, childrenOf, roots, itemCounts, iconSrc, categoryLabel, matches };
  },
  template: `
  <div>
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <span class="text-sm text-slate-500">{{ categories.length }} categories</span>
      <input v-model="search" type="search" placeholder="Search category…" class="ml-auto min-w-[12rem] border border-slate-300 rounded px-3 py-1.5 text-sm" />
    </div>
    <div class="bg-white rounded-lg border border-slate-200 divide-y divide-slate-100">
      <template v-for="root in roots" :key="root.id">
        <div v-if="matches(root) || (childrenOf[root.id]||[]).some(matches)">
          <div class="flex items-center gap-2 px-3 py-2">
            <span class="checker rounded w-7 h-7 flex items-center justify-center overflow-hidden shrink-0">
              <img v-if="iconSrc(root.id)" :src="iconSrc(root.id)" :alt="root.id" loading="lazy" class="max-w-full max-h-full" />
            </span>
            <span class="font-medium">{{ categoryLabel(root.id) }}</span>
            <span class="text-xs text-slate-400 font-mono">{{ root.id }}</span>
            <span v-if="itemCounts[root.id]" class="ml-auto text-xs text-slate-500">{{ itemCounts[root.id] }} items</span>
          </div>
          <div v-for="child in (childrenOf[root.id]||[])" :key="child.id" v-show="matches(root) || matches(child)" class="flex items-center gap-2 pl-10 pr-3 py-1.5 text-sm">
            <span class="checker rounded w-6 h-6 flex items-center justify-center overflow-hidden shrink-0">
              <img v-if="iconSrc(child.id)" :src="iconSrc(child.id)" :alt="child.id" loading="lazy" class="max-w-full max-h-full" />
            </span>
            <span>{{ categoryLabel(child.id) }}</span>
            <span class="text-xs text-slate-400 font-mono">{{ child.id }}</span>
            <span v-if="itemCounts[child.id]" class="ml-auto text-xs text-slate-500">{{ itemCounts[child.id] }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
  `,
};
