from pydantic import BaseModel
from typing import List, Dict, Optional

## Pydantic for Input and Output Data Type to Prevent Data MissMatch

class Vehicle(BaseModel):
    id: str
    start: int
    capacity: Optional[int] = float('inf')  # Optional, infinite by default , can be zero 

class Job(BaseModel):
    id: str
    loc: int
    delivery: Optional[int] = 0  # Optional
    service: Optional[int] = 0   # Optional

class InputData(BaseModel):
    vehicles: List[Vehicle]
    jobs: List[Job]
    matrix: List[List[int]]

# Output classes for response
class Route(BaseModel):
    jobs: List[str]
    delivery_duration: int

class OutputData(BaseModel):
    total_delivery_duration: int
    routes: Dict[str, Route]


# Sample Input 
# {
#   "vehicles": [
#     {
#       "id": "V1",
#       "start": 0,
#       "capacity": 10
#     },
#     {
#       "id": "V2",
#       "start": 0,
#       "capacity": 8
#     },
#     {
#       "id": "V3",
#       "start": 0
#     }
#   ],
#   "jobs": [
#     {
#       "id": "J1",
#       "loc": 1,
#       "delivery": 5,
#       "service": 60
#     },
#     {
#       "id": "J2",
#       "loc": 2,
#       "delivery": 3,
#       "service": 30
#     },
#     {
#       "id": "J3",
#       "loc": 3,
#       "delivery": 2,
#       "service": 45
#     }
#   ],
#   "matrix": [
#     [0, 100, 200, 300],
#     [100, 0, 150, 250],
#     [200, 150, 0, 100],
#     [300, 250, 100, 0]
#   ]
# } 