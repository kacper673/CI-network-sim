from models import Layer

class Infrastructure(Layer):
    """Base class for all infrastructure components"""
    _instances = {}  # Class variable to hold singleton instances
    
    def __new__(cls, *args, **kwargs):
        # Singleton pattern - one instance per layer type
        if cls not in cls._instances:
            cls._instances[cls] = super(Infrastructure, cls).__new__(cls)
        return cls._instances[cls]
    
    def __init__(self, name, supported_resources, default_attributes=None):
        # Only initialize if not already initialized
        if not hasattr(self, 'initialized'):
            super().__init__(name, supported_resources)
            self.default_attributes = default_attributes or {
                "capacity": 100,
                "status": "active",
                "travel_time": 1
            }
            self.initialized = True

    def connect_buildings(self, from_building, to_building, custom_attributes=None):
        """Connect two buildings with this infrastructure layer"""
        attributes = self.default_attributes.copy()
        if custom_attributes:
            attributes.update(custom_attributes)
        attributes.setdefault("layer",self.name)
        return self.connect_nodes(from_building, to_building, attributes)

# Define the infrastructure layer types
class RoadNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Road Network",
            supported_resources=["personnel", "basic_resources", "critical_resources", "heavy_resources"],
            default_attributes={"capacity": 50, "travel_time": 2, "status": "active"}
        )

class EnergyGrid(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Energy Grid",
            supported_resources=["electricity"],
            default_attributes={"capacity": 100, "travel_time": 1, "status": "active"}
        )

class WaterNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Water Network",
            supported_resources=["water"],
            default_attributes={"capacity": 80, "travel_time": 1, "status": "active"}
        )

class RailwayNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Railway Network",
            supported_resources=["heavy_resources", "personnel"],
            default_attributes={"capacity": 200, "travel_time": 4, "status": "active"}
        )

class TelecomNetwork(Infrastructure):
    def __init__(self):
        super().__init__(
            name="Telecom Network",
            supported_resources=["data"],
            default_attributes={"capacity": 1000, "travel_time": 1, "status": "active"}
        )
