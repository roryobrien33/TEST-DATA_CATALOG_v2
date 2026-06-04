from rdflib import Graph, URIRef, RDF
from rdflib.namespace import DCAT, DCTERMS

from simple_data_catalog_generator.create_metadata_table import create_metadata_table
from simple_data_catalog_generator.analysis_functions import create_theme_word_cloud
from simple_data_catalog_generator.page_creation_functions import (
    write_file,
    get_title,
    get_description,
    add_to_nav,
    get_id,
    create_local_link,
)
import os
import re


def _first_literal(graph: Graph, subject: URIRef, predicates):
    """
    Return the first non-empty value found for the given subject
    across the supplied predicate list.
    """
    for pred in predicates:
        val = graph.value(subject, pred)
        if val is not None and str(val).strip() and str(val).strip() != "None":
            return str(val).strip()
    return ""


def _build_dataset_table(catalog_graph: Graph, catalog: URIRef) -> str:
    """
    Build an AsciiDoc table listing datasets in the catalog.

    Columns:
    - Name
    - ID
    - Use Case
    - Description
    """
    dataset_rows = []

    # The catalog links to datasets via dcat:dataset
    for dataset in catalog_graph.objects(catalog, DCAT.dataset):
        dataset_name = get_title(dataset, catalog_graph)
        dataset_id = get_id(dataset, catalog_graph)
        dataset_description = get_description(dataset, catalog_graph)

        # Use case is not formally in the current schema,
        # but try likely predicates in case it exists in the graph.
        dataset_use_case = _first_literal(
            catalog_graph,
            dataset,
            [
                URIRef("https://www.uuidea.eu/profiles/data-catalog/use_case"),
                URIRef("https://www.uuidea.eu/profiles/data-catalog/useCase"),
            ],
        )

        # Make the dataset name clickable to its dataset page
        dataset_link = create_local_link(dataset, catalog_graph)
        dataset_name_display = dataset_link if dataset_link else dataset_name

        if not dataset_description or dataset_description == "None":
            dataset_description = "Not available"

        if not dataset_use_case:
            dataset_use_case = "Not available"

        dataset_rows.append(
            (
                dataset_name_display,
                dataset_id,
                dataset_use_case,
                dataset_description,
            )
        )

    if not dataset_rows:
        return "No datasets available.\n\n"

    table_str = '|===\n'
    table_str += '| Name | ID | Use Case | Description\n\n'

    for name, ds_id, use_case, description in dataset_rows:
        table_str += f'| {name}\n'
        table_str += f'| `{ds_id}`\n'
        table_str += f'| {use_case}\n'
        table_str += f'| {description}\n\n'

    table_str += '|===\n\n'
    return table_str


def create_catalog_page(catalog_graph: Graph, output_dir: str = 'modules/data-catalog/pages/'):
    adoc_str = str()

    catalog = None
    for datacat in catalog_graph.subjects(RDF.type, DCAT.Catalog):
        catalog = datacat

    if catalog is None:
        raise ValueError("No resource found with rdf:type dcat:Catalog")

    # ---------------------------
    # Title
    # ---------------------------
    adoc_str += "= " + get_title(catalog, catalog_graph) + "\n\n"

    # ---------------------------
    # Description
    # ---------------------------
    adoc_str += "== Description\n\n" + get_description(catalog, catalog_graph) + "\n\n"

    # ---------------------------
    # Machine-readable link
    # ---------------------------
    adoc_str += (
        "A machine readable version of this data catalog can be found here: "
        "xref:attachment$data-catalog.ttl[data-catalog.ttl]\n\n"
    )

    # ---------------------------
    # Overview
    # ---------------------------
    adoc_str += "== Overview\n\n"
    adoc_str += create_metadata_table(
        catalog_graph=catalog_graph,
        resource=catalog
    ) + "\n\n"

    # ---------------------------
    # Datasets table (NEW)
    # ---------------------------
    adoc_str += "== Datasets\n\n"
    adoc_str += _build_dataset_table(catalog_graph=catalog_graph, catalog=catalog)

    # ---------------------------
    # Datasets by Theme
    # ---------------------------
    adoc_str += "== Datasets by Theme\n\n"

    create_theme_word_cloud(
        catalog_graph=catalog_graph,
        output_dir='modules/data-catalog/images/'
    )
    adoc_str += "image:wordcloud.svg[Theme Word Cloud]\n\n"

    # ---------------------------
    # Write file
    # ---------------------------
    write_file(
        adoc_str=adoc_str,
        resource=catalog,
        output_dir=output_dir,
        catalog_graph=catalog_graph
    )


if __name__ == "__main__":
    catalog_graph = Graph()
    catalog_graph.parse('data-catalog/data-catalog.ttl')
    create_catalog_page(catalog_graph=catalog_graph)
