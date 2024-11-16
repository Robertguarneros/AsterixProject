import numpy as np

def get_rotation_matrix(lat, lon):
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    return np.array([
        [-np.sin(lon_rad), np.cos(lon_rad), 0],
        [-np.sin(lat_rad) * np.cos(lon_rad), -np.sin(lat_rad) * np.sin(lon_rad), np.cos(lat_rad)],
        [np.cos(lat_rad) * np.cos(lon_rad), np.cos(lat_rad) * np.sin(lon_rad), np.sin(lat_rad)]
    ])

def get_translation_vector(lat, lon, alt):
    A = 6378137.0  # Semi-major axis
    E2 = 0.00669437999014  # Eccentricity squared
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    nu = A / np.sqrt(1 - E2 * np.sin(lat_rad)**2)
    return np.array([
        [(nu + alt) * np.cos(lat_rad) * np.cos(lon_rad)],
        [(nu + alt) * np.cos(lat_rad) * np.sin(lon_rad)],
        [(nu * (1 - E2) + alt) * np.sin(lat_rad)]
    ])

def geocentric2system_cartesian(geocentric_coords):
    geo = {'X': geocentric_coords[0], 'Y': geocentric_coords[1], 'Z': geocentric_coords[2]}  
    center = {'Lat': 41.10904, 'Lon': 1.226947, 'Alt': 3438.954}
    R = get_rotation_matrix(center['Lat'], center['Lon'])
    T = get_translation_vector(center['Lat'], center['Lon'], center['Alt'])
    
    input_vector = np.array([[geo['X']], [geo['Y']], [geo['Z']]])
    result_vector = R @ (input_vector - T)
    
    return {
        'X': result_vector[0, 0],
        'Y': result_vector[1, 0],
        'Z': result_vector[2, 0]
    }

def system_cartesian2system_stereographical(c):
    class CoordinatesUVH:
        def __init__(self):
            self.U = 0
            self.V = 0
            self.Height = 0

    res = CoordinatesUVH()
    center = {'Lat': 41.10904, 'Lon': 1.226947, 'Alt': 3438.954}
    
    A = 6378137.0  # Semi-major axis
    E2 = 0.00669437999013  # Eccentricity squared
    lat_rad = np.radians(center['Lat'])
    
    R_S = (A * (1.0 - E2)) / (1 - E2 * np.sin(lat_rad)**2)**1.5
    
    d_xy2 = c['X']**2 + c['Y']**2
    res.Height = np.sqrt(d_xy2 + (c['Z'] + center['Alt'] + R_S)**2) - R_S
    
    k = (2 * R_S) / (2 * R_S + center['Alt'] + c['Z'] + res.Height)
    res.U = k * c['X']
    res.V = k * c['Y']

    return {
        'U': res.U,
        'V': res.V,
        'Height': res.Height
    }

def calculate_distance(U1, V1, U2, V2):
    distance = np.sqrt((U1 - U2)**2 + (V1 - V2)**2) / 1852
    return distance


#geo_input1 = {'X': 87655.98047131, 'Y': 50146.10981296, 'Z': 4324.09816745}  
geo_input1 = [ 8963.28342975, 25957.22593226,   650.87712685]
result_cartesian1 = geocentric2system_cartesian(geo_input1)
print(result_cartesian1)

stereographical_result1 = system_cartesian2system_stereographical(result_cartesian1)
print(stereographical_result1)

#geo_input2 = {'X': 29139.84179419, 'Y': 12933.52048435, 'Z': 714.11578617}
geo_input2 = [38483.29661417, 67000.72207847,  2262.83451426]
result_cartesian2 = geocentric2system_cartesian(geo_input2)
print(result_cartesian2)

stereographical_result2 = system_cartesian2system_stereographical(result_cartesian2)
print(stereographical_result2)

distance = calculate_distance(stereographical_result1['U'], stereographical_result1['V'], stereographical_result2['U'], stereographical_result2['V'])
print(f"Distance: {distance} nautical miles")
