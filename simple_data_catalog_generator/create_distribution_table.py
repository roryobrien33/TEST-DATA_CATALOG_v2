from rdflib import Graph, URIRef, DCAT
from simple_data_catalog_generator.page_creation_functions import get_id


def create_distribution_table(dataset: URIRef, catalog_graph: Graph) -> str:
    """
    Render graph-backed distributions if present.
    Fallback text if no RDF distributions are available.
    """
    distributions = list(catalog_graph.objects(dataset, DCAT.distribution))

    if not distributions:
        return "No distributions available.\n\n"

    rows = []

    for dist in distributions:
        format_value = ""
        access_url = ""
        issued = ""

        for fmt in catalog_graph.objects(dist, DCAT.mediaType):
            format_value = str(fmt).strip()
            if format_value:
                break

        for url in catalog_graph.objects(dist, DCAT.accessURL):
            access_url = str(url).strip()
            if access_url:
                break

        for dt in catalog_graph.objects(dist, DCAT.releaseDate):
            issued = str(dt).strip()
            if issued:
                break

        if not format_value:
            format_value = "Not available"
        if not access_url:
            access_url = "Not available"
        if not issued:
            issued = "–"

        rows.append((format_value.lower(), format_value, access_url, issued))

    rows.sort(key=lambda x: x[0])

    table_str = "|===\n"
    table_str += "| Format | Access URL | Issued\n\n"

    for _, fmt, access_url, issued in rows:
        if access_url != "Not available":
            access_cell = f"link:{access_url}[{access_url}]"
        else:
            access_cell = access_url

        table_str += f"| {fmt}\n"
        table_str += f"| {access_cell}\n"
        table_str += f"| {issued}\n\n"

    table_str += "|===\n\n"
    return table_str
