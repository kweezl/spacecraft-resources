from dataclasses import dataclass


@dataclass(frozen=True)
class Setting:
    env: str
    default: str


DATA = Setting("SC_DATA", "unpacked/data.cdb")
ASSETS = Setting("SC_ASSETS", "unpacked")
# The .pak path has no sensible built-in default; an empty default means
# "required" — the extract command errors if neither the argument nor the env
# var supplies it.
EXTRACT_PAK = Setting("SC_EXTRACT_PAK", "")
EXTRACT_OUT = Setting("SC_EXTRACT_OUT", "unpacked")
PARSE_ITEMS_OUT = Setting("SC_PARSE_ITEMS_OUT", "generated/items.json")
PARSE_CRAFT_OUT = Setting("SC_PARSE_CRAFT_OUT", "generated/craft.json")
PARSE_WORKSHOPS_OUT = Setting("SC_PARSE_WORKSHOPS_OUT", "generated/workshops.json")
PARSE_CONTRACTS_OUT = Setting("SC_PARSE_CONTRACTS_OUT", "generated/contracts.json")
PARSE_ITEM_CATEGORIES_OUT = Setting("SC_PARSE_ITEM_CATEGORIES_OUT", "generated/item_categories.json")
PARSE_SPACE_OBJECTS_OUT = Setting("SC_PARSE_SPACE_OBJECTS_OUT", "generated/space_objects.json")
PARSE_FACTIONS_OUT = Setting("SC_PARSE_FACTIONS_OUT", "generated/factions.json")
PARSE_TRANSLATIONS_OUT = Setting("SC_PARSE_TRANSLATIONS_OUT", "generated/i18n")
PARSE_TRANSLATIONS_LANG_DIR = Setting("SC_PARSE_TRANSLATIONS_LANG_DIR", "unpacked/extra/lang")
GENERATE_ICONS_OUT = Setting("SC_GENERATE_ICONS_OUT", "generated/icons")
GENERATE_ICONS_MANIFEST = Setting("SC_GENERATE_ICONS_MANIFEST", "generated/icons_manifest.json")
GENERATE_ICONS_ALIASES = Setting("SC_GENERATE_ICONS_ALIASES", "generated/aliases.json")
# CDB sheet to generate icons from (each row uses its own icon). "item" gives
# every item its own icon; an empty value scans all sheets with the file filter.
GENERATE_ICONS_SHEET = Setting("SC_GENERATE_ICONS_SHEET", "item")
# Icon output image format: "webp" (default, small; good for web/Discord) or "png".
GENERATE_ICONS_FORMAT = Setting("SC_GENERATE_ICONS_FORMAT", "webp")
# Extra icon sets generated from other sheets into their own dirs + alias maps
# (their ids are not globally unique, so they cannot share aliases.json).
GENERATE_ICONS_CATEGORIES_OUT = Setting("SC_GENERATE_ICONS_CATEGORIES_OUT", "generated/icons-categories")
GENERATE_ICONS_CATEGORIES_MANIFEST = Setting("SC_GENERATE_ICONS_CATEGORIES_MANIFEST", "generated/icons-categories_manifest.json")
GENERATE_ICONS_CATEGORIES_ALIASES = Setting("SC_GENERATE_ICONS_CATEGORIES_ALIASES", "generated/aliases-categories.json")
GENERATE_ICONS_FACTIONS_OUT = Setting("SC_GENERATE_ICONS_FACTIONS_OUT", "generated/icons-factions")
GENERATE_ICONS_FACTIONS_MANIFEST = Setting("SC_GENERATE_ICONS_FACTIONS_MANIFEST", "generated/icons-factions_manifest.json")
GENERATE_ICONS_FACTIONS_ALIASES = Setting("SC_GENERATE_ICONS_FACTIONS_ALIASES", "generated/aliases-factions.json")
DEDUPLICATE_ICONS_MANIFEST = Setting("SC_DEDUPLICATE_ICONS_MANIFEST", "generated/icons_manifest.json")

# serve: dev-only static server for the items inspector (fixed mount table:
# /generated -> generated/, / -> src/public/), so it has no directory setting.
SERVE_HOST = Setting("SC_SERVE_HOST", "127.0.0.1")
SERVE_PORT = Setting("SC_SERVE_PORT", "8000")

# Order groups shared settings first, then per-command settings. Used to
# generate and validate .env.example.
ALL_SETTINGS = [
    DATA,
    ASSETS,
    EXTRACT_PAK,
    EXTRACT_OUT,
    PARSE_ITEMS_OUT,
    PARSE_CRAFT_OUT,
    PARSE_WORKSHOPS_OUT,
    PARSE_CONTRACTS_OUT,
    PARSE_ITEM_CATEGORIES_OUT,
    PARSE_SPACE_OBJECTS_OUT,
    PARSE_FACTIONS_OUT,
    PARSE_TRANSLATIONS_OUT,
    PARSE_TRANSLATIONS_LANG_DIR,
    GENERATE_ICONS_OUT,
    GENERATE_ICONS_MANIFEST,
    GENERATE_ICONS_ALIASES,
    GENERATE_ICONS_SHEET,
    GENERATE_ICONS_FORMAT,
    GENERATE_ICONS_CATEGORIES_OUT,
    GENERATE_ICONS_CATEGORIES_MANIFEST,
    GENERATE_ICONS_CATEGORIES_ALIASES,
    GENERATE_ICONS_FACTIONS_OUT,
    GENERATE_ICONS_FACTIONS_MANIFEST,
    GENERATE_ICONS_FACTIONS_ALIASES,
    DEDUPLICATE_ICONS_MANIFEST,
    SERVE_HOST,
    SERVE_PORT,
]
