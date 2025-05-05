import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple, Dict, Any

def parse_timestamp(timestamp_str: str) -> datetime:
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")

def extract_way_ids_from_relation(xml_data: str) -> List[int]:
    root = ET.fromstring(xml_data)
    way_ids = []
    
    # Find all member elements with type="way"
    for member in root.findall(".//member[@type='way']"):
        way_id = int(member.get('ref'))
        way_ids.append(way_id)
    
    return way_ids

def parse_osm_xml(xml_data: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    root = ET.fromstring(xml_data)
    
    nodes = []
    ways = []
    way_nodes = []
    
    for elem in root:
        if elem.tag == 'node':
            node = {
                'node_id': int(elem.get('id')),
                'lat': float(elem.get('lat')),
                'lon': float(elem.get('lon')),
                'version': int(elem.get('version')),
                'timestamp': parse_timestamp(elem.get('timestamp'))
            }
            nodes.append(node)
            
        elif elem.tag == 'way':
            way_id = int(elem.get('id'))
            way_data = {
                'way_id': way_id,
                'lanes': None,
                'highway_type': None,
                'name': None,
                'maxspeed': None,
                'version': int(elem.get('version')),
                'timestamp': parse_timestamp(elem.get('timestamp'))
            }
            
            # Get way attributes
            for tag in elem.findall('tag'):
                key = tag.get('k')
                value = tag.get('v')
                if key == 'lanes':
                    way_data['lanes'] = int(value)
                elif key == 'highway':
                    way_data['highway_type'] = value
                elif key == 'name':
                    way_data['name'] = value
                elif key == 'maxspeed':
                    way_data['maxspeed'] = value
            
            ways.append(way_data)
            
            # Get node sequence
            for i, nd in enumerate(elem.findall('nd')):
                way_nodes.append({
                    'way_id': way_id,
                    'node_id': int(nd.get('ref')),
                    'sequence': i
                })
    
    return nodes, ways, way_nodes 