import requests
import json
import time


BASE_URL = "http://localhost:8000"

# Test data
sample_data = {
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
}

def test_health_endpoints():
    """Test health check endpoints"""
    print("Testing health endpoints...")
    
    # Root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"Root: {data['service']}")
            print(f"Available solvers: {data['available_solvers']}")
            print(f"OR-tools available: {data['or_tools_available']}")
        else:
            print(f"Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"Health: {data['status']}")
            print(f"Solvers: {data['solvers']}")
        else:
            print(f"Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"Health endpoint error: {e}")

def test_solver(solver_name):
    """Test a specific solver"""
    print(f"\nTesting {solver_name.upper()} solver...")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/solve",
            json=sample_data,
            params={"solver": solver_name},
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"{solver_name}: SUCCESS ({duration:.2f}s)")
            print(f"Total duration: {result['total_delivery_duration']} seconds")
            print("Routes:")
            
            for vehicle_id, route in result['routes'].items():
                if route['jobs']:
                    print(f"{vehicle_id}: {route['jobs']} -> {route['delivery_duration']}s")
                else:
                    print(f"{vehicle_id}: EMPTY -> {route['delivery_duration']}s")
                    
        else:
            print(f"{solver_name}: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"{solver_name}: Connection error - Is the service running?")
    except Exception as e:
        print(f"{solver_name}: Unexpected error - {e}")

def compare_solvers():
    """Compare both solvers performance"""
    print(f"\n SOLVER COMPARISON")
    print("="*50)
    
    results = {}
    
    for solver in ["brute_force", "or_tools"]:
        print(f"\nRunning {solver}...")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/solve",
                json=sample_data,
                params={"solver": solver},
                headers={"Content-Type": "application/json"}
            )
            
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                results[solver] = {
                    "success": True,
                    "duration": end_time - start_time,
                    "total_delivery_duration": result['total_delivery_duration'],
                    "routes": result['routes']
                }
            else:
                results[solver] = {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            results[solver] = {
                "success": False,
                "error": str(e)
            }
    
    # Print comparison
    print(f"\nCOMPARISON RESULTS")
    print("-" * 40)
    
    for solver, data in results.items():
        print(f"\n🔧 {solver.upper()}:")
        if data['success']:
            print(f"Status: SUCCESS")
            print(f"Execution time: {data['duration']:.3f}s")
            print(f"Solution quality: {data['total_delivery_duration']}s")
            print(f"Active vehicles: {sum(1 for r in data['routes'].values() if r['jobs'])}")
        else:
            print(f"Status: FAILED")
            print(f"Error: {data['error']}")
    
    # Quality comparison
    successful_results = {k: v for k, v in results.items() if v['success']}
    
    if len(successful_results) > 1:
        print(f"\n🏆 WINNER:")
        best_solver = min(
            successful_results.keys(), 
            key=lambda k: successful_results[k]['total_delivery_duration']
        )
        best_duration = successful_results[best_solver]['total_delivery_duration']
        print(f"   🥇 {best_solver.upper()} with {best_duration}s total delivery time")

def test_error_cases():
    """Test error handling"""
    print(f"\nTesting error cases...")
    
    # Empty vehicles
    bad_data1 = {**sample_data, "vehicles": []}
    response = requests.post(f"{BASE_URL}/solve", json=bad_data1)
    print(f"Empty vehicles: {response.status_code} - {'✅' if response.status_code == 400 else '❌'}")
    
    # Invalid matrix
    bad_data2 = {**sample_data, "matrix": []}
    response = requests.post(f"{BASE_URL}/solve", json=bad_data2)
    print(f"Empty matrix: {response.status_code} - {'✅' if response.status_code == 400 else '❌'}")
    
    # Invalid solver
    response = requests.post(f"{BASE_URL}/solve", json=sample_data, params={"solver": "invalid"})
    print(f"Invalid solver: {response.status_code} - {'✅' if response.status_code == 422 else '❌'}")

if __name__ == "__main__":
    print("TESTING")
    print("=" * 50)
    
    # Test health endpoints
    test_health_endpoints()
    
    # Test individual solvers
    test_solver("brute_force")
    test_solver("or_tools")
    
    # Compare solvers
    compare_solvers()
    
    # Test error cases  
    test_error_cases()
    
    print(f"\n🏁 Testing complete!")
    print("\nUsage examples:")
    print(f"   Brute force: POST {BASE_URL}/solve?solver=brute_force")
    print(f"   OR-tools:    POST {BASE_URL}/solve?solver=or_tools")
    print(f"   Health:      GET {BASE_URL}/health")