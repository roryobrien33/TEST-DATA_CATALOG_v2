from rdflib import Graph, URIRef, Namespace, RDF
from rdflib.namespace import DCTERMS

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    create_local_link,
    get_id,
    get_prefLabel,
)

SDCDC = Namespace("https://www.uuidea.eu/profiles/data-catalog/")
DQV = Namespace("http://www.w3.org/ns/dqv#")
ODRL = Namespace("http://www.w3.org/ns/odrl/2/")

DCAT_IN_SERIES = URIRef("http://www.w3.org/ns/dcat#inSeries")
DCAT_THEME = URIRef("http://www.w3.org/ns/dcat#theme")
DCAT_DISTRIBUTION = URIRef("http://www.w3.org/ns/dcat#distribution")
DCAT_ACCESS_URL = URIRef("http://www.w3.org/ns/dcat#accessURL")
ODRL_HAS_POLICY = URIRef("http://www.w3.org/ns/odrl/2/hasPolicy")

DQV_QUALITY_MEASUREMENT = URIRef("http://www.w3.org/ns/dqv#QualityMeasurement")
DQV_COMPUTED_ON = URIRef("http://www.w3.org/ns/dqv#computedOn")
DQV_IS_MEASUREMENT_OF = URIRef("http://www.w3.org/ns/dqv#isMeasurementOf")
DQV_VALUE = URIRef("http://www.w3.org/ns/dqv#value")


def _first_literal(graph: Graph, subject: URIRef, predicates):
    for pred in predicates:
        val = graph.value(subject, pred)
        if val is not None and str(val).strip() and str(val).strip() != "None":
            return str(val).strip()
    return ""


def _linked_concepts_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for concept in catalog_graph.objects(dataset, DCAT_THEME):
        concept_name = get_prefLabel(concept, catalog_graph)
        if not concept_name or concept_name == "None":
            concept_name = get_title(concept, catalog_graph)
        if not concept_name or concept_name == "None":
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


def _linked_policies_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for policy in catalog_graph.objects(dataset, ODRL_HAS_POLICY):
        policy_name = get_title(policy, catalog_graph)
        if not policy_name or policy_name == "None":
            policy_name = get_id(policy, catalog_graph)

        policy_id = get_id(policy, catalog_graph)
        policy_link = create_local_link(policy, catalog_graph)
        policy_name_display = policy_link if policy_link else policy_name

        rows.append((policy_name.lower(), policy_name_display, policy_id))

    if not rows:
        return "No linked policies.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Policy | ID\n\n"

    for _, policy_name_display, policy_id in rows:
        table_str += f"| {policy_name_display}\n"
        table_str += f"| `{policy_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def _linked_metrics_rows(dataset: URIRef, catalog_graph: Graph):
    rows = []

    for qm in catalog_graph.subjects(RDF.type, DQV_QUALITY_MEASUREMENT):
        computed_on = list(catalog_graph.objects(qm, DQV_COMPUTED_ON))
        if dataset not in computed_on:
            continue

        qm_id = get_id(qm, catalog_graph)
        qm_value = str(catalog_graph.value(qm, DQV_VALUE) or "").strip()
        if not qm_value or qm_value == "None":
            qm_value = "Not available"

        metrics = list(catalog_graph.objects(qm, DQV_IS_MEASUREMENT_OF))
        if not metrics:
            rows.append(
                (
                    "",
                    "Unknown metric",
                    "Not available",
                    qm_id,
                    qm_value,
                )
            )
            continue

        for metric in metrics:
            metric_name = get_prefLabel(metric, catalog_graph)
            if not metric_name or metric_name == "None":
                metric_name = get_title(metric, catalog_graph)
            if not metric_name or metric_name == "None":
                metric_name = get_id(metric, catalog_graph)

            metric_id = get_id(metric, catalog_graph)
            metric_link = create_local_link(metric, catalog_graph)
            metric_name_display = metric_link if metric_link else metric_name

            rows.append(
                (
                    metric_name.lower(),
                    metric_name_display,
                    metric_id,
                    qm_id,
                    qm_value,
                )
            )

    rows.sort(key=lambda x: x[0] if x[0] else "")
    return rows


def _linked_metrics_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = _linked_metrics_rows(dataset, catalog_graph)

    if not rows:
        return "No linked metrics.\n\n"

    table_str = "|===\n"
    table_str += "| Metric | Metric ID | Measurement ID | Value\n\n"

    for _, metric_name_display, metric_id, qm_id, qm_value in rows:
        table_str += f"| {metric_name_display}\n"
        table_str += f"| `{metric_id}`\n"
        table_str += f"| `{qm_id}`\n"
        table_str += f"| {qm_value}\n\n"

    table_str += "|===\n\n"
    return table_str


def _distribution_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for distribution in catalog_graph.objects(dataset, DCAT_DISTRIBUTION):
        dist_id = get_id(distribution, catalog_graph)

        dist_title = get_title(distribution, catalog_graph)
        if not dist_title or dist_title == "None":
            dist_title = dist_id

        access_url = str(catalog_graph.value(distribution, DCAT_ACCESS_URL) or "").strip()
        if not access_url or access_url == "None":
            access_url = "Not available"

        dist_format = str(catalog_graph.value(distribution, DCTERMS.format) or "").strip()
        if not dist_format or dist_format == "None":
            dist_format = "Not available"

        dist_issued = str(catalog_graph.value(distribution, DCTERMS.issued) or "").strip()
        if not dist_issued or dist_issued == "None":
            dist_issued = "–"

        rows.append(
            (
                dist_title.lower(),
                dist_title,
                dist_id,
                access_url,
                dist_format,
                dist_issued,
            )
        )

    if not rows:
        return "No distributions available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Distribution | ID | Access URL | Format | Issued\n\n"

    for _, dist_title, dist_id, access_url, dist_format, dist_issued in rows:
        if access_url != "Not available":
            access_cell = f"link:{access_url}[{access_url}]"
        else:
            access_cell = access_url

        table_str += f"| {dist_title}\n"
        table_str += f"| `{dist_id}`\n"
        table_str += f"| {access_cell}\n"
        table_str += f"| {dist_format}\n"
        table_str += f"| {dist_issued}\n\n"

    table_str += "|===\n\n"
    return table_str


def create_dataset_page(dataset: URIRef, catalog_graph: Graph):
    adoc_str = str()

    dataset_name = get_title(dataset, catalog_graph)
    dataset_id = get_id(dataset, catalog_graph)
    dataset_description = get_description(subject=dataset, graph=catalog_graph)

    linked_series = catalog_graph.value(dataset, DCAT_IN_SERIES)
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

    linked_distributions = list(catalog_graph.objects(dataset, DCAT_DISTRIBUTION))
    linked_policies = list(catalog_graph.objects(dataset, ODRL_HAS_POLICY))
    linked_metrics = _linked_metrics_rows(dataset, catalog_graph)

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

    if linked_distributions:
        adoc_str += f"* **Distributions:** {len(linked_distributions)} available (see section below)\n"
    else:
        adoc_str += "* **Distributions:** None\n"

    if linked_policies:
        adoc_str += f"* **Policies:** {len(linked_policies)} available (see section below)\n"
    else:
        adoc_str += "* **Policies:** None\n"

    if linked_metrics:
        adoc_str += f"* **Metrics:** {len(linked_metrics)} available (see section below)\n"
    else:
        adoc_str += "* **Metrics:** None\n"

    adoc_str += "\n"

    adoc_str += "== Description\n\n"
    if dataset_description and dataset_description != "None":
        adoc_str += dataset_description + "\n\n"
    else:
        adoc_str += "No description available.\n\n"

    adoc_str += "== Themes\n\n"
    adoc_str += _linked_concepts_table(dataset, catalog_graph)

    adoc_str += "== Policies\n\n"
    adoc_str += _linked_policies_table(dataset, catalog_graph)

    adoc_str += "== Metrics\n\n"
    adoc_str += _linked_metrics_table(dataset, catalog_graph)

    adoc_str += "== Distributions\n\n"
    adoc_str += _distribution_table(dataset, catalog_graph)

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