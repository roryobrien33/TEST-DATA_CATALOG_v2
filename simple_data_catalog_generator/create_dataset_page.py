from rdflib import Graph, URIRef, DCAT, DCTERMS, Namespace
from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    create_local_link,
    get_id,
)
from simple_data_catalog_generator.create_distribution_table import create_distribution_table

DQV = Namespace("http://www.w3.org/ns/dqv#")
SDCDC = Namespace("https://www.uuidea.eu/profiles/data-catalog/")


def _first_literal(graph: Graph, subject: URIRef, predicates):
    for pred in predicates:
        val = graph.value(subject, pred)
        if val is not None and str(val).strip() and str(val).strip() != "None":
            return str(val).strip()
    return ""


def _linked_concepts_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for concept in catalog_graph.objects(dataset, DCAT.theme):
        concept_name = get_title(concept, catalog_graph)
        if not concept_name or concept_name == "None":
            # For concepts, title may be absent; fall back to id
            concept_name = get_id(concept, catalog_graph)

        concept_id = get_id(concept, catalog_graph)
        concept_link = create_local_link(concept, catalog_graph)
        concept_name_display = concept_link if concept_link else concept_name
        rows.append((concept_name.lower(), concept_name_display, concept_id))

    if not rows:
        return "No linked concepts.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Concept | ID\n\n"

    for _, concept_name_display, concept_id in rows:
        table_str += f"| {concept_name_display}\n"
        table_str += f"| `{concept_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def create_dataset_page(dataset: URIRef, catalog_graph: Graph):
    adoc_str = str()

    dataset_name = get_title(dataset, catalog_graph)
    dataset_id = get_id(dataset, catalog_graph)
    dataset_description = get_description(subject=dataset, graph=catalog_graph)

    linked_series = catalog_graph.value(dataset, DCAT.inSeries)
    linked_catalog_id = ""
    linked_catalog_link = ""
    if linked_series is not None:
        linked_catalog_id = get_id(linked_series, catalog_graph)
        linked_catalog_link = create_local_link(linked_series, catalog_graph)

    dataset_use_case = _first_literal(
        catalog_graph,
        dataset,
        [
            SDCDC.use_case,
            SDCDC.useCase,
            Namespace("https://www.uuidea.eu/profiles/data-catalog/")["use_case"],
            Namespace("https://www.uuidea.eu/profiles/data-catalog/")["useCase"],
        ],
    )

    distributions = list(catalog_graph.objects(dataset, DCAT.distribution))

    adoc_str += "= " + dataset_name + "\n\n"

    adoc_str += "== Dataset Details\n\n"
    adoc_str += f"* **Name:** {dataset_name}\n"
    adoc_str += f"* **ID:** `{dataset_id}`\n"

    if linked_catalog_link:
        adoc_str += f"* **Linked Catalog ID:** `{linked_catalog_id}` ({linked_catalog_link})\n"
    elif linked_catalog_id:
        adoc_str += f"* **Linked Catalog ID:** `{linked_catalog_id}`\n"
    else:
        adoc_str += "* **Linked Catalog ID:** Not available\n"

    if dataset_description and dataset_description != "None":
        adoc_str += f"* **Description:** {dataset_description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    if dataset_use_case:
        adoc_str += f"* **Use case:** {dataset_use_case}\n"
    else:
        adoc_str += "* **Use case:** Not available\n"

    if distributions:
        adoc_str += f"* **Distributions:** {len(distributions)} available (see section below)\n"
    else:
        adoc_str += "* **Distributions:** None\n"

    adoc_str += "\n"

    adoc_str += "== Description\n\n"
    if dataset_description and dataset_description != "None":
        adoc_str += dataset_description + "\n\n"
    else:
        adoc_str += "No description available.\n\n"

    adoc_str += "== Linked Concepts\n\n"
    adoc_str += _linked_concepts_table(dataset=dataset, catalog_graph=catalog_graph)

    adoc_str += "== Distributions\n\n"
    if distributions:
        adoc_str += create_distribution_table(dataset=dataset, catalog_graph=catalog_graph)
        adoc_str += "\n\n"
    else:
        adoc_str += "No distributions available.\n\n"

    adoc_str += "== Overview\n\n"
    adoc_str += (
        f"|===\n"
        f"|Field |Value\n\n"
        f"|Name |{dataset_name}\n"
        f"|ID |`{dataset_id}`\n"
        f"|Linked Catalog ID |{linked_catalog_id if linked_catalog_id else 'Not available'}\n"
        f"|Use case |{dataset_use_case if dataset_use_case else 'Not available'}\n"
        f"|===\n\n"
    )

    write_file(
        adoc_str=adoc_str,
        resource=dataset,
        output_dir="modules/dataset/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
