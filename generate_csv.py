# generate_big_world.py
import csv, json, random, math
from itertools import count
import time
random.seed(time.time())

N_POWER = 16
N_WATER = 20
N_DATA = 16
N_MAGAZINES = 14
N_HOSPITALS = 10  # so total ~100 (8+12+8+15+57 = 100)

initial_offline_prob = 0.02  # 2% węzłów startuje offline (rzadko)

RESOURCE_TYPES = ["electricity", "water", "basic_resources", "data"]

nodes = []
edges = []

id_counter = count(1)

def nid(prefix):
    return f"{prefix}_{next(id_counter):03d}"

# helper to sample boolean by prob
def prob(p): return random.random() < p

# Create PowerPlants
for i in range(N_POWER):
    idn = f"POWER_{i+1:03d}"
    prod = {"electricity": random.randint(15, 60)}  # produces per tick
    req = {"water": random.randint(2, 10)}  # needs some water
    resources = {"water": random.randint(30, 150), "electricity": 0}
    status = "offline" if prob(initial_offline_prob) else "active"
    nodes.append({
        "id": idn,
        "type": "PowerPlant",
        "status": status,
        "priority": 2,
        "requires": json.dumps(req),
        "produces": json.dumps(prod),
        "resources": json.dumps(resources),
    })

# Create WaterPlants
for i in range(N_WATER):
    idn = f"WATER_{i+1:03d}"
    prod = {"water": random.randint(8, 25)}
    req = {"electricity": random.randint(2, 10)}
    resources = {"electricity": random.randint(0, 40), "water": 0}
    status = "offline" if prob(initial_offline_prob) else "active"
    nodes.append({
        "id": idn,
        "type": "WaterPlant",
        "status": status,
        "priority": 2,
        "requires": json.dumps(req),
        "produces": json.dumps(prod),
        "resources": json.dumps(resources),
    })

# Create DataCenters
for i in range(N_DATA):
    idn = f"DATA_{i+1:03d}"
    prod = {"data": random.randint(20, 60)}
    req = {"electricity": random.randint(8, 12), "water": random.randint(0,6)}
    resources = {"electricity": random.randint(5, 14), "water": random.randint(0,10), "data": 0}
    status = "offline" if prob(initial_offline_prob) else "active"
    nodes.append({
        "id": idn,
        "type": "DataCenter",
        "status": status,
        "priority": 1,
        "requires": json.dumps(req),
        "produces": json.dumps(prod),
        "resources": json.dumps(resources),
    })

# Create Magazines (depots)
for i in range(N_MAGAZINES):
    idn = f"MAG_{i+1:03d}"
    prod = {"basic_resources": random.randint(8, 25)}
    req = {"electricity": random.randint(1,6)}
    resources = {"basic_resources": random.randint(50,300), "electricity": random.randint(0,10)}
    status = "offline" if prob(initial_offline_prob) else "active"
    nodes.append({
        "id": idn,
        "type": "Magazine",
        "status": status,
        "priority": 2,
        "requires": json.dumps(req),
        "produces": json.dumps(prod),
        "resources": json.dumps(resources),
    })

# Create Hospitals
for i in range(N_HOSPITALS):
    idn = f"HOSP_{i+1:03d}"
    req = {
        "electricity": random.randint(6, 12),
        "water": random.randint(3, 10),
        "basic_resources": random.randint(3, 9)
    }
    resources = {
        "electricity": random.randint(5, 10),
        "water": random.randint(5, 10),
        "basic_resources": random.randint(20, 80)
    }
    status = "offline" if prob(initial_offline_prob) else "active"
    nodes.append({
        "id": idn,
        "type": "Hospital",
        "status": status,
        "priority": 1,
        "requires": json.dumps(req),
        "produces": json.dumps({}),   # hospitals don't produce
        "resources": json.dumps(resources),
    })

# --- create edges ---
# layers: Energy Grid (electricity), Water Network (water), Road Network (basic_resources/personnel),
# Telecom Network (data)
layers = {
    "energy": "Energy Grid",
    "water": "Water Network",
    "road": "Road Network",
    "telecom": "Telecom Network"
}

# helper to add edge
def add_edge(frm, to, layer_key, capacity=None, travel_time=None):
    if capacity is None:
        capacity = random.randint(30, 120) if layer_key=="energy" else random.randint(20, 80)
    if travel_time is None:
        travel_time = random.randint(1,4) if layer_key!="telecom" else 1
    attr = {
        "layer": layers[layer_key],
        "capacity": capacity,
        "travel_time": travel_time,
        "status": "active"
    }
    edges.append({
        "from": frm,
        "to": to,
        "layer": layers[layer_key],
        "capacity": capacity,
        "travel_time": travel_time,
        "status": "active",
        "attributes_json": json.dumps(attr)
    })

# Collect lists by type for connections
type_map = {}
for n in nodes:
    type_map.setdefault(n["type"], []).append(n["id"])

# Energy edges: connect each PowerPlant to many consumers (hospitals, data, magazines, water plants)
for p in type_map["PowerPlant"]:
    consumers = type_map["Hospital"] + type_map.get("DataCenter",[]) + type_map.get("Magazine",[]) + type_map.get("WaterPlant",[])
    # each power plant connects to 20..35 random consumers
    k = min(len(consumers), random.randint(12, 30))
    for to in random.sample(consumers, k):
        add_edge(p, to, "energy", capacity=random.randint(40,120), travel_time=1)

# Water edges: each WaterPlant to some hospitals and power plants
for w in type_map["WaterPlant"]:
    consumers = random.sample(type_map["Hospital"], min(25, len(type_map["Hospital"])))
    for to in consumers:
        add_edge(w, to, "water", capacity=random.randint(30,90), travel_time=random.randint(1,4))
    # also water -> power plants (cooling)
    for to in random.sample(type_map["PowerPlant"], min(3, len(type_map["PowerPlant"]))):
        add_edge(w, to, "water", capacity=random.randint(20,60), travel_time=random.randint(1,3))

# Road edges: magazines -> hospitals (supply chain). Each magazine supplies many hospitals
for mag in type_map["Magazine"]:
    to_h = random.sample(type_map["Hospital"], min(30, len(type_map["Hospital"])))
    for to in to_h:
        add_edge(mag, to, "road", capacity=random.randint(10,60), travel_time=random.randint(1,6))

# Telecom edges: data centers -> hospitals (and some magazines)
for d in type_map["DataCenter"]:
    targets = random.sample(type_map["Hospital"], min(30, len(type_map["Hospital"])))
    for t in targets:
        add_edge(d, t, "telecom", capacity=random.randint(100,600), travel_time=1)
    # to some magazines as well
    for t in random.sample(type_map["Magazine"], min(5, len(type_map["Magazine"]))):
        add_edge(d, t, "telecom", capacity=random.randint(80,500), travel_time=1)

# Optionally: add some inter-magazine logistic edges and hospital-to-hospital transfers (road)
for _ in range(30):
    a,b = random.sample(type_map["Magazine"], 2)
    add_edge(a,b,"road", capacity=random.randint(10,40), travel_time=random.randint(1,5))

# --- persist CSVs ---
with open("big_nodes.csv", "w", newline="", encoding="utf-8") as f:
    fieldnames = ["id","type","status","priority","requires","produces","resources"]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for n in nodes:
        w.writerow(n)

with open("big_edges.csv", "w", newline="", encoding="utf-8") as f:
    fieldnames = ["from","to","layer","capacity","travel_time","status","attributes_json"]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for e in edges:
        w.writerow(e)

print("Wygenerowano big_nodes.csv i big_edges.csv")
print(f"Nodes: {len(nodes)}, edges: {len(edges)}")