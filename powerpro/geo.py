"""Geocoding through Google (key lives in PowerPro Settings as a Password field) and
county -> ERPNext Territory mapping."""
import frappe
import requests
from frappe import _
from frappe.utils import cstr

STATE_NAMES = {"OR": "Oregon", "WA": "Washington"}
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def api_key():
    settings = frappe.get_single("PowerPro Settings")
    try:
        return settings.get_password("google_maps_api_key", raise_exception=False)
    except Exception:
        return None


def geocode(address, region="us"):
    """Return dict(lat, lng, formatted, county, place_id, status). Never raises."""
    key = api_key()
    if not key:
        return {"status": "NO_KEY"}
    try:
        r = requests.get(GEOCODE_URL, params={"address": address, "region": region or "us", "key": key}, timeout=8)
        data = r.json()
    except Exception as e:
        frappe.log_error(title="Geocoding request failed", message=f"{address}\n{e}")
        return {"status": "REQUEST_FAILED"}
    status = data.get("status")
    if status != "OK" or not data.get("results"):
        return {"status": status or "UNKNOWN"}
    res = data["results"][0]
    loc = res["geometry"]["location"]
    county = ""
    for comp in res.get("address_components", []):
        if "administrative_area_level_2" in comp.get("types", []):
            county = comp.get("long_name", "")
    return {"status": "OK", "lat": loc["lat"], "lng": loc["lng"], "formatted": res.get("formatted_address"),
            "county": county, "place_id": res.get("place_id")}


def property_address(doc):
    return ", ".join([x for x in [doc.address_line, doc.city, f"{doc.state or ''} {doc.zip_code or ''}".strip(), "USA"] if x])


def geocode_property(doc):
    """Fill latitude/longitude/county on a Property document (called from validate)."""
    region = cstr(frappe.db.get_single_value("PowerPro Settings", "geocode_region") or "us")
    result = geocode(property_address(doc), region)
    doc.geocode_status = result["status"]
    if result["status"] != "OK":
        return
    doc.latitude, doc.longitude = result["lat"], result["lng"]
    doc.formatted_address = result.get("formatted")
    doc.google_place_id = result.get("place_id")
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
