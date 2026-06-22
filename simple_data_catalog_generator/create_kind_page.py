from rdflib import Graph, URIRef

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_id,
    create_local_link,
)

VCARD_CONTACT_POINT = URIRef("http://www.w3.org/2006/vcard/ns#contactPoint")
VCARD_FN = URIRef("http://www.w3.org/2006/vcard/ns#fn")
VCARD_HAS_EMAIL = URIRef("http://www.w3.org/2006/vcard/ns#hasEmail")
VCARD_HAS_URL = URIRef("http://www.w3.org/2006/vcard/ns#hasURL")


def _literal(graph: Graph, subject: URIRef, predicate: URIRef, default: str = "Not available") -> str:
    value = graph.value(subject, predicate)
    if value is None:
        return default

    value_str = str(value).strip()
    if not value_str or value_str == "None":
        return default

    return value_str


def _datasets_with_contact_table(kind: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for dataset in catalog_graph.subjects(VCARD_CONTACT_POINT, kind):
        dataset_name = get_title(dataset, catalog_graph)
        dataset_id = get_id(dataset, catalog_graph)
        dataset_link = create_local_link(dataset, catalog_graph)
        dataset_display = dataset_link if dataset_link else dataset_name

        rows.append((dataset_name.lower(), dataset_display, dataset_id))

    if not rows:
        return "No datasets currently use this contact point.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Dataset | ID\n\n"

    for _, dataset_display, dataset_id in rows:
        table_str += f"| {dataset_display}\n"
        table_str += f"| `{dataset_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def create_kind_page(kind: URIRef, catalog_graph: Graph):
    kind_name = _literal(catalog_graph, kind, VCARD_FN, default="")
    if not kind_name:
        kind_name = get_title(kind, catalog_graph)

    kind_id = get_id(kind, catalog_graph)
    email = _literal(catalog_graph, kind, VCARD_HAS_EMAIL)
    url = _literal(catalog_graph, kind, VCARD_HAS_URL)

    adoc_str = ""

    adoc_str += f"= {kind_name}\n\n"

    adoc_str += "== Contact Point Details\n\n"
    adoc_str += f"* **Name:** {kind_name}\n"
    adoc_str += f"* **ID:** `{kind_id}`\n"

    if email != "Not available" and email.startswith("mailto:"):
        adoc_str += f"* **Email:** link:{email}[{email.replace('mailto:', '')}]\n"
    else:
        adoc_str += f"* **Email:** {email}\n"

    if url != "Not available":
        adoc_str += f"* **URL:** link:{url}[{url}]\n"
    else:
        adoc_str += "* **URL:** Not available\n"

    adoc_str += "\n"

    adoc_str += "== Datasets Using This Contact Point\n\n"
    adoc_str += _datasets_with_contact_table(kind, catalog_graph)

    adoc_str += "== Overview\n\n"
    adoc_str += "|===\n"
    adoc_str += "|Field |Value\n\n"
    adoc_str += f"|Name |{kind_name}\n"
    adoc_str += f"|ID |`{kind_id}`\n"
    adoc_str += f"|Email |{email}\n"
    adoc_str += f"|URL |{url}\n"
    adoc_str += "|===\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=kind,
        output_dir="modules/kind/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
