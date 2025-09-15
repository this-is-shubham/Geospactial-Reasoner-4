# import requests

# OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# def fetch_osm_data(lat, lon, radius_km=5):
#     """
#     Fetch disaster-relevant features from OpenStreetMap within radius_km of lat/lon.
#     Returns structured JSON with multiple categories.
#     """
#     radius = radius_km * 1000  # convert to meters

#     queries = {
#         "hospitals": f"""
#             node(around:{radius},{lat},{lon})["amenity"="hospital"];
#             out center;
#         """,
#         "clinics": f"""
#             node(around:{radius},{lat},{lon})["amenity"~"clinic|doctors"];
#             out center;
#         """,
#         "pharmacies": f"""
#             node(around:{radius},{lat},{lon})["amenity"="pharmacy"];
#             out center;
#         """,
#         "police_stations": f"""
#             node(around:{radius},{lat},{lon})["amenity"="police"];
#             out center;
#         """,
#         "fire_stations": f"""
#             node(around:{radius},{lat},{lon})["amenity"="fire_station"];
#             out center;
#         """,
#         "government_offices": f"""
#             node(around:{radius},{lat},{lon})["office"="government"];
#             out center;
#         """,
#         "shelters": f"""
#             node(around:{radius},{lat},{lon})["amenity"="shelter"];
#             out center;
#         """,
#         "community_centers": f"""
#             node(around:{radius},{lat},{lon})["amenity"="community_centre"];
#             out center;
#         """,
#         "schools": f"""
#             node(around:{radius},{lat},{lon})["amenity"="school"];
#             out center;
#         """,
#         "universities": f"""
#             node(around:{radius},{lat},{lon})["amenity"="university"];
#             out center;
#         """,
#         "roads": f"""
#             way(around:{radius},{lat},{lon})["highway"];
#             out center;
#         """,
#         "railway_stations": f"""
#             node(around:{radius},{lat},{lon})["railway"="station"];
#             out center;
#         """,
#         "bus_stations": f"""
#             node(around:{radius},{lat},{lon})["amenity"="bus_station"];
#             out center;
#         """,
#         "airports": f"""
#             node(around:{radius},{lat},{lon})["aeroway"="aerodrome"];
#             out center;
#         """,
#         "power_substations": f"""
#             node(around:{radius},{lat},{lon})["power"="substation"];
#             out center;
#         """,
#         "fuel_stations": f"""
#             node(around:{radius},{lat},{lon})["amenity"="fuel"];
#             out center;
#         """,
#         "water_towers": f"""
#             node(around:{radius},{lat},{lon})["man_made"="water_tower"];
#             out center;
#         """,
#         "dams": f"""
#             way(around:{radius},{lat},{lon})["man_made"="dam"];
#             out center;
#         """,
#         "bridges": f"""
#             way(around:{radius},{lat},{lon})["man_made"="bridge"];
#             out center;
#         """
#     }

#     results = {}

#     for category, query in queries.items():
#         try:
#             response = requests.post(OVERPASS_URL, data={"data": f"[out:json];{query}"})
#             response.raise_for_status()
#             data = response.json()
#             results[category] = data.get("elements", [])
#         except Exception as e:
#             results[category] = {"error": str(e)}

#     return results

# file: phase3_features.py
# phase3_features.py
# import requests
# import ee

# # ----------------------------
# # Earth Engine Initialization
# # ----------------------------
# PROJECT = "LTIFINAL"  # your GCP project name

# try:
    
#     ee.Initialize(project=PROJECT)
#     print(f"✅ GEE initialized with project {PROJECT}")
# except Exception as e:
#     print(f"⚠️ GEE init failed, trying auth: {e}")
#     try:
#         ee.Authenticate(project=PROJECT)
#         ee.Initialize(project=PROJECT)
#         print(f"✅ GEE authenticated and initialized with project {PROJECT}")
#     except Exception as e2:
#         print(f"❌ GEE authentication failed: {e2}")


# # ----------------------------
# # GEE HAZARD ANALYSIS
# # ----------------------------
# def get_flood_extent(bbox):
#     """Return flooded area (km²) using Sentinel-1 water detection."""
#     region = ee.Geometry.Rectangle([bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]])
#     s1 = (
#         ee.ImageCollection("COPERNICUS/S1_GRD")
#         .filterBounds(region)
#         .filterDate("2025-01-01", "2025-09-01")
#         .filter(ee.Filter.eq("instrumentMode", "IW"))
#         .select("VV")
#     )
#     img = s1.median()
#     water = img.lt(-17)  # VV threshold for water
#     area = water.multiply(ee.Image.pixelArea()).reduceRegion(
#         reducer=ee.Reducer.sum(),
#         geometry=region,
#         scale=30,
#         maxPixels=1e12
#     )
#     return float(area.get("VV").getInfo() or 0) / 1e6  # km²


# def get_rainfall_anomaly(bbox):
#     """Return rainfall anomaly (%) using CHIRPS dataset."""
#     region = ee.Geometry.Rectangle([bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]])

#     chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(region)
#     recent = chirps.filterDate("2025-06-01", "2025-09-01").sum()
#     baseline = chirps.filterDate("2000-06-01", "2020-09-01").mean()

#     anomaly = recent.subtract(baseline).divide(baseline).multiply(100)
#     val = anomaly.reduceRegion(
#         reducer=ee.Reducer.mean(),
#         geometry=region,
#         scale=5000,
#         maxPixels=1e12
#     )
#     return float(val.get("precipitation").getInfo() or 0)


# def get_slope_risk(bbox):
#     """Return % area with slope >30° (landslide proxy) using SRTM DEM."""
#     region = ee.Geometry.Rectangle([bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]])
#     dem = ee.Image("USGS/SRTMGL1_003")
#     slope = ee.Terrain.slope(dem)
#     risky = slope.gt(30)

#     area_total = ee.Image.pixelArea().reduceRegion(
#         reducer=ee.Reducer.sum(), geometry=region, scale=90, maxPixels=1e12
#     )
#     area_risky = risky.multiply(ee.Image.pixelArea()).reduceRegion(
#         reducer=ee.Reducer.sum(), geometry=region, scale=90, maxPixels=1e12
#     )

#     total = float(area_total.get("area").getInfo() or 1)
#     risky_area = float(area_risky.get("slope").getInfo() or 0)
#     return (risky_area / total) * 100


# def get_earthquake_zone(lat, lon):
#     """Rough classification using GSHAP seismic hazard zones (placeholder)."""
#     if lat < 25 and lon > 80:
#         return "Moderate Risk"
#     elif lat > 25 and lon > 85:
#         return "High Risk"
#     else:
#         return "Low Risk"


# # ----------------------------
# # OSM FEATURES FETCHER
# # ----------------------------
# OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# OSM_QUERIES = {
#     "hospitals": 'node["amenity"="hospital"]',
#     "shelters": 'node["amenity"="shelter"]',
#     "roads": 'way["highway"]',
#     "critical_infra": 'node["amenity"~"fire_station|police|power|water_works"]'
# }


# def fetch_osm_features(bbox: list, feature_types: list = None) -> dict:
#     """Fetch OSM features inside bounding box (with SSL fallback)."""
#     if feature_types is None:
#         feature_types = list(OSM_QUERIES.keys())

#     min_lat, min_lon = bbox[0]
#     max_lat, max_lon = bbox[1]

#     features = {}
#     for f in feature_types:
#         query = f"""
#         [out:json][timeout:25];
#         (
#           {OSM_QUERIES[f]}({min_lat},{min_lon},{max_lat},{max_lon});
#         );
#         out center;
#         """
#         try:
#             try:
#                 r = requests.post(
#                     OVERPASS_URL,
#                     data=query,
#                     headers={"User-Agent": "DisasterAI/1.0"},
#                     timeout=60
#                 )
#                 r.raise_for_status()
#             except requests.exceptions.SSLError:
#                 # SSL fallback
#                 r = requests.post(
#                     OVERPASS_URL,
#                     data=query,
#                     headers={"User-Agent": "DisasterAI/1.0"},
#                     timeout=60,
#                     verify=False
#                 )
#                 r.raise_for_status()

#             data = r.json()
#             features[f] = [
#                 {
#                     "lat": elem.get("lat", elem.get("center", {}).get("lat")),
#                     "lon": elem.get("lon", elem.get("center", {}).get("lon")),
#                     "tags": elem.get("tags", {})
#                 }
#                 for elem in data.get("elements", [])
#                 if "lat" in elem or "center" in elem
#             ]
#         except Exception as e:
#             print(f"Error fetching {f} from OSM: {e}")
#             features[f] = []

#     return features


# # ----------------------------
# # COMBINED FETCHER (GEE + OSM)
# # ----------------------------
# def get_disaster_features(bbox: list, hazard_types: list = None) -> dict:
#     """Return combined hazard indicators from GEE + OSM features."""
#     result = {"hazard_data": {}, "osm_features": {}}

#     # GEE hazard indicators
#     try:
#         if hazard_types:
#             if "flood" in hazard_types:
#                 result["hazard_data"]["flooded_area_km2"] = get_flood_extent(bbox)
#             if "drought" in hazard_types:
#                 result["hazard_data"]["rainfall_anomaly"] = get_rainfall_anomaly(bbox)
#             if "landslide" in hazard_types:
#                 result["hazard_data"]["slope_risk_percent"] = get_slope_risk(bbox)
#             if "earthquake" in hazard_types:
#                 lat = (bbox[0][0] + bbox[1][0]) / 2
#                 lon = (bbox[0][1] + bbox[1][1]) / 2
#                 result["hazard_data"]["earthquake_risk_zone"] = get_earthquake_zone(lat, lon)
#     except Exception as e:
#         print(f"GEE hazard fetch failed: {e}")
#         result["hazard_data"] = {}

#     # OSM features
#     try:
#         result["osm_features"] = fetch_osm_features(bbox)
#     except Exception as e:
#         print(f"Error fetching OSM features: {e}")
#         result["osm_features"] = {}

#     return result

import requests
import ee

# ----------------------------
# Earth Engine Initialization
# ----------------------------
PROJECT = "ltifinal"  # your GCP project name

try:
    ee.Initialize(project=PROJECT)
    print(f"✅ GEE initialized with project {PROJECT}")
except Exception as e:
    print(f"❌ GEE init failed: {e}")
    # Make sure you've run:
    #   earthengine authenticate
    #   earthengine set_project LTIFINAL
    raise

# ----------------------------
# Bounding Box Expander
# ----------------------------
def expand_bbox(bbox, buffer_deg=0.05):
    """
    Expand bounding box by buffer_deg (~0.05° ≈ 5.5 km).
    bbox = [[min_lat, min_lon], [max_lat, max_lon]]
    """
    min_lat, min_lon = bbox[0]
    max_lat, max_lon = bbox[1]
    return [
        [min_lat - buffer_deg, min_lon - buffer_deg],
        [max_lat + buffer_deg, max_lon + buffer_deg]
    ]

# ----------------------------
# GEE HAZARD ANALYSIS
# ----------------------------
def get_flood_extent(bbox):
    """Return flooded area (km²) using Sentinel-1 water detection."""
    region = ee.Geometry.Rectangle([bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]])
    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filterDate("2025-01-01", "2025-09-01")
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .select("VV")
    )
    img = s1.median()
    water = img.lt(-17)  # VV threshold for water
    area = water.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=region,
        scale=30,
        maxPixels=1e12
    )
    return float(area.get("VV").getInfo() or 0) / 1e6  # km²

def get_rainfall_anomaly(bbox):
    """Return rainfall anomaly (%) using CHIRPS dataset."""
    region = ee.Geometry.Rectangle([bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]])
    chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(region)
    recent = chirps.filterDate("2025-06-01", "2025-09-01").sum()
    baseline = chirps.filterDate("2000-06-01", "2020-09-01").mean()
    anomaly = recent.subtract(baseline).divide(baseline).multiply(100)
    val = anomaly.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=5000,
        maxPixels=1e12
    )
    return float(val.get("precipitation").getInfo() or 0)

def get_slope_risk(bbox):
    """Return % area with slope >30° (landslide proxy) using SRTM DEM."""
    region = ee.Geometry.Rectangle([bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]])
    dem = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(dem)
    risky = slope.gt(30)
    area_total = ee.Image.pixelArea().reduceRegion(
        reducer=ee.Reducer.sum(), geometry=region, scale=90, maxPixels=1e12
    )
    area_risky = risky.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=region, scale=90, maxPixels=1e12
    )
    total = float(area_total.get("area").getInfo() or 1)
    risky_area = float(area_risky.get("slope").getInfo() or 0)
    return (risky_area / total) * 100

def get_earthquake_zone(lat, lon):
    """Rough classification using GSHAP seismic hazard zones (placeholder)."""
    if lat < 25 and lon > 80:
        return "Moderate Risk"
    elif lat > 25 and lon > 85:
        return "High Risk"
    else:
        return "Low Risk"

# ----------------------------
# OSM FEATURES FETCHER
# ----------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OSM_QUERIES = {
    "hospitals": 'node["amenity"="hospital"]',
    "shelters": 'node["amenity"="shelter"]',
    "roads": 'way["highway"]',
    "critical_infra": 'node["amenity"~"fire_station|police|power|water_works"]'
}

def fetch_osm_features(bbox: list, feature_types: list = None) -> dict:
    """Fetch OSM features inside bounding box (with SSL fallback)."""
    if feature_types is None:
        feature_types = list(OSM_QUERIES.keys())
    min_lat, min_lon = bbox[0]
    max_lat, max_lon = bbox[1]
    features = {}
    for f in feature_types:
        query = f"""
        [out:json][timeout:25];
        (
          {OSM_QUERIES[f]}({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center;
        """
        try:
            r = requests.post(
                OVERPASS_URL,
                data=query,
                headers={"User-Agent": "DisasterAI/1.0"},
                timeout=60,
                verify=False  # ⚠️ temp SSL workaround
            )
            r.raise_for_status()
            data = r.json()
            features[f] = [
                {
                    "lat": elem.get("lat", elem.get("center", {}).get("lat")),
                    "lon": elem.get("lon", elem.get("center", {}).get("lon")),
                    "tags": elem.get("tags", {})
                }
                for elem in data.get("elements", [])
                if "lat" in elem or "center" in elem
            ]
        except Exception as e:
            print(f"Error fetching {f} from OSM: {e}")
            features[f] = []
    return features

# ----------------------------
# COMBINED FETCHER
# ----------------------------
def get_disaster_features(bbox: list, hazard_types: list = None) -> dict:
    """Return combined hazard indicators from GEE + OSM features."""
    result = {"hazard_data": {}, "osm_features": {}}

    # 🔹 Expand bbox for better coverage
    expanded_bbox = expand_bbox(bbox, buffer_deg=0.05)

    # GEE hazard indicators
    try:
        if hazard_types:
            if "flood" in hazard_types:
                result["hazard_data"]["flooded_area_km2"] = get_flood_extent(expanded_bbox)
            if "drought" in hazard_types:
                result["hazard_data"]["rainfall_anomaly"] = get_rainfall_anomaly(expanded_bbox)
            if "landslide" in hazard_types:
                result["hazard_data"]["slope_risk_percent"] = get_slope_risk(expanded_bbox)
            if "earthquake" in hazard_types:
                lat = (expanded_bbox[0][0] + expanded_bbox[1][0]) / 2
                lon = (expanded_bbox[0][1] + expanded_bbox[1][1]) / 2
                result["hazard_data"]["earthquake_risk_zone"] = get_earthquake_zone(lat, lon)
    except Exception as e:
        print(f"GEE hazard fetch failed: {e}")
        result["hazard_data"] = {}

    # OSM features
    try:
        result["osm_features"] = fetch_osm_features(expanded_bbox)
    except Exception as e:
        print(f"Error fetching OSM features: {e}")
        result["osm_features"] = {}

    return result

