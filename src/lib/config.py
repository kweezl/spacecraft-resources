from dataclasses import dataclass


@dataclass(frozen=True)
class Setting:
    env: str
    default: str


DATA = Setting("SC_DATA", "unpacked/data.cdb")
ASSETS = Setting("SC_ASSETS", "unpacked")
EXTRACT_OUT = Setting("SC_EXTRACT_OUT", "unpacked")
PARSE_ITEMS_OUT = Setting("SC_PARSE_ITEMS_OUT", "generated/items.json")
PARSE_TRANSLATIONS_OUT = Setting("SC_PARSE_TRANSLATIONS_OUT", "generated/i18n")
PARSE_TRANSLATIONS_LANG_DIR = Setting("SC_PARSE_TRANSLATIONS_LANG_DIR", "unpacked/extra/lang")
GENERATE_ICONS_OUT = Setting("SC_GENERATE_ICONS_OUT", "generated/icons")
GENERATE_ICONS_MANIFEST = Setting("SC_GENERATE_ICONS_MANIFEST", "generated/icons_manifest.json")
DEDUPLICATE_ICONS_MANIFEST = Setting("SC_DEDUPLICATE_ICONS_MANIFEST", "generated/icons_manifest.json")

# Order groups shared settings first, then per-command settings. Used to
# generate and validate .env.example.
ALL_SETTINGS = [
    DATA,
    ASSETS,
    EXTRACT_OUT,
    PARSE_ITEMS_OUT,
    PARSE_TRANSLATIONS_OUT,
    PARSE_TRANSLATIONS_LANG_DIR,
    GENERATE_ICONS_OUT,
    GENERATE_ICONS_MANIFEST,
    DEDUPLICATE_ICONS_MANIFEST,
]
