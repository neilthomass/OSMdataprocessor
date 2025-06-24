import requests
from parser import parse_osm_xml
from database import DatabaseManager

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Bounding box for California
BBOX = (32.5343, -124.4096, 42.0095, -114.1315)

QUERY_TEMPLATE = """
[out:xml][timeout:3600];
way["highway"~"motorway|trunk"]({south},{west},{north},{east});
(._;>;);
out body;
"""

def fetch_freeways():
    query = QUERY_TEMPLATE.format(
        south=BBOX[0], west=BBOX[1], north=BBOX[2], east=BBOX[3]
    )
    response = requests.post(OVERPASS_URL, data={"data": query})
    response.raise_for_status()
    return response.text


def main():
    db = DatabaseManager()
    db.init_db()
    xml_data = fetch_freeways()
    nodes, ways, way_nodes = parse_osm_xml(xml_data)
    db.store_osm_data(nodes, ways, way_nodes)
    print(f"Stored {len(ways)} ways and {len(nodes)} nodes")


if __name__ == "__main__":
    main()

