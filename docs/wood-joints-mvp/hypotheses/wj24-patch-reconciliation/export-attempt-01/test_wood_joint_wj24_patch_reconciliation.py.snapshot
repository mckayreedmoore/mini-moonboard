import hashlib
import io
import json
import tarfile

import pytest

from scripts import wood_joint_wj24_patch_reconciliation as reconciliation


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_archive_inputs(
    tmp_path,
    *,
    archive_member_name: str,
    archive_payload: bytes,
    indexed_payload: bytes,
):
    archive_path = tmp_path / "complete-mesh-evidence.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        member = tarfile.TarInfo(archive_member_name)
        member.size = len(archive_payload)
        archive.addfile(member, io.BytesIO(archive_payload))

    contents_path = tmp_path / "bundle-contents.json"
    contents_path.write_text(
        json.dumps(
            {
                "mesh.json": {
                    "bytes": len(indexed_payload),
                    "sha256": _sha256(indexed_payload),
                }
            },
            sort_keys=True,
        )
    )
    hashes_path = tmp_path / "sha256.json"
    hashes_path.write_text(
        json.dumps(
            {
                "bundle-contents.json": _sha256(contents_path.read_bytes()),
                "complete-mesh-evidence.tar.gz": _sha256(archive_path.read_bytes()),
            },
            sort_keys=True,
        )
    )
    return archive_path, contents_path, hashes_path


def test_archived_mesh_report_member_is_read_and_verified_without_extraction(tmp_path):
    payload = b'{"status": "mesh-only"}'
    archive_path, contents_path, hashes_path = _write_archive_inputs(
        tmp_path,
        archive_member_name="mesh.json",
        archive_payload=payload,
        indexed_payload=payload,
    )

    report, record = reconciliation._read_archived_json_member(
        archive_path, contents_path, hashes_path, "mesh.json"
    )

    assert report == {"status": "mesh-only"}
    assert record == {"bytes": len(payload), "sha256": _sha256(payload)}


def test_archived_mesh_report_requires_the_exact_indexed_member_identity(tmp_path):
    payload = b'{"status": "mesh-only"}'
    archive_path, contents_path, hashes_path = _write_archive_inputs(
        tmp_path,
        archive_member_name="nested/mesh.json",
        archive_payload=payload,
        indexed_payload=payload,
    )

    with pytest.raises(ValueError, match="missing or ambiguous"):
        reconciliation._read_archived_json_member(
            archive_path, contents_path, hashes_path, "mesh.json"
        )


def test_archived_mesh_report_rejects_a_missing_indexed_member(tmp_path):
    payload = b'{"status": "mesh-only"}'
    archive_path, contents_path, hashes_path = _write_archive_inputs(
        tmp_path,
        archive_member_name="other.json",
        archive_payload=payload,
        indexed_payload=payload,
    )

    with pytest.raises(ValueError, match="missing or ambiguous"):
        reconciliation._read_archived_json_member(
            archive_path, contents_path, hashes_path, "mesh.json"
        )


def test_archived_mesh_report_rejects_tampered_member_bytes(tmp_path):
    indexed_payload = b'{"status": "mesh-only"}'
    tampered_payload = b'{"status": "MESH-only"}'
    archive_path, contents_path, hashes_path = _write_archive_inputs(
        tmp_path,
        archive_member_name="mesh.json",
        archive_payload=tampered_payload,
        indexed_payload=indexed_payload,
    )

    with pytest.raises(ValueError, match="hash/size mismatch"):
        reconciliation._read_archived_json_member(
            archive_path, contents_path, hashes_path, "mesh.json"
        )
