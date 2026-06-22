from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    get_id,
    create_local_link,
)

DCAT_ACCESS_URL = URIRef("http://www.w3.org/ns/dcat#accessURL")
DCTERMS_LICENSE = URIRef("http://purl.org/dc/terms/license")


def _literal(graph: Graph, subject: URIRef, predicate: URIRef, default: str = "Not available") -> str:
    value = graph.value(subject, predicate)
    if value is None:
        return default

    value_str = str(value).strip()
    if not value_str or value_str == "None":
        return default

    return value_str


def _licensed_datasets_table(license_resource: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for dataset in catalog_graph.subjects(DCTERMS_LICENSE, license_resource):
        dataset_name = get_title(dataset, catalog_graph)
        dataset_id = get_id(dataset, catalog_graph)
        dataset_link = create_local_link(dataset, catalog_graph)
        dataset_display = dataset_link if dataset_link else dataset_name

        rows.append((dataset_name.lower(), dataset_display, dataset_id))

    if not rows:
        return "No datasets currently use this license.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Dataset | ID\n\n"

    for _, dataset_display, dataset_id in rows:
        table_str += f"| {dataset_display}\n"
        table_str += f"| `{dataset_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def create_license_page(license_resource: URIRef, catalog_graph: Graph):
    license_name = get_title(license_resource, catalog_graph)
    license_id = get_id(license_resource, catalog_graph)
    description = get_description(license_resource, catalog_graph)
    access_url = _literal(catalog_graph, license_resource, DCAT_ACCESS_URL)

    adoc_str = ""

    adoc_str += f"= {license_name}\n\n"

    adoc_str += "== License Details\n\n"
    adoc_str += f"* **Name:** {license_name}\n"
    adoc_str += f"* **ID:** `{license_id}`\n"

    if description and description != "None":
        adoc_str += f"* **Description:** {description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    if access_url != "Not available":
        adoc_str += f"* **Access URL:** link:{access_url}[{access_url}]\n"
    else:
        adoc_str += "* **Access URL:** Not available\n"

    adoc_str += "\n"

    adoc_str += "== Datasets Using This License\n\n"
    adoc_str += _licensed_datasets_table(license_resource, catalog_graph)

    adoc_str += "== Overview\n\n"
    adoc_str += "|===\n"
    adoc_str += "|Field |Value\n\n"
    adoc_str += f"|Name |{license_name}\n"
    adoc_str += f"|ID |`{license_id}`\n"
    adoc_str += f"|Access URL |{access_url}\n"
    adoc_str += "|===\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=license_resource,
        output_dir="modules/license/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
