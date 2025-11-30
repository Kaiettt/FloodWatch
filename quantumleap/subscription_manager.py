import requests
import logging
from typing import List

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ORION_URL = "http://localhost:1026/ngsi-ld/v1"
QUANTUMLEAP_URL = "http://localhost:8668"
CORE_CONTEXT = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

class QuantumLeapSubscriptionManager:
    def __init__(self, orion_url: str = ORION_URL, quantumleap_url: str = QUANTUMLEAP_URL):
        self.orion_url = orion_url.rstrip('/')
        self.quantumleap_url = quantumleap_url.rstrip('/')
        self.subscription_url = f"{self.orion_url}/subscriptions"
        self.quantumleap_ingest_url = f"{self.quantumleap_url}/v2/notify"
        self.headers = {"Content-Type": "application/ld+json", "Accept": "application/ld+json"}

    def create_subscription(self, entity_type: str, attrs: List[str]):
        subscription = {
            "type": "Subscription",
            "name": f"sub-{entity_type}",
            "entities": [{"type": entity_type, "idPattern": ".*"}],
            "notification": {
                "endpoint": {
                    "uri": self.quantumleap_ingest_url,
                    "accept": "application/ld+json"
                },
                "attributes": attrs,
                "format": "normalized"
            },
            "@context": CORE_CONTEXT
        }
        
        try:
            r = requests.post(
                self.subscription_url,
                headers=self.headers,
                json=subscription
            )
            r.raise_for_status()
            logger.info(f"✅ Subscription created for {entity_type}")
            return r.headers.get("Location", None)
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to create subscription for {entity_type}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def list_subscriptions(self):
        try:
            r = requests.get(self.subscription_url, headers=self.headers)
            r.raise_for_status()
            # Orion-LD returns a list of subscriptions directly
            subscriptions = r.json()
            if isinstance(subscriptions, list):
                return subscriptions
            # Fallback in case the response is an object with a subscriptions key
            return subscriptions.get("subscriptions", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to list subscriptions: {e}")
            return []

    def delete_subscription(self, subscription_id: str):
        try:
            r = requests.delete(f"{self.subscription_url}/{subscription_id}", headers=self.headers)
            r.raise_for_status()
            logger.info(f"✅ Deleted subscription {subscription_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to delete subscription {subscription_id}: {e}")
            return False

def setup_subscriptions():
    logger.info("🚀 Starting Orion-LD → QuantumLeap subscription setup...")
    manager = QuantumLeapSubscriptionManager()

    # Delete existing subscriptions
    logger.info("Cleaning up existing subscriptions...")
    for sub in manager.list_subscriptions():
        if "id" in sub:
            manager.delete_subscription(sub["id"])

    # Define entities and attributes
    entity_subscriptions = {
        "WaterLevelSensor": ["waterLevel", "location", "timestamp", "status"],
        "CrowdReport": ["floodLevel", "location", "timestamp", "reporterId", "description"],
        "CameraStream": ["streamUrl", "location", "floodDetected", "confidence", "timestamp"],
        "FloodRisk": ["riskLevel", "location", "timestamp", "description", "affectedArea"]
    }

    # Create subscriptions
    for etype, attrs in entity_subscriptions.items():
        manager.create_subscription(etype, attrs)

    logger.info("✅ Subscription setup completed. Check Orion-LD for created subscriptions.")

if __name__ == "__main__":
    setup_subscriptions()
