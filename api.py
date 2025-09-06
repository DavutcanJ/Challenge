from fastapi import FastAPI, HTTPException
from typing import List
from itertools import combinations, permutations
import sys
from input_classes import Job, Vehicle, OutputData, InputData, Route

sys.setrecursionlimit(10000)  # Increase recursion limit for brute force

app = FastAPI(title="Davutcan Route Optimizer", description="Brute force VRP solver , Second Approach")

def compute_route_duration(start: int, job_locs: List[int], matrix: List[List[int]], services: List[int] = None) -> int:
    """
    Compute total duration for a route: travel times + optional service times.
    Args:
        start: Starting location index
        job_locs: List of job location indices in order
        matrix: Duration matrix
        services: List of service times (optional, None if not used)
    Returns:
        Total duration in seconds
    """
    if not job_locs:
        return 0
    
    duration = matrix[start][job_locs[0]]  # Travel to first job
    if services:
        duration += services[0]  # Service time at first job
    
    # Travel between jobs and add service times
    for i in range(len(job_locs) - 1):
        duration += matrix[job_locs[i]][job_locs[i + 1]]
        if services and i + 1 < len(services):
            duration += services[i + 1]
    
    return duration

def is_capacity_feasible(assigned_jobs: List[Job], capacity: int) -> bool:
    """
    Check if total delivery demand <= vehicle capacity.
    Args:
        assigned_jobs: List of Job objects assigned to vehicle
        capacity: Vehicle capacity
    Returns:
        True if feasible, False otherwise
    """
    if capacity is None:  # Infinite capacity
        return True
    
    total_delivery = sum(job.delivery for job in assigned_jobs)
    return total_delivery <= capacity

def brute_force_solve(vehicles: List[Vehicle], jobs: List[Job], matrix: List[List[int]]) -> OutputData:
    """
    Brute force solver
    Args:
        vehicles: List of Vehicle objects
        jobs: List of Job objects
        matrix: Duration matrix
    Returns:
        OutputData with total duration and routes
    """
    if not jobs:
        # If there is no job, no calculation , saves time complexity
        routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}
        return OutputData(total_delivery_duration=0, routes=routes)
    
    job_ids = [j.id for j in jobs]
    job_dict = {j.id: j for j in jobs}  
    n = len(vehicles)
    min_total = float('inf')
    best_routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}

    def partition_jobs(remaining_jobs: List[str], current_assignment: List[List[str]], vehicle_idx: int):
        nonlocal min_total, best_routes
        
        if vehicle_idx == n:
            total_dur = 0
            routes = {}
            feasible = True
            
            for v_idx, (vehicle, assigned_ids) in enumerate(zip(vehicles, current_assignment)):
                assigned_jobs = [job_dict[jid] for jid in assigned_ids]
                
                # Check capacity constraint
                if not is_capacity_feasible(assigned_jobs, vehicle.capacity):
                    feasible = False
                    break
                
                if not assigned_ids:
                    routes[vehicle.id] = Route(jobs=[], delivery_duration=0)
                    continue
                
                # Optimize sequence for this vehicle
                job_locs = [job_dict[jid].location_index for jid in assigned_ids]
                services = [job_dict[jid].service for jid in assigned_ids] if any(job_dict[jid].service > 0 for jid in assigned_ids) else None
                
                min_route_dur = float('inf')
                best_seq = []
                
                # Try all permutations of jobs for this vehicle , find the minimum duration
                for perm in permutations(assigned_ids):
                    perm_locs = [job_dict[jid].location_index for jid in perm]
                    perm_services = [job_dict[jid].service for jid in perm] if services else None
                    dur = compute_route_duration(vehicle.start_index, perm_locs, matrix, perm_services)
                    
                    if dur < min_route_dur:
                        min_route_dur = dur
                        best_seq = list(perm)
                
                total_dur += min_route_dur
                routes[vehicle.id] = Route(jobs=best_seq, delivery_duration=min_route_dur)
            
            if feasible and total_dur < min_total:
                min_total = total_dur
                best_routes = routes
            return

        # Generate all possible subsets for current vehicle
        for k in range(len(remaining_jobs) + 1):
            for subset in combinations(remaining_jobs, k):
                subset_list = list(subset)
                new_remaining = [j for j in remaining_jobs if j not in subset_list]
                partition_jobs(new_remaining, current_assignment + [subset_list], vehicle_idx + 1)

    partition_jobs(job_ids, [], 0)
    
    return OutputData(total_delivery_duration=int(min_total), routes=best_routes)

@app.post("/solve", response_model=OutputData)
async def solve_routes(input_data: InputData):
    """
    POST endpoint to solve  using brute force.
    Args:
        input_data: InputData with vehicles, jobs, and matrix
    Returns:
        OutputData with total delivery duration and routes
    """
    try:
        # Validate input
        if not input_data.vehicles:
            raise ValueError("No vehicles provided")
        
        if not input_data.matrix:
            raise ValueError("Duration matrix is empty")
        
        # Validate matrix size
        max_vehicle_index = max([v.start_index for v in input_data.vehicles], default=-1)
        max_job_index = max([j.location_index for j in input_data.jobs], default=-1)
        max_index = max(max_vehicle_index, max_job_index)
        
        if max_index >= len(input_data.matrix):
            raise ValueError(f"Matrix size ({len(input_data.matrix)}) too small for maximum index ({max_index})")
        
        # Check matrix is square
        for i, row in enumerate(input_data.matrix):
            if len(row) != len(input_data.matrix):
                raise ValueError(f"Matrix row {i} has incorrect length")
        
        # Solve the problem
        result = brute_force_solve(input_data.vehicles, input_data.jobs, input_data.matrix)
        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)