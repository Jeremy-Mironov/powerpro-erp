import frappe
from frappe.model.document import Document


class Permit(Document):
    def validate(self):
        if self.project:
            self.property = frappe.db.get_value("Project", self.project, "pp_property")
            if self.property and not self.jurisdiction:
                self.jurisdiction = frappe.db.get_value("Property", self.property, "jurisdiction")
        finals = [r for r in (self.inspections or []) if r.inspection_type == "Final" and r.result == "Pass"]
        if finals:
            self.status = "Final"
            self.finaled_on = max(r.inspection_date for r in finals)
        elif any(r.result == "Corrections" for r in (self.inspections or [])) and self.status != "Final":
            self.status = "Corrections"

    def on_update(self):
        if self.project:
            frappe.db.set_value("Project", self.project, {"pp_permit": self.name, "pp_permit_required": 1}, update_modified=False)
