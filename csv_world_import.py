import csv
import json
from unittest import case

import pandas as pd
import buildings, models, infrastructure


class World:
    def __init__(self):
        self.road_network = infrastructure.RoadNetwork()
        self.energy_grid = infrastructure.EnergyGrid()
        self.water_network = infrastructure.WaterNetwork()
        self.railway_network = infrastructure.RailwayNetwork()        
        self.telecom_network = infrastructure.TelecomNetwork()
        
        self.infrastructure_networks = {
            self.road_network.name: self.road_network,
            self.energy_grid.name: self.energy_grid,
            self.water_network.name: self.water_network,
            self.railway_network.name: self.railway_network,
            self.telecom_network.name: self.telecom_network,
            }
        self.buildings = {}
        self.edges = []
        self.current_tick = 0        

    def add_building(self, building):
        self.buildings[building.id] = building
        return building

    def connect_buildings(self, infrastructure_layer, from_building, to_building, custom_attributes=None):
        edge = infrastructure_layer.connect_buildings(from_building, to_building, custom_attributes)
        self.edges.append(edge)
        return edge   

    def tick(self):
        self.current_tick += 1

        for building in sorted([b for b in self.buildings.values() if not b.produces and b.status == "active"], key=lambda b: b.priority):
            success = building.tick()
            print(f"{building.id} operational: {success}")

        for building in sorted([b for b in self.buildings.values() if b.produces and b.status == "active"], key=lambda b: b.priority):
            if building.tick():
                print(f"{building.id} produced resources")
                self.distribute_resources(building)

        for edge in self.edges:
            if edge.attributes.get("status", "active") != "destroyed":
                edge.tick()
        
        return self.current_tick    

    def distribute_resources(self, building):
        outgoing_edges = [e for e in self.edges if e.from_node.id == building.id and e.attributes.get("status", "active") != "destroyed"]

        if not outgoing_edges:
            return

        for resource, amount in building.produces.items():
            availible = building.resources.get(resource, 0)
            if availible <= 0:
                continue

            amount_per_edge = min(availible, amount) / len(outgoing_edges)
            
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


# w1 = create_world_from_csv("nodes.csv", "edges.csv")
