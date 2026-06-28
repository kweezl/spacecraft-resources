import { ref, computed, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

export const ContractsView = {
  name: "contracts-view",
  props: {
    contracts: { type: Array, required: true },
    aliases: { type: Object, required: true },
    tr: { type: Object, required: true },
    base: { type: String, required: true },
  },
  setup(props) {
    const { iconSrc } = useIcons(props.base, toRef(props, "aliases"));
    const { name, contractTitle, factionName } = useTranslations(toRef(props, "tr"));
    const search = ref("");
    const clientFilter = ref("all");

    const clients = computed(() => {
      const counts = {};
      for (const c of props.contracts) {
        const k = c.client || "(none)";
        counts[k] = (counts[k] || 0) + 1;
      }
      return Object.entries(counts).map(([n, count]) => ({ name: n, count }))
        .sort((a, b) => factionName(a.name).localeCompare(factionName(b.name)));
    });
    const filtered = computed(() => {
      let list = props.contracts;
      if (clientFilter.value !== "all")
        list = list.filter((c) => (c.client || "(none)") === clientFilter.value);
      const q = search.value.trim().toLowerCase();
      if (q) list = list.filter((c) =>
        c.id.toLowerCase().includes(q) || contractTitle(c.id).toLowerCase().includes(q));
      return [...list].sort((a, b) => contractTitle(a.id).localeCompare(contractTitle(b.id)));
    });
    function itemHref(id) { return "#/items/" + encodeURIComponent(id); }
    function creditFactor(c) { return (c.props && c.props.creditFactor) ?? 1; }
    return { search, clientFilter, clients, filtered, iconSrc, name, contractTitle, factionName, itemHref, creditFactor };
  },
  template: `
  <div>
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <span class="text-sm text-slate-500">{{ filtered.length }} / {{ contracts.length }}</span>
      <input v-model="search" type="search" placeholder="Search contract…" class="flex-1 min-w-[12rem] border border-slate-300 rounded px-3 py-1.5 text-sm" />
      <select v-model="clientFilter" class="border border-slate-300 rounded px-2 py-1.5 text-sm">
        <option value="all">All clients</option>
        <option v-for="c in clients" :key="c.name" :value="c.name">{{ factionName(c.name) }} ({{ c.count }})</option>
      </select>
    </div>
    <div class="grid gap-3 grid-cols-1 lg:grid-cols-2">
      <article v-for="c in filtered" :key="c.id" class="bg-white rounded-lg border border-slate-200 p-3 flex flex-col gap-2">
        <div class="flex items-center gap-2">
          <span class="font-medium">{{ contractTitle(c.id) }}</span>
          <span v-if="c.level" class="text-[11px] bg-slate-100 rounded px-1.5 py-0.5">L{{ c.level }}</span>
        </div>
        <div class="text-xs text-slate-400 font-mono truncate" :title="c.id">{{ c.id }}</div>
        <dl class="text-xs grid grid-cols-2 gap-x-3 gap-y-0.5">
          <template v-if="c.client"><dt class="text-slate-400">client</dt><dd class="text-right">{{ factionName(c.client) }}</dd></template>
          <template v-if="c.creditFormula !== undefined"><dt class="text-slate-400">credits</dt><dd class="text-right tabular-nums">{{ c.creditFormula }}</dd></template>
          <dt class="text-slate-400" title="Payout multiplier on item market value (default 1)">payout ×</dt><dd class="text-right tabular-nums">{{ creditFactor(c) }}</dd>
        </dl>
        <section v-if="c.items && c.items.length" class="border-t border-slate-100 pt-2">
          <div class="text-xs font-semibold text-slate-500 mb-1">Deliver</div>
          <div class="flex flex-col gap-1">
            <a v-for="(io,i) in c.items" :key="'d'+i" :href="itemHref(io.item)" :title="io.item" class="flex items-center gap-1 bg-slate-50 rounded px-1.5 py-1 hover:bg-slate-100">
              <span class="checker rounded w-7 h-7 flex items-center justify-center overflow-hidden">
                <img v-if="iconSrc(io.item)" :src="iconSrc(io.item)" :alt="io.item" loading="lazy" class="max-w-full max-h-full" />
              </span>
              <span class="text-xs whitespace-nowrap">{{ name(io.item) || io.item }} × {{ io.qty }}</span>
            </a>
          </div>
        </section>
        <section v-if="c.rewards && c.rewards.length" class="border-t border-slate-100 pt-2">
          <div class="text-xs font-semibold text-slate-500 mb-1">Rewards</div>
          <div class="flex flex-wrap gap-1">
            <a v-for="(io,i) in c.rewards" :key="'r'+i" :href="itemHref(io.item)" :title="io.item" class="flex items-center gap-1 bg-emerald-50 rounded px-1.5 py-1 hover:bg-emerald-100">
              <span class="checker rounded w-7 h-7 flex items-center justify-center overflow-hidden">
                <img v-if="iconSrc(io.item)" :src="iconSrc(io.item)" :alt="io.item" loading="lazy" class="max-w-full max-h-full" />
              </span>
              <span class="text-xs whitespace-nowrap">{{ name(io.item) || io.item }} × {{ io.count }}</span>
            </a>
          </div>
        </section>
      </article>
    </div>
  </div>
  `,
};
