import struct
import types
import unittest

from src.lib import extract


def entry(name, entry_type, payload):
    encoded = name.encode("utf-8")
    return bytes([len(encoded)]) + encoded + bytes([entry_type]) + payload


class ExtractParserTests(unittest.TestCase):
    def test_type2_offsets_are_sequential_with_mandatory_16_byte_gap(self):
        index = (
            b"\x00"
            + b"\x01"
            + struct.pack("<I", 3)
            + entry("a.bin", 0, struct.pack("<III", 0, 4, 0))
            + entry("b.bin", 2, struct.pack("<IIII", 0xAA000000, 0x12345678, 3, 0))
            + entry("c.bin", 2, struct.pack("<IIII", 0xBB000000, 0x87654321, 2, 0))
        )

        files = extract.parse_files(index, pak_data_size=64, kind2_words=4)

        by_path = {item["path"]: item for item in files}
        self.assertEqual(by_path["a.bin"]["offset"], 0)
        self.assertEqual(by_path["b.bin"]["offset"], 16)
        self.assertEqual(by_path["b.bin"]["packed_size"], 3)
        self.assertEqual(by_path["c.bin"]["offset"], 32)
        self.assertEqual(by_path["c.bin"]["packed_size"], 2)

    def test_iter_files_streams_entries_without_returning_a_list(self):
        index = (
            b"\x00"
            + b"\x01"
            + struct.pack("<I", 2)
            + entry("a.bin", 0, struct.pack("<III", 0, 4, 0))
            + entry("b.bin", 2, struct.pack("<IIII", 0xAA000000, 0x12345678, 3, 0))
        )

        files = extract.iter_files(index, pak_data_size=64)

        self.assertIsInstance(files, types.GeneratorType)
        first = next(files)
        second = next(files)
        self.assertEqual(first["path"], "a.bin")
        self.assertEqual(second["path"], "b.bin")
        self.assertEqual(second["offset"], 16)

    def test_total_extracted_size_cannot_exceed_pak_data_size(self):
        files = [
            {"path": "a.bin", "packed_size": 6},
            {"path": "b.bin", "packed_size": 5},
        ]

        with self.assertRaises(SystemExit) as caught:
            extract.validate_total_extracted_size(files, pak_data_size=10)

        self.assertIn("Refusing to extract", str(caught.exception))
        self.assertIn("11 bytes", str(caught.exception))
        self.assertIn("10 bytes", str(caught.exception))

    def test_format_extract_progress_names_current_file(self):
        item = {"path": "assets/file.bin", "packed_size": 123}

        line = extract.format_extract_progress(2, 10, item)

        self.assertEqual(line, "Extracting 2/10: assets/file.bin (123 bytes)")

    def test_unknown_entry_type_reports_parse_context(self):
        index = (
            b"\x00"
            + b"\x01"
            + struct.pack("<I", 1)
            + entry("bad.bin", 9, b"\xAA\xBB\xCC\xDD")
        )

        with self.assertRaises(extract.PakParseError) as caught:
            extract.parse_files(index, pak_data_size=64)

        message = str(caught.exception)
        self.assertIn("Unknown entry type 9", message)
        self.assertIn("entry_start=0x6", message)
        self.assertIn("reader_pos=0xF", message)
        self.assertIn("path=bad.bin", message)
        self.assertIn("Index bytes around failure", message)

    def test_unexpected_trailing_index_bytes_raise_parse_error(self):
        index = b"\x00" + b"\x01" + struct.pack("<I", 0) + b"JUNK"

        with self.assertRaises(extract.PakParseError) as caught:
            extract.parse_files(index, pak_data_size=64)

        message = str(caught.exception)
        self.assertIn("Unexpected trailing index bytes", message)
        self.assertIn("reader_pos=0x6", message)

    def test_known_data_footer_after_index_is_accepted(self):
        index = b"\x00" + b"\x01" + struct.pack("<I", 0) + (b"\x00" * 10) + b"DATA"

        files = extract.parse_files(index, pak_data_size=64)

        self.assertEqual(files, [])


if __name__ == "__main__":
    unittest.main()
