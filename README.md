# Critical Infrastructure Resilience Simulator
# HackYeah 2025 Hackathon project 

A comprehensive framework for modeling interdependencies, vulnerabilities, and attack scenarios in critical infrastructure systems.

## Overview

This project simulates resource flows (electricity, water, supplies, personnel, data) between interconnected facilities through various infrastructure networks. It models building operations, resource consumption/production, and infrastructure status while accounting for cascading effects during normal operations and crisis scenarios.

## Project Structure

- `models.py` - Core simulation components (resources, layers, edges)
- `buildings.py` - Building classes with unique resource requirements and outputs
- `infrastructure.py` - Infrastructure network types with singleton pattern
- `csv_world_import.py` - World management and CSV import/export utilities
- `simulation.py` - Simulation scenarios and attack/recovery implementations
- `testUI.py` - Visualization interface using NetworkX
- `graphsGUI.py` - More complex visualization interface using pyQT

## Features

- Diverse building types (hospitals, power plants, data centers, etc.)
- Multiple infrastructure network types with varying capacities
- Resource production, consumption, and transportation simulation
- Building and infrastructure damage/recovery modeling
- Attack simulation with variable severity levels
- Status tracking for all components
- CSV import/export for scenario management
- Visualization capabilities

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install pandas networkx matplotlib`
3. Run `python simulation.py` to execute a sample simulation
4. Or run `python csv_world_import.py` to load from CSV files
5. Or run `testUI.py` to run sample simulation with UI
6. Or run `graphsGUI.py` to run a simulation with more advanced UI

## Extending the System

- Add new building types in `buildings.py`
- Create custom scenarios in `simulation.py`
- Define custom attacks and recoveries using the World class methods
- Let user create custom buildings, infrastructure and resources

## Requirements

- Python 3.x
- pandas
- networkx
- matplotlib
- pyQT
