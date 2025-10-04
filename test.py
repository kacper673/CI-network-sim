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

        self.requires = requires
        self.produces = produces

        self.status = "active" # active offline destroyed

        self.input_supply = {}

class Hospital(Building):
    def __init__(self, id, basic_resources, consumption_per_tick):
        super().__init__(id=id)
        self.basic_resources = basic_resources
        self.consumption_per_tick = consumption_per_tick        

    def tick(self):
        if self.basic_resources >= self.consumption_per_tick:
            self.basic_resources -= self.consumption_per_tick
            return True
        else:            
            self.basic_resources = 0
            return False        

    def receive_supplies(self, amount):        
        self.basic_resources += amount            

class Magazine(Building):
    def __init__(self, id, basic_resources, supply_per_tick):
        super().__init__(id=id)
        self.basic_resources = basic_resources
        self.supply_per_tick = supply_per_tick

    def tick(self):        
        if self.basic_resources >= self.supply_per_tick:
            self.basic_resources -= self.supply_per_tick
            return self.supply_per_tick
        else:            
            return 0
            
class Road(Layer):
    def __init__(self, name, resource_type, state, capacity, status, travel_time):
        super().__init__(name=name, resource_type=resource_type)
        # self.resource_type = ["personnel", "basic_resources"]
        self.state = state
        self.capacity = capacity
        self.status = status            
        self.travel_time = travel_time
        self.supplies_in_transit = []

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
    print("Symulator")

    hospital = Hospital(id = "HOSP_001", basic_resources=100, consumption_per_tick=10)    

    magazine = Magazine(id = "MAG_001", basic_resources=500, supply_per_tick=10)    

    road = Road(name = "ROAD_001", resource_type = ["personnel", "basic_resources"], state="good", capacity=50, status="active", travel_time=3)    

    for tick in range(1, 11):
        print(f"Tick: {tick}")

        hospital_success = hospital.tick()
        print(f"Hospital {hospital.id} consumed {hospital.consumption_per_tick} resources")
        print(f"Hospital {hospital.id} resources: {hospital.basic_resources}")
        
        # Magazine supplies resources
        supply_amount = magazine.tick()
        print(f"Magazine {magazine.id} supplied {supply_amount} resources")
        print(f"Magazine {magazine.id} resources: {magazine.basic_resources}")
        
        # Road processes transit
        if supply_amount > 0:
            road.send_supplies(supply_amount)
        
        arrived_supplies = road.tick()
        if arrived_supplies > 0:
            hospital.receive_supplies(arrived_supplies)
            print(f"Supplies arrived at hospital {hospital.id}: {arrived_supplies}")
        
        print(f"Supplies in transit: {len(road.supplies_in_transit)}")

if __name__ == "__main__":
    simulate()