from pydantic import BaseModel
from typing import List, Dict, Optional

class Vehicle(BaseModel):
    id: str
    start_index: int  
    capacity: Optional[int] = None  

class Job(BaseModel):
    id: str
    location_index: int  
    delivery: Optional[int] = 0
    service: Optional[int] = 0

class InputData(BaseModel):
    vehicles: List[Vehicle]
    jobs: List[Job]
    matrix: List[List[int]]

class Route(BaseModel):
    jobs: List[str]
    delivery_duration: int

class OutputData(BaseModel):
    total_delivery_duration: int
    routes: Dict[str, Route]