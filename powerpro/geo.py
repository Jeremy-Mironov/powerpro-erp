"""Geocoding without keys or billing: US Census Geocoder first (US-only, returns the
county), OpenStreetMap Nominatim as a fallback for addresses Census cannot match.
Coordinates are ours to keep and to show on the OSM map of ERPNext.
County -> ERPNext Territory mapping lives here too."""
import re
import time

import frappe
import requests
from frappe import _

STATE_NAMES = {"OR": "Oregon", "WA": "Washington"}
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
OSM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim's policy: identify the application, max 1 request per second, cache results (we store them)
USER_AGENT = "PowerPro-ERP/1.0 (+https://powerprofessor.co)"
# trailing "Apt 4", "Unit B", "Ste. 200", "#12-B" — only when the unit id looks like one (a digit in it, or a single letter)
UNIT_RE = re.compile(r"(?:\s*,?\s*\b(?:apt|apartment|unit|ste|suite|bldg|fl|rm|spc|trlr)\b\.?\s*#?\s*(?:[A-Za-z]|(?=[\w-]*\d)[\w-]+)"
                     r"|\s*,?\s*#\s*[\w-]+)\s*$", re.I)


def geocoder():
    return frappe.db.get_single_value("PowerPro Settings", "geocoder") or "US Census + OpenStreetMap fallback"


def street_only(address_line):
    """'123 Main St Apt 4' -> '123 Main St' (the unit confuses street-level geocoders)."""
    return UNIT_RE.sub("", address_line or "").strip(" ,")


def one_line(doc, with_unit=True):
    line = doc.address_line if with_unit else street_only(doc.address_line)
    return ", ".join([x for x in [line, doc.city, f"{doc.state or ''} {doc.zip_code or ''}".strip()] if x])


def geocode_census(address):
    """US Census Geocoder: free, no key, county included. Returns dict(status, ...). Never raises."""
    try:
        r = requests.get(CENSUS_URL, params={"address": address, "benchmark": "Public_AR_Current",
                                             "vintage": "Current_Current", "format": "json"}, timeout=10)
        matches = r.json().get("result", {}).get("addressMatches") or []
    except Exception as e:
        frappe.log_error(title="Census geocoding failed", message=f"{address}\n{e}")
        return {"status": "REQUEST_FAILED"}
    if not matches:
        return {"status": "NO_MATCH"}
    m = matches[0]
    geos = m.get("geographies") or {}
    counties = next((v for k, v in geos.items() if "Counties" in k), None) or []
    county = (counties[0].get("NAME") or "") if counties else ""
    return {"status": "OK", "lat": float(m["coordinates"]["y"]), "lng": float(m["coordinates"]["x"]),
            "formatted": m.get("matchedAddress") or "", "county": county, "source": "US Census"}


def geocode_osm(address):
    """OpenStreetMap Nominatim (public instance, light use only). Never raises."""
    time.sleep(1)  # policy: at most one request per second
    try:
        r = requests.get(OSM_URL, params={"q": address, "format": "jsonv2", "addressdetails": 1, "limit": 1,
                                          "countrycodes": "us"}, headers={"User-Agent": USER_AGENT}, timeout=10)
        data = r.json()
    except Exception as e:
        frappe.log_error(title="OSM geocoding failed", message=f"{address}\n{e}")
        return {"status": "REQUEST_FAILED"}
    if not data:
        return {"status": "NO_MATCH"}
    res = data[0]
    addr = res.get("address") or {}
    return {"status": "OK", "lat": float(res["lat"]), "lng": float(res["lon"]),
            "formatted": res.get("display_name") or "", "county": addr.get("county") or "", "source": "OpenStreetMap"}


def geocode(doc):
    """Geocode a Property according to the geocoder chosen in PowerPro Settings."""
    mode = geocoder()
    result = {"status": "NO_MATCH"}
    if mode.startswith("US Census"):
        result = geocode_census(one_line(doc, with_unit=False))
    if result["status"] != "OK" and (mode.startswith("OpenStreetMap") or "fallback" in mode):
        result = geocode_osm(one_line(doc, with_unit=False))
    return result


def geocode_property(doc):
    """Fill latitude/longitude/county on a Property document (called from validate)."""
    result = geocode(doc)
    doc.geocode_status = result["status"]
    if result["status"] != "OK":
        return
    doc.latitude, doc.longitude = result["lat"], result["lng"]
    doc.formatted_address = result.get("formatted")
    doc.geocode_source = result.get("source")
    if result.get("county"):
        doc.county = result["county"]
        doc.territory = territory_for_county(doc.county, doc.state)


def territory_for_county(county, state):
    """County territory under the state, created on demand: All Territories > Oregon > Multnomah County."""
    if not county:
        return None
    state_name = STATE_NAMES.get((state or "").upper(), state or "USA")
    root = "All Territories"
    if not frappe.db.exists("Territory", state_name):
        frappe.get_doc({"doctype": "Territory", "territory_name": state_name, "parent_territory": root,
                        "is_group": 1}).insert(ignore_permissions=True)
    if not frappe.db.exists("Territory", county):
        frappe.get_doc({"doctype": "Territory", "territory_name": county, "parent_territory": state_name,
                        "is_group": 0}).insert(ignore_permissions=True)
    return county


@frappe.whitelist()
def regeocode(property):
    doc = frappe.get_doc("Property", property)
    doc.check_permission("write")
    geocode_property(doc)
    doc.save()
    if doc.geocode_status != "OK":
        frappe.msgprint(_("Geocoding returned {0}").format(doc.geocode_status), indicator="orange")
    return {"status": doc.geocode_status, "latitude": doc.latitude, "longitude": doc.longitude}
