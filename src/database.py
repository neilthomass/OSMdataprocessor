from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from typing import List, Dict, Any, Optional, Tuple
import os
from dotenv import load_dotenv
from models import Base, Node, Way, WayNode, UserData

load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Use system username instead of 'postgres'
        database_url = os.getenv('DATABASE_URL', f'postgresql://{os.getenv("USER")}@localhost:5432/osm_data')
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        Base.metadata.create_all(self.engine)
        
    def store_osm_data(self, nodes: List[Dict[str, Any]], ways: List[Dict[str, Any]], way_nodes: List[Dict[str, Any]]):
        session = self.Session()
        try:
            # Store nodes
            for node_data in nodes:
                stmt = insert(Node).values(**node_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['node_id'],
                    set_=node_data
                )
                session.execute(stmt)
            
            # Store ways
            for way_data in ways:
                stmt = insert(Way).values(**way_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['way_id'],
                    set_=way_data
                )
                session.execute(stmt)
            
            # Store way_nodes
            for way_node_data in way_nodes:
                stmt = insert(WayNode).values(**way_node_data)
                stmt = stmt.on_conflict_do_nothing()
                session.execute(stmt)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_nearest_way(self, lat: float, lon: float, max_distance: float = 0.001):
        session = self.Session()
        try:
            query = text("""
            SELECT w.way_id, w.lanes, w.lanes_forward, w.lanes_backward,
                   w.highway_type, w.name, w.maxspeed,
                   ST_Distance(n.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) as distance
            FROM ways w
            JOIN way_nodes wn ON w.way_id = wn.way_id
            JOIN nodes n ON wn.node_id = n.node_id
            WHERE ST_DWithin(
                n.geom,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                :max_distance
            )
            ORDER BY distance
            LIMIT 1
            """)
            
            result = session.execute(query, {
                'lat': lat,
                'lon': lon,
                'max_distance': max_distance
            }).first()
            
            return result
        finally:
            session.close()

    def get_lanes_at_coordinate(
        self, lat: float, lon: float, max_distance: float = 0.001
    ) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[float]]:
        """
        Get the number of lanes at a given coordinate.
        
        Args:
            lat (float): Latitude of the coordinate
            lon (float): Longitude of the coordinate
            max_distance (float): Maximum distance to search for nearest way (in degrees)
            
        Returns:
            Tuple[Optional[int], Optional[int], Optional[int], Optional[float]]:
            A tuple containing:
                - Total lanes (None if not specified)
                - Lanes forward
                - Lanes backward
                - Distance to the way (None if no way found)
        """
        result = self.get_nearest_way(lat, lon, max_distance)

        if result is None:
            return None, None, None, None

        return (
            result.lanes,
            result.lanes_forward,
            result.lanes_backward,
            result.distance,
        )

    def store_user_data(self, data: Dict[str, Any]) -> None:
        """Store user-submitted speed data."""
        session = self.Session()
        try:
            stmt = insert(UserData).values(**data)
            session.execute(stmt)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

