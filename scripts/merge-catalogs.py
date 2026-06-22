#!/usr/bin/env python3

from pathlib import Path
import yaml


ROOT = Path("data-catalog")
CATALOG_FILE = ROOT / "catalog.yaml"
OUTPUT_FILE = ROOT / "data-catalog.yaml"

# Folder name -> (expected top-level key inside each file, output Container section name)
ENTITY_SOURCES = {
    "datasets": ("dataset", "datasets"),
    "concepts": ("concept", "concepts"),
    "dataset-series": ("datasetSeries", "series"),
    "distributions": ("distribution", "distributions"),
    "metrics": ("metric", "metrics"),
    "quality-measurements": ("qualityMeasurement", "qualityMeasurements"),
    "data-services": ("dataService", "dataServices"),
    "policies": ("policy", "policies"),

    # Supporting entities now included in merged Container
    "agents": ("agent", "agents"),
    "kinds": ("kind", "kinds"),
    "licenses": ("licenseDocument", "licenseDocuments"),
    "periods": ("periodOfTime", "periods"),
}


def load_yaml(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def load_catalog():
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(f"Missing root catalog file: {CATALOG_FILE}")

    doc = load_yaml(CATALOG_FILE)

    # Accept either:
    #   catalog:
    # or
    #   dataCatalog:
    if "catalog" in doc:
        catalog_obj = doc["catalog"] or {}
    elif "dataCatalog" in doc:
        catalog_obj = doc["dataCatalog"] or {}
    else:
        raise ValueError(
            f"{CATALOG_FILE} must contain either top-level 'catalog' or 'dataCatalog'"
        )

    if not isinstance(catalog_obj, dict):
        raise ValueError(
            f"{CATALOG_FILE} catalog/dataCatalog value must be an object/dictionary"
        )

    return catalog_obj


def load_entity_folder(folder_name: str, top_key: str):
    folder = ROOT / folder_name
    items = []

    if not folder.exists():
        return items

    files = sorted(folder.glob("*.yaml")) + sorted(folder.glob("*.yml"))

    for yf in files:
        doc = load_yaml(yf)

        if top_key not in doc:
            raise ValueError(
                f"File {yf} must contain top-level key '{top_key}'"
            )

        entity = doc[top_key] or {}
        if not isinstance(entity, dict):
            raise ValueError(
                f"Top-level key '{top_key}' in {yf} must map to an object/dictionary"
            )

        items.append(entity)

    return items


def collect_entities():
    merged_sections = {}

    for folder_name, (top_key, output_section) in ENTITY_SOURCES.items():
        merged_sections[output_section] = load_entity_folder(folder_name, top_key)

    return merged_sections


def validate_identifiers(merged):
    seen = {}

    # Validate dataCatalog identifier
    catalog_obj = merged.get("dataCatalog", {}) or {}
    catalog_identifier = str(
        catalog_obj.get("identifier") or catalog_obj.get("id") or catalog_obj.get("uid") or ""
    ).strip()

    if not catalog_identifier:
        raise ValueError("dataCatalog is missing identifier/id/uid")

    seen[catalog_identifier] = "dataCatalog"

    # Validate entity section identifiers
    for section_name, items in merged.items():
        if section_name == "dataCatalog":
            continue

        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            identifier = str(
                item.get("identifier") or item.get("id") or item.get("uid") or ""
            ).strip()

            if not identifier:
                raise ValueError(
                    f"Entity in section '{section_name}' is missing identifier/id/uid: {item}"
                )

            if identifier in seen:
                raise ValueError(
                    f"Duplicate identifier '{identifier}' found in sections "
                    f"'{seen[identifier]}' and '{section_name}'"
                )

            seen[identifier] = section_name


def build_merged_container():
    catalog_obj = load_catalog()
    entity_sections = collect_entities()

    merged = {
        "dataCatalog": catalog_obj,

        # Core entities
        "datasets": entity_sections.get("datasets", []),
        "concepts": entity_sections.get("concepts", []),
        "series": entity_sections.get("series", []),
        "distributions": entity_sections.get("distributions", []),
        "metrics": entity_sections.get("metrics", []),
        "qualityMeasurements": entity_sections.get("qualityMeasurements", []),
        "dataServices": entity_sections.get("dataServices", []),
        "policies": entity_sections.get("policies", []),

        # Supporting entities
        "agents": entity_sections.get("agents", []),
        "kinds": entity_sections.get("kinds", []),
        "licenseDocuments": entity_sections.get("licenseDocuments", []),
        "periods": entity_sections.get("periods", []),
    }

    return merged


def main():
    ROOT.mkdir(parents=True, exist_ok=True)

    merged = build_merged_container()
    validate_identifiers(merged)

    OUTPUT_FILE.write_text(
        yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    counts = []
    for key in (
        "datasets",
        "concepts",
        "series",
        "distributions",
        "metrics",
        "qualityMeasurements",
        "dataServices",
        "policies",
        "agents",
        "kinds",
        "licenseDocuments",
        "periods",
    ):
        counts.append(f"{len(merged.get(key, []))} {key}")

    print(f"OK: wrote merged container YAML to {OUTPUT_FILE}")
    print("Contents: " + ", ".join(counts))


if __name__ == "__main__":
    main()