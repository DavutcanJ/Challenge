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
    """
    if capacity is None:  # Infinite capacity
        return True
    
    total_delivery = sum(job.delivery for job in assigned_jobs)
    print(f"  📊 Kapasite kontrolü: {total_delivery}/{capacity}")
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
    print(f"🔍 DEBUG: {len(vehicles)} Vehicle, {len(jobs)} job taken")
    
    for vehicle in vehicles:
        print(f"🚗 Vehicle: ID={vehicle.id}, start_index={vehicle.start_index}, capacity={vehicle.capacity}")
    
    for job in jobs:
        print(f"📦 Job: ID={job.id}, location_index={job.location_index}, delivery={job.delivery}, service={job.service}")
    
    if not jobs:
        print("⚠️  Empty Job Input!")
        routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}
        return OutputData(total_delivery_duration=0, routes=routes)
    
    job_ids = [j.id for j in jobs]
    job_dict = {j.id: j for j in jobs}
    n_vehicles = len(vehicles)
    min_total = float('inf')
    best_routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}

    print(f"🔄 Trying every possible route for ... ({n_vehicles} vehicle)")
    
    def generate_all_assignments(job_list, num_vehicles):
        """
        İşlerin atanması için tüm rotaları dener
        """
        if not job_list:
            yield [[] for _ in range(num_vehicles)]
            return
        
        first_job = job_list[0]
        remaining_jobs = job_list[1:]
        
        # Assing the first job to every vehicle 
        for vehicle_idx in range(num_vehicles):
            for assignment in generate_all_assignments(remaining_jobs, num_vehicles):
                assignment[vehicle_idx].append(first_job)
                yield assignment

    assignment_count = 0
    best_assignment = None
    
    for assignment in generate_all_assignments(job_ids, n_vehicles):
        assignment_count += 1
        
        total_duration = 0
        routes = {}
        feasible = True
        
        # Calculate every route for every vehicle
        for vehicle_idx, vehicle in enumerate(vehicles):
            assigned_job_ids = assignment[vehicle_idx]
            assigned_jobs = [job_dict[jid] for jid in assigned_job_ids]
            
            # Capacity check
            if not is_capacity_feasible(assigned_jobs, vehicle.capacity):
                feasible = False
                break
            
            if not assigned_job_ids:
                # Empty car
                routes[vehicle.id] = Route(jobs=[], delivery_duration=0)
                continue
            
            # Find the best sequence
            min_route_duration = float('inf')
            best_sequence = []
            
            # Check all permutations
            for perm in permutations(assigned_job_ids):
                perm_jobs = [job_dict[jid] for jid in perm]
                perm_locs = [job.location_index for job in perm_jobs]
                perm_services = [job.service for job in perm_jobs]
                
                duration = compute_route_duration(
                    vehicle.start_index, 
                    perm_locs, 
                    matrix, 
                    perm_services
                )
                
                if duration < min_route_duration:
                    min_route_duration = duration
                    best_sequence = list(perm)
            
            total_duration += min_route_duration
            routes[vehicle.id] = Route(jobs=best_sequence, delivery_duration=min_route_duration)
        
        if feasible and total_duration < min_total:
            min_total = total_duration
            best_routes = routes
            best_assignment = assignment
            print(f"✅ Found a better one ! Total Duration: {min_total} second")
            
            # Print the best sequence
            for vehicle_idx, vehicle in enumerate(vehicles):
                assigned = assignment[vehicle_idx]
                if assigned:
                    print(f"  🚗 {vehicle.id}: {assigned}")
                else:
                    print(f"  🚗 {vehicle.id}: Empty")
    
    print(f"🏁 Total of  {assignment_count} sequence tried")
    print(f"🎯 Best duration: {min_total} second")
    
    if min_total == float('inf'):
        print("❌ No solution found !")
        return OutputData(total_delivery_duration=0, routes={v.id: Route(jobs=[], delivery_duration=0) for v in vehicles})
    
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


def simple_test():
    """
    Simple Test
    """
    vehicles = [
        Vehicle(id="v1", start_index=0, capacity=100),
        Vehicle(id="v2", start_index=0, capacity=100)
    ]
    
    jobs = [
        Job(id="j1", location_index=1, delivery=30, service=300),
        Job(id="j2", location_index=2, delivery=40, service=600)
    ]
    
    matrix = [
        [0, 600, 900],    # Depot
        [600, 0, 300],    # Nokta 1
        [900, 300, 0]     # Nokta 2
    ]
    
    result = brute_force_solve(vehicles, jobs, matrix)
    

    print(f"   Total Duration: {result.total_delivery_duration} second")
    for vehicle_id, route in result.routes.items():
        print(f"   {vehicle_id}: {route.jobs} - {route.delivery_duration} second")
    
    return result

if __name__ == "__main__":
    import uvicorn
    simple_test()
    uvicorn.run(app, host="0.0.0.0", port=8000)
