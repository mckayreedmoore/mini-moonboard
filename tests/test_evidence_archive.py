"""Small end-to-end checks for preservation and safe pruning."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import evidence_archive as archive


class EvidenceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("scratch/\n")
        subprocess.run(["git", "-C", str(self.root), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Initial"], check=True)
        self.source = self.root / "scratch" / "closed"
        (self.source / "empty").mkdir(parents=True)
        (self.source / "payload.bin").write_bytes(bytes(range(256)) * 1024)
        (self.source / "run.py").write_text("print('historical evidence')\n")
        (self.source / "run.py").chmod(0o755)

    def create(self):
        return archive.create(self.root, ["scratch/closed"], self.base / "closed.tar.gz")

    def test_archive_restore_and_prune_preserve_bytes_modes_and_empty_directories(self):
        manifest = self.create()
        restored = archive.restore(manifest, self.base / "restored")
        self.assertEqual(archive.inventory(self.root, ["scratch/closed"]), archive.inventory(restored, ["scratch/closed"]))
        if shutil.which("pigz"):
            alternate = archive.create(self.root, ["scratch/closed"], self.base / "parallel.tar.gz", pigz=True)
            archived, path = archive.load_manifest(alternate)
            archive.walk_archive(path, archived)
        with self.assertRaises(FileExistsError):
            archive.restore(manifest, restored)
        archive.prune(self.root, manifest)
        self.assertFalse(self.source.exists())
        self.assertTrue((restored / "scratch/closed/empty").is_dir())

    def test_changed_or_added_source_refuses_pruning_without_deleting_anything(self):
        manifest = self.create()
        payload = self.source / "payload.bin"
        original = payload.read_bytes()
        payload.write_bytes(b"changed")
        changed = archive.inventory(self.root, ["scratch/closed"])
        with self.assertRaisesRegex(ValueError, "Source tree changed"):
            archive.prune(self.root, manifest)
        self.assertEqual(archive.inventory(self.root, ["scratch/closed"]), changed)
        payload.write_bytes(original)
        (self.source / "new.txt").write_text("Do not delete")
        changed = archive.inventory(self.root, ["scratch/closed"])
        with self.assertRaisesRegex(ValueError, "Source tree changed"):
            archive.prune(self.root, manifest)
        self.assertEqual(archive.inventory(self.root, ["scratch/closed"]), changed)

    def test_corrupt_backup_refuses_pruning_and_preserves_complete_source_tree(self):
        manifest_path = self.create()
        before = archive.inventory(self.root, ["scratch/closed"])
        _, backup = archive.load_manifest(manifest_path)
        with backup.open("ab") as output:
            output.write(b"corrupt backup")
        with self.assertRaisesRegex(ValueError, "Archive SHA-256 differs"):
            archive.prune(self.root, manifest_path)
        self.assertEqual(archive.inventory(self.root, ["scratch/closed"]), before)

    def test_newly_staged_evidence_refuses_pruning_without_changing_source(self):
        manifest_path = self.create()
        before = archive.inventory(self.root, ["scratch/closed"])
        subprocess.run(["git", "-C", str(self.root), "add", "-f", "scratch/closed/run.py"], check=True)
        with self.assertRaisesRegex(ValueError, "Tracked, dirty"):
            archive.prune(self.root, manifest_path)
        self.assertEqual(archive.inventory(self.root, ["scratch/closed"]), before)

    def test_tracked_symlink_and_internal_destination_are_refused(self):
        subprocess.run(["git", "-C", str(self.root), "add", "-f", "scratch/closed/run.py"], check=True)
        with self.assertRaisesRegex(ValueError, "Tracked, dirty"):
            self.create()
        subprocess.run(["git", "-C", str(self.root), "reset", "-q", "HEAD", "--", "scratch/closed/run.py"], check=True)
        (self.source / "link").symlink_to("run.py")
        with self.assertRaisesRegex(ValueError, "Symlink or special file"):
            self.create()
        (self.source / "link").unlink()
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            archive.create(self.root, ["scratch/closed"], self.root / "oops.tar.gz")


if __name__ == "__main__":
    unittest.main()
