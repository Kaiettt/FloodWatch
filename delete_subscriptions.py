# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import requests

# Orion-LD endpoint
ORION_URL = "http://localhost:1026/ngsi-ld/v1/subscriptions"

def delete_all_subscriptions():
    """Delete all subscriptions from Orion-LD"""
    try:
        # Get all subscriptions
        print("Fetching subscriptions...")
        response = requests.get(ORION_URL, headers={"Accept": "application/ld+json"})
        response.raise_for_status()
        
        subscriptions = response.json()
        if not isinstance(subscriptions, list):
            print("No subscriptions found or invalid response format")
            return
            
        print(f"Found {len(subscriptions)} subscriptions to delete\n")
        
        # Delete each subscription
        for i, sub in enumerate(subscriptions, 1):
            sub_id = sub.get('id')
            if not sub_id:
                continue
                
            print(f"{i}. Deleting subscription: {sub_id}")
            try:
                del_response = requests.delete(f"{ORION_URL}/{sub_id}")
                if del_response.status_code == 204:
                    print(f"   ✓ Successfully deleted")
                else:
                    print(f"   ✗ Failed with status code: {del_response.status_code}")
                    if del_response.text:
                        print(f"     Error: {del_response.text}")
            except Exception as e:
                print(f"   ✗ Error: {str(e)}")
                
        print("\nAll subscriptions processed")
        
    except requests.exceptions.RequestException as e:
        print(f"\nError connecting to Orion-LD: {str(e)}")
        print("Please make sure Orion-LD is running and accessible at", ORION_URL)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    print("="*50)
    print("  Orion-LD Subscription Cleanup Tool")
    print("="*50 + "\n")
    delete_all_subscriptions()
    print("\n" + "="*50)
    print("  Cleanup Complete")
    print("="*50)