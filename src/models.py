from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

Base = declarative_base()

class Node(Base):
    __tablename__ = 'nodes'
    
    node_id = Column(BigInteger, primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    version = Column(Integer)
    timestamp = Column(DateTime)
    geom = Column(Geometry('POINT', srid=4326))
    
    def __repr__(self):
        return f"<Node(id={self.node_id}, lat={self.lat}, lon={self.lon})>"

class Way(Base):
    __tablename__ = 'ways'
    
    way_id = Column(BigInteger, primary_key=True)
    lanes = Column(Integer)
    highway_type = Column(String(50))
    name = Column(String(255))
    maxspeed = Column(String(20))
    version = Column(Integer)
    timestamp = Column(DateTime)
    
    nodes = relationship("WayNode", back_populates="way")
    
    def __repr__(self):
        return f"<Way(id={self.way_id}, lanes={self.lanes}, highway={self.highway_type})>"

class WayNode(Base):
    __tablename__ = 'way_nodes'
    
    way_id = Column(BigInteger, ForeignKey('ways.way_id'), primary_key=True)
    node_id = Column(BigInteger, ForeignKey('nodes.node_id'), primary_key=True)
    sequence = Column(Integer, primary_key=True)
    
    way = relationship("Way", back_populates="nodes")
    node = relationship("Node")
    
    def __repr__(self):
        return f"<WayNode(way_id={self.way_id}, node_id={self.node_id}, sequence={self.sequence})>" 