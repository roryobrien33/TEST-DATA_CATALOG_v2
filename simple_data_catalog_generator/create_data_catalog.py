from rdflib import Graph, URIRef, RDF
from rdflib.namespace import SKOS

from simple_data_catalog_generator.page_creation_functions import create_nav_header

from simple_data_catalog_generator.create_catalog_page import create_catalog_page
from simple_data_catalog_generator.create_series_page import create_series_page
from simple_data_catalog_generator.create_dataservice_page import create_dataservice_page
from simple_data_catalog_generator.create_dataset_page import create_dataset_page
from simple_data_catalog_generator.create_concept_page import create_concept_page
from simple_data_catalog_generator.create_metric_page import create_metric_page
from simple_data_catalog_generator.create_policy_page import create_policy_page

from simple_data_catalog_generator.create_agent_page import create_agent_page
from simple_data_catalog_generator.create_kind_page import create_kind_page
from simple_data_catalog_generator.create_license_page import create_license_page
from simple_data_catalog_generator.create_period_page import create_period_page


DCAT_DATASET = URIRef("http://www.w3.org/ns/dcat#Dataset")
DCAT_DATASET_SERIES = URIRef("http://www.w3.org/ns/dcat#DatasetSeries")
DCAT_DATASERVICE = URIRef("http://www.w3.org/ns/dcat#DataService")

DQV_METRIC = URIRef("http://www.w3.org/ns/dqv#Metric")

ODRL_POLICY = URIRef("http://www.w3.org/ns/odrl/2/Policy")

FOAF_AGENT = URIRef("http://xmlns.com/foaf/0.1/Agent")
VCARD_KIND = URIRef("http://www.w3.org/2006/vcard/ns#Kind")

DCTERMS_LICENSE_DOCUMENT = URIRef("http://purl.org/dc/terms/LicenseDocument")
DCTERMS_PERIOD_OF_TIME = URIRef("http://purl.org/dc/terms/PeriodOfTime")


def create_data_catalog(catalog_graph: Graph):
    create_catalog_page(catalog_graph=catalog_graph)

    create_nav_header(page_type="Dataset Series")
    for series in catalog_graph.subjects(RDF.type, DCAT_DATASET_SERIES):
        create_series_page(series=series, catalog_graph=catalog_graph)

    create_nav_header(page_type="Data Services")
    for dataservice in catalog_graph.subjects(RDF.type, DCAT_DATASERVICE):
        create_dataservice_page(dataservice=dataservice, catalog_graph=catalog_graph)

    create_nav_header(page_type="Datasets")
    for dataset in catalog_graph.subjects(RDF.type, DCAT_DATASET):
        create_dataset_page(dataset=dataset, catalog_graph=catalog_graph)

    create_nav_header(page_type="Concepts")
    for concept in catalog_graph.subjects(RDF.type, SKOS.Concept):
        create_concept_page(concept=concept, catalog_graph=catalog_graph)

    create_nav_header(page_type="Metrics")
    for metric in catalog_graph.subjects(RDF.type, DQV_METRIC):
        create_metric_page(metric=metric, catalog_graph=catalog_graph)

    create_nav_header(page_type="Policies")
    for policy in catalog_graph.subjects(RDF.type, ODRL_POLICY):
        create_policy_page(policy=policy, catalog_graph=catalog_graph)

    create_nav_header(page_type="Agents")
    for agent in catalog_graph.subjects(RDF.type, FOAF_AGENT):
        create_agent_page(agent=agent, catalog_graph=catalog_graph)

    create_nav_header(page_type="Contact Points")
    for kind in catalog_graph.subjects(RDF.type, VCARD_KIND):
        create_kind_page(kind=kind, catalog_graph=catalog_graph)

    create_nav_header(page_type="Licenses")
    for license_resource in catalog_graph.subjects(RDF.type, DCTERMS_LICENSE_DOCUMENT):
        create_license_page(license_resource=license_resource, catalog_graph=catalog_graph)

    create_nav_header(page_type="Periods")
    for period in catalog_graph.subjects(RDF.type, DCTERMS_PERIOD_OF_TIME):
        create_period_page(period=period, catalog_graph=catalog_graph)

    return 1
