from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    get_id,
    create_local_link,
)

DCTERMS_PUBLISHER = URIRef("http://purl.org/dc/terms/publisher")
FOAF_NAME = URIRef("http://xmlns.com/foaf/0.1/name")


def _literal(graph: Graph, subject: URIRef, predicate: URIRef, default: str = "Not available") -> str:
    value = graph.value(subject, predicate)
    if value is None:
        return default

    value_str = str(value).strip()
    if not value_str or value_str == "None":
        return default

    return value_str


def _published_datasets_table(agent: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for dataset in catalog_graph.subjects(DCTERMS_PUBLISHER, agent):
        dataset_name = get_title(dataset, catalog_graph)
        dataset_id = get_id(dataset, catalog_graph)
        dataset_link = create_local_link(dataset, catalog_graph)
        dataset_display = dataset_link if dataset_link else dataset_name

        rows.append((dataset_name.lower(), dataset_display, dataset_id))

    if not rows:
        return "No datasets currently list this agent as publisher.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Dataset | ID\n\n"

    for _, dataset_display, dataset_id in rows:
        table_str += f"| {dataset_display}\n"
        table_str += f"| `{dataset_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def create_agent_page(agent: URIRef, catalog_graph: Graph):
    agent_name = get_title(agent, catalog_graph)
    agent_id = get_id(agent, catalog_graph)
    agent_description = get_description(agent, catalog_graph)
    foaf_name = _literal(catalog_graph, agent, FOAF_NAME)

    adoc_str = ""

    adoc_str += f"= {agent_name}\n\n"

    adoc_str += "== Agent Details\n\n"
    adoc_str += f"* **Name:** {agent_name}\n"
    adoc_str += f"* **ID:** `{agent_id}`\n"
    adoc_str += f"* **FOAF name:** {foaf_name}\n"

    if agent_description and agent_description != "None":
        adoc_str += f"* **Description:** {agent_description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    adoc_str += "\n"

    adoc_str += "== Published Datasets\n\n"
    adoc_str += _published_datasets_table(agent, catalog_graph)

    adoc_str += "== Overview\n\n"
    adoc_str += "|===\n"
    adoc_str += "|Field |Value\n\n"
    adoc_str += f"|Name |{agent_name}\n"
    adoc_str += f"|ID |`{agent_id}`\n"
    adoc_str += f"|FOAF name |{foaf_name}\n"
    adoc_str += "|===\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=agent,
        output_dir="modules/agent/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
