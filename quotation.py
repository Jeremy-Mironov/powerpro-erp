import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from powerpro.utils import guard_mirror, settings


def validate(doc, method=None):
    guard_mirror(doc, flag="pp_is_mirror")
    threshold = flt(settings().owner_approval_threshold) or 5000
    commercial = bool(doc.get("pp_property")) and frappe.db.get_value("Property", doc.pp_property, "property_type") in ("Commercial", "Industrial")
    doc.pp_needs_owner_approval = 1 if (flt(doc.grand_total) > threshold or commercial) else 0
    if doc.pp_needs_owner_approval and not doc.pp_owner_approved_on and "PP Owner" in frappe.get_roles():
        doc.pp_owner_approved_by = frappe.session.user
        doc.pp_owner_approved_on = now_datetime()


def before_submit(doc, method=None):
    if doc.pp_needs_owner_approval and not doc.pp_owner_approved_on:
        frappe.throw(_("This quotation is above the owner approval threshold. An owner has to approve it before it is sent."))
