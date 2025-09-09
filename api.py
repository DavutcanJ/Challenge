from fastapi import FastAPI, HTTPException
from typing import List, Optional
from itertools import combinations, permutations
import sys
from input_classes import Job, Vehicle, OutputData, InputData, Route
from enum import Enum

# Google OR-tools import
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("⚠️  Google OR-tools not installed. Only brute force solver available.")
    print("Install with: pip install ortools")

sys.setrecursionlimit(10000)

app = FastAPI(
    title="DRP Solver Microservice", 
    description="Vehicle Routing Problem solver with BruteForce and Google OR-Tools algorithms",
    version="1.0.0"
)

class SolverType(str, Enum):
    BRUTE_FORCE = "brute_force"
    OR_TOOLS = "or_tools"

def compute_route_duration(start: int, job_locs: List[int], matrix: List[List[int]], services: List[int] = None) -> int:
    """
    Compute total duration for a route: travel times + optional service times.
    """
    if not job_locs:
        return 0
    
    duration = matrix[start][job_locs[0]]
    if services:
        duration += services[0]
    
    for i in range(len(job_locs) - 1):
        duration += matrix[job_locs[i]][job_locs[i + 1]]
        if services and i + 1 < len(services):
            duration += services[i + 1]
    
    return duration

def is_capacity_feasible(assigned_jobs: List[Job], capacity: Optional[int]) -> bool:
    """
    Check if total delivery demand <= vehicle capacity.
    """
    if capacity is None:
        return True
    
    total_delivery = sum(job.delivery for job in assigned_jobs)
    return total_delivery <= capacity

def brute_force_solve(vehicles: List[Vehicle], jobs: List[Job], matrix: List[List[int]]) -> OutputData:
    """
    Brute force solver - original implementation
    """
    print(f"BRUTE FORCE: {len(vehicles)} vehicles, {len(jobs)} jobs")
    
    if not jobs:
        routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}
        return OutputData(total_delivery_duration=0, routes=routes)
    
    job_ids = [j.id for j in jobs]
    job_dict = {j.id: j for j in jobs}
    n_vehicles = len(vehicles)
    min_total = float('inf')
    best_routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}

    def generate_all_assignments(job_list, num_vehicles):
        """
        Generate all possible job assignments to vehicles
        """
        if not job_list:
            yield [[] for _ in range(num_vehicles)]
            return
        
        first_job = job_list[0]
        remaining_jobs = job_list[1:]
        
        for vehicle_idx in range(num_vehicles):
            for assignment in generate_all_assignments(remaining_jobs, num_vehicles):
                assignment[vehicle_idx].append(first_job)
                yield assignment

    assignment_count = 0
    
    for assignment in generate_all_assignments(job_ids, n_vehicles):
        assignment_count += 1
        
        total_duration = 0
        routes = {}
        feasible = True
        
        for vehicle_idx, vehicle in enumerate(vehicles):
            assigned_job_ids = assignment[vehicle_idx]
            assigned_jobs = [job_dict[jid] for jid in assigned_job_ids]
            
            if not is_capacity_feasible(assigned_jobs, vehicle.capacity):
                feasible = False
                break
            
            if not assigned_job_ids:
                routes[vehicle.id] = Route(jobs=[], delivery_duration=0)
                continue
            
            min_route_duration = float('inf')
            best_sequence = []
            
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
    
    print(f"Tested {assignment_count} assignments, best: {min_total}s")
    
    if min_total == float('inf'):
        return OutputData(
            total_delivery_duration=0, 
            routes={v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}
        )
    
    return OutputData(total_delivery_duration=int(min_total), routes=best_routes)

def or_tools_solve(vehicles: List[Vehicle], jobs: List[Job], matrix: List[List[int]]) -> OutputData:
    """
    Google OR-tools solver implementation
    """
    if not ORTOOLS_AVAILABLE:
        raise HTTPException(status_code=400, detail="Google OR-tools not installed")
    
    print(f"🚀 OR-TOOLS: {len(vehicles)} vehicles, {len(jobs)} jobs")
    
    if not jobs:
        routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}
        return OutputData(total_delivery_duration=0, routes=routes)
    
    # Create data model
    data = {}
    
    # Locations: depot + job locations
    all_locations = [v.start_index for v in vehicles]  # Vehicle starting points
    job_locations = [j.location_index for j in jobs]   # Job locations
    
    # Create location mapping
    location_to_index = {}
    index_to_location = {}
    current_index = 0
    
    # Add vehicle depots
    depot_indices = []
    for vehicle in vehicles:
        if vehicle.start_index not in location_to_index:
            location_to_index[vehicle.start_index] = current_index
            index_to_location[current_index] = vehicle.start_index
            current_index += 1
        depot_indices.append(location_to_index[vehicle.start_index])
    
    # Add job locations
    job_indices = []
    for job in jobs:
        if job.location_index not in location_to_index:
            location_to_index[job.location_index] = current_index
            index_to_location[current_index] = job.location_index
            current_index += 1
        job_indices.append(location_to_index[job.location_index])
    
    num_locations = current_index
    num_vehicles = len(vehicles)
    
    # Build distance matrix for OR-tools
    or_matrix = [[0 for _ in range(num_locations)] for _ in range(num_locations)]
    
    for i in range(num_locations):
        for j in range(num_locations):
            orig_i = index_to_location[i]
            orig_j = index_to_location[j]
            or_matrix[i][j] = matrix[orig_i][orig_j]
    
    data['distance_matrix'] = or_matrix
    data['num_vehicles'] = num_vehicles
    data['depot'] = depot_indices[0]  # Use first depot as main depot
    data['starts'] = depot_indices     # Different start points for vehicles
    data['ends'] = depot_indices       # Can end anywhere, but we'll handle this
    
    # Add demands and capacities
    demands = [0]  # Depot has 0 demand
    for job in jobs:
        demands.append(job.delivery)
    
    # Pad demands to match number of locations
    while len(demands) < num_locations:
        demands.append(0)
    
    data['demands'] = demands
    data['vehicle_capacities'] = [v.capacity if v.capacity is not None else 9999 for v in vehicles]
    
    # Add service times
    service_times = [0]  # Depot has 0 service time
    for job in jobs:
        service_times.append(job.service)
    
    while len(service_times) < num_locations:
        service_times.append(0)
    
    data['service_times'] = service_times
    
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(
        num_locations,
        num_vehicles, 
        data['starts'],
        data['ends']
    )
    
    # Create routing model
    routing = pywrapcp.RoutingModel(manager)
    
    # Create and register a transit callback
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node] + data['service_times'][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Add capacity constraint if needed
    if any(v.capacity is not None for v in vehicles):
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],
            True,  # start cumul to zero
            'Capacity'
        )
    
    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(30)
    
    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        return extract_or_tools_solution(
            manager, routing, solution, vehicles, jobs, 
            location_to_index, index_to_location, data['distance_matrix']
        )
    else:
        print("OR-tools: No solution found")
        routes = {v.id: Route(jobs=[], delivery_duration=0) for v in vehicles}
        return OutputData(total_delivery_duration=0, routes=routes)

def extract_or_tools_solution(manager, routing, solution, vehicles, jobs, 
                             location_to_index, index_to_location, or_matrix):
    """
    Extract solution from OR-tools result
    """
    job_dict = {j.id: j for j in jobs}
    job_location_to_id = {j.location_index: j.id for j in jobs}
    
    routes = {}
    total_duration = 0
    
    for vehicle_idx, vehicle in enumerate(vehicles):
        route_jobs = []
        route_duration = 0
        
        index = routing.Start(vehicle_idx)
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            location = index_to_location[node]
            
            # If this location has a job, add it to route
            if location in job_location_to_id:
                job_id = job_location_to_id[location]
                route_jobs.append(job_id)
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            
            if not routing.IsEnd(index):
                route_duration += or_matrix[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
        
        # Add service times
        for job_id in route_jobs:
            route_duration += job_dict[job_id].service
        
        routes[vehicle.id] = Route(jobs=route_jobs, delivery_duration=route_duration)
        total_duration += route_duration
    
    print(f"OR-tools solution: {total_duration}s total")
    
    return OutputData(total_delivery_duration=total_duration, routes=routes)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "DRP Solver Microservice",
        "version": "1.0.0",
        "available_solvers": list(SolverType),
        "or_tools_available": ORTOOLS_AVAILABLE
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "solvers": {
            "brute_force": "available",
            "or_tools": "available" if ORTOOLS_AVAILABLE else "not_installed"
        }
    }

@app.post("/solve")
async def solve_routes(input_data: InputData, solver: SolverType = SolverType.BRUTE_FORCE):
    """
    Solve VRP with selected algorithm
    
    Args:
        input_data: InputData with vehicles, jobs, and matrix
        solver: Algorithm to use ('brute_force' or 'or_tools')
    
    Returns:
        OutputData with total delivery duration and routes
    """
    try:
        # Validate input
        if not input_data.vehicles:
            raise ValueError("No vehicles provided")
        
        if not input_data.matrix:
            raise ValueError("Duration matrix is empty")
        
        # Validate matrix dimensions
        max_vehicle_index = max([v.start_index for v in input_data.vehicles], default=-1)
        max_job_index = max([j.location_index for j in input_data.jobs], default=-1)
        max_index = max(max_vehicle_index, max_job_index)
        
        if max_index >= len(input_data.matrix):
            raise ValueError(f"Matrix size ({len(input_data.matrix)}) too small for max index ({max_index})")
        
        # Check matrix is square
        for i, row in enumerate(input_data.matrix):
            if len(row) != len(input_data.matrix):
                raise ValueError(f"Matrix row {i} has incorrect length")
        
        # Select and run solver
        if solver == SolverType.BRUTE_FORCE:
            result = brute_force_solve(input_data.vehicles, input_data.jobs, input_data.matrix)
        elif solver == SolverType.OR_TOOLS:
            if not ORTOOLS_AVAILABLE:
                raise HTTPException(status_code=400, detail="OR-tools solver not available")
            result = or_tools_solve(input_data.vehicles, input_data.jobs, input_data.matrix)
        else:
            raise ValueError(f"Unknown solver: {solver}")
        
        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Starting DRP Solver Microservice...")
    print(f"Available solvers: {list(SolverType)}")
    print(f"OR-tools available: {ORTOOLS_AVAILABLE}")

    uvicorn.run(app, host="0.0.0.0", port=8000)