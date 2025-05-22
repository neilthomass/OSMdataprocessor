from flask import Flask, request, jsonify, render_template
from database import DatabaseManager
import os
import random
from collections import deque

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'OSM Lanes API is running'
    })


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

if __name__ == '__main__':
    # Get port from environment or use 5000 as default
    port = int(os.getenv('PORT', 5000))
    
    # Run the app with debug mode in development
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 