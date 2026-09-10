import frappe
from frappe.model.document import Document


class Permit(Document):
    def validate(self):
        if self.job:
            self.property = frappe.db.get_value("Job", self.job, "property")
        rows = self.inspections or []
        finals = [r for r in rows if r.inspection_type == "Final" and r.result == "Pass"]
        if finals:
            self.status = "Final"
            self.finaled_on = max(r.inspection_date for r in finals)
        elif any(r.result == "Corrections" for r in rows) and self.status != "Final":
            self.status = "Corrections"

    def on_update(self):
        if self.job:
            frappe.db.set_value("Job", self.job, {"permit": self.name, "permit_required": 1}, update_modified=False)
