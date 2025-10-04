from buildings import Hospital, PowerPlant, Magazine
from infrastructure import RoadNetwork, EnergyGrid

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

    for tick in range(1, 11):
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

if __name__ == "__main__":
    simulate()