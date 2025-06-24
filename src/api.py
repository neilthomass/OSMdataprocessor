from flask import Flask, request, jsonify, render_template
from database import DatabaseManager
import os
import random
from collections import deque
from sqlalchemy import text

# simple in-memory store for previous coordinates keyed by client address.
# Each client id maps to a deque holding the last 15 coordinates.
previous_coords = {}

app = Flask(__name__, template_folder='templates')
db_manager = DatabaseManager()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/lanes', methods=['GET'])
def get_lanes():
    """
    Get the number of lanes at a specific coordinate.
    
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    - errordist: Maximum search distance in degrees (optional, default: 0.001)
    
    Returns:
    JSON with lane information or error message
    """
    try:
        # Get parameters from query string
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        max_distance = request.args.get('errordist', default=0.001, type=float)
        
        # Validate parameters
        if lat is None or lon is None:
            return jsonify({
                'error': 'Missing parameters',
                'message': 'Both lat and lon parameters are required'
            }), 400
            
        # Get lanes information
        lanes, distance = db_manager.get_lanes_at_coordinate(lat, lon, max_distance)
        
        if lanes is None:
            return jsonify({
                'found': False,
                'message': 'No road found within the specified distance'
            })
        
        # Determine direction using moving average of the last 15 requests
        client_id = request.remote_addr
        history = previous_coords.setdefault(client_id, deque(maxlen=15))
        history.append({'lat': lat, 'lon': lon})

        direction = None
        if len(history) > 1:
            lat_diffs = [history[i + 1]['lat'] - history[i]['lat'] for i in range(len(history) - 1)]
            avg_lat_diff = sum(lat_diffs) / len(lat_diffs)
            direction = 'north' if avg_lat_diff > 0 else 'south'

        # Get additional information about the way
        way_info = db_manager.get_nearest_way(lat, lon, max_distance)
        
        return jsonify({
            'found': True,
            'lanes': lanes,
            'distance': distance,
            'distance_km': distance * 111.0,  # Approximate conversion to kilometers
            'way_id': way_info.way_id,
            'highway_type': way_info.highway_type,
            'name': way_info.name,
            'maxspeed': way_info.maxspeed,
            'direction': direction
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Server error',
            'message': str(e)
        }), 500

@app.route('/api/suggested_speed', methods=['GET'])
def suggested_speed():
    """Return a random suggested speed for now."""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    lane = request.args.get('lane', type=int)

    if lat is None or lon is None or lane is None:
        return jsonify({'error': 'Missing parameters'}), 400

    speed = random.randint(0, 60)
    return jsonify({'suggested_speed': speed})

@app.route('/speed', methods=['POST'])
def post_speed():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    timestamp = data.get('timestamp')
    speed = data.get('speed')
    lane_index = data.get('lane_index')

    # Validate input
    if None in (lat, lon, timestamp, speed, lane_index):
        return jsonify({'error': 'Missing required fields'}), 400

    # Find nearest segment (way)
    way = db_manager.get_nearest_way(lat, lon)
    if not way:
        return jsonify({'error': 'No segment found'}), 404

    # For demo, create a fake segment id and confidence
    matched_segment_id = f"680N-{way.way_id}"
    suggested_speed = 77  # Placeholder logic
    confidence = 0.94     # Placeholder logic

    return jsonify({
        'suggested_speed': suggested_speed,
        'matched_segment_id': matched_segment_id,
        'confidence': confidence
    })

@app.route('/segments', methods=['GET'])
def get_segments():
    session = db_manager.Session()
    segments = []
    try:
        # Only select Sinclair Freeway segments
        ways = session.execute(
            text("""SELECT way_id, name FROM ways WHERE name ILIKE '%Sinclair%'""")
        ).fetchall()
        if not ways:
            return jsonify([])  # Return empty list if no segments found
        for way in ways:
            nodes = session.execute(
                text("""SELECT n.lat, n.lon FROM nodes n
                          JOIN way_nodes wn ON n.node_id = wn.node_id
                          WHERE wn.way_id = :way_id
                          ORDER BY wn.sequence"""),
                {'way_id': way.way_id}
            ).fetchall()
            polyline = [[n.lat, n.lon] for n in nodes]
            segments.append({
                'id': f"Sinclair-{way.way_id}",
                'lane_index': 2,
                'polyline': polyline,
                'mile_range': [12.3, 12.8]
            })
        return jsonify(segments)
    except Exception as e:
        print(f"Error in /segments: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'OSM Lanes API is running'
    })

if __name__ == '__main__':
    # Get port from environment or use 5000 as default
    port = int(os.getenv('PORT', 5000))
    
    # Run the app with debug mode in development
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 