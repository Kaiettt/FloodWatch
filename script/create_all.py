import os
import requests

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026/ngsi-ld/v1/entities/")
ENTITIES_DIR = os.getenv("ENTITIES_DIR", "entities")

def main():
    print("=== FloodWatchX – Create All Entities ===")

    for filename in os.listdir(ENTITIES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(ENTITIES_DIR, filename)
            print(f"\n[Uploading] {filename}")

            with open(filepath, "r", encoding="utf-8") as f:
                data = f.read()

            r = requests.post(
                ORION_URL,
                data=data.encode("utf-8"),
                headers={"Content-Type": "application/ld+json"}
            )

            print(f"→ Status: {r.status_code}")
            try:
                print(r.json())
            except:
                print(r.text)

    print("\n=== DONE: All entities uploaded ===")

if __name__ == "__main__":
    main()