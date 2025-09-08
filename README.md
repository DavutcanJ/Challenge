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

**Implementations**
- Assumed Matrix Input 

    Vehicle0 -->[0, 600, 900, 1200],    
    Vehicle1    [600, 0, 300, 800],     
    Vehicle2    [900, 300, 0, 400],      
    Vehicle3    [1200, 800, 400, 0]

    D0             D1       
    * -- (600m) -- *      
    Vehicle0     

    D0             D2      
    * -- (900m) -- *
    Vehicle0

    D0             D3          
    * -- (1200m)--  * 
    Vehicle0

-   Based on this structure when job and the duration matrix comes, algorithm runs and calculate each job to vehicle route and gives us a permutation of every possible route. In this scenario it picks the smallest duration route, job_id and vehicle id and assigns the job to its vehcile with smallest duration.



**Improvements**

- Because of brute force , all jobs may be assigned to one vehicle because if one vehicle moves to another destination while carrying other packages, its easier to work with only one because of the routing. This one vehicle focused approach may be improve in future.