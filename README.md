# OSM Data Processor

This project processes OpenStreetMap (OSM) data and stores it in a PostgreSQL database with PostGIS extension for efficient spatial queries.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ with PostGIS extension
- pip (Python package manager)

## Setup

1. Create a PostgreSQL database:
```sql
CREATE DATABASE osm_data;
\c osm_data
CREATE EXTENSION postgis;
```

2. Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://username:password@localhost:5432/osm_data
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the main script:
```bash
python src/main.py
```

This will:
- Initialize the database schema
- Process the example way IDs
- Store the data in the database
- Perform an example query

## Database Schema

The database consists of three main tables:

1. `nodes`: Stores node information including coordinates
2. `ways`: Stores way information including number of lanes
3. `way_nodes`: Stores the relationship between ways and nodes

## Querying the Data

To find the nearest way to a given coordinate:

```python
from database import DatabaseManager

# Initialize database manager
db = DatabaseManager()


result = db.get_nearest_way(lat=37.3981366, lon=-121.8752114)

```