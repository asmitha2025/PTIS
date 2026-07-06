from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_DATASET_FIELDS = [
    "dataset_id",
    "title",
    "status",
    "source_name",
    "source_url",
    "license",
    "collection_start",
    "collection_end",
    "geography",
    "schema_version",
]

FIELD_REPLAY_STATUSES = {"field_observed", "official_open_data", "licensed_partner_data"}
REFERENCE_STATUSES = {"official_planning_reference"}
CCTV_DETECTION_STATUSES = {"public_cctv_detection_dataset"}
VALID_DATASET_STATUSES = FIELD_REPLAY_STATUSES | REFERENCE_STATUSES | CCTV_DETECTION_STATUSES | {"synthetic_verification_fixture"}
PLACEHOLDER_VALUES = {"", "todo", "tbd", "unknown", "n/a", "na", "link", "[link]"}


def validate_dataset_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_DATASET_FIELDS:
        value = data.get(field)
        if value is None or str(value).strip().lower() in PLACEHOLDER_VALUES:
            errors.append(f"missing_or_placeholder:{field}")

    status = str(data.get("status", "")).strip()
    if status not in VALID_DATASET_STATUSES:
        errors.append(f"invalid_status:{status}")

    if status == "synthetic_verification_fixture":
        warnings.append("dataset_is_synthetic_not_field_data")

    if status == "official_planning_reference":
        warnings.append("dataset_is_official_reference_not_field_replay")

    if status == "public_cctv_detection_dataset":
        warnings.append("dataset_is_cctv_detection_not_field_replay")

    if status in FIELD_REPLAY_STATUSES | REFERENCE_STATUSES | CCTV_DETECTION_STATUSES:
        for field in ["checksum_sha256", "provenance_contact", "privacy_review"]:
            value = data.get(field)
            if value is None or str(value).strip().lower() in PLACEHOLDER_VALUES:
                errors.append(f"real_dataset_requires:{field}")

    return {
        "path": str(manifest_path),
        "valid": not errors,
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }
