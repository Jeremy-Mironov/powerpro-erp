import re

import frappe
from frappe import _

INTEGRATION_ROLES = {"PP Integration", "System Manager", "Administrator"}


def settings():
    return frappe.get_single("PowerPro Settings")


def normalize_e164(value):
    """Return +1XXXXXXXXXX for US numbers, keep other +CC numbers, None when empty."""
    if not value:
        return None
    s = str(value).strip()
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    if s.startswith("+") and 8 <= len(digits) <= 15:
        return "+" + digits
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return "+" + digits


def find_customer_by_phone(e164):
    """(customer, contact) for a normalised phone, or (None, None)."""
    if not e164:
        return None, None
    contact = frappe.db.get_value("Contact", {"pp_phone_e164": e164}, "name")
    if contact:
        customer = frappe.db.get_value(
            "Dynamic Link",
            {"parenttype": "Contact", "parent": contact, "link_doctype": "Customer"},
            "link_name",
        )
        return customer, contact
    customer = frappe.db.get_value("Customer", {"pp_phone_e164": e164}, "name")
    return customer, None


def is_integration_user():
    return bool(set(frappe.get_roles()) & INTEGRATION_ROLES)


def guard_mirror(doc, flag="is_mirror"):
    """Records mirrored from Jobber are read-only for humans until that module
    becomes the system of record. Integration and System Manager may write."""
    if not doc.get(flag) or doc.flags.get("ignore_mirror") or doc.is_new():
        return
    if is_integration_user():
        return
    frappe.throw(
        _("{0} {1} is mirrored from Jobber and is read-only here. Edit it in Jobber; the change syncs back.")
        .format(doc.doctype, doc.name)
    )
