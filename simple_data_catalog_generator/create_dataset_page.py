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

DCAT_IN_SERIES = URIRef("http://www.w3.org/ns/dcat#inSeries")
DCAT_THEME = URIRef("http://www.w3.org/ns/dcat#theme")
DCAT_DISTRIBUTION = URIRef("http://www.w3.org/ns/dcat#distribution")
DCAT_ACCESS_URL = URIRef("http://www.w3.org/ns/dcat#accessURL")

DCTERMS_PUBLISHER = URIRef("http://purl.org/dc/terms/publisher")
DCTERMS_LICENSE = URIRef("http://purl.org/dc/terms/license")
DCTERMS_TEMPORAL = URIRef("http://purl.org/dc/terms/temporal")

VCARD_CONTACT_POINT = URIRef("http://www.w3.org/2006/vcard/ns#contactPoint")
VCARD_FN = URIRef("http://www.w3.org/2006/vcard/ns#fn")
VCARD_HAS_EMAIL = URIRef("http://www.w3.org/2006/vcard/ns#hasEmail")
VCARD_HAS_URL = URIRef("http://www.w3.org/2006/vcard/ns#hasURL")

TIME_HAS_BEGINNING = URIRef("http://www.w3.org/2006/time#hasBeginning")
TIME_HAS_END = URIRef("http://www.w3.org/2006/time#hasEnd")

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


def _literal(graph: Graph, subject: URIRef, predicate: URIRef, default: str = "Not available") -> str:
    val = graph.value(subject, predicate)
    if val is None:
        return default

    val_str = str(val).strip()
    if not val_str or val_str == "None":
        return default

    return val_str


def _linked_resource_table(
    subject: URIRef,
    predicate: URIRef,
    catalog_graph: Graph,
    label_singular: str,
) -> str:
    rows = []

    for resource in catalog_graph.objects(subject, predicate):
        resource_name = get_title(resource, catalog_graph)
        if not resource_name or resource_name == "None":
            resource_name = get_prefLabel(resource, catalog_graph)
        if not resource_name or resource_name == "None":
            resource_name = get_id(resource, catalog_graph)

        resource_id = get_id(resource, catalog_graph)
        resource_link = create_local_link(resource, catalog_graph)
        resource_display = resource_link if resource_link else resource_name

        rows.append((resource_name.lower(), resource_display, resource_id))

    if not rows:
        return f"No linked {label_singular.lower()}s.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += f"| {label_singular} | ID\n\n"

    for _, resource_display, resource_id in rows:
        table_str += f"| {resource_display}\n"
        table_str += f"| `{resource_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


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
        concept_display = concept_link if concept_link else concept_name

        rows.append((concept_name.lower(), concept_display, concept_id))

    if not rows:
        return "No linked concepts.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Concept | ID\n\n"

    for _, concept_display, concept_id in rows:
        table_str += f"| {concept_display}\n"
        table_str += f"| `{concept_id}`\n\n"

    table_str += "|===\n\n"
    return table_str


def _linked_policies_table(dataset: URIRef, catalog_graph: Graph) -> str:
    return _linked_resource_table(
        subject=dataset,
        predicate=ODRL_HAS_POLICY,
        catalog_graph=catalog_graph,
        label_singular="Policy",
    )


def _publisher_table(dataset: URIRef, catalog_graph: Graph) -> str:
    return _linked_resource_table(
        subject=dataset,
        predicate=DCTERMS_PUBLISHER,
        catalog_graph=catalog_graph,
        label_singular="Publisher",
    )


def _license_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for license_resource in catalog_graph.objects(dataset, DCTERMS_LICENSE):
        license_name = get_title(license_resource, catalog_graph)
        if not license_name or license_name == "None":
            license_name = get_id(license_resource, catalog_graph)

        license_id = get_id(license_resource, catalog_graph)
        license_link = create_local_link(license_resource, catalog_graph)
        license_display = license_link if license_link else license_name

        description = get_description(license_resource, catalog_graph)
        if not description or description == "None":
            description = "Not available"

        access_url = _literal(
            graph=catalog_graph,
            subject=license_resource,
            predicate=DCAT_ACCESS_URL,
            default="Not available",
        )

        rows.append((license_name.lower(), license_display, license_id, access_url, description))

    if not rows:
        return "No linked licenses.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| License | ID | Access URL | Description\n\n"

    for _, license_display, license_id, access_url, description in rows:
        if access_url != "Not available":
            access_cell = f"link:{access_url}[{access_url}]"
        else:
            access_cell = access_url

        table_str += f"| {license_display}\n"
        table_str += f"| `{license_id}`\n"
        table_str += f"| {access_cell}\n"
        table_str += f"| {description}\n\n"

    table_str += "|===\n\n"
    return table_str


def _contact_point_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for contact in catalog_graph.objects(dataset, VCARD_CONTACT_POINT):
        contact_name = _literal(catalog_graph, contact, VCARD_FN, default="")
        if not contact_name:
            contact_name = get_title(contact, catalog_graph)
        if not contact_name or contact_name == "None":
            contact_name = get_id(contact, catalog_graph)

        contact_id = get_id(contact, catalog_graph)

        email = _literal(catalog_graph, contact, VCARD_HAS_EMAIL)
        url = _literal(catalog_graph, contact, VCARD_HAS_URL)

        rows.append((contact_name.lower(), contact_name, contact_id, email, url))

    if not rows:
        return "No linked contact points.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Contact point | ID | Email | URL\n\n"

    for _, contact_name, contact_id, email, url in rows:
        if email != "Not available" and email.startswith("mailto:"):
            email_cell = f"link:{email}[{email.replace('mailto:', '')}]"
        elif email != "Not available":
            email_cell = email
        else:
            email_cell = "Not available"

        if url != "Not available":
            url_cell = f"link:{url}[{url}]"
        else:
            url_cell = "Not available"

        table_str += f"| {contact_name}\n"
        table_str += f"| `{contact_id}`\n"
        table_str += f"| {email_cell}\n"
        table_str += f"| {url_cell}\n\n"

    table_str += "|===\n\n"
    return table_str


def _temporal_table(dataset: URIRef, catalog_graph: Graph) -> str:
    rows = []

    for period in catalog_graph.objects(dataset, DCTERMS_TEMPORAL):
        period_id = get_id(period, catalog_graph)

        beginning = _literal(
            graph=catalog_graph,
            subject=period,
            predicate=TIME_HAS_BEGINNING,
            default="Not available",
        )

        end = _literal(
            graph=catalog_graph,
            subject=period,
            predicate=TIME_HAS_END,
            default="Not available",
        )

        rows.append((period_id.lower(), period_id, beginning, end))

    if not rows:
        return "No temporal coverage available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Period | Start | End\n\n"

    for _, period_id, beginning, end in rows:
        table_str += f"| `{period_id}`\n"
        table_str += f"| {beginning}\n"
        table_str += f"| {end}\n\n"

    table_str += "|===\n\n"
    return table_str


def _linked_metrics_rows(dataset: URIRef, catalog_graph: Graph):
    rows = []

    for qm in catalog_graph.subjects(RDF.type, DQV_QUALITY_MEASUREMENT):
        computed_on = list(catalog_graph.objects(qm, DQV_COMPUTED_ON))
        if dataset not in computed_on:
            continue

        qm_id = get_id(qm, catalog_graph)
        qm_value = _literal(catalog_graph, qm, DQV_VALUE)

        metrics = list(catalog_graph.objects(qm, DQV_IS_MEASUREMENT_OF))
        if not metrics:
            rows.append(("", "Unknown metric", "Not available", qm_id, qm_value))
            continue

        for metric in metrics:
            metric_name = get_prefLabel(metric, catalog_graph)
            if not metric_name or metric_name == "None":
                metric_name = get_title(metric, catalog_graph)
            if not metric_name or metric_name == "None":
                metric_name = get_id(metric, catalog_graph)

            metric_id = get_id(metric, catalog_graph)
            metric_link = create_local_link(metric, catalog_graph)
            metric_display = metric_link if metric_link else metric_name

            rows.append(
                (
                    metric_name.lower(),
                    metric_display,
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

    for _, metric_display, metric_id, qm_id, qm_value in rows:
        table_str += f"| {metric_display}\n"
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

        access_url = _literal(catalog_graph, distribution, DCAT_ACCESS_URL)
        dist_format = _literal(catalog_graph, distribution, DCTERMS.format)
        dist_issued = _literal(catalog_graph, distribution, DCTERMS.issued, default="–")

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
    linked_series_id = ""
    linked_series_link = ""
    if linked_series is not None:
        linked_series_id = get_id(linked_series, catalog_graph)
        linked_series_link = create_local_link(linked_series, catalog_graph)

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

    linked_publishers = list(catalog_graph.objects(dataset, DCTERMS_PUBLISHER))
    linked_contact_points = list(catalog_graph.objects(dataset, VCARD_CONTACT_POINT))
    linked_licenses = list(catalog_graph.objects(dataset, DCTERMS_LICENSE))
    linked_temporal = list(catalog_graph.objects(dataset, DCTERMS_TEMPORAL))
    linked_concepts = list(catalog_graph.objects(dataset, DCAT_THEME))
    linked_distributions = list(catalog_graph.objects(dataset, DCAT_DISTRIBUTION))
    linked_policies = list(catalog_graph.objects(dataset, ODRL_HAS_POLICY))
    linked_metrics = _linked_metrics_rows(dataset, catalog_graph)

    adoc_str += "= " + dataset_name + "\n\n"

    adoc_str += "== Dataset Details\n\n"
    adoc_str += f"* **Name:** {dataset_name}\n"
    adoc_str += f"* **ID:** `{dataset_id}`\n"

    if linked_series_link:
        adoc_str += f"* **Dataset Series:** `{linked_series_id}` ({linked_series_link})\n"
    elif linked_series_id:
        adoc_str += f"* **Dataset Series:** `{linked_series_id}`\n"
    else:
        adoc_str += "* **Dataset Series:** Not available\n"

    if dataset_description and dataset_description != "None":
        adoc_str += f"* **Description:** {dataset_description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    if dataset_use_case:
        adoc_str += f"* **Use case:** {dataset_use_case}\n"
    else:
        adoc_str += "* **Use case:** Not available\n"

    adoc_str += f"* **Publishers:** {len(linked_publishers)} linked\n"
    adoc_str += f"* **Contact points:** {len(linked_contact_points)} linked\n"
    adoc_str += f"* **Licenses:** {len(linked_licenses)} linked\n"
    adoc_str += f"* **Temporal coverage:** {len(linked_temporal)} linked\n"
    adoc_str += f"* **Themes:** {len(linked_concepts)} linked\n"
    adoc_str += f"* **Policies:** {len(linked_policies)} linked\n"
    adoc_str += f"* **Metrics:** {len(linked_metrics)} available\n"
    adoc_str += f"* **Distributions:** {len(linked_distributions)} available\n"

    adoc_str += "\n"

    adoc_str += "== Description\n\n"
    if dataset_description and dataset_description != "None":
        adoc_str += dataset_description + "\n\n"
    else:
        adoc_str += "No description available.\n\n"

    adoc_str += "== Publishers\n\n"
    adoc_str += _publisher_table(dataset, catalog_graph)

    adoc_str += "== Contact Points\n\n"
    adoc_str += _contact_point_table(dataset, catalog_graph)

    adoc_str += "== Licenses\n\n"
    adoc_str += _license_table(dataset, catalog_graph)

    adoc_str += "== Temporal Coverage\n\n"
    adoc_str += _temporal_table(dataset, catalog_graph)

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
        f"|Dataset Series |{linked_series_id if linked_series_id else 'Not available'}\n"
        f"|Use case |{dataset_use_case if dataset_use_case else 'Not available'}\n"
        f"|Publishers |{len(linked_publishers)}\n"
        f"|Contact points |{len(linked_contact_points)}\n"
        f"|Licenses |{len(linked_licenses)}\n"
        f"|Temporal coverage |{len(linked_temporal)}\n"
        f"|Themes |{len(linked_concepts)}\n"
        f"|Policies |{len(linked_policies)}\n"
        f"|Metrics |{len(linked_metrics)}\n"
        f"|Distributions |{len(linked_distributions)}\n"
        f"|===\n\n"
    )

    write_file(
        adoc_str=adoc_str,
        resource=dataset,
        output_dir="modules/dataset/pages/",
        catalog_graph=catalog_graph,
    )

    return 1