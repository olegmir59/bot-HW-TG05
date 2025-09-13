import requests

def fetch_elevation(lat, lon):

    base_url = 'https://api.opentopodata.org/v1/srtm30m'
    params = {
        'locations': f'{lat},{lon}',
        'interpolation': 'cubic',
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    return float(data['results'][0]['elevation'])


route_points = [
    (55.115502, 82.9442),    # Гребенщикова
    (55.109380, 82.963507),  # Красных зорь
    (55.114086, 82.973386),  # Тайгинская
    (55.115923, 82.970700),  # Озеро Спартак
    (55.124041, 82.970680),  # Солнечная
    (55.131073, 82.966964)   # Выезд на трассу
]
""",    
    (55.127125, 82.967206),   # Госпиталь
    (55.131073, 82.966964),    # Выезд на трассу
"""
  # список координат вашего маршрута

heights = []

for point in route_points:
    heights.append(fetch_elevation(point[0], point[1]))
delta_heights = []
start_height = heights[0]
for i in range(0, len(heights)):
    delta_heights.append(heights[i] - start_height)

print(heights)
print(delta_heights)
