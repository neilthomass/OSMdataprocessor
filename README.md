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

## Fetching Freeway Data

To load all major California freeways into the database, run:

```bash
python src/fetch_freeways.py
```

This script uses the Overpass API to download motorway and trunk roads within
California and stores them in the database.

## Storing User Speed Data

The `/speed` endpoint now stores submitted speed records in a `user_data` table.

## Speed Recommendations

Use the `/api/recommended_speed` endpoint to obtain predicted speeds for each
lane for the next 30 seconds. Pass a PeMS `station_id` as a query parameter.

Example:

```bash
curl 'http://localhost:5000/api/recommended_speed?station_id=1234'
```

The response contains a list of speeds for each lane:

```json
{
  "station_id": 1234,
  "recommendations": {
    "1": [60.1, 59.8, ...],
    "2": [58.2, 58.0, ...]
  }
}
```
