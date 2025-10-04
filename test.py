import pandas as pd,json
import networkx as nx
from copy import deepcopy
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Resource types 
RESOURCE_TYPES = [
    "electricity",
    "water",
    "basic_resources",
    "critical_resources", 
    "heavy_resources",
    "personnel",
    "data"
]

class Layer:
    def __init__(self, name, supported_resources):
        self.name = name        
        self.supported_resources = supported_resources        
        self.edges = []

    def connect_nodes(self, from_node, to_node, attributes):
        """Connect two nodes with an edge having specific attributes"""
        edge = Edge(
            from_node=from_node,
            to_node=to_node,
            attributes=attributes
        )
        self.edges.append(edge)
        return edge

class Edge:
    def __init__(self, from_node, to_node, attributes):
        self.from_node = from_node
        self.to_node = to_node
        self.attributes = attributes
        self.resources_in_transit = {resource: [] for resource in RESOURCE_TYPES}
    
    def send_resource(self, resource_type, amount):
        """Send resources through this edge"""
        if resource_type not in self.from_node.produces:
            return False
            
        travel_time = self.attributes.get("travel_time", 1)
        self.resources_in_transit[resource_type].append({
            'amount': amount,
            'ticks_remaining': travel_time
        })
        return True
    
    def tick(self):
        """Process one time unit of transportation"""
        arrived_resources = {resource: 0 for resource in RESOURCE_TYPES}
        
        for resource_type in RESOURCE_TYPES:
            for resource in self.resources_in_transit[resource_type][:]:
                resource['ticks_remaining'] -= 1
                if resource['ticks_remaining'] <= 0:
                    arrived_resources[resource_type] += resource['amount']
                    self.resources_in_transit[resource_type].remove(resource)
                    
            if arrived_resources[resource_type] > 0:
                self.to_node.receive_supplies(resource_type, arrived_resources[resource_type])
                
        return arrived_resources

class Building:
    def __init__(self, id, requires=None, produces=None, priority=1):
        self.id = id
        self.priority = priority
        self.requires = requires or {}
        self.produces = produces or {}
        self.status = "active"  # active, offline, destroyed
        self.resources = {resource: 0 for resource in RESOURCE_TYPES}

    def works(self) -> bool:
       for resource, amount in self.requires.items():
            if self.resources.get(resource, 0) < amount:
                return False
            return True
       
    def update_status(self):

        if self.works():
            self.status = "active"
            return
        
        self.status = "offline"

    def tick(self):
        """Base tick method to be implemented by subclasses"""
        # Check if all required resources are available
        for resource, amount in self.requires.items():
            if self.resources[resource] < amount:
                return False
        
        # Consume required resources
        for resource, amount in self.requires.items():
            self.resources[resource] -= amount
            
        return True
        
    def receive_supplies(self, resource_type, amount):
        """Generic method to receive supplies of any resource type"""
        if resource_type in RESOURCE_TYPES:
            self.resources[resource_type] += amount

class Hospital(Building):
    def __init__(self, id, resources=None, consumption=None, priority=1):
        resources = resources or {}
        consumption = consumption or {"electricity": 5, "water": 3, "basic_resources": 10}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces={},
            priority=priority
        )
        
        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount

class PowerPlant(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=2):
        resources = resources or {}
        consumption = consumption or {"water": 5}
        production = production or {"electricity": 20}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )
        
        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount
            
    def tick(self):
        if super().tick():
            # Produce resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False

class Magazine(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=2):
        resources = resources or {}
        consumption = consumption or {"electricity": 3}
        production = production or {"basic_resources": 10}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )
        
        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount
            
    def tick(self):
        if super().tick():
            # Produce resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False

class Infrastructure(Layer):
    """Base class for all infrastructure components"""
    _instances = {}  # Class variable to hold singleton instances
    
    def __new__(cls, *args, **kwargs):
        # Singleton pattern - one instance per layer type
        if cls not in cls._instances:
            cls._instances[cls] = super(Infrastructure, cls).__new__(cls)
        return cls._instances[cls]
    
    def __init__(self, name, supported_resources, default_attributes=None):
        # Only initialize if not already initialized
        if not hasattr(self, 'initialized'):
            super().__init__(name, supported_resources)
            self.default_attributes = default_attributes or {
                "capacity": 100,
                "status": "active",
                "travel_time": 1
            }
            self.initialized = True

    def connect_buildings(self, from_building, to_building, custom_attributes=None):
        """Connect two buildings with this infrastructure layer"""
        attributes = self.default_attributes.copy()
        if custom_attributes:
            attributes.update(custom_attributes)
        attributes.setdefault("layer",self.name) 
        return self.connect_nodes(from_building, to_building, attributes)

# Define the infrastructure layer types
class RoadNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Road Network",
            supported_resources=["personnel", "basic_resources", "critical_resources", "heavy_resources"],
            default_attributes={"capacity": 50, "travel_time": 2, "status": "active"}
        )

class EnergyGrid(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Energy Grid",
            supported_resources=["electricity"],
            default_attributes={"capacity": 100, "travel_time": 1, "status": "active"}
        )

class WaterNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Water Network",
            supported_resources=["water"],
            default_attributes={"capacity": 80, "travel_time": 1, "status": "active"}
        )

class RailwayNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Railway Network",
            supported_resources=["heavy_resources", "personnel"],
            default_attributes={"capacity": 200, "travel_time": 4, "status": "active"}
        )

class TelecomNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Telecom Network",
            supported_resources=["data"],
            default_attributes={"capacity": 1000, "travel_time": 1, "status": "active"}
        )


# snapshotów może być kilka (np. po każdym ticku)
G_snapshots = []

def build_graph(buildings, edges):
    G = nx.DiGraph()

    for b in buildings:
        G.add_node(
            b.id,
            layer=getattr(b, "layer", "Unknown"),
            status=getattr(b, "status", "active"),
            supply=getattr(b, "produces", {}),   
            demand=getattr(b, "requires", {}),
        )

    for e in edges:
        G.add_edge(
            e.from_node.id,          
            e.to_node.id,            
            capacity=e.attributes.get("capacity", 1.0),
            type=e.attributes.get("layer", "generic")
        )
    return G


def simulate():
    print("Critical Infrastructure Simulator")
    
    # Create buildings
    hospital = Hospital(
        id="HOSP_001",
        resources={"basic_resources": 100}
    )
    
    power_plant = PowerPlant(
        id="POWER_001",
        resources={"water": 100}
    )
    
    magazine = Magazine(
        id="MAG_001",
        resources={"basic_resources": 500, "electricity": 0}
    )

    # Create infrastructure layers
    road_network = RoadNetwork()
    energy_grid = EnergyGrid()
    
    # Connect buildings
    road_edge = road_network.connect_buildings(
        magazine, hospital, {"travel_time": 3}
    )
    
    energy_edge = energy_grid.connect_buildings(
        power_plant, magazine
    )

    buildings = [hospital,power_plant,magazine]
    edges = [road_edge,energy_edge]

    snapshots = []

    df_nodes = pd.DataFrame([{
    "id": b.id,
    "type": b.__class__.__name__,
    "status": b.status,
    "priority": b.priority,
    "requires": json.dumps(b.requires),
    "produces": json.dumps(b.produces),
    "resources": json.dumps(b.resources),
    } for b in buildings])
    df_nodes.to_csv("nodes.csv", index=False)

    df_edges = pd.DataFrame([{
    "from": e.from_node.id,
    "to": e.to_node.id,
    "layer": e.attributes.get("layer", ""),
    "capacity": e.attributes.get("capacity", ""),
    "travel_time": e.attributes.get("travel_time", ""),
    "status": e.attributes.get("status", ""),
    "attributes_json": json.dumps(e.attributes),
    } for e in edges])
    df_edges.to_csv("edges.csv", index=False)
    
    for tick in range(1, 11):

        if(tick == 3):
            power_plant.resources['electricity'] = 0
            power_plant.status = "offline"
        print(f"\nTick: {tick}")
        
        # Process power plant
        power_plant.tick()
        print(f"Power plant {power_plant.id} electricity: {power_plant.resources['electricity']}")
        
        # Send electricity to magazine
        if power_plant.resources['electricity'] > 0:
            amount_to_send = min(power_plant.resources['electricity'], 10)
            power_plant.resources['electricity'] -= amount_to_send
            energy_edge.send_resource("electricity", amount_to_send)
            
        # Process magazine
        magazine.tick()
        print(f"Magazine {magazine.id} resources: {magazine.resources}")
        
        # Send supplies to hospital
        if magazine.resources['basic_resources'] > 0:
            amount_to_send = min(magazine.resources['basic_resources'], 10)
            magazine.resources['basic_resources'] -= amount_to_send
            road_edge.send_resource("basic_resources", amount_to_send)
            
        # Process hospital
        hospital_success = hospital.tick()
        print(f"Hospital {hospital.id} operational: {hospital_success}")
        print(f"Hospital {hospital.id} resources: {hospital.resources}")
        
        # Process infrastructure networks
        energy_grid_results = energy_edge.tick()
        road_results = road_edge.tick()
        
        print(f"Resources in transit (energy): {energy_edge.resources_in_transit}")
        print(f"Resources in transit (road): {road_edge.resources_in_transit}")

        G = build_graph(buildings, edges)
        snapshots.append(deepcopy(G))       
        
        for b in buildings:
            b.update_status()

    return snapshots 




if __name__ == "__main__":
    # uruchom symulację i odbierz migawki grafu
    G_snapshots = simulate()
    if not G_snapshots:
        raise SystemExit("No snapshots to animate")

    # stały układ węzłów (na podstawie pierwszego snapshotu)
    fig, ax = plt.subplots(figsize=(8, 6))
    pos = nx.spring_layout(G_snapshots[0], seed=42)

    def update(frame):
        ax.clear()
        G = G_snapshots[frame]
        colors = []
        for n, d in G.nodes(data=True):
            status = d.get("status", "active")
            colors.append({"active": "green", "offline": "red", "UPS": "yellow"}.get(status, "gray"))
        nx.draw(G, pos, ax=ax, node_color=colors, with_labels=True, arrows=True)
        ax.set_title(f"Tick {frame+1}")

    ani = FuncAnimation(fig, update, frames=len(G_snapshots), interval=800)
    plt.show()



