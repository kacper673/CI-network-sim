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

        for building in self.buildings.values():
            building.update_status()

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

    def execute_attack(self, target_id=None, severity=0.5):
        attacked_something = False
        
        if target_id in self.buildings:
            building = self.buildings[target_id]
            old_status = building.status

            if severity > 0.8:
                building.status = "destroyed"
                building.efficiency = 0.0
            elif severity > 0.5:
                building.status = "offline"
                building.efficiency = 0.2
            else:
                building.status = "degraded"
                building.efficiency = 1.0 - severity
                
                for resource in building.resources:
                    building.resources[resource] *= int((1 - severity))

            print(f"Attack on {building.id}: {old_status} -> {building.status}")  
            attacked_sth = True

        for edge in self.edges:
        # Match by layer name, or if edge connects to/from target
            if (edge.attributes.get("layer") == target_id or 
                edge.from_node.id == target_id or 
                edge.to_node.id == target_id):

                old_status = edge.attributes.get("status", "active")

                if severity > 0.8:
                    edge.attributes["status"] = "destroyed"
                elif severity > 0.5:
                    edge.attributes["status"] = "damaged"
                    # Store original capacity if not already stored
                    if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                        edge.attributes["original_capacity"] = edge.attributes["capacity"]
                    # Reduce capacity
                    if "capacity" in edge.attributes:
                        edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))
                else:
                    # Just reduce capacity
                    if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                        edge.attributes["original_capacity"] = edge.attributes["capacity"]
                    if "capacity" in edge.attributes:
                        edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))

                print(f"Attack on {edge.attributes.get('layer', 'unknown')} connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                attacked_something = True

        if not attacked_something and "-" in target_id:
            parts = target_id.split("-")
            if len(parts) == 2:
                from_id, to_id = parts
                for edge in self.edges:
                    if edge.from_node.id == from_id and edge.to_node.id == to_id:
                        old_status = edge.attributes.get("status", "active")

                        if severity > 0.8:
                            edge.attributes["status"] = "destroyed"
                        elif severity > 0.5:
                            edge.attributes["status"] = "damaged"
                            # Store original capacity if not already stored
                            if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                                edge.attributes["original_capacity"] = edge.attributes["capacity"]
                            # Reduce capacity
                            if "capacity" in edge.attributes:
                                edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))
                        else:
                            # Just reduce capacity
                            if "original_capacity" not in edge.attributes and "capacity" in edge.attributes:
                                edge.attributes["original_capacity"] = edge.attributes["capacity"]
                            if "capacity" in edge.attributes:
                                edge.attributes["capacity"] = int(edge.attributes["capacity"] * (1 - severity))
                    
                        print(f"Attack on connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                        attacked_something = True

        if not attacked_something:
            print(f"No valid target found for attack")
        
        return attacked_something

    def execute_recovery(self, target_id=None, repair_level=0.8):
        recovered_something = False
    
        # Recover a specific building
        if target_id in self.buildings:
            building = self.buildings[target_id]
            old_status = building.status

            # Can't recover destroyed buildings
            if building.status != "destroyed":
                if repair_level > 0.8:
                    building.status = "active"
                    building.efficiency = 1.0
                else:
                    building.status = "degraded"
                    building.efficiency = repair_level

                print(f"Recovery of {building.id}: {old_status} -> {building.status}")
                recovered_something = True
            else:
                print(f"Cannot recover destroyed building {building.id}")

        # Recover infrastructure connection
        for edge in self.edges:
            # Match by layer name, or if edge connects to/from target
            if (edge.attributes.get("layer") == target_id or 
                edge.from_node.id == target_id or 
                edge.to_node.id == target_id):

                old_status = edge.attributes.get("status", "active")

                # Can't recover destroyed infrastructure
                if old_status != "destroyed":
                    if repair_level > 0.8:
                        edge.attributes["status"] = "active"
                        # Restore original capacity if available
                        if "original_capacity" in edge.attributes:
                            edge.attributes["capacity"] = edge.attributes["original_capacity"]
                    else:
                        # Improve but not fully recover
                        if old_status == "damaged":
                            if "original_capacity" in edge.attributes:
                                edge.attributes["capacity"] = int(edge.attributes["original_capacity"] * repair_level)

                    print(f"Recovery of {edge.attributes.get('layer', 'unknown')} connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                    recovered_something = True
                else:
                    print(f"Cannot recover destroyed connection {edge.from_node.id}->{edge.to_node.id}")

        # Check for specific edge format "from-to"
        if not recovered_something and "-" in target_id:
            parts = target_id.split("-")
            if len(parts) == 2:
                from_id, to_id = parts
                for edge in self.edges:
                    if edge.from_node.id == from_id and edge.to_node.id == to_id:
                        old_status = edge.attributes.get("status", "active")

                        # Can't recover destroyed infrastructure
                        if old_status != "destroyed":
                            if repair_level > 0.8:
                                edge.attributes["status"] = "active"
                                # Restore original capacity if available
                                if "original_capacity" in edge.attributes:
                                    edge.attributes["capacity"] = edge.attributes["original_capacity"]
                            else:
                                # Improve but not fully recover
                                if old_status == "damaged":
                                    if "original_capacity" in edge.attributes:
                                        edge.attributes["capacity"] = int(edge.attributes["original_capacity"] * repair_level)

                            print(f"Recovery of connection {edge.from_node.id}->{edge.to_node.id}: {old_status} -> {edge.attributes.get('status', 'active')}")
                            recovered_something = True
                        else:
                            print(f"Cannot recover destroyed connection {edge.from_node.id}->{edge.to_node.id}")

        if not recovered_something:
            print(f"No valid target found for recovery: {target_id}")

        return recovered_something

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
                case "WaterPlant": new_building = buildings.WaterPlant(row["id"])
                case "DataCenter": new_building = buildings.DataCenter(row["id"])

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
