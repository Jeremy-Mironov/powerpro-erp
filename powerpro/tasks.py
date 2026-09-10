import frappe
from frappe.utils import today


def daily():
    """Housekeeping: jobs past their warranty date leave 'Under warranty'."""
    for name in frappe.get_all(
        "Project", filters={"pp_status": "Under warranty", "pp_warranty_until": ("<", today())}, pluck="name"
    ):
        frappe.db.set_value("Project", name, {"pp_status": "Closed", "status": "Completed"}, update_modified=False)
