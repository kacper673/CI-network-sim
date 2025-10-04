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
        self.road_network = infrastructure.RoadNetwork()
        self.buildings = {}

    def add_building(self, building, id):
        self.buildings[id] = building


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
            new_building.priority = row["priority"]

            world.add_building(new_building, row["id"])


    with open(csv_path_edges, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_id = row["from"]
            to_id = row["to"]
            custom_attributes = json.loads(row["attributes_json"])
            match row["layer"]:
                case "Road Network": world.road_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                case "Energy Grid": world.energy_grid.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                case "Water Network": world.water_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                case "Railway Network": world.railway_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)
                case "Road Network": world.road_network.connect_buildings(world.buildings[from_id], world.buildings[to_id], custom_attributes)

    return world


w1 = create_world_from_csv("nodes.csv", "edges.csv")
