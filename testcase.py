import requests
import json

url = "http://localhost:8000/solve"

sample_data = {
    "vehicles": [
        {
            "id": "vehicle_1",
            "start_index": 0,  
            "capacity": 70 ## 100
        },
        {
            "id": "vehicle_2", 
            "start_index": 0,
            "capacity": 25 ## 150
        }
    ],
    "jobs": [
        {
            "id": "job_1",
            "location_index": 1,  
            "delivery": 30,
            "service": 300  ## Second
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

def send_request_with_requests():
    """
    Send Post Request with Request Library
    """
    try:
        response = requests.post(
            url,
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request Succesful !")
            print(f"Total duration: {result['total_delivery_duration']} second")
            print("\Routes:")
            for vehicle_id, route in result['routes'].items():
                print(f"  {vehicle_id}: {route['jobs']} - Duration: {route['delivery_duration']} second")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Check if the API is working")
    except Exception as e:
        print(f"❌ Error : {e}")


def send_request_with_curl():
    """
    CURL Command Sample 
    """
    curl_command = f'''
curl -X POST "{url}" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(sample_data, indent=2)}'
    '''
    print("🔧 Curl command:")
    print(curl_command)

if __name__ == "__main__":
    print("🚀 Sending Request to API...")
    print("📍 URL:", url)
    print("📦 Data:", json.dumps(sample_data, indent=2)[:200] + "...")
    print("\n" + "="*50 + "\n")

    send_request_with_requests()
    
    print("\n" + "="*30 + "\n")
    
    send_request_with_curl()