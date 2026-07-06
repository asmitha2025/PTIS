from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .provenance import validate_dataset_manifest

DEFAULT_SAMPLE_ROOT = Path("Real data") / "BMD-45-Val"
DEFAULT_MANIFEST = Path("data") / "bmd45_cctv_manifest.json"
DEFAULT_OUTPUT = Path("evidence") / "cctv_bmd45_report.json"


def validate_cctv_dataset_sample(
    sample_root: str | Path = DEFAULT_SAMPLE_ROOT,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    output_path: str | Path | None = None,
    min_local_images: int = 5,
) -> dict[str, Any]:
    root = Path(sample_root)
    manifest_candidate = Path(manifest_path)
    metadata_path = root / "metadata.jsonl"
    annotations_path = root / "_annotations.coco.json"

    manifest = _manifest_result(manifest_candidate)
    metadata_records = _read_metadata(metadata_path) if metadata_path.exists() else []
    metadata_files = {str(row.get("file_name", "")) for row in metadata_records}
    metadata_by_file = {str(row.get("file_name", "")): row for row in metadata_records}

    coco: dict[str, Any] = {}
    if annotations_path.exists():
        coco = json.loads(annotations_path.read_text(encoding="utf-8-sig"))

    coco_images = coco.get("images", [])
    coco_annotations = coco.get("annotations", [])
    coco_categories = coco.get("categories", [])
    coco_images_by_file = {str(image.get("file_name", "")): image for image in coco_images}
    coco_image_ids_by_file = {str(image.get("file_name", "")): image.get("id") for image in coco_images}

    annotation_count_by_image: dict[Any, int] = defaultdict(int)
    category_counts: Counter[int] = Counter()
    for annotation in coco_annotations:
        annotation_count_by_image[annotation.get("image_id")] += 1
        if "category_id" in annotation:
            category_counts[int(annotation["category_id"])] += 1

    category_name_by_id = {int(item["id"]): str(item["name"]) for item in coco_categories if "id" in item and "name" in item}
    category_summary = [
        {
            "id": category_id,
            "name": category_name_by_id.get(category_id, "unknown"),
            "annotation_count": count,
        }
        for category_id, count in category_counts.most_common()
    ]

    local_images = sorted(root.glob("images_*/*.png"))
    sample_images = []
    for image_path in local_images:
        rel = image_path.relative_to(root).as_posix()
        dimensions = _png_dimensions(image_path)
        coco_image = coco_images_by_file.get(rel, {})
        image_id = coco_image_ids_by_file.get(rel)
        metadata_row = metadata_by_file.get(rel, {})
        metadata_objects = metadata_row.get("objects", {}).get("bbox", []) if isinstance(metadata_row.get("objects"), dict) else []
        sample_images.append(
            {
                "file_name": rel,
                "exists": image_path.exists(),
                "width": dimensions[0],
                "height": dimensions[1],
                "bytes": image_path.stat().st_size,
                "metadata_match": rel in metadata_files,
                "coco_match": rel in coco_images_by_file,
                "coco_dimension_match": dimensions == (coco_image.get("width"), coco_image.get("height")),
                "metadata_object_count": len(metadata_objects),
                "coco_annotation_count": annotation_count_by_image.get(image_id, 0),
                "sha256": _sha256(image_path),
            }
        )

    files = {
        "sample_root": str(root),
        "manifest": str(manifest_candidate),
        "metadata": str(metadata_path),
        "annotations": str(annotations_path),
        "local_image_count": len(local_images),
        "checksums": {
            "metadata_sha256": _sha256(metadata_path) if metadata_path.exists() else None,
            "annotations_sha256": _sha256(annotations_path) if annotations_path.exists() else None,
        },
    }

    metrics = {
        "metadata_rows": len(metadata_records),
        "coco_image_count": len(coco_images),
        "coco_annotation_count": len(coco_annotations),
        "category_count": len(coco_categories),
        "local_image_count": len(local_images),
        "local_image_total_mb": round(sum(path.stat().st_size for path in local_images) / (1024 * 1024), 2),
        "sample_annotation_count": sum(item["coco_annotation_count"] for item in sample_images),
    }

    assertions = [
        _assertion("manifest_valid", manifest["valid"], {"status": manifest.get("status"), "errors": manifest.get("errors", [])}),
        _assertion("manifest_declares_cctv_not_field_replay", manifest.get("status") == "public_cctv_detection_dataset", {"status": manifest.get("status")}),
        _assertion("metadata_file_exists", metadata_path.exists(), {"path": str(metadata_path)}),
        _assertion("annotations_file_exists", annotations_path.exists(), {"path": str(annotations_path)}),
        _assertion("metadata_rows_match_coco_images", len(metadata_records) > 0 and len(metadata_records) == len(coco_images), {"metadata_rows": len(metadata_records), "coco_images": len(coco_images)}),
        _assertion("coco_annotations_present", len(coco_annotations) > 0, {"annotation_count": len(coco_annotations)}),
        _assertion("vehicle_categories_present", len(coco_categories) >= 10, {"category_count": len(coco_categories)}),
        _assertion("local_validation_images_present", len(local_images) >= min_local_images, {"local_image_count": len(local_images), "minimum": min_local_images}),
        _assertion("local_images_match_metadata_and_coco", bool(sample_images) and all(item["metadata_match"] and item["coco_match"] for item in sample_images), {"checked": len(sample_images)}),
        _assertion("local_images_are_1080p_and_match_coco", bool(sample_images) and all(item["width"] == 1920 and item["height"] == 1080 and item["coco_dimension_match"] for item in sample_images), {"checked": len(sample_images)}),
        _assertion("no_od_or_field_replay_claim", "dataset_is_cctv_detection_not_field_replay" in manifest.get("warnings", []), {"warnings": manifest.get("warnings", [])}),
    ]

    report = {
        "dataset_id": "bmd45_bengaluru_cctv_validation_sample_v1",
        "title": "BMD-45 Bengaluru CCTV validation sample",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": all(item["passed"] for item in assertions),
        "status": "real_cctv_detection_evidence_ready",
        "evidence_type": "real_public_cctv_detection_dataset",
        "truth_boundary": "BMD-45 validates real Bengaluru CCTV vehicle-detection/counting evidence. It does not provide anonymized vehicle trajectories, OD labels, or checkpoint field replay proof.",
        "source": {
            "name": "AIM@IISc BMD-45 Bengaluru Mobility Dataset",
            "url": "https://huggingface.co/datasets/iisc-aim/BMD-45",
            "license": "CC BY 4.0",
        },
        "manifest": manifest,
        "files": files,
        "metrics": metrics,
        "categories": category_summary,
        "sample_images": sample_images,
        "assertions": assertions,
    }

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return report


def _manifest_result(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "valid": False,
            "status": "missing",
            "errors": ["manifest_missing"],
            "warnings": [],
        }
    return validate_dataset_manifest(path)


def _read_metadata(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _png_dimensions(path: Path) -> tuple[int | None, int | None]:
    with path.open("rb") as handle:
        header = handle.read(24)
    png_signature = b"\x89PNG\r\n\x1a\n"
    if len(header) < 24 or not header.startswith(png_signature):
        return (None, None)
    width, height = struct.unpack(">II", header[16:24])
    return (width, height)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _assertion(name: str, passed: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details or {}}
