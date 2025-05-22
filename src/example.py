from database import DatabaseManager

def main():
    # Initialize database manager
    db = DatabaseManager()
    
    # Example coordinates (San Jose area)
    coordinates = [
        (37.3981366, -121.8752114),  # Sinclair Freeway
        (37.3969108, -121.8747250),  # Another point on I-680
        (37.3382, -121.8863),        # Downtown San Jose
    ]
    
    print("Checking number of lanes at various coordinates:")
    print("-" * 50)
    
    for lat, lon in coordinates:
        lanes, distance = db.get_lanes_at_coordinate(lat, lon)
        
        if lanes is None:
            print(f"Coordinates ({lat}, {lon}): No road found within search radius")
        else:
            print(f"Coordinates ({lat}, {lon}):")
            print(f"  Number of lanes: {lanes}")
            print(f"  Distance to road: {distance:.6f} degrees")
            print(f"  (approximately {distance * 111:.2f} kilometers)")
        print("-" * 50)

if __name__ == "__main__":
    main() 