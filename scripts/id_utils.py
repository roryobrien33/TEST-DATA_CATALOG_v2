#!/usr/bin/env python3
"""
Central ID generation / normalization utilities for the data catalog.

Goal:
- keep all entity ID logic in one place
- make IDs predictable, reusable, and easier to maintain
- avoid ad hoc string handling in workflows and scripts

Suggested conventions currently implemented:
- Catalog ID:
    <CATALOG-NAME-NORMALIZED>-<RANDOM6>
  Example:
    GRID-DATA-AB12CD

- Dataset ID:
    sdcdc:<catalog-id>-<dataset-short-id>
  Example:
    sdcdc:GRID-DATA-AB12CD-voltage-timeseries

- Concept ID:
    sdcdc:concept-<concept-name>
  Example:
    sdcdc:concept-voltage

- Policy ID:
    plcy:<policy-name>
  Example:
    plcy:open-information-policy

- Metric ID:
    sdcdc:metric-<metric-name>
  Example:
    sdcdc:metric-voltage-quality
"""

from __future__ import annotations

import random
import re
from typing import Optional


# -----------------------------
# Generic helpers
# -----------------------------

def slugify(value: str) -> str:
    """
    Lowercase slug for human-entered labels/titles.

    Example:
        "Voltage Quality" -> "voltage-quality"
    """
    s = str(value or "").strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def normalize_id_base(value: str) -> str:
    """
    Uppercase normalized base used for catalog IDs.

    Example:
        "Grid Data" -> "GRID-DATA"
    """
    s = str(value or "").strip().upper()
    s = re.sub(r"[\s\-_]+", "-", s)
    s = re.sub(r"[^A-Z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def random_token6() -> str:
    """
    Random 6-character base36 token.
    """
    n = random.randint(0, (36 ** 6) - 1)
    return base36(n).rjust(6, "0")


def base36(num: int) -> str:
    """
    Convert integer to uppercase base36.
    """
    if num < 0:
        raise ValueError("base36 input must be non-negative")
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return "0"

    parts = []
    while num:
        num, rem = divmod(num, 36)
        parts.append(chars[rem])
    return "".join(reversed(parts))


def ensure_curie(value: str, default_prefix: str = "sdcdc") -> str:
    """
    Ensure a CURIE-like identifier if the value is not already a CURIE/IRI.

    Examples:
        "concept-voltage" -> "sdcdc:concept-voltage"
        "plcy:open-policy" -> "plcy:open-policy"
        "https://example.org/x" -> "https://example.org/x"
    """
    s = str(value or "").strip()
    if not s:
        return s
    if s.startswith("http://") or s.startswith("https://"):
        return s
    if ":" in s:
        return s
    return f"{default_prefix}:{s}"


def sanitize_page_id(value: str) -> str:
    """
    Convert a display ID / CURIE / IRI into a filesystem/xref-safe page ID.

    Examples:
        "sdcdc:concept-voltage" -> "concept-voltage"
        "plcy:open-policy" -> "open-policy"
        "https://x/y/z" -> "z"
    """
    s = str(value or "").strip()

    if ":" in s and not s.startswith("http://") and not s.startswith("https://"):
        s = s.split(":", 1)[1]

    if "#" in s:
        s = s.split("#")[-1]

    if "/" in s:
        s = s.rstrip("/").split("/")[-1]

    s = re.sub(r"[^A-Za-z0-9._-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


# -----------------------------
# Catalog IDs
# -----------------------------

def generate_catalog_id(catalog_name: str, add_random_suffix: bool = True) -> str:
    """
    Generate a catalog ID.

    Example:
        generate_catalog_id("Grid Data")
        -> "GRID-DATA-AB12CD"
    """
    base = normalize_id_base(catalog_name)
    if not base:
        raise ValueError("Catalog name produced an empty normalized ID base")

    if add_random_suffix:
        return f"{base}-{random_token6()}"
    return base


def normalize_catalog_id(catalog_id: str) -> str:
    """
    Normalize an existing catalog ID to the uppercase dash format.
    """
    base = normalize_id_base(catalog_id)
    if not base:
        raise ValueError("Catalog ID produced an empty normalized value")
    return base


# -----------------------------
# Dataset IDs
# -----------------------------

def is_iri(value: str) -> bool:
    s = str(value or "").strip()
    return s.startswith("http://") or s.startswith("https://")


def is_curie(value: str) -> bool:
    s = str(value or "").strip()
    return (":" in s) and (not is_iri(s))


def generate_dataset_id(catalog_id: str, dataset_short_id: str) -> str:
    """
    Generate a catalog-scoped dataset ID.

    Example:
        generate_dataset_id("GRID-DATA-AB12CD", "voltage-timeseries")
        -> "sdcdc:GRID-DATA-AB12CD-voltage-timeseries"
    """
    cid = normalize_catalog_id(catalog_id)
    ds_short = slugify(dataset_short_id)
    if not ds_short:
        raise ValueError("Dataset short ID is empty after normalization")
    return f"sdcdc:{cid}-{ds_short}"


def normalize_dataset_id(catalog_id: str, dataset_id_value: str) -> str:
    """
    Normalize a dataset identifier.

    Rules:
    - if already an IRI -> return as-is
    - if already a CURIE -> return as-is
    - otherwise -> generate catalog-scoped dataset ID

    Example:
        normalize_dataset_id("GRID-DATA-AB12CD", "test")
        -> "sdcdc:GRID-DATA-AB12CD-test"
    """
    s = str(dataset_id_value or "").strip()
    if not s:
        return s
    if is_iri(s):
        return s
    if is_curie(s):
        return s
    return generate_dataset_id(catalog_id, s)


# -----------------------------
# Concept IDs
# -----------------------------

def generate_concept_id(concept_label: str) -> str:
    """
    Generate a concept ID.

    Example:
        generate_concept_id("Voltage")
        -> "sdcdc:concept-voltage"
    """
    slug = slugify(concept_label)
    if not slug:
        raise ValueError("Concept label is empty after normalization")
    return f"sdcdc:concept-{slug}"


def normalize_concept_id(concept_id_or_label: str) -> str:
    """
    Normalize a concept ID.

    Rules:
    - if already an IRI -> return as-is
    - if already a CURIE -> return as-is
    - if starts with 'concept-' -> prefix with sdcdc:
    - otherwise -> treat as label and generate concept ID
    """
    s = str(concept_id_or_label or "").strip()
    if not s:
        return s
    if is_iri(s):
        return s
    if is_curie(s):
        return s
    if s.startswith("concept-"):
        return f"sdcdc:{s}"
    return generate_concept_id(s)


# -----------------------------
# Policy IDs
# -----------------------------

def generate_policy_id(policy_title: str) -> str:
    """
    Generate a policy ID.

    Example:
        generate_policy_id("Open Information Policy")
        -> "plcy:open-information-policy"
    """
    slug = slugify(policy_title)
    if not slug:
        raise ValueError("Policy title is empty after normalization")
    return f"plcy:{slug}"


def normalize_policy_id(policy_id_or_title: str) -> str:
    """
    Normalize a policy ID.

    Rules:
    - if already an IRI -> return as-is
    - if already a CURIE -> return as-is
    - otherwise -> treat as title/slug and return plcy:<slug>
    """
    s = str(policy_id_or_title or "").strip()
    if not s:
        return s
    if is_iri(s):
        return s
    if is_curie(s):
        return s
    return generate_policy_id(s)


# -----------------------------
# Metric IDs
# -----------------------------

def generate_metric_id(metric_label: str) -> str:
    """
    Generate a metric ID.

    Example:
        generate_metric_id("Voltage Quality")
        -> "sdcdc:metric-voltage-quality"
    """
    slug = slugify(metric_label)
    if not slug:
        raise ValueError("Metric label is empty after normalization")
    return f"sdcdc:metric-{slug}"


def normalize_metric_id(metric_id_or_label: str) -> str:
    """
    Normalize a metric ID.

    Rules:
    - if already an IRI -> return as-is
    - if already a CURIE -> return as-is
    - if starts with 'metric-' -> prefix with sdcdc:
    - otherwise -> treat as label and generate metric ID
    """
    s = str(metric_id_or_label or "").strip()
    if not s:
        return s
    if is_iri(s):
        return s
    if is_curie(s):
        return s
    if s.startswith("metric-"):
        return f"sdcdc:{s}"
    return generate_metric_id(s)


# -----------------------------
# Bulk list helpers
# -----------------------------

def parse_csv_ids(raw: Optional[str], normalizer) -> list[str]:
    """
    Parse a comma-separated string of IDs/labels using a normalizer function.

    Example:
        parse_csv_ids("Voltage, sdcdc:concept-harmonics", normalize_concept_id)
        -> ["sdcdc:concept-voltage", "sdcdc:concept-harmonics"]
    """
    if not raw:
        return []
    values = [x.strip() for x in str(raw).split(",") if x.strip()]
    return [normalizer(v) for v in values if normalizer(v)]


# -----------------------------
# Small CLI/demo
# -----------------------------

if __name__ == "__main__":
    print("Examples:")
    print("catalog:", generate_catalog_id("Grid Data"))
    print("dataset:", normalize_dataset_id("GRID-DATA-AB12CD", "voltage-timeseries"))
    print("concept:", normalize_concept_id("Voltage"))
    print("policy:", normalize_policy_id("Open Information Policy"))
    print("metric:", normalize_metric_id("Voltage Quality"))
    print("page id:", sanitize_page_id("sdcdc:concept-voltage"))
