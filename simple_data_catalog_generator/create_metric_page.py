from pathlib import Path
import yaml

from rdflib import Graph, URIRef, RDF
from rdflib.namespace import DCTERMS, DCAT
from rdflib import Namespace

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_id,
    create_local_link,
)

DQV = Namespace("http://www.w3.org/ns/dqv#")


def _load_source_metric_yaml(metric: URIRef, catalog_graph: Graph):
    metric_id = get_id(metric, catalog_graph)

    candidate_names = [metric_id]
    if ":" in metric_id:
        candidate_names.append(metric_id.split(":", 1)[1])
    if "/" in metric_id:
        candidate_names.append(metric_id.rstrip("/").split("/")[-1])
    if "#" in metric_id:
        candidate_names.append(metric_id.split("#")[-1])

    seen = set()
    candidate_names = [x for x in candidate_names if not (x in seen or seen.add(x))]

    for name in candidate_names:
        for ext in (".yaml", ".yml"):
            p = Path(f"data-catalog/metrics/{name}{ext}")
            if p.exists():
                return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    return {}


def create_metric_page(metric: URIRef, catalog_graph: Graph):
    adoc_str = str()

    source_doc = _load_source_metric_yaml(metric, catalog_graph)
    source_metric = source_doc.get("metric", {}) or {}

    metric_id = get_id(metric, catalog_graph)
    metric_name = str(catalog_graph.value(metric, DCTERMS.title) or "").strip()
    if not metric_name:
        metric_name = str(catalog_graph.value(metric, Namespace("http://www.w3.org/2004/02/skos/core#").prefLabel) or "").strip()
    if not metric_name:
        metric_name = metric_id

    metric_definition = str(
        catalog_graph.value(metric, Namespace("http://www.w3.org/2004/02/skos/core#").definition) or ""
    ).strip()

    expected_data_type = str(source_metric.get("expectedDataType", "")).strip()
    in_dimension = str(source_metric.get("inDimension", "")).strip()

    adoc_str += "= " + metric_name + "\n\n"

    adoc_str += "== Metric Details\n\n"
    adoc_str += f"* **Name:** {metric_name}\n"
    adoc_str += f"* **ID:** `{metric_id}`\n"

    if metric_definition:
        adoc_str += f"* **Definition:** {metric_definition}\n"
    else:
        adoc_str += "* **Definition:** Not available\n"

    if expected_data_type:
        adoc_str += f"* **Expected data type:** {expected_data_type}\n"
    else:
        adoc_str += "* **Expected data type:** Not available\n"

    if in_dimension:
        adoc_str += f"* **Metric dimension:** {in_dimension}\n"
    else:
        adoc_str += "* **Metric dimension:** Not available\n"

    adoc_str += "\n"

    adoc_str += "== Linked datasets\n\n"
    adoc_str += "Metric linkage will be shown through data quality measurements.\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=metric,
        output_dir="modules/metric/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
