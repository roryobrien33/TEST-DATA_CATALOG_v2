from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_id,
    create_local_link,
    get_title,
)

DCTERMS_TEMPORAL = URIRef("http://purl.org/dc/terms/temporal")
TIME_HAS_BEGINNING = URIRef("http://www.w3.org/2006/time#hasBeginning")
TIME_HAS_END = URIRef("http://www.w3.org/2006/time#hasEnd")


def _literal(graph: Graph, subject: URIRef, predicate: URIRef, default: str = "Not available") -> str:
    value = graph.value(subject, predicate)
    if value is None:
        return default

    value_str = str(value).strip()
    if not value_str or value_str == "None":
        return default

    return value_str


def _datasets_with_period_table(period: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for dataset in catalog_graph.subjects(DCTERMS_TEMPORAL, period):
        dataset_name = get_title(dataset, catalog_graph)
        dataset_id = get_id(dataset, catalog_graph)
        dataset_link = create_local_link(dataset, catalog_graph)
        dataset_display = dataset_link if dataset_link else dataset_name

        rows.append((dataset_name.lower(), dataset_display, dataset_id))

    if not rows:
        return "No datasets currently use this temporal period.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Dataset | ID\n\n"

    for _, dataset_display, dataset_id in rows:
        table_str += f"| {dataset_display}\n"
        table_str += f"| `{dataset_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def create_period_page(period: URIRef, catalog_graph: Graph):
    period_id = get_id(period, catalog_graph)
    beginning = _literal(catalog_graph, period, TIME_HAS_BEGINNING)
    end = _literal(catalog_graph, period, TIME_HAS_END)

    adoc_str = ""

    adoc_str += f"= {period_id}\n\n"

    adoc_str += "== Period Details\n\n"
    adoc_str += f"* **ID:** `{period_id}`\n"
    adoc_str += f"* **Start:** {beginning}\n"
    adoc_str += f"* **End:** {end}\n\n"

    adoc_str += "== Datasets Using This Period\n\n"
    adoc_str += _datasets_with_period_table(period, catalog_graph)

    adoc_str += "== Overview\n\n"
    adoc_str += "|===\n"
    adoc_str += "|Field |Value\n\n"
    adoc_str += f"|ID |`{period_id}`\n"
    adoc_str += f"|Start |{beginning}\n"
    adoc_str += f"|End |{end}\n"
    adoc_str += "|===\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=period,
        output_dir="modules/period/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
