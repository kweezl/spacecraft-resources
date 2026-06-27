import json
import tempfile
import unittest
from pathlib import Path

import generate_icons


class GenerateIconsTests(unittest.TestCase):
    def test_iter_icon_jobs_uses_cdb_id_as_output_name(self):
        data = {
            "sheets": [
                {
                    "name": "item",
                    "lines": [
                        {
                            "id": "IronOre",
                            "name": "Iron Ore",
                            "icon": {
                                "file": "ui/icons/sprite_sheet_icon_64.png",
                                "size": 64,
                                "x": 0,
                                "y": 1,
                            },
                            "color": {
                                "colors": [-16777216, -1],
                                "positions": [0, 1],
                            },
                        },
                        {
                            "id": "Ignored",
                            "icon": {"file": "ui/actionIcons.png", "size": 32, "x": 0, "y": 0},
                        },
                    ],
                }
            ]
        }

        jobs = list(generate_icons.iter_icon_jobs(data, {"ui/icons/sprite_sheet_icon_64.png"}))

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].item_id, "IronOre")
        self.assertEqual(jobs[0].output_name, "IronOre.png")
        self.assertEqual(jobs[0].sheet, "item")
        self.assertEqual(jobs[0].crop_box, (0, 64, 64, 128))
        self.assertEqual(jobs[0].gradient.colors, [(0, 0, 0), (255, 255, 255)])

    def test_iter_icon_jobs_sheet_filter_restricts_to_named_sheet(self):
        data = {
            "sheets": [
                {
                    "name": "item",
                    "lines": [{"id": "ItemA", "icon": {"file": "f.png", "size": 64, "x": 0, "y": 0}}],
                },
                {
                    "name": "icon",
                    "lines": [{"id": "IconB", "icon": {"file": "f.png", "size": 64, "x": 1, "y": 0}}],
                },
            ]
        }
        # No sheet filter: both sheets contribute.
        all_ids = {job.item_id for job in generate_icons.iter_icon_jobs(data)}
        self.assertEqual(all_ids, {"ItemA", "IconB"})
        # Restricted to the item sheet: only its rows.
        item_ids = {job.item_id for job in generate_icons.iter_icon_jobs(data, sheet="item")}
        self.assertEqual(item_ids, {"ItemA"})

    def test_recolor_rgba_uses_pixel_brightness_as_gradient_position(self):
        pixels = bytes(
            [
                0,
                0,
                0,
                255,
                128,
                128,
                128,
                128,
                255,
                255,
                255,
                0,
            ]
        )
        gradient = generate_icons.Gradient(colors=[(10, 20, 30), (110, 120, 130)], positions=[0, 1])

        out = generate_icons.recolor_rgba(pixels, gradient)

        self.assertEqual(out[0:4], bytes([10, 20, 30, 255]))
        self.assertEqual(out[4:8], bytes([60, 70, 80, 128]))
        self.assertEqual(out[8:12], bytes([110, 120, 130, 0]))

    def test_png_encoder_decoder_round_trips_crop(self):
        image = generate_icons.RgbaImage(
            3,
            2,
            bytes(
                [
                    1,
                    2,
                    3,
                    255,
                    4,
                    5,
                    6,
                    255,
                    7,
                    8,
                    9,
                    255,
                    10,
                    11,
                    12,
                    255,
                    13,
                    14,
                    15,
                    255,
                    16,
                    17,
                    18,
                    255,
                ]
            ),
        )

        encoded = generate_icons.encode_png_rgba(image)
        loaded = generate_icons.decode_png_rgba(encoded)

        cropped = loaded.crop((1, 0, 3, 2))

        self.assertEqual(cropped.width, 2)
        self.assertEqual(cropped.height, 2)
        self.assertEqual(cropped.pixels[0:4], bytes([4, 5, 6, 255]))
        self.assertEqual(cropped.pixels[8:12], bytes([13, 14, 15, 255]))

    def test_manifest_records_source_and_output(self):
        job = generate_icons.IconJob(
            sheet="item",
            item_id="IronOre",
            name="Iron Ore",
            source_file="ui/icons/sprite_sheet_icon_64.png",
            size=64,
            x=0,
            y=0,
            width=1,
            height=1,
            gradient=None,
        )

        record = generate_icons.manifest_record(job, Path("generated/icons/IronOre.png"))

        self.assertEqual(record["id"], "IronOre")
        self.assertEqual(record["output"], "generated/icons/IronOre.png")
        self.assertEqual(record["source"]["file"], "ui/icons/sprite_sheet_icon_64.png")


class GenerateIconsDedupTests(unittest.TestCase):
    """End-to-end behaviour of generate_icons() with and without dedup.

    Three items share the same 64x64 crop of the same sheet: A and B have no
    colour (visually identical), C is recoloured (a distinct visual). Dedup
    should therefore keep two canonical files (A, C) and alias B -> A.
    """

    SHEET = "ui/icons/sprite_sheet_icon_64.png"

    def _make_project(self, root: Path) -> tuple[Path, Path, Path, Path]:
        sheet_path = root / self.SHEET
        sheet_path.parent.mkdir(parents=True, exist_ok=True)
        blank = generate_icons.RgbaImage(64, 64, bytes(64 * 64 * 4))
        sheet_path.write_bytes(generate_icons.encode_png_rgba(blank))

        cdb = {
            "sheets": [
                {
                    "name": "item",
                    "lines": [
                        {"id": "A", "icon": {"file": self.SHEET, "size": 64, "x": 0, "y": 0}},
                        {"id": "B", "icon": {"file": self.SHEET, "size": 64, "x": 0, "y": 0}},
                        {
                            "id": "C",
                            "icon": {"file": self.SHEET, "size": 64, "x": 0, "y": 0},
                            "color": {"colors": [-16777216, -1], "positions": [0, 1]},
                        },
                    ],
                }
            ]
        }
        cdb_path = root / "data.cdb"
        cdb_path.write_text(json.dumps(cdb), encoding="utf-8")
        out_dir = root / "icons"
        manifest_path = root / "icons_manifest.json"
        aliases_path = root / "aliases.json"
        return cdb_path, out_dir, manifest_path, aliases_path

    def test_dedup_writes_canonical_only_with_alias_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cdb_path, out_dir, manifest_path, aliases_path = self._make_project(root)

            count, records = generate_icons.generate_icons(
                cdb_path=cdb_path,
                assets_root=root,
                out_dir=out_dir,
                manifest_path=manifest_path,
                allowed_icon_files=None,
                recolor=True,
                clean=False,
                dry_run=False,
                dedup=True,
                aliases_path=aliases_path,
                fmt="png",
            )

            self.assertEqual(count, 3)
            pngs = sorted(p.name for p in out_dir.glob("*.png"))
            self.assertEqual(pngs, ["A.png", "C.png"])

            aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
            self.assertEqual(aliases["total"], 3)
            self.assertEqual(aliases["unique"], 2)
            self.assertEqual(aliases["icons"]["B"], "A.png")
            self.assertEqual(aliases["icons"]["A"], "A.png")
            self.assertEqual(aliases["icons"]["C"], "C.png")

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["count"], 3)
            self.assertTrue(manifest["icons"]["B"]["output"].endswith("A.png"))

    def test_no_dedup_writes_one_png_per_item_and_no_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cdb_path, out_dir, manifest_path, aliases_path = self._make_project(root)

            generate_icons.generate_icons(
                cdb_path=cdb_path,
                assets_root=root,
                out_dir=out_dir,
                manifest_path=manifest_path,
                allowed_icon_files=None,
                recolor=True,
                clean=False,
                dry_run=False,
                dedup=False,
                aliases_path=aliases_path,
                fmt="png",
            )

            pngs = sorted(p.name for p in out_dir.glob("*.png"))
            self.assertEqual(pngs, ["A.png", "B.png", "C.png"])
            self.assertFalse(aliases_path.exists(), "aliases.json must not be written without dedup")

    def test_webp_format_writes_valid_webp_files(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cdb_path, out_dir, manifest_path, aliases_path = self._make_project(root)

            generate_icons.generate_icons(
                cdb_path=cdb_path,
                assets_root=root,
                out_dir=out_dir,
                manifest_path=manifest_path,
                allowed_icon_files=None,
                recolor=True,
                clean=False,
                dry_run=False,
                dedup=True,
                aliases_path=aliases_path,
                fmt="webp",
            )

            names = sorted(p.name for p in out_dir.glob("*.webp"))
            self.assertEqual(names, ["A.webp", "C.webp"])
            self.assertEqual(list(out_dir.glob("*.png")), [])

            aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
            self.assertEqual(aliases["icons"]["B"], "A.webp")

            with Image.open(out_dir / "A.webp") as img:
                self.assertEqual(img.format, "WEBP")
                self.assertEqual(img.size, (64, 64))


if __name__ == "__main__":
    unittest.main()
