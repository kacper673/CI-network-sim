import csv
import json
from unittest import case
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
import buildings, models, infrastructure

class World:
    def __init__(self):
        self.road_network = infrastructure.RoadNetwork()
        self.energy_grid = infrastructure.EnergyGrid()
        self.water_network = infrastructure.WaterNetwork()
        self.railway_network = infrastructure.RailwayNetwork()
        self.road_network = infrastructure.RoadNetwork()
        self.infrastructure_networks = {
            self.road_network.name: self.road_network,
            self.energy_grid.name: self.energy_grid,
            self.water_network.name: self.water_network,
            self.railway_network.name: self.railway_network,
            self.road_network.name: self.road_network,             
            }
        self.buildings = {}
        self.edges = []
        self.current_tick = 0    
        self.snapshots = []    

    def add_building(self, building):
        self.buildings[building.id] = building
        return building

    def connect_buildings(self, infrastructure_layer, from_building, to_building, custom_attributes=None):
        edge = infrastructure_layer.connect_buildings(from_building, to_building, custom_attributes)
        self.edges.append(edge)
        return edge   

    def tick(self):
        self.current_tick += 1

        for building in sorted([b for b in self.buildings.values() if b.produces and b.status == "active"], key=lambda b: b.priority):
            if building.tick():
                print(f"{building.id} produced resources")
                self.distribute_resources(building)

        for edge in self.edges:
            if edge.attributes.get("status", "active") != "destroyed":
                edge.tick()

        for building in sorted([b for b in self.buildings.values() if not b.produces and b.status == "active"], key=lambda b: b.priority):
            success = building.tick()
            print(f"{building.id} operational: {success}")

        return self.current_tick    

    def distribute_resources(self, building):
        outgoing_edges = [e for e in self.edges if e.from_node.id == building.id and e.attributes.get("status", "active") != "destroyed"]

        if not outgoing_edges:
            return

        for resource, amount in building.produces.items():
            avalible = building.resources.get(resource, 0)
            if avalible <= 0:
                continue

            amount_per_edge = min(avalible, amount) / len(outgoing_edges)
            
            for edge in outgoing_edges:
                if amount_per_edge <= 0: #min(avalible, amount)
                    break

                if resource in edge.to_node.requires:
                    send_amount = min(amount_per_edge, edge.to_node.requires[resource])
                else:
                    send_amount = amount_per_edge

                building.resources[resource] -= send_amount
                edge.send_resource(resource, send_amount)
                print(f"Sent {send_amount} {resource} from {building.id} to {edge.to_node.id}")

    def status_summary(self):        
        active_buildings = sum(1 for b in self.buildings.values() if b.status == "active")
        active_edges = sum(1 for e in self.edges if e.attributes.get("status", "active") == "active")
        
        resources = {}
        for resource in set(r for b in self.buildings.values() for r in b.resources if b.resources[r] > 0):
            resources[resource] = sum(b.resources.get(resource, 0) for b in self.buildings.values())
        
        return {
            "tick": self.current_tick,
            "buildings": f"{active_buildings}/{len(self.buildings)}",
            "infrastructure": f"{active_edges}/{len(self.edges)}",
            "resources": resources
        }       

    G_snapshots = []

    def build_graph(self):
        """Zbuduj graf NetworkX z aktualnego stanu świata."""
        G = nx.DiGraph()

        for b in self.buildings.values():
            G.add_node(
                b.id,
                status=b.status,
                priority=b.priority,
                requires=b.requires,
                produces=b.produces
            )
            
        for e in self.edges:
            G.add_edge(
                e.from_node.id,
                e.to_node.id,
                layer=e.attributes.get("layer", "generic"),
                capacity=e.attributes.get("capacity", 1.0),
                travel_time=e.attributes.get("travel_time", 1),
                status=e.attributes.get("status", "active")
            )
        return G

    def capture_snapshot(self):
        """Zapisz migawkę grafu po bieżącym ticku."""
        if not hasattr(self, "_snapshots"):
            self._snapshots = []
        self._snapshots.append(self.build_graph())

    def animate(self, interval_ms=800, seed=42):
        """Pokaż animację z zebranych migawek."""
        snaps = getattr(self, "_snapshots", [])
        if not snaps:
            print("Brak migawek do animacji – uruchom najpierw run()/capture_snapshot().")
            return

        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(snaps[0], seed=seed)  # stały układ

        def update(frame):
            ax.clear()
            G = snaps[frame]

            # kolory węzłów wg statusu
            color_map = {"active": "green", "UPS": "yellow", "offline": "red"}
            node_colors = [color_map.get(G.nodes[n].get("status","active"), "gray") for n in G.nodes()]

            # krawędzie wg warstwy
            edge_colors = []
            for u,v,d in G.edges(data=True):
                layer = d.get("layer","generic")
                edge_colors.append({
                    "Energy Grid":"dimgray",
                    "Road Network":"cornflowerblue",
                    "Water Network":"teal",
                    "Railway Network":"saddlebrown",
                    "Telecom Network":"purple"
                }.get(layer, "lightgray"))

            nx.draw(G, pos, ax=ax,
                    node_color=node_colors, with_labels=True, arrows=True,
                    edge_color=edge_colors)
            ax.set_title(f"Tick {frame+1}")

        anim = FuncAnimation(fig, update, frames=len(snaps), interval=interval_ms, repeat=False)
        return anim

    def run_with_viz(self, ticks=10, capture_every_tick=True):
        """Uruchom symulację i zbieraj migawki do animacji."""
        print("Starting simulation")
        self._snapshots = []
        for _ in range(ticks):
            self.tick()
            if capture_every_tick:
                self.capture_snapshot()
            print(f"STATUS: {self.status_summary()}")
        print("Simulation complete")
        anim = self.animate()
        return anim

    def run(self, ticks=10):
        print("Starting simulation")
        for _ in range(ticks):
            self.tick()
            print(f"STATUS: {self.status_summary()}")
        print("Simulation complete")         


def create_world_from_csv(csv_path_buildings, csv_path_edges):
    world = World()

    rows = []

    with open(csv_path_buildings, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            match row["type"]:
                case "PowerPlant": new_building = buildings.PowerPlant(row["id"])
                case "Magazine": new_building = buildings.Magazine(row["id"])
                case "Hospital": new_building = buildings.Hospital(row["id"])

            new_building.resources = json.loads(row["resources"])
            new_building.requires = json.loads(row["requires"])
            new_building.produces = json.loads(row["produces"])
            new_building.priority = int(row["priority"])

            world.add_building(new_building)


    with open(csv_path_edges, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_id = row["from"]
            to_id = row["to"]
            custom_attributes = json.loads(row["attributes_json"])
            
            infrastructure_layer = world.infrastructure_networks.get(row["layer"])
            if infrastructure_layer:
                world.connect_buildings(infrastructure_layer, world.buildings[from_id], world.buildings[to_id], custom_attributes)

            # match row["layer"]:
                # case "Road Network": world.road_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                # case "Energy Grid": world.energy_grid.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                # case "Water Network": world.water_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                # case "Railway Network": world.railway_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)

    return world

if __name__ == "__main__":
    w = create_world_from_csv("final_nodes.csv", "final_edges.csv")
    anim = w.run_with_viz(ticks=10)
    if anim:
        plt.show()
