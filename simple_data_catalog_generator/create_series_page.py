from rdflib import Graph, URIRef, RDF
from rdflib.namespace import DCTERMS

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    create_local_link,
    get_id,
)

DCAT_IN_SERIES = URIRef("http://www.w3.org/ns/dcat#inSeries")
DCAT_DATASET = URIRef("http://www.w3.org/ns/dcat#Dataset")


def _linked_datasets_table(series: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for dataset in catalog_graph.subjects(DCAT_IN_SERIES, series):
        dataset_name = get_title(dataset, catalog_graph)
        if not dataset_name or dataset_name == "None":
            dataset_name = get_id(dataset, catalog_graph)

        dataset_id = get_id(dataset, catalog_graph)
        dataset_link = create_local_link(dataset, catalog_graph)
        dataset_name_display = dataset_link if dataset_link else dataset_name

        rows.append((dataset_name.lower(), dataset_name_display, dataset_id))

    if not rows:
        return "No linked datasets.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Dataset | ID\n\n"

    for _, dataset_name_display, dataset_id in rows:
        table_str += f"| {dataset_name_display}\n"
        table_str += f"| `{dataset_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def create_series_page(series: URIRef, catalog_graph: Graph):
    adoc_str = str()

    series_name = get_title(series, catalog_graph)
    series_id = get_id(series, catalog_graph)
    series_description = get_description(subject=series, graph=catalog_graph)

    linked_datasets = list(catalog_graph.subjects(DCAT_IN_SERIES, series))

    adoc_str += "= " + series_name + "\n\n"

    adoc_str += "== Series Details\n\n"
    adoc_str += f"* **Name:** {series_name}\n"
    adoc_str += f"* **ID:** `{series_id}`\n"

    if series_description and series_description != "None":
        adoc_str += f"* **Description:** {series_description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    if linked_datasets:
        adoc_str += f"* **Datasets:** {len(linked_datasets)} linked dataset(s) (see section below)\n"
    else:
        adoc_str += "* **Datasets:** None\n"

    adoc_str += "\n"

    adoc_str += "== Description\n\n"
    if series_description and series_description != "None":
        adoc_str += series_description + "\n\n"
    else:
        adoc_str += "No description available.\n\n"

    adoc_str += "== Datasets in Series\n\n"
    adoc_str += _linked_datasets_table(series, catalog_graph)

    adoc_str += "== Overview\n\n"
    adoc_str += (
        f"|===\n"
        f"|Field |Value\n\n"
        f"|Name |{series_name}\n"
        f"|ID |`{series_id}`\n"
        f"|===\n\n"
    )

    write_file(
        adoc_str=adoc_str,
        resource=series,
        output_dir="modules/dataset-series/pages/",
        catalog_graph=catalog_graph,
    )

    return 1