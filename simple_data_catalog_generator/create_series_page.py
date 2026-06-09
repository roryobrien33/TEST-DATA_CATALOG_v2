from pathlib import Path
import yaml

from rdflib import Graph, URIRef, DCAT
from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    create_local_link,
    get_id,
    get_prefLabel,
    get_definition,
)
from simple_data_catalog_generator.create_metadata_table import create_metadata_table


def _candidate_series_names(raw_id: str, title: str):
    candidates = []

    if raw_id:
        raw_id = str(raw_id).strip()
        candidates.append(raw_id)

        if ":" in raw_id:
            candidates.append(raw_id.split(":", 1)[1])

        if "/" in raw_id:
            candidates.append(raw_id.rstrip("/").split("/")[-1])

        if "#" in raw_id:
            candidates.append(raw_id.split("#")[-1])

    if title:
        candidates.append(str(title).strip())

    seen = set()
    cleaned = []
    for c in candidates:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            cleaned.append(c)

    return cleaned


def _load_deleted_datasets_for_series(series: URIRef, catalog_graph: Graph):
    raw_series_id = get_id(series, catalog_graph)
    series_title = get_title(series, catalog_graph)
    candidate_names = _candidate_series_names(raw_series_id, series_title)

    source_file = None
    for name in candidate_names:
        for ext in (".yaml", ".yml"):
            candidate = Path(f"data-catalog/user-catalogs/{name}{ext}")
            if candidate.exists():
                source_file = candidate
                break
        if source_file is not None:
            break

    if source_file is None:
        catalog_files = sorted(Path("data-catalog/user-catalogs").glob("*.yaml")) + sorted(
            Path("data-catalog/user-catalogs").glob("*.yml")
        )

        for yf in catalog_files:
            doc = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
            cat = doc.get("catalog", {}) or {}

            cat_id = str(cat.get("id") or cat.get("identifier") or "").strip()
            cat_title = str(cat.get("title") or cat.get("name") or "").strip()

            if cat_id in candidate_names:
                source_file = yf
                break

            if series_title and cat_title == series_title:
                source_file = yf
                break

    if source_file is None:
        return []

    doc = yaml.safe_load(source_file.read_text(encoding="utf-8")) or {}
    deleted_datasets = doc.get("deleted_datasets", [])

    if deleted_datasets is None:
        return []

    if not isinstance(deleted_datasets, list):
        return []

    cleaned = []
    for item in deleted_datasets:
        if isinstance(item, dict):
            cleaned.append(item)

    return cleaned


def _build_theme_concept_table_for_series(series: URIRef, catalog_graph: Graph) -> str:
    """
    Build a table of concepts actually linked to datasets in this series.
    """
    concept_to_datasets = {}

    for dataset in catalog_graph.subjects(DCAT.inSeries, series):
        dataset_id = get_id(dataset, catalog_graph)

        for concept in catalog_graph.objects(dataset, DCAT.theme):
            concept_to_datasets.setdefault(concept, set()).add(dataset_id)

    if not concept_to_datasets:
        return "No concepts linked to datasets in this catalog.\n\n"

    rows = []
    for concept, linked_dataset_ids in concept_to_datasets.items():
        concept_name = get_prefLabel(concept, catalog_graph)
        if not concept_name or concept_name == "None":
            concept_name = get_title(concept, catalog_graph)
        if not concept_name or concept_name == "None":
            concept_name = get_id(concept, catalog_graph)

        concept_id = get_id(concept, catalog_graph)
        concept_definition = get_definition(concept, catalog_graph)
        if not concept_definition or concept_definition == "None":
            concept_definition = "Not available"

        concept_link = create_local_link(concept, catalog_graph)
        concept_name_display = concept_link if concept_link else concept_name

        rows.append(
            (
                concept_name.lower(),
                concept_name_display,
                concept_id,
                len(linked_dataset_ids),
                concept_definition,
            )
        )

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Concept | ID | Linked datasets | Definition\n\n"

    for _, concept_name_display, concept_id, linked_count, concept_definition in rows:
        table_str += f"| {concept_name_display}\n"
        table_str += f"| `{concept_id}`\n"
        table_str += f"| {linked_count}\n"
        table_str += f"| {concept_definition}\n\n"

    table_str += "|===\n\n"
    return table_str


def create_series_page(series: URIRef, catalog_graph: Graph):
    adoc_str = str()

    deleted_datasets = _load_deleted_datasets_for_series(series, catalog_graph)
    deleted_ids = {
        str(item.get("id", "")).strip()
        for item in deleted_datasets
        if str(item.get("id", "")).strip()
    }

    # Title
    adoc_str += "= " + get_title(series, catalog_graph) + "\n\n"

    # Description
    adoc_str += "== Description\n\n"
    desc = get_description(subject=series, graph=catalog_graph)
    if desc and desc != "None":
        adoc_str += desc + "\n\n"
    else:
        adoc_str += "No description available.\n\n"

    # Themes (concepts linked to datasets in this series)
    adoc_str += "== Themes\n\n"
    adoc_str += _build_theme_concept_table_for_series(series=series, catalog_graph=catalog_graph)

    # Overview
    adoc_str += "== Overview\n\n"
    adoc_str += create_metadata_table(
        catalog_graph=catalog_graph,
        resource=series
    )
    adoc_str += "\n\n"

    # Active datasets
    adoc_str += "== Datasets in this series\n\n"

    active_dataset_links = []
    for dataset in catalog_graph.subjects(DCAT.inSeries, series):
        dataset_id = get_id(dataset, catalog_graph)
        if dataset_id in deleted_ids:
            continue
        active_dataset_links.append(create_local_link(dataset, catalog_graph))

    if active_dataset_links:
        adoc_str += "\n".join(active_dataset_links) + "\n\n"
    else:
        adoc_str += "No active datasets in this series.\n\n"

    # Deleted datasets
    adoc_str += "== Deleted datasets in this series\n\n"

    if deleted_datasets:
        adoc_str += "|===\n"
        adoc_str += "| Name | ID | Deleted at | Description\n\n"

        for item in deleted_datasets:
            ds_id = str(item.get("id", "")).strip() or "Not available"
            ds_title = str(item.get("title", "")).strip() or "Not available"
            ds_deleted_at = str(item.get("deleted_at", "")).strip() or "Not available"
            ds_description = str(item.get("description", "")).strip() or "Not available"

            adoc_str += f"| {ds_title}\n"
            adoc_str += f"| `{ds_id}`\n"
            adoc_str += f"| {ds_deleted_at}\n"
            adoc_str += f"| {ds_description}\n\n"

        adoc_str += "|===\n\n"
    else:
        adoc_str += "No deleted datasets recorded for this series.\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=series,
        output_dir='modules/dataset-series/pages/',
        catalog_graph=catalog_graph
    )

    return 1
