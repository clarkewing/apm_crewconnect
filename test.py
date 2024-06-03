from urllib.parse import urlencode, urljoin, quote
from apm_client import ApmClient

apm = ApmClient("https://crewmobile.to.aero")

apm.authenticate()

print(apm.credentials)

params = {
    "from": "2024-06-11",
    "to": "2024-06-12",
    "zoneOffset": "+02:00",
}

print(
    apm.request(
        "get",
        "/api/crews/CWH/flight-schedule?" + urlencode(params),
    ).text
)
