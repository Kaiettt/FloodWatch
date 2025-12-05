import requests

# Orion-LD endpoint
ORION_URL = "http://localhost:1026/ngsi-ld/v1/subscriptions"

def delete_all_subscriptions():
    # First, get all subscriptions
    try:
        response = requests.get(ORION_URL)
        if response.status_code != 200:
            print(f"Failed to fetch subscriptions. Status code: {response.status_code}")
            print(response.text)
            return
            
        subscriptions = response.json()
        
        if not subscriptions:
            print("No subscriptions found.")
            return
            
        print(f"Found {len(subscriptions)} subscriptions. Starting deletion...")
        
        # Delete each subscription
        for sub in subscriptions:
            sub_id = sub.get('id')
            if not sub_id:
                print("Warning: Subscription without ID found, skipping...")
                continue
                
            delete_url = f"{ORION_URL}/{sub_id}"
            del_response = requests.delete(delete_url)
            
            if del_response.status_code in (204, 404):
                print(f"✓ Deleted subscription: {sub_id}")
            else:
                print(f"Failed to delete {sub_id}. Status code: {del_response.status_code}")
                print(del_response.text)
    
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while connecting to Orion: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting to delete all subscriptions from Orion Context Broker...")
    delete_all_subscriptions()
    print("Subscription cleanup completed.")
