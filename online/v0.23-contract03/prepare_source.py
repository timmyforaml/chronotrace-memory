"""Reconstruct a recorded service snapshot locally, without network or execution."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


HERE = Path(__file__).resolve().parent
ARCHIVE_SHA256 = "d3a93e76dec07dde5bf9319189db10c6fb982b507ec24361c13e1d83a915025d"
ORIGINAL_ID = "027b67c8fcb81674da70eaac1f8573632c033b95813dc82714d715e640a7fbd1"
REPAIRED_ID = "4f7aa733e817f906605e6c9ef88c6a5f9e39ef54e5acaa2283e1f6ac997d8429"
ENCODER_SHA256 = "3959e2d8c8d3d95aa1e92f553bcfe59d8670dd39ed7e2b3a6a274157beea3174"
ENCODER = "adaptive_evidence/remote_encoder.py"


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def identity(files: dict[str, str]) -> str:
    return sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode())


def relative_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or ".." in path.parts
            or "\\" in name or ":" in name or path.as_posix() != name):
        raise ValueError("Unsafe archive path")
    return path


def verify(blobs: dict[str, bytes], manifest: dict, expected: str) -> None:
    files = manifest["source_files_sha256"]
    if (manifest["source_manifest_sha256"] != expected or identity(files) != expected
            or set(blobs) != set(files) | {"manifest.json"}):
        raise ValueError("Source manifest identity or file set differs")
    for name, digest in files.items():
        relative_path(name)
        if sha256(blobs[name]) != digest:
            raise ValueError("Source file checksum differs: " + name)


def prepare(output: Path, *, archive_only: bool = False) -> str:
    if output.exists() or output.is_symlink():
        raise FileExistsError("Output must be a new directory")
    archive = (HERE / "source.tar.gz").read_bytes()
    if sha256(archive) != ARCHIVE_SHA256:
        raise ValueError("Original archive checksum differs")
    blobs = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
        for member in package.getmembers():
            relative_path(member.name)
            if not member.isfile() or member.name in blobs:
                raise ValueError("Archive contains a non-file or duplicate member")
            stream = package.extractfile(member)
            if stream is None:
                raise ValueError("Missing archive member")
            blobs[member.name] = stream.read()
    manifest = json.loads(blobs["manifest.json"])
    verify(blobs, manifest, ORIGINAL_ID)
    expected = ORIGINAL_ID
    if not archive_only:
        manifest = json.loads((HERE / "recorded-length-repair" / "manifest.json").read_bytes())
        repair = (HERE / "recorded-length-repair" / "remote_encoder.py").read_bytes()
        if sha256(repair) != ENCODER_SHA256:
            raise ValueError("Recorded encoder checksum differs")
        blobs[ENCODER] = repair
        blobs["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        expected = REPAIRED_ID
        verify(blobs, manifest, expected)
    # All validation occurs before creation. Never extract links or overwrite files.
    output.mkdir(parents=True, exist_ok=False)
    for name, blob in blobs.items():
        target = output.joinpath(*relative_path(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(blob)
    print("source_manifest_sha256=" + expected)
    print("verified_source_files=" + str(len(manifest["source_files_sha256"])))
    print("output=" + str(output.resolve()))
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New source directory")
    parser.add_argument("--archive-only", action="store_true", help="Extract the original 2026-10-31 snapshot")
    args = parser.parse_args()
    prepare(args.output, archive_only=args.archive_only)


if __name__ == "__main__":
    main()
