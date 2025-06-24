import requests
import json

BASE_URL = 'http://localhost:5000'

def test_health():
    r = requests.get(f'{BASE_URL}/api/health')
    print('GET /api/health:', r.status_code, r.json())

def test_lanes():
    params = {'lat': 37.3981366, 'lon': -121.8752114}
    r = requests.get(f'{BASE_URL}/api/lanes', params=params)
    print('GET /api/lanes:', r.status_code, r.json())

def test_suggested_speed():
    params = {'lat': 37.3981366, 'lon': -121.8752114, 'lane': 2}
    r = requests.get(f'{BASE_URL}/api/suggested_speed', params=params)
    print('GET /api/suggested_speed:', r.status_code, r.json())

def test_post_speed():
    payload = {
        "lat": 37.3981366,  # Use a known coordinate in the database
        "lon": -121.8752114,
        "timestamp": "2025-06-24T18:12:00Z",
        "speed": 44,
        "lane_index": 2
    }
    r = requests.post(f'{BASE_URL}/speed', json=payload)
    print('POST /speed:', r.status_code, r.json())

def test_segments():
    r = requests.get(f'{BASE_URL}/segments')
    print('GET /segments:', r.status_code)
    try:
        if r.status_code == 200:
            segments = r.json()
            print(f'  Number of segments: {len(segments)}')
            if segments:
                print('  First segment:', json.dumps(segments[0], indent=2))
        else:
            print('  Error:', r.json())
    except Exception as e:
        print('  Error parsing segments response:', e)

def main():
    print('--- Testing API Endpoints ---')
    test_health()
    test_lanes()
    test_suggested_speed()
    test_post_speed()
    test_segments()

if __name__ == '__main__':
    main() 