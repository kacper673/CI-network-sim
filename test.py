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
    def __init__(self, basic_resources, consumption_per_tick):
        super().__init__()
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
    def __init__(self, basic_resources, supply_per_tick):
        super().__init__()
        self.basic_resources = basic_resources
        self.supply_per_tick = supply_per_tick

    def tick(self):        
        if self.basic_resources >= self.supply_per_tick:
            self.basic_resources -= self.supply_per_tick
            return self.supply_per_tick
        else:            
            return 0
            
class Road(Layer):
    def __init__(self, state, capacity, status):
        super().__init__()
        self.resource_type = ["personnel", "basic_resources"]
        self.state = state
        self.capacity = capacity
        self.status = status            