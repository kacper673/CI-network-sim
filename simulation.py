from pdb import run
from csv_world_import import World
from buildings import Hospital, PowerPlant, Magazine, DataCenter, WaterPlant
from infrastructure import RoadNetwork, EnergyGrid, WaterNetwork, TelecomNetwork, RailwayNetwork

def create_simple_world():
    world = World()

    world.infrastructure_networks = {
        world.road_network.name: world.road_network,
        world.energy_grid.name: world.energy_grid,
        world.water_network.name: world.water_network,
        world.railway_network.name: world.railway_network,
        world.telecom_network.name: world.telecom_network 
    }

    power_plant = world.add_building(PowerPlant(
        id="POWER_001",
        resources={"water": 100},
        production={"electricity": 25}
    ))
    
    water_plant = world.add_building(WaterPlant(
        id="WATER_001",
        resources={"electricity": 0},
        consumption={"electricity": 8},
        production={"water": 20}
    ))
    
    data_center = world.add_building(DataCenter(
        id="DATA_001",
        resources={"electricity": 0, "water": 0},
        consumption={"electricity": 12, "water": 5},
        production={"data": 30}
    ))
    
    magazine = world.add_building(Magazine(
        id="MAG_001",
        resources={"electricity": 0, "basic_resources": 200},
        consumption={"electricity": 3},
        production={"basic_resources": 15}
    ))

    hospital_1 = world.add_building(Hospital(
        id="HOSP_001",
        resources={"electricity": 0, "water": 0, "basic_resources": 50},
        consumption={"electricity": 10, "water": 8, "basic_resources": 5}
    ))
    
    hospital_2 = world.add_building(Hospital(
        id="HOSP_002",
        resources={"electricity": 0, "water": 0, "basic_resources": 30},
        consumption={"electricity": 8, "water": 6, "basic_resources": 7}
    ))

    # Power plant connections
    world.connect_buildings(world.energy_grid, power_plant, water_plant)
    world.connect_buildings(world.energy_grid, power_plant, data_center)
    world.connect_buildings(world.energy_grid, power_plant, magazine)
    world.connect_buildings(world.energy_grid, power_plant, hospital_1)
    world.connect_buildings(world.energy_grid, power_plant, hospital_2)
    
    # Water plant connections
    world.connect_buildings(world.water_network, water_plant, power_plant, {"travel_time": 2})
    world.connect_buildings(world.water_network, water_plant, data_center, {"travel_time": 3})
    world.connect_buildings(world.water_network, water_plant, hospital_1, {"travel_time": 2})
    world.connect_buildings(world.water_network, water_plant, hospital_2, {"travel_time": 4})

    # Data center connections (data)
    telecom_network = world.infrastructure_networks.get("Telecom Network")
    if not telecom_network:
        # If Telecom Network not in dict, create it
        telecom_network = TelecomNetwork()
        world.infrastructure_networks[telecom_network.name] = telecom_network
    
    world.connect_buildings(telecom_network, data_center, hospital_1)
    world.connect_buildings(telecom_network, data_center, hospital_2)
    
    # Magazine connections (basic_resources)
    world.connect_buildings(world.road_network, magazine, hospital_1, {"travel_time": 3})
    world.connect_buildings(world.road_network, magazine, hospital_2, {"travel_time": 5})

    return world

def run_sim():
    world = create_simple_world()
    
    print("=== INITIAL STATE ===")
    for building_id, building in world.buildings.items():
        print(f"{building_id}: {building.resources}")
    
    # Run for 20 ticks
    world.run(ticks=20)
    
    print("\n=== FINAL STATE ===")
    for building_id, building in world.buildings.items():
        print(f"{building_id}: Status={building.status}, Resources={building.resources}")

if __name__ == "__main__":
    run_sim()