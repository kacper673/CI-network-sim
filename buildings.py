from itertools import product
from models import RESOURCE_TYPES

class Building:
    def __init__(self, id, requires=None, produces=None, priority=1):
        self.id = id
        self.priority = priority
        self.requires = requires or {}
        self.produces = produces or {}
        self.status = "active"  # active, offline, destroyed
        self.resources = {resource: 0 for resource in RESOURCE_TYPES}

    def works(self) -> bool:
        for resource, amount in self.requires.items():
            if self.resources.get(resource, 0) < amount:
                return False
        return True

    def update_status(self):

        if self.works():
            self.status = "active"
            return
        
        self.status = "offline"
        
    def tick(self):
        """Base tick method to be implemented by subclasses"""
        # Check if all required resources are available
        for resource, amount in self.requires.items():
            if self.resources[resource] < amount:
                return False
        
        # Consume required resources
        for resource, amount in self.requires.items():
            self.resources[resource] -= amount
            
        return True
        
    def receive_supplies(self, resource_type, amount):
        """Generic method to receive supplies of any resource type"""
        if resource_type in RESOURCE_TYPES:
            self.resources[resource_type] += amount

class Hospital(Building):
    def __init__(self, id, resources=None, consumption=None, priority=1):
        resources = resources or {}
        consumption = consumption or {"electricity": 5, "water": 3, "basic_resources": 10}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces={},
            priority=priority
        )
        
        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount

class PowerPlant(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=2):
        resources = resources or {}
        consumption = consumption or {"water": 5}
        production = production or {"electricity": 20}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )
        
        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount
            
    def tick(self):
        if super().tick():
            # Produce resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False

class Magazine(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=2):
        resources = resources or {}
        consumption = consumption or {"electricity": 3}
        production = production or {"basic_resources": 10}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )
        
        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount
            
    def tick(self):
        if super().tick():
            # Produce resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False

class DataCenter(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=2):
        resources = resources or {}
        consumption = consumption or {"electricity": 15, "water": 8}
        production = production or {"data": 30} 

        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )

        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount

    def tick(self):
        if super().tick():
            # Produce data resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False

class WaterPlant(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=1):
        resources = resources or {}
        consumption = consumption or {"electricity": 8}
        production = production or {"water": 25}

        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )

        # Initialize resources
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount

    def tick(self):
        if super().tick():
            # Produce water
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False        

class Factory(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=3):
        resources = resources or {}
        consumption = consumption or {"electicity": 12, "water": 7, "basic_resources": 15}
        production = production or {"heavy_resources": 8}

        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )

        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount

    def tick(self):
        if super().tick():
            # produce heavy resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False

class EmergencyCenter(Building):
    def __init__(self, id, resources=None, consumption=None, production=None, priority=1):
        resources = resources or {}
        consumption = consumption or {"electricity": 6, "water": 4, "basic_resources": 5}
        production = production or {"personnel": 10, "critical_resources": 5}
        
        super().__init__(
            id=id,
            requires=consumption,
            produces=production,
            priority=priority
        )
                
        for resource_type, amount in resources.items():
            self.resources[resource_type] = amount
            
    def tick(self):
        if super().tick():
            # Produce personnel and critical resources
            for resource, amount in self.produces.items():
                self.resources[resource] += amount
            return True
        return False