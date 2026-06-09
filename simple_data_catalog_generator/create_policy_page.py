from pathlib import Path
import yaml

from rdflib import Graph, URIRef, RDF
from rdflib.namespace import DCTERMS
from rdflib import Namespace

from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_id,
    get_title,
    get_description,
)

ODRL = Namespace("http://www.w3.org/ns/odrl/2/")


def _load_source_policy_yaml(policy: URIRef, catalog_graph: Graph):
    """
    Load the source policy YAML file corresponding to this policy.
    """
    policy_id = get_id(policy, catalog_graph)

    candidate_names = [policy_id]
    if ":" in policy_id:
        candidate_names.append(policy_id.split(":", 1)[1])
    if "/" in policy_id:
        candidate_names.append(policy_id.rstrip("/").split("/")[-1])
    if "#" in policy_id:
        candidate_names.append(policy_id.split("#")[-1])

    seen = set()
    candidate_names = [x for x in candidate_names if not (x in seen or seen.add(x))]

    for name in candidate_names:
        for ext in (".yaml", ".yml"):
            p = Path(f"data-catalog/policies/{name}{ext}")
            if p.exists():
                return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    return {}


def create_policy_page(policy: URIRef, catalog_graph: Graph):
    adoc_str = str()

    source_doc = _load_source_policy_yaml(policy, catalog_graph)
    source_policy = source_doc.get("policy", {}) or {}

    policy_id = get_id(policy, catalog_graph)

    policy_title = get_title(policy, catalog_graph)
    if not policy_title or policy_title == "None":
        policy_title = str(source_policy.get("title", "")).strip()
    if not policy_title or policy_title == "None":
        policy_title = policy_id

    policy_description = get_description(policy, catalog_graph)
    if not policy_description or policy_description == "None":
        policy_description = str(source_policy.get("description", "")).strip()

    # Title
    adoc_str += "= " + policy_title + "\n\n"

    # Policy details
    adoc_str += "== Policy Details\n\n"
    adoc_str += f"* **Title:** {policy_title}\n"
    adoc_str += f"* **ID:** `{policy_id}`\n"

    if policy_description and policy_description != "None":
        adoc_str += f"* **Description:** {policy_description}\n"
    else:
        adoc_str += "* **Description:** Not available\n"

    adoc_str += "\n"

    # Placeholder linkage section
    adoc_str += "== Linked datasets\n\n"
    adoc_str += "Policy linkage will be shown once policies are explicitly linked to datasets.\n\n"

    write_file(
        adoc_str=adoc_str,
        resource=policy,
        output_dir="modules/policy/pages/",
        catalog_graph=catalog_graph,
    )

    return 1
