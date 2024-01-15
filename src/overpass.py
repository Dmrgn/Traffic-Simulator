import requests
import urllib
import math
import numpy as np
import json

from globals import geocode as global_geocode

SEARCH_RADIUS = 500

with open("../data/roads.json", "r") as f:
    data = json.load(f)
    data_roads = data["roads"]
    data_lights = data["lights"]
    data_stops = data["stops"]
    data_buildings = data["buildings"]

def get_roads_in_geocode(g):
    geocode = g
    query = urllib.parse.quote(f"""
    [out:json][timeout:25];
    (
        nwr(around:{SEARCH_RADIUS}, {geocode[0]}, {geocode[1]})[highway~"^(primary|secondary|tertiary|motorway|motorway_link|residential|traffic_signals)$"];
        nwr(around:{SEARCH_RADIUS}, {geocode[0]}, {geocode[1]})[building];
    );
    out geom;
    """)
    result = requests.get(f"https://overpass-api.de/api/interpreter?data={query}").json()
    roads = {"primary":[], "secondary":[], "tertiary":[]}
    lights = []
    stops = []
    buildings = []
    for element in result["elements"]:
        if not "geometry" in element:
            continue
        if "highway" in element["tags"]:
            if (element["tags"]["highway"] in "motorway motorway_link primary"):
                roads["primary"].append(element)
            elif (element["tags"]["highway"] in "secondary tertiary"):
                roads["secondary"].append(element)
            elif (element["tags"]["highway"] in "residential"):
                roads["tertiary"].append(element)
            elif (element["tags"]["highway"] in "traffic_signals"):
                lights.append(element)
        elif ("building" in element["tags"]):
            buildings.append(element["geometry"])
    
    return {"roads":roads, "lights":lights, "stops":stops, "buildings": buildings}

# get the offset in meters of the two geocodes
def geocode_offset(origin, geocode):
    return (-(geocode[0]-origin[0])*111111, (geocode[1]-origin[1])*111111*math.cos(math.radians(geocode[0])))

# with open("../data/medium_roads.json", "w") as f:
#     json.dump(get_roads_in_geocode(global_geocode), f)