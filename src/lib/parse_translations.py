#!/usr/bin/env python3
"""Extract translatable strings (name + desc) into per-language translation files.

Pure logic plus a thin argparse ``main`` driven by
src/commands/parse_translations.py.

English is the base language and comes from data.cdb itself.
Other languages come from the extra/lang/export_<lang>.xml files.

Output: one file per language, e.g.
    generated/i18n/translation.en.json
    generated/i18n/translation.fr.json

Each file is keyed by sheet then row id:
    {"lang": "fr", "item": {"IronOre": {"name": "...", "desc": "..."}}, ...}

The app loads these and builds in-memory indexes. Re-run after a game update.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Which sheets to translate and where each sheet keeps its name/desc.
# name_path / desc_path are dotted column paths inside a CDB row (and the
# matching XML element tag names, which mirror those paths).
SHEETS = {
    "item": {"name": "name", "desc": "desc"},
    "attribute": {"name": "name", "desc": "props.desc"},
    # Craft categories (recipe `category`) and item types live here; only a
    # localized name, no desc.
    "itemType": {"name": "name", "desc": "desc"},
}


def dig(row: dict, path: str):
    """Follow a dotted path (e.g. 'props.desc') into a nested CDB row."""
    node = row
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def clean_text(value) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def entry_from(name, desc) -> dict | None:
    record = {}
    name = clean_text(name)
    desc = clean_text(desc)
    if name is not None:
        record["name"] = name
    if desc is not None:
        record["desc"] = desc
    return record or None


# ---- English: straight from data.cdb -------------------------------------

def load_cdb(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def translations_from_cdb(cdb: dict) -> dict:
    out = {}
    sheets = {sheet.get("name"): sheet for sheet in cdb.get("sheets", [])}
    for sheet_name, paths in SHEETS.items():
        sheet = sheets.get(sheet_name)
        if sheet is None:
            continue
        rows = {}
        for row in sheet.get("lines", []):
            if not isinstance(row, dict):
                continue
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                continue
            entry = entry_from(dig(row, paths["name"]), dig(row, paths["desc"]))
            if entry is not None:
                rows[row_id] = entry
        out[sheet_name] = rows
    return out


# ---- Other languages: from export_<lang>.xml -----------------------------

def translations_from_xml(xml_path: Path) -> dict:
    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    out = {}
    for sheet_name, paths in SHEETS.items():
        rows = {}
        for sheet in root.findall("sheet"):
            if sheet.get("name") != sheet_name:
                continue
            for row in sheet:
                children = {child.tag: child.text for child in row}
                entry = entry_from(children.get(paths["name"]), children.get(paths["desc"]))
                if entry is not None:
                    rows[row.tag] = entry
        out[sheet_name] = rows
    return out


def lang_of(xml_path: Path) -> str:
    # export_pt-BR.xml -> pt-BR
    stem = xml_path.stem
    return stem[len("export_"):] if stem.startswith("export_") else stem


def write_lang(out_dir: Path, lang: str, sheets: dict) -> Path:
    payload = {"lang": lang}
    payload.update(sheets)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"translation.{lang}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Extract per-language translation files from SpaceCraft data.")
    parser.add_argument("--data", type=Path, default=Path("unpacked/data.cdb"), help="Path to data.cdb (English base).")
    parser.add_argument("--lang-dir", type=Path, default=Path("unpacked/extra/lang"), help="Folder with export_<lang>.xml files.")
    parser.add_argument("--out", type=Path, default=Path("generated/i18n"), help="Output directory for translation files.")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without writing files.")
    return parser.parse_args(argv)


def summarize(sheets: dict) -> str:
    return ", ".join(f"{name}={len(rows)}" for name, rows in sheets.items())


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        written = []

        en = translations_from_cdb(load_cdb(args.data))
        if not args.dry_run:
            write_lang(args.out, "en", en)
        written.append(("en", en))

        for xml_path in sorted(args.lang_dir.glob("export_*.xml")):
            sheets = translations_from_xml(xml_path)
            lang = lang_of(xml_path)
            if not args.dry_run:
                write_lang(args.out, lang, sheets)
            written.append((lang, sheets))
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    action = "Would write" if args.dry_run else "Wrote"
    for lang, sheets in written:
        print(f"{action} {lang}: {summarize(sheets)}")
    if not args.dry_run:
        print(f"Output: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
