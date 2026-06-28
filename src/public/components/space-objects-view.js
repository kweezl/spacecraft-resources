import { ref, computed, toRef } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";
import { useIcons, useTranslations } from "../composables.js";

export const SpaceObjectsView = {
  name: "space-objects-view",
  props: {
    spaceObjects: { type: Array, required: true },
    aliases: { type: Object, required: true },
    factionAliases: { type: Object, required: true },
    tr: { type: Object, required: true },
    base: { type: String, required: true },
  },
  setup(props) {
    const { iconSrc } = useIcons(props.base, toRef(props, "aliases"));
    const { iconSrc: factionIcon } = useIcons(props.base, toRef(props, "factionAliases"), "icons-factions");
    const { name, spaceObjectName, factionName, instanceName } = useTranslations(toRef(props, "tr"));
    const search = ref("");
    const filtered = computed(() => {
      const q = search.value.trim().toLowerCase();
      let list = props.spaceObjects;
      if (q) list = list.filter((o) =>
        o.id.toLowerCase().includes(q) || spaceObjectName(o.id).toLowerCase().includes(q));
      return [...list].sort((a, b) => spaceObjectName(a.id).localeCompare(spaceObjectName(b.id)));
    });
    function itemHref(id) { return "#/items/" + encodeURIComponent(id); }
    function floors(o) { return (o.props && o.props.floors) || []; }
    function buyout(o) { return (o.props && o.props.buyout) || []; }
    return { search, filtered, iconSrc, factionIcon, name, spaceObjectName, factionName, instanceName, itemHref, floors, buyout };
  },
  template: `
  <div>
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <span class="text-sm text-slate-500">{{ filtered.length }} / {{ spaceObjects.length }}</span>
      <input v-model="search" type="search" placeholder="Search space object…" class="ml-auto min-w-[12rem] border border-slate-300 rounded px-3 py-1.5 text-sm" />
    </div>
    <div class="grid gap-3 grid-cols-1 lg:grid-cols-2">
      <article v-for="o in filtered" :key="o.id" class="bg-white rounded-lg border border-slate-200 p-3 flex flex-col gap-2">
        <div class="flex items-center gap-2">
          <span v-if="o.owner && factionIcon(o.owner)" class="checker rounded w-7 h-7 flex items-center justify-center overflow-hidden">
            <img :src="factionIcon(o.owner)" :alt="o.owner" loading="lazy" class="max-w-full max-h-full" />
          </span>
          <span class="font-medium">{{ spaceObjectName(o.id) }}</span>
        </div>
        <div class="text-xs text-slate-400 font-mono truncate" :title="o.id">{{ o.id }}</div>
        <dl class="text-xs grid grid-cols-2 gap-x-3 gap-y-0.5">
          <template v-if="o.owner"><dt class="text-slate-400">owner</dt><dd class="text-right">{{ factionName(o.owner) }}</dd></template>
          <template v-if="o.building"><dt class="text-slate-400">building</dt>
            <dd class="text-right"><a :href="itemHref(o.building)" class="text-sky-600 hover:underline">{{ name(o.building) || o.building }}</a></dd>
          </template>
        </dl>
        <section v-if="floors(o).length" class="border-t border-slate-100 pt-2">
          <div class="text-xs font-semibold text-slate-500 mb-1">Floors</div>
          <div class="flex flex-wrap gap-1">
            <span v-for="(f,i) in floors(o)" :key="'f'+i" class="text-[11px] bg-slate-100 rounded px-1.5 py-0.5" :title="f.instance">{{ instanceName(f.instance) }}</span>
          </div>
        </section>
        <section v-if="buyout(o).length" class="border-t border-slate-100 pt-2">
          <div class="text-xs font-semibold text-slate-500 mb-1">Buyout</div>
          <div class="flex flex-col gap-1">
            <a v-for="(b,i) in buyout(o)" :key="'b'+i" :href="itemHref(b.item)" :title="b.item" class="flex items-center gap-1 bg-slate-50 rounded px-1.5 py-1 hover:bg-slate-100">
              <span class="checker rounded w-7 h-7 flex items-center justify-center overflow-hidden">
                <img v-if="iconSrc(b.item)" :src="iconSrc(b.item)" :alt="b.item" loading="lazy" class="max-w-full max-h-full" />
              </span>
              <span class="text-xs whitespace-nowrap">{{ name(b.item) || b.item }}</span>
              <span class="ml-auto text-xs tabular-nums text-slate-500" v-if="b.value !== undefined">{{ b.value }}</span>
            </a>
          </div>
        </section>
      </article>
    </div>
  </div>
  `,
};
