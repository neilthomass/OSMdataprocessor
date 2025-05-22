from flask import Flask, request, jsonify, render_template
from database import DatabaseManager
import os

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
    - max_distance: Maximum search distance in degrees (optional, default: 0.001)
    
    Returns:
    JSON with lane information or error message
    """
    try:
        # Get parameters from query string
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        max_distance = request.args.get('max_distance', default=0.001, type=float)
        
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
            'maxspeed': way_info.maxspeed
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

if __name__ == '__main__':
    # Get port from environment or use 5000 as default
    port = int(os.getenv('PORT', 5000))
    
    # Run the app with debug mode in development
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 