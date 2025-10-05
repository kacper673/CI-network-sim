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
        if self.attributes.get("status") == "destroyed":
            return False

        if self.from_node.resources.get(resource_type, 0) < amount:
            return False       

        capacity_factor = 1.0
        if self.attributes.get("status") == "damaged":
            capacity_factor = 0.5

        max_amount = amount
        if "capacity" in self.attributes:
            max_amount = min(amount, self.attributes["capacity"] * capacity_factor)
            
        travel_time = self.attributes.get("travel_time", 1)
        if self.attributes.get("status") == "damaged":
            travel_time = int(travel_time * 1.5)
            
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
