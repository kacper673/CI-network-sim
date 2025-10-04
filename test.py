class Layer:
    def __init__(self, name, resource_type):
        self.name = name
        self.resource_type = resource_type
        self.nodes = set()
        self.edges = []

class Edge:
    def __init__(self, from_node, to_node, attributes):
        self.from_node = from_node
        self.to_node = to_node
        self.attributes = attributes # ex. dict: {"capacity": 100, "status": "active"}

class Bulding:
    def __init__(self, id, requires=None, produces=None, priority=1):
        self.id = id

        self.priority = priority

        self.requires = requires
        self.produces = produces

        self.status = "active" # active offline 