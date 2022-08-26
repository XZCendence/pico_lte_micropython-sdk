"""
Example code for performing HTTP request to a server with using custom headers.

Example Configuration
---------------------
Create a config.json file in the root directory of the picocell device.
config.json file must include the following parameters for this example:

config.json
{
    "https":{
        "server":"[HTTP_SERVER]",
        "username":"[YOUR_HTTP_USERNAME]",
        "password":"[YOUR_HTTP_PASSWORD]"
    },
}
"""

import json
import time
from core.utils.status import Status
from core.modem import Modem
from core.temp import debug
from core.utils.helpers import get_parameter

# Prepare HTTP connection.
modem = Modem()
modem.network.register_network()
modem.http.set_context_id()
modem.network.get_pdp_ready()
modem.http.set_server_url()

# Get URL from the config.json.
url = get_parameter(["https", "server"])

if url:
    url = url.replace("https://", "").replace("http://", "")
    index = url.find("/") if url.find("/") != -1 else len(url)
    host = url[:index]
    query = url[index:]
else:
    debug.error("Missing argument: server")


# Custom header
HEADER = "\n".join([
    f"GET {query} HTTP/1.1",
    f"Host: {host}",
    "Custom-Header-Name: Custom-Data",
    "Content-Type: application/json",
    "Content-Length: 0\n",
    "\n\n"
])

debug.info("Sending a GET request with custom header...")
result = modem.http.get(HEADER, header_mode=1)
debug.info("Result:", result)

time.sleep(5)

result = modem.http.read_response()
debug.info(result)
if result["status"] == Status.SUCCESS:
    debug.info("GET request succeeded.")
