import frappe
from frappe import _
from frappe.model.document import Document


class ChangeOrder(Document):
    def validate(self):
        if self.project:
            self.customer = frappe.db.get_value("Project", self.project, "customer")
        if self.status == "Approved":
            if not self.customer_approved_on or not self.approval_evidence:
                frappe.throw(_("A change order is Approved only with a date and written evidence from the customer"))
        if self.amount is not None and self.amount == 0 and self.status == "Approved":
            frappe.msgprint(_("Approved change order with $0 amount"), indicator="orange")
