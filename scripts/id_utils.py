#!/usr/bin/env python3
"""
Central ID generation / normalization utilities for the data catalog.

Current conventions:

Catalog:
    <CATALOG-NAME-NORMALIZED>-<RANDOM6>
Example:
    GRID-DATA-AB12CD

Dataset:
    sdcdc:<catalog-id>-<dataset-slug>
Example:
    sdcdc:GRID-DATA-AB12CD-voltage-timeseries

Concept:
    sdcdc:concept-<slug>-<RANDOM6>
Example:
    sdcdc:concept-voltage-2H4KL0

Policy:
    sdcdc:policy-<slug>-<RANDOM6>
Example:
    sdcdc:policy-open-information-policy-7B9QX2

Metric:
    sdcdc:metric-<slug>-<RANDOM6>
Example:
    sdcdc:metric-voltage-quality-5M1ZP8
"""

from __future__ import annotations

import random
import re
from typing import Optional, Callable


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


def random_token6() -> str:
    """
    Random 6-character uppercase base36 token.
    """
    n = random.randint(0, (36 ** 6) - 1)
    return base36(n).rjust(6, "0")


def ensure_curie(value: str, default_prefix: str = "sdcdc") -> str:
    """
    Ensure a CURIE-like identifier if the value is not already a CURIE/IRI.

    Examples:
        "concept-voltage" -> "sdcdc:concept-voltage"
        "sdcdc:metric-x" -> "sdcdc:metric-x"
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


def is_iri(value: str) -> bool:
    s = str(value or "").strip()
    return s.startswith("http://") or s.startswith("https://")


def is_curie(value: str) -> bool:
    s = str(value or "").strip()
    return (":" in s) and (not is_iri(s))


def sanitize_page_id(value: str) -> str:
    """
    Convert a display ID / CURIE / IRI into a filesystem/xref-safe page ID.

    Examples:
        "sdcdc:concept-voltage-2H4KL0" -> "concept-voltage-2H4KL0"
        "sdcdc:policy-open-information-policy-7B9QX2" -> "policy-open-information-policy-7B9QX2"
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


def has_random_suffix(value: str) -> bool:
    """
    Detect whether an identifier local part already ends with -XXXXXX
    where X is uppercase alphanumeric base36-like.
    """
    s = str(value or "").strip()

    # strip CURIE prefix
    if ":" in s and not is_iri(s):
        s = s.split(":", 1)[1]

    return re.search(r"-[A-Z0-9]{6}$", s) is not None


def append_random_suffix(base_value: str) -> str:
    """
    Append a random 6-character suffix to a base identifier local part.

    Example:
        "concept-voltage" -> "concept-voltage-2H4KL0"
    """
    s = str(base_value or "").strip()
    if not s:
        raise ValueError("Base value for random suffix is empty")
    return f"{s}-{random_token6()}"


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

    Note: this does not add/remove any random suffix; it only normalizes
    characters and casing.
    """
    base = normalize_id_base(catalog_id)
    if not base:
        raise ValueError("Catalog ID produced an empty normalized value")
    return base


# -----------------------------
# Dataset IDs
# -----------------------------

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
    Generate a concept ID with random suffix.

    Example:
        generate_concept_id("Voltage")
        -> "sdcdc:concept-voltage-2H4KL0"
    """
    slug = slugify(concept_label)
    if not slug:
        raise ValueError("Concept label is empty after normalization")
    local = append_random_suffix(f"concept-{slug}")
    return f"sdcdc:{local}"


def normalize_concept_id(concept_id_or_label: str) -> str:
    """
    Normalize a concept ID.

    Rules:
    - if already IRI -> return as-is
    - if already CURIE -> return as-is
    - if starts with 'concept-' -> prefix with sdcdc:
    - otherwise treat as label and generate a new concept ID with suffix

    IMPORTANT:
    - This function only generates a new random-suffixed ID if the input is NOT already an ID.
    - Existing IDs remain stable.
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
    Generate a policy ID with random suffix.

    Example:
        generate_policy_id("Open Information Policy")
        -> "sdcdc:policy-open-information-policy-7B9QX2"
    """
    slug = slugify(policy_title)
    if not slug:
        raise ValueError("Policy title is empty after normalization")
    local = append_random_suffix(f"policy-{slug}")
    return f"sdcdc:{local}"


def normalize_policy_id(policy_id_or_title: str) -> str:
    """
    Normalize a policy ID.

    Rules:
    - if already IRI -> return as-is
    - if already CURIE -> return as-is
    - if starts with 'policy-' -> prefix with sdcdc:
    - otherwise treat as title and generate a new policy ID with suffix
    """
    s = str(policy_id_or_title or "").strip()
    if not s:
        return s
    if is_iri(s):
        return s
    if is_curie(s):
        return s
    if s.startswith("policy-"):
        return f"sdcdc:{s}"
    return generate_policy_id(s)


# -----------------------------
# Metric IDs
# -----------------------------

def generate_metric_id(metric_label: str) -> str:
    """
    Generate a metric ID with random suffix.

    Example:
        generate_metric_id("Voltage Quality")
        -> "sdcdc:metric-voltage-quality-5M1ZP8"
    """
    slug = slugify(metric_label)
    if not slug:
        raise ValueError("Metric label is empty after normalization")
    local = append_random_suffix(f"metric-{slug}")
    return f"sdcdc:{local}"


def normalize_metric_id(metric_id_or_label: str) -> str:
    """
    Normalize a metric ID.

    Rules:
    - if already IRI -> return as-is
    - if already CURIE -> return as-is
    - if starts with 'metric-' -> prefix with sdcdc:
    - otherwise treat as label and generate a new metric ID with suffix
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

def parse_csv_ids(raw: Optional[str], normalizer: Callable[[str], str]) -> list[str]:
    """
    Parse a comma-separated string of IDs/labels using a normalizer function.

    Example:
        parse_csv_ids("Voltage, sdcdc:concept-harmonics-ABC123", normalize_concept_id)
        -> [
            "sdcdc:concept-voltage-<RANDOM6>",
            "sdcdc:concept-harmonics-ABC123"
           ]
    """
    if not raw:
        return []

    values = [x.strip() for x in str(raw).split(",") if x.strip()]
    out = []
    for v in values:
        normalized = normalizer(v)
        if normalized:
            out.append(normalized)
    return out


# -----------------------------
# Small demo
# -----------------------------

if __name__ == "__main__":
    print("Examples:")
    print("catalog:", generate_catalog_id("Grid Data"))
    print("dataset:", normalize_dataset_id("GRID-DATA-AB12CD", "voltage-timeseries"))
    print("concept:", generate_concept_id("Voltage"))
    print("policy:", generate_policy_id("Open Information Policy"))
    print("metric:", generate_metric_id("Voltage Quality"))
    print("page id:", sanitize_page_id("sdcdc:concept-voltage-2H4KL0"))
