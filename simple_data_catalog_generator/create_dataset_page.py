from rdflib import Graph, URIRef, DCAT, RDF, DCTERMS, Namespace
from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    create_local_link,
    get_id,
)
from simple_data_catalog_generator.create_distribution_table import create_distribution_table

# Existing namespaces already used elsewhere
DQV = Namespace("http://www.w3.org/ns/dqv#")
SDCDC = Namespace("https://www.uuidea.eu/profiles/data-catalog/")


def _first_literal(graph: Graph, subject: URIRef, predicates):
    """
    Return the first non-empty literal/object value found for the given subject
    across the supplied predicate list.
    """
    for pred in predicates:
        val = graph.value(subject, pred)
        if val is not None and str(val).strip() and str(val).strip() != "None":
            return str(val).strip()
    return ""


def create_dataset_page(dataset: URIRef, catalog_graph: Graph):
    adoc_str = str()

    # ---------------------------
    # Core values
    # ---------------------------
    dataset_name = get_title(dataset, catalog_graph)
    dataset_id = get_id(dataset, catalog_graph)
    dataset_description = get_description(subject=dataset, graph=catalog_graph)

    # Linked Catalog ID (represented in your current architecture via inSeries)
    linked_series = catalog_graph.value(dataset, DCAT.inSeries)
    linked_catalog_id = ""
    linked_catalog_link = ""
    if linked_series is not None:
        linked_catalog_id = get_id(linked_series, catalog_graph)
        linked_catalog_link = create_local_link(linked_series, catalog_graph)

    # Use case
    # Your current schema does not formally define a dataset use_case slot,
    # but we try a few likely predicates so this page can display it if/when
    # it is present in the graph.
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

    # Linked Concepts (themes)
    linked_concepts = [
        create_local_link(theme, catalog_graph)
        for theme in catalog_graph.objects(dataset, DCAT.theme)
    ]

    # Distributions
    distributions = list(catalog_graph.objects(dataset, DCAT.distribution))

    # ---------------------------
    # Page title
    # ---------------------------
    adoc_str += "= " + dataset_name + "\n\n"

    # ---------------------------
    # Dataset summary
    # ---------------------------
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

    if linked_concepts:
        adoc_str += "* **Linked Concepts:**\n"
        for concept_link in linked_concepts:
            adoc_str += f"** {concept_link}\n"
    else:
        adoc_str += "* **Linked Concepts:** None\n"

    if distributions:
        adoc_str += f"* **Distributions:** {len(distributions)} available (see section below)\n"
    else:
        adoc_str += "* **Distributions:** None\n"

    adoc_str += "\n"

    # ---------------------------
    # Description section
    # ---------------------------
    adoc_str += "== Description\n\n"
    if dataset_description and dataset_description != "None":
        adoc_str += dataset_description + "\n\n"
    else:
        adoc_str += "No description available.\n\n"

    # ---------------------------
    # Linked Concepts section
    # ---------------------------
    adoc_str += "== Linked Concepts\n\n"
    if linked_concepts:
        adoc_str += "\n".join(linked_concepts) + "\n\n"
    else:
        adoc_str += "No linked concepts.\n\n"

    # ---------------------------
    # Distributions section
    # ---------------------------
    adoc_str += "== Distributions\n\n"
    if distributions:
        adoc_str += create_distribution_table(dataset=dataset, catalog_graph=catalog_graph)
        adoc_str += "\n\n"
    else:
        adoc_str += "No distributions available.\n\n"

    # ---------------------------
    # Optional metadata overview
    # Keep this if you still want the generic table
    # ---------------------------
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

    # ---------------------------
    # Write file
    # ---------------------------
    write_file(
        adoc_str=adoc_str,
        resource=dataset,
        output_dir="modules/dataset/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
