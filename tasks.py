import frappe
from frappe.utils import today


def daily():
    """Housekeeping: jobs past warranty leave 'Under warranty'."""
    for name in frappe.get_all(
        "Job", filters={"status": "Under warranty", "warranty_until": ("<", today())}, pluck="name"
    ):
        frappe.db.set_value("Job", name, "status", "Closed", update_modified=False)
