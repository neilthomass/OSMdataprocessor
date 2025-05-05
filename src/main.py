import requests
from parser import parse_osm_xml, extract_way_ids_from_relation
from database import DatabaseManager
import time
from typing import List
import os

def fetch_osm_way(way_id: int) -> str:
    url = f"https://api.openstreetmap.org/api/0.6/way/{way_id}/full"
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def process_way_ids(way_ids: List[int], db_manager: DatabaseManager):
    total = len(way_ids)
    for i, way_id in enumerate(way_ids, 1):
        try:
            print(f"Processing way {way_id} ({i}/{total})...")
            xml_data = fetch_osm_way(way_id)
            nodes, ways, way_nodes = parse_osm_xml(xml_data)
            db_manager.store_osm_data(nodes, ways, way_nodes)
            print(f"Successfully processed way {way_id}")
            time.sleep(1)  # Be nice to the OSM API
        except Exception as e:
            print(f"Error processing way {way_id}: {str(e)}")

def main():
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    # Read and parse the relation XML file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(os.path.dirname(script_dir), '156071.xml')
    
    with open(xml_path, 'r') as f:
        relation_xml = f.read()
    
    # Extract way IDs from the relation
    way_ids = extract_way_ids_from_relation(relation_xml)
    print(f"Found {len(way_ids)} ways to process")
    
    # Process all way IDs
    process_way_ids(way_ids, db_manager)
    
    # Example query
    lat, lon = 37.3981366, -121.8752114  # Example coordinates
    result = db_manager.get_nearest_way(lat, lon)
    if result:
        print(f"\nNearest way found:")
        print(f"Way ID: {result.way_id}")
        print(f"Lanes: {result.lanes}")
        print(f"Highway Type: {result.highway_type}")
        print(f"Name: {result.name}")
        print(f"Max Speed: {result.maxspeed}")
        print(f"Distance: {result.distance} degrees")

if __name__ == "__main__":
    main() 