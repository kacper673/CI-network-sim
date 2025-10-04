RESOURCE_TYPES = [
    
]


class Layer:
    def __init__(self, name, resource_type):
        self.name = name
        self.resource_type = resource_type        
        self.edges = []

class Edge:
    def __init__(self, from_node, to_node, attributes):
        self.from_node = from_node
        self.to_node = to_node
        self.attributes = attributes # ex. dict: {"capacity": 100, "status": "active"}

class Building:
    def __init__(self, id, requires=None, produces=None, priority=1):
        self.id = id
        self.priority = priority
        self.requires = requires or {}
        self.produces = produces or {}
        self.status = "active" # active offline destroyed
        self.input_supply = {}

    def tick(self):
        pass

    def receive_supplies(self, resource_type, amount):
        if resource_type not in self.input_supply:
            self.input_supply[resource_type] = 0
        self.input_supply[resource_type] += amount

class Hospital(Building):
    def __init__(self, id, basic_resources=0, consumption_per_tick=0, electricity_required=5, priority=1):
        super().__init__(
            id=id,
            requires={"electricity": electricity_required, "basic_resources": consumption_per_tick},
            produces={},
            priority=priority
            )
        self.basic_resources = basic_resources
        self.consumption_per_tick = consumption_per_tick        

    def tick(self):
        if self.basic_resources >= self.consumption_per_tick:
            self.basic_resources -= self.consumption_per_tick
            return True
        else:            
            self.basic_resources = 0
            return False        

    def receive_supplies(self, resource_type, amount):
        super().receive_supplies(resource_type, amount)
        if resource_type == "basic_resources":
            self.basic_resources += amount            

class Magazine(Building):
    def __init__(self, id, basic_resources=0, production_per_tick=0, electricity_required=3, priority=2):
        super().__init__(
            id=id,
            requires={"electricity": electricity_required},
            produces={"basic_resources": production_per_tick},
            priority=priority
            )
        self.basic_resources = basic_resources
        self.production_per_tick = production_per_tick

    def tick(self):        
        if self.basic_resources >= self.production_per_tick:
            self.basic_resources -= self.production_per_tick
            return self.production_per_tick
        else:            
            return 0
            
class Infrastructure(Layer):
    def __init__(self, name, resource_type, state="good", capacity=0, status="active"):
        super().__init__(name, resource_type)
        self.state = state  # good, damaged, destroyed
        self.capacity = capacity
        self.status = status  # active, offline
        
    def connect_buildings(self, from_building, to_building, attributes=None):        
        edge_attributes = attributes or {}
        edge_attributes.update({
            "capacity": self.capacity,
            "status": self.status,
        })
        
        edge = Edge(
            from_node=from_building,
            to_node=to_building,
            attributes=edge_attributes
        )
        self.edges.append(edge)
        return edge

class Road(Infrastructure):
    def __init__(self, name, resource_type, state="good", capacity=0, status="active", travel_time=1):
        super().__init__(
            name=name,
            resource_type=resource_type,
            state=state,
            capacity=capacity,
            status=status
        )
        self.travel_time = travel_time
        self.supplies_in_transit = []
        
    def connect_buildings(self, from_building, to_building):
        return super().connect_buildings(from_building, to_building, {
            "travel_time": self.travel_time
        })
        
    def send_supplies(self, amount):        
        self.supplies_in_transit.append({
            'amount': amount,
            'ticks_remaining': self.travel_time
        })
    
    def tick(self):        
        arrived_supplies = 0
        for supply in self.supplies_in_transit[:]:
            supply['ticks_remaining'] -= 1
            if supply['ticks_remaining'] <= 0:
                arrived_supplies += supply['amount']
                self.supplies_in_transit.remove(supply)
        return arrived_supplies    

def simulate():
    print("Simulator")

    hospital = Hospital(id = "HOSP_001", basic_resources=100, consumption_per_tick=10)
    magazine = Magazine(id = "MAG_001", basic_resources=500, production_per_tick=10)
    road = Road(name = "ROAD_001", resource_type = ["personnel", "basic_resources"], state="good", capacity=50, status="active", travel_time=3)    

    road.connect_buildings(magazine, hospital)

    for tick in range(1, 11):
        print(f"Tick: {tick}")

        hospital_success = hospital.tick()
        print(f"Hospital {hospital.id} consumed {hospital.consumption_per_tick} resources")
        print(f"Hospital {hospital.id} resources: {hospital.basic_resources}")
        
        # Magazine supplies resources
        produced_amount = magazine.tick()
        print(f"Magazine {magazine.id} supplied {produced_amount} resources")
        print(f"Magazine {magazine.id} resources: {magazine.basic_resources}")
        
        # Road processes transit
        if produced_amount > 0:
            road.send_supplies(produced_amount)
        
        arrived_supplies = road.tick()
        if arrived_supplies > 0:
            hospital.receive_supplies("basic_resources", arrived_supplies)
            print(f"Supplies arrived at hospital {hospital.id}: {arrived_supplies}")
        
        print(f"Supplies in transit: {len(road.supplies_in_transit)}")

if __name__ == "__main__":
    simulate()