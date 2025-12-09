# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

import requests
ORION_URL = "http://localhost:1026/ngsi-ld/v1/entities?idPattern=urn:ngsi-ld:.*"

r = requests.delete(ORION_URL)
print(r.status_code, r.text)