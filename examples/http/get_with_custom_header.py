"""
Example code for performing HTTP request to a server with using custom headers.

Example Configuration
---------------------
Create a config.json file in the root directory of the PicoLTE device.
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
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug
from pico_lte.utils.helpers import get_parameter

# Prepare HTTP connection.
picoLTE = PicoLTE()
picoLTE.network.register_network()
picoLTE.http.set_context_id()
picoLTE.network.get_pdp_ready()
picoLTE.http.set_server_url()

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
HEADER = "\n".join(
    [
        f"GET {query} HTTP/1.1",
        f"Host: {host}",
        "Custom-Header-Name: Custom-Data",
        "Content-Type: application/json",
        "Content-Length: 0\n",
        "\n\n",
    ]
)

debug.info("Sending a GET request with custom header...")
result = picoLTE.http.get(HEADER, header_mode=1)
debug.info("Result:", result)

time.sleep(5)

result = picoLTE.http.read_response()
debug.info(result)
if result["status"] == Status.SUCCESS:
    debug.info("GET request succeeded.")
