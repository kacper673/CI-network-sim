# Critical Infrastructure Simulator

A simulation framework for modeling interdependencies in critical infrastructure systems.

## Overview

This project provides a dynamic simulation of resource flows (electricity, water, supplies, personnel, data) between interconnected facilities through various infrastructure networks.

## Project Structure

- `models.py` - Core simulation components (resources, layers, edges)
- `buildings.py` - Building classes (hospitals, power plants, magazines)
- `infrastructure.py` - Infrastructure network types (roads, power grid, water, etc.)
- `simulation.py` - Example simulation implementation
- `testUI.py` - Example simulation with UI

## Features

- Multiple building types with unique resource requirements and outputs
- Various infrastructure networks with different capacities and travel times
- Resource production, consumption, and transportation simulation
- Time-based simulation with "tick" advancement
- Singleton infrastructure layers for consistent network management

## Future Development

- Additional building types for comprehensive infrastructure modeling
- Attack and disruption simulation capabilities
- Intelligent resource management algorithms
- Visualization using NetworkX and Matplotlib

## Getting Started

1. Clone the repository
2. Run `simulation.py` or `testUI.py` to see a simple simulation in action
3. Extend with custom building types or infrastructure networks

## Requirements

- Python 3.x
