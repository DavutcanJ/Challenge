# Davutcan Routing Problem (DRP) Solver

A FastAPI-based microservice that solves the Vehicle Routing Problem using a brute force algorithm. The service optimizes delivery routes for multiple vehicles to minimize total delivery duration. I used both brute force and OR-Tools solving method , just send the information of solver as parameter 

(POST http://localhost:8000/solve?solver=brute_force)
(POST http://localhost:8000/solve?solver=or_tools)


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


**Try Yourself**
- Instead of vehicle_1 and job_1 you can just use index (0,1,2,3) , its just for visual check
- curl -X POST "http://localhost:8000/solve?solver=brute_force" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicles": [
      {
        "id": "vehicle_1",
        "start_index": 0,
        "capacity": 100
      },
      {
        "id": "vehicle_2",
        "start_index": 0,
        "capacity": 150
      }
    ],
    "jobs": [
      {
        "id": "job_1",
        "location_index": 1,
        "delivery": 30,
        "service": 300
      },
      {
        "id": "job_2",
        "location_index": 2,
        "delivery": 40,
        "service": 600
      },
      {
        "id": "job_3",
        "location_index": 3,
        "delivery": 25,
        "service": 450
      }
    ],
    "matrix": [
      [0, 600, 900, 1200],
      [600, 0, 300, 800],
      [900, 300, 0, 400],
      [1200, 800, 400, 0]
    ]
  }'

- Expected Outcome 
    {
    "total_delivery_duration":2650,
    "routes":{
    "vehicle_1":{
        "jobs":["job_1","job_2","job_3"],
        "delivery_duration":2650},
    "vehicle_2":{
        "jobs":[],
        "delivery_duration":0}
    }
    }