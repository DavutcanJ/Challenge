# Davutcan Routing Problem (DRP) Solver

A FastAPI-based microservice that solves the Vehicle Routing Problem using a brute force algorithm. The service optimizes delivery routes for multiple vehicles to minimize total delivery duration.

## Problem Statement

Given:
- **n vehicles** with starting locations and optional capacity constraints
- **m delivery orders** with locations, delivery amounts, and service times
- **Duration matrix** representing travel times between all locations

**Objective**: Find optimal routes that minimize total delivery duration across all vehicles.

**Constraints**:
- Vehicles have infinite stock (no need to return to depot)
- Optional vehicle capacity limits
- Optional service times at delivery locations
- Each job must be assigned to exactly one vehicle

