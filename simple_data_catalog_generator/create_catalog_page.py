from rdflib import Graph, URIRef, RDF
from rdflib.namespace import DCTERMS, SKOS

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    create_local_link,
    get_id,
    get_prefLabel,
)

DCAT_CATALOG = URIRef("http://www.w3.org/ns/dcat#Catalog")
DCAT_DATASET = URIRef("http://www.w3.org/ns/dcat#Dataset")
DCAT_DISTRIBUTION = URIRef("http://www.w3.org/ns/dcat#Distribution")
DCAT_DATASET_SERIES = URIRef("http://www.w3.org/ns/dcat#DatasetSeries")
DCAT_DATASERVICE = URIRef("http://www.w3.org/ns/dcat#DataService")
DCAT_THEME = URIRef("http://www.w3.org/ns/dcat#theme")
DCAT_DISTRIBUTION_PRED = URIRef("http://www.w3.org/ns/dcat#distribution")
DCAT_INSERIES = URIRef("http://www.w3.org/ns/dcat#inSeries")

ODRL_POLICY = URIRef("http://www.w3.org/ns/odrl/2/Policy")
ODRL_HAS_POLICY = URIRef("http://www.w3.org/ns/odrl/2/hasPolicy")

DQV_METRIC = URIRef("http://www.w3.org/ns/dqv#Metric")
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


def _resource_label(resource: URIRef, catalog_graph: Graph) -> str:
    title = get_title(resource, catalog_graph)
    if title and title != "None":
        return title

    pref_label = get_prefLabel(resource, catalog_graph)
    if pref_label and pref_label != "None":
        return pref_label

    return get_id(resource, catalog_graph)


def _resource_link_or_label(resource: URIRef, catalog_graph: Graph) -> str:
    link = create_local_link(resource, catalog_graph)
    if link:
        return link
    return _resource_label(resource, catalog_graph)


def _entity_table(
    catalog_graph: Graph,
    rdf_type: URIRef,
    entity_label: str,
    include_description: bool = True,
) -> str:
    rows = []

    for resource in catalog_graph.subjects(RDF.type, rdf_type):
        name = _resource_label(resource, catalog_graph)
        display_name = _resource_link_or_label(resource, catalog_graph)
        identifier = get_id(resource, catalog_graph)
        description = get_description(resource, catalog_graph)

        if not description or description == "None":
            description = "Not available"

        if include_description:
            rows.append((name.lower(), display_name, identifier, description))
        else:
            rows.append((name.lower(), display_name, identifier))

    if not rows:
        return f"No {entity_label.lower()}s available.\n\n"

    rows.sort(key=lambda x: x[0])

    if include_description:
        table_str = "|===\n"
        table_str += f"| {entity_label} | ID | Description\n\n"

        for _, display_name, identifier, description in rows:
            table_str += f"| {display_name}\n"
            table_str += f"| `{identifier}`\n"
            table_str += f"| {description}\n\n"

        table_str += "|===\n\n"
        return table_str

    table_str = "|===\n"
    table_str += f"| {entity_label} | ID\n\n"

    for _, display_name, identifier in rows:
        table_str += f"| {display_name}\n"
        table_str += f"| `{identifier}`\n\n"

    table_str += "|===\n\n"
    return table_str


def _dataset_table(catalog_graph: Graph) -> str:
    rows = []

    for dataset in catalog_graph.subjects(RDF.type, DCAT_DATASET):
        dataset_name = _resource_label(dataset, catalog_graph)
        dataset_display = _resource_link_or_label(dataset, catalog_graph)
        dataset_id = get_id(dataset, catalog_graph)
        dataset_description = get_description(dataset, catalog_graph)

        if not dataset_description or dataset_description == "None":
            dataset_description = "Not available"

        distributions_count = len(list(catalog_graph.objects(dataset, DCAT_DISTRIBUTION_PRED)))
        themes_count = len(list(catalog_graph.objects(dataset, DCAT_THEME)))
        policies_count = len(list(catalog_graph.objects(dataset, ODRL_HAS_POLICY)))

        rows.append(
            (
                dataset_name.lower(),
                dataset_display,
                dataset_id,
                distributions_count,
                themes_count,
                policies_count,
                dataset_description,
            )
        )

    if not rows:
        return "No datasets available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Dataset | ID | Distributions | Themes | Policies | Description\n\n"

    for _, dataset_display, dataset_id, distributions_count, themes_count, policies_count, description in rows:
        table_str += f"| {dataset_display}\n"
        table_str += f"| `{dataset_id}`\n"
        table_str += f"| {distributions_count}\n"
        table_str += f"| {themes_count}\n"
        table_str += f"| {policies_count}\n"
        table_str += f"| {description}\n\n"

    table_str += "|===\n\n"
    return table_str


def _concept_table(catalog_graph: Graph) -> str:
    rows = []

    for concept in catalog_graph.subjects(RDF.type, SKOS.Concept):
        concept_name = get_prefLabel(concept, catalog_graph)
        if not concept_name or concept_name == "None":
            concept_name = get_title(concept, catalog_graph)
        if not concept_name or concept_name == "None":
            concept_name = get_id(concept, catalog_graph)

        concept_display = create_local_link(concept, catalog_graph) or concept_name
        concept_id = get_id(concept, catalog_graph)
        definition = str(catalog_graph.value(concept, SKOS.definition) or "").strip()

        if not definition or definition == "None":
            definition = "Not available"

        linked_dataset_ids = sorted(
            {
                get_id(dataset, catalog_graph)
                for dataset in catalog_graph.subjects(DCAT_THEME, concept)
            }
        )

        linked_count = len(linked_dataset_ids)

        rows.append(
            (
                concept_name.lower(),
                concept_display,
                concept_id,
                linked_count,
                definition,
            )
        )

    if not rows:
        return "No concepts available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Concept | ID | Linked datasets | Definition\n\n"

    for _, concept_display, concept_id, linked_count, definition in rows:
        table_str += f"| {concept_display}\n"
        table_str += f"| `{concept_id}`\n"
        table_str += f"| {linked_count}\n"
        table_str += f"| {definition}\n\n"

    table_str += "|===\n\n"
    return table_str


def _distribution_table(catalog_graph: Graph) -> str:
    rows = []

    for distribution in catalog_graph.subjects(RDF.type, DCAT_DISTRIBUTION):
        distribution_name = _resource_label(distribution, catalog_graph)
        distribution_display = _resource_link_or_label(distribution, catalog_graph)
        distribution_id = get_id(distribution, catalog_graph)

        access_url = str(
            catalog_graph.value(distribution, URIRef("http://www.w3.org/ns/dcat#accessURL")) or ""
        ).strip()
        if not access_url or access_url == "None":
            access_url = "Not available"

        fmt = str(catalog_graph.value(distribution, DCTERMS.format) or "").strip()
        if not fmt or fmt == "None":
            fmt = "Not available"

        rows.append((distribution_name.lower(), distribution_display, distribution_id, access_url, fmt))

    if not rows:
        return "No distributions available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Distribution | ID | Access URL | Format\n\n"

    for _, distribution_display, distribution_id, access_url, fmt in rows:
        if access_url != "Not available":
            access_cell = f"link:{access_url}[{access_url}]"
        else:
            access_cell = access_url

        table_str += f"| {distribution_display}\n"
        table_str += f"| `{distribution_id}`\n"
        table_str += f"| {access_cell}\n"
        table_str += f"| {fmt}\n\n"

    table_str += "|===\n\n"
    return table_str


def _metric_table(catalog_graph: Graph) -> str:
    rows = []

    for metric in catalog_graph.subjects(RDF.type, DQV_METRIC):
        metric_name = get_prefLabel(metric, catalog_graph)
        if not metric_name or metric_name == "None":
            metric_name = get_title(metric, catalog_graph)
        if not metric_name or metric_name == "None":
            metric_name = get_id(metric, catalog_graph)

        metric_display = create_local_link(metric, catalog_graph) or metric_name
        metric_id = get_id(metric, catalog_graph)
        definition = str(catalog_graph.value(metric, SKOS.definition) or "").strip()

        if not definition or definition == "None":
            definition = "Not available"

        measurement_count = len(
            list(catalog_graph.subjects(DQV_IS_MEASUREMENT_OF, metric))
        )

        rows.append((metric_name.lower(), metric_display, metric_id, measurement_count, definition))

    if not rows:
        return "No metrics available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Metric | ID | Measurements | Definition\n\n"

    for _, metric_display, metric_id, measurement_count, definition in rows:
        table_str += f"| {metric_display}\n"
        table_str += f"| `{metric_id}`\n"
        table_str += f"| {measurement_count}\n"
        table_str += f"| {definition}\n\n"

    table_str += "|===\n\n"
    return table_str


def _quality_measurement_table(catalog_graph: Graph) -> str:
    rows = []

    for measurement in catalog_graph.subjects(RDF.type, DQV_QUALITY_MEASUREMENT):
        measurement_id = get_id(measurement, catalog_graph)

        computed_on = list(catalog_graph.objects(measurement, DQV_COMPUTED_ON))
        metrics = list(catalog_graph.objects(measurement, DQV_IS_MEASUREMENT_OF))

        resource_display = "Not available"
        resource_id = "Not available"
        if computed_on:
            resource = computed_on[0]
            resource_display = _resource_link_or_label(resource, catalog_graph)
            resource_id = get_id(resource, catalog_graph)

        metric_display = "Not available"
        metric_id = "Not available"
        if metrics:
            metric = metrics[0]
            metric_display = _resource_link_or_label(metric, catalog_graph)
            metric_id = get_id(metric, catalog_graph)

        value = str(catalog_graph.value(measurement, DQV_VALUE) or "").strip()
        if not value or value == "None":
            value = "Not available"

        rows.append((measurement_id.lower(), measurement_id, resource_display, resource_id, metric_display, metric_id, value))

    if not rows:
        return "No quality measurements available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Measurement ID | Resource | Resource ID | Metric | Metric ID | Value\n\n"

    for _, measurement_id, resource_display, resource_id, metric_display, metric_id, value in rows:
        table_str += f"| `{measurement_id}`\n"
        table_str += f"| {resource_display}\n"
        table_str += f"| `{resource_id}`\n"
        table_str += f"| {metric_display}\n"
        table_str += f"| `{metric_id}`\n"
        table_str += f"| {value}\n\n"

    table_str += "|===\n\n"
    return table_str


def _series_table(catalog_graph: Graph) -> str:
    rows = []

    for series in catalog_graph.subjects(RDF.type, DCAT_DATASET_SERIES):
        series_name = _resource_label(series, catalog_graph)
        series_display = _resource_link_or_label(series, catalog_graph)
        series_id = get_id(series, catalog_graph)
        description = get_description(series, catalog_graph)

        if not description or description == "None":
            description = "Not available"

        dataset_count = len(list(catalog_graph.subjects(DCAT_INSERIES, series)))

        rows.append((series_name.lower(), series_display, series_id, dataset_count, description))

    if not rows:
        return "No dataset series available.\n\n"

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Series | ID | Datasets | Description\n\n"

    for _, series_display, series_id, dataset_count, description in rows:
        table_str += f"| {series_display}\n"
        table_str += f"| `{series_id}`\n"
        table_str += f"| {dataset_count}\n"
        table_str += f"| {description}\n\n"

    table_str += "|===\n\n"
    return table_str


def _policy_table(catalog_graph: Graph) -> str:
    return _entity_table(
        catalog_graph=catalog_graph,
        rdf_type=ODRL_POLICY,
        entity_label="Policy",
        include_description=True,
    )


def _dataservice_table(catalog_graph: Graph) -> str:
    return _entity_table(
        catalog_graph=catalog_graph,
        rdf_type=DCAT_DATASERVICE,
        entity_label="Data service",
        include_description=True,
    )


def _count_resources(catalog_graph: Graph, rdf_type: URIRef) -> int:
    return len(list(catalog_graph.subjects(RDF.type, rdf_type)))


def create_catalog_page(catalog_graph: Graph):
    catalogs = list(catalog_graph.subjects(RDF.type, DCAT_CATALOG))

    if not catalogs:
        raise ValueError("No resource found with rdf:type dcat:Catalog")

    catalog = catalogs[0]

    catalog_name = get_title(catalog, catalog_graph)
    catalog_id = get_id(catalog, catalog_graph)
    catalog_description = get_description(catalog, catalog_graph)

    adoc_str = ""

    adoc_str += f"= {catalog_name}\n\n"

    adoc_str += "== Catalog Details\n\n"
    adoc_str += f"* **Name:** {catalog_name}\n"
    adoc_str += f"* **ID:** `{catalog_id}`\n"

    if catalog_description and catalog_description != "None":
        adoc_str += f"* **Description:** {catalog_description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    adoc_str += "\n"

    adoc_str += "== Summary\n\n"
    adoc_str += "|===\n"
    adoc_str += "| Entity type | Count\n\n"
    adoc_str += f"| Datasets | {_count_resources(catalog_graph, DCAT_DATASET)}\n"
    adoc_str += f"| Dataset series | {_count_resources(catalog_graph, DCAT_DATASET_SERIES)}\n"
    adoc_str += f"| Distributions | {_count_resources(catalog_graph, DCAT_DISTRIBUTION)}\n"
    adoc_str += f"| Concepts | {_count_resources(catalog_graph, SKOS.Concept)}\n"
    adoc_str += f"| Policies | {_count_resources(catalog_graph, ODRL_POLICY)}\n"
    adoc_str += f"| Metrics | {_count_resources(catalog_graph, DQV_METRIC)}\n"
    adoc_str += f"| Quality measurements | {_count_resources(catalog_graph, DQV_QUALITY_MEASUREMENT)}\n"
    adoc_str += f"| Data services | {_count_resources(catalog_graph, DCAT_DATASERVICE)}\n"
    adoc_str += "|===\n\n"

    adoc_str += "== Datasets\n\n"
    adoc_str += _dataset_table(catalog_graph)

    adoc_str += "== Dataset Series\n\n"
    adoc_str += _series_table(catalog_graph)

    adoc_str += "== Distributions\n\n"
    adoc_str += _distribution_table(catalog_graph)

    adoc_str += "== Concepts\n\n"
    adoc_str += _concept_table(catalog_graph)

    adoc_str += "== Policies\n\n"
    adoc_str += _policy_table(catalog_graph)

    adoc_str += "== Metrics\n\n"
    adoc_str += _metric_table(catalog_graph)

    adoc_str += "== Quality Measurements\n\n"
    adoc_str += _quality_measurement_table(catalog_graph)

    adoc_str += "== Data Services\n\n"
    adoc_str += _dataservice_table(catalog_graph)

    write_file(
        adoc_str=adoc_str,
        resource=catalog,
        output_dir="modules/data-catalog/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
