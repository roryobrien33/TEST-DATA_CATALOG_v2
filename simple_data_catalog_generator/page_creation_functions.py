import os
import re
from pathlib import Path

import yaml
from rdflib import Graph, URIRef, RDF, DCAT, DCTERMS, SKOS, Namespace

DQV = Namespace("http://www.w3.org/ns/dqv#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
ODRL = Namespace("http://www.w3.org/ns/odrl/2/")

DCAT_CATALOG = URIRef("http://www.w3.org/ns/dcat#Catalog")
DCAT_DATASET = URIRef("http://www.w3.org/ns/dcat#Dataset")
DCAT_DISTRIBUTION = URIRef("http://www.w3.org/ns/dcat#Distribution")
DCAT_DATASET_SERIES = URIRef("http://www.w3.org/ns/dcat#DatasetSeries")
DCAT_DATASERVICE = URIRef("http://www.w3.org/ns/dcat#DataService")
DQV_METRIC = URIRef("http://www.w3.org/ns/dqv#Metric")
DQV_QUALITY_MEASUREMENT = URIRef("http://www.w3.org/ns/dqv#QualityMeasurement")
ODRL_POLICY = URIRef("http://www.w3.org/ns/odrl/2/Policy")


def _sanitize_page_id(value: str) -> str:
    """
    Convert a display ID / CURIE / IRI into a filesystem/xref-safe page ID.
    """
    s = (value or "").strip()

    if ":" in s and not s.startswith("http://") and not s.startswith("https://"):
        s = s.split(":", 1)[1]

    if "#" in s:
        s = s.split("#")[-1]
    if "/" in s:
        s = s.rstrip("/").split("/")[-1]

    s = re.sub(r"[^A-Za-z0-9._-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _identifier_from_source_yaml(resource: URIRef, entity_dir: str, yaml_key: str, id_field: str) -> str:
    """
    Generic fallback for identifiers when dcterms:identifier is not present in the RDF graph.
    """
    resource_str = str(resource)
    candidate_names = []

    if "#" in resource_str:
        candidate_names.append(resource_str.split("#")[-1])
    if "/" in resource_str:
        candidate_names.append(resource_str.rstrip("/").split("/")[-1])

    expanded = []
    for name in candidate_names:
        expanded.append(name)

        if name.startswith("data-catalog"):
            expanded.append(name.replace("data-catalog", "", 1).lstrip("-_/"))

        if "catalog-" in name:
            expanded.append(name[name.find("catalog-"):])

        if "concept-" in name:
            expanded.append(name[name.find("concept-"):])

        if "metric-" in name:
            expanded.append(name[name.find("metric-"):])

        if "qm-" in name:
            expanded.append(name[name.find("qm-"):])

        if "quality-measurement-" in name:
            expanded.append(name[name.find("quality-measurement-"):])

        if "policy-" in name:
            expanded.append(name[name.find("policy-"):])

        if "distribution-" in name:
            expanded.append(name[name.find("distribution-"):])

        if "dataset-" in name:
            expanded.append(name[name.find("dataset-"):])

        if "series-" in name:
            expanded.append(name[name.find("series-"):])

        if "dataservice-" in name:
            expanded.append(name[name.find("dataservice-"):])

        if "data-service-" in name:
            expanded.append(name[name.find("data-service-"):])

    seen = set()
    final_candidates = []
    for c in expanded:
        c = str(c).strip()
        if c and c not in seen:
            seen.add(c)
            final_candidates.append(c)

    for name in final_candidates:
        for ext in (".yaml", ".yml"):
            path = Path(f"data-catalog/{entity_dir}/{name}{ext}")
            if path.exists():
                doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                entity = doc.get(yaml_key, {}) or {}
                identifier = str(entity.get(id_field, "")).strip()
                if identifier:
                    return identifier

    return ""


def _catalog_identifier_from_source_yaml() -> str:
    path = Path("data-catalog/catalog.yaml")
    if not path.exists():
        return ""

    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if "catalog" in doc:
        catalog = doc.get("catalog", {}) or {}
    elif "dataCatalog" in doc:
        catalog = doc.get("dataCatalog", {}) or {}
    else:
        catalog = {}

    identifier = str(catalog.get("identifier") or catalog.get("id") or catalog.get("uid") or "").strip()
    return identifier


def _concept_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="concepts",
        yaml_key="concept",
        id_field="identifier",
    )


def _metric_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="metrics",
        yaml_key="metric",
        id_field="identifier",
    )


def _quality_measurement_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="quality-measurements",
        yaml_key="qualityMeasurement",
        id_field="identifier",
    )


def _policy_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="policies",
        yaml_key="policy",
        id_field="identifier",
    )


def _distribution_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="distributions",
        yaml_key="distribution",
        id_field="identifier",
    )


def _dataset_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="datasets",
        yaml_key="dataset",
        id_field="identifier",
    )


def _series_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="dataset-series",
        yaml_key="datasetSeries",
        id_field="identifier",
    )


def _dataservice_identifier_from_source_yaml(resource: URIRef) -> str:
    return _identifier_from_source_yaml(
        resource=resource,
        entity_dir="data-services",
        yaml_key="dataService",
        id_field="identifier",
    )


def create_local_link(resource: URIRef, catalog_graph: Graph) -> str:
    page_id = get_page_id(resource=resource, catalog_graph=catalog_graph)
    rdf_type = catalog_graph.value(subject=resource, predicate=RDF.type)

    if rdf_type == DCAT_DATASET:
        title = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:dataset:{page_id}.adoc[{title}]"

    elif rdf_type == SKOS.Concept:
        pref_label = get_prefLabel(subject=resource, graph=catalog_graph)
        local_link = f"xref:concept:{page_id}.adoc[{pref_label}]"

    elif rdf_type == DQV_METRIC:
        pref_label = get_prefLabel(subject=resource, graph=catalog_graph)
        if not pref_label or pref_label == "None":
            pref_label = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:metric:{page_id}.adoc[{pref_label}]"

    elif rdf_type == DCAT_DATASERVICE:
        title = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:dataservice:{page_id}.adoc[{title}]"

    elif rdf_type == DCAT_DATASET_SERIES:
        title = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:dataset-series:{page_id}.adoc[{title}]"

    elif rdf_type == DCAT_CATALOG:
        title = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:data-catalog:{page_id}.adoc[{title}]"

    elif rdf_type == ODRL_POLICY:
        title = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:policy:{page_id}.adoc[{title}]"

    elif rdf_type == DCAT_DISTRIBUTION:
        title = get_title(subject=resource, graph=catalog_graph)
        local_link = f"xref:distribution:{page_id}.adoc[{title}]"

    else:
        local_link = ""

    return local_link


def write_file(adoc_str: str, resource: URIRef, output_dir: str, catalog_graph: Graph) -> None:
    file_name = get_page_id(resource=resource, catalog_graph=catalog_graph)
    output_path = os.path.join(output_dir, file_name + ".adoc")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(adoc_str)

    add_to_nav(
        output_dir=output_dir,
        file_name=file_name,
        resource=resource,
        catalog_graph=catalog_graph,
    )


def get_prefLabel(subject: URIRef, graph: Graph) -> str:
    pref_label = str(graph.value(subject, SKOS.prefLabel))
    return pref_label


def get_altLabel(subject: URIRef, graph: Graph) -> str:
    alt_label = str(graph.value(subject, SKOS.altLabel))
    return alt_label


def get_definition(subject: URIRef, graph: Graph) -> str:
    definition = str(graph.value(subject, SKOS.definition))
    return definition


def get_title(subject: URIRef, graph: Graph) -> str:
    title = graph.value(subject, DCTERMS.title)
    title_str = str(title)

    if title_str == "None" or not title_str.strip():
        pref_label = str(graph.value(subject, SKOS.prefLabel))
        if pref_label != "None" and pref_label.strip():
            return pref_label.strip()

        subject_str = str(subject)
        if "#" in subject_str:
            title_str = subject_str.split("#")[1]
        elif "/" in subject_str:
            title_str = subject_str.rstrip("/").split("/")[-1]
        else:
            title_str = re.sub(r".*?\/", "/", subject_str).replace("/", "")

    return title_str


def get_status(subject: URIRef, graph: Graph) -> str:
    title = graph.value(subject, ADMS.status)
    title_str = str(title)
    return title_str


def get_description(subject: URIRef, graph: Graph) -> str:
    description = graph.value(subject, DCTERMS.description)
    description_str = str(description)
    return description_str


def get_id(resource: URIRef, catalog_graph: Graph) -> str:
    """
    Display identifier.

    Priority:
    1. dcterms:identifier from RDF graph
    2. source YAML fallback for entity types
    3. URI-derived fallback
    """
    identifier = str(catalog_graph.value(URIRef(resource), DCTERMS.identifier))
    if identifier != "None" and identifier.strip():
        return identifier.strip()

    rdf_type = catalog_graph.value(subject=resource, predicate=RDF.type)

    if rdf_type == DCAT_CATALOG:
        catalog_identifier = _catalog_identifier_from_source_yaml()
        if catalog_identifier:
            return catalog_identifier

    if rdf_type == SKOS.Concept:
        concept_identifier = _concept_identifier_from_source_yaml(resource)
        if concept_identifier:
            return concept_identifier

    if rdf_type == DQV_METRIC:
        metric_identifier = _metric_identifier_from_source_yaml(resource)
        if metric_identifier:
            return metric_identifier

    if rdf_type == DQV_QUALITY_MEASUREMENT:
        qm_identifier = _quality_measurement_identifier_from_source_yaml(resource)
        if qm_identifier:
            return qm_identifier

    if rdf_type == ODRL_POLICY:
        policy_identifier = _policy_identifier_from_source_yaml(resource)
        if policy_identifier:
            return policy_identifier

    if rdf_type == DCAT_DISTRIBUTION:
        distribution_identifier = _distribution_identifier_from_source_yaml(resource)
        if distribution_identifier:
            return distribution_identifier

    if rdf_type == DCAT_DATASET:
        dataset_identifier = _dataset_identifier_from_source_yaml(resource)
        if dataset_identifier:
            return dataset_identifier

    if rdf_type == DCAT_DATASET_SERIES:
        series_identifier = _series_identifier_from_source_yaml(resource)
        if series_identifier:
            return series_identifier

    if rdf_type == DCAT_DATASERVICE:
        dataservice_identifier = _dataservice_identifier_from_source_yaml(resource)
        if dataservice_identifier:
            return dataservice_identifier

    resource_str = str(resource)

    if "#" in resource_str:
        identifier = resource_str.split("#")[1]
    elif "/" in resource_str:
        identifier = resource_str.rstrip("/").split("/")[-1]
    else:
        identifier = re.sub(r".*?\/", "/", resource_str).replace("/", "")

    return identifier


def get_page_id(resource: URIRef, catalog_graph: Graph) -> str:
    """
    Safe file/xref target id. This should be used for filenames and xrefs.
    """
    display_id = get_id(resource=resource, catalog_graph=catalog_graph)
    return _sanitize_page_id(display_id)


def add_to_nav(file_name: str, output_dir: str, resource: URIRef, catalog_graph: Graph):
    name = create_local_link(resource=resource, catalog_graph=catalog_graph) + "\n\n"

    if output_dir == "modules/data-catalog/pages/":
        nav_entry = f"* {name}"
    else:
        nav_entry = f"*** {name}"

    nav_file_path = "modules/data-catalog/nav.adoc"

    try:
        with open(nav_file_path, "a", encoding="utf-8") as f:
            f.write(nav_entry)
    except FileNotFoundError:
        pass


def create_nav_header(page_type: str):
    nav_file_path = "modules/data-catalog/nav.adoc"
    nav_header = f"** {page_type} \n\n"

    with open(nav_file_path, "a", encoding="utf-8") as f:
        f.write(nav_header)