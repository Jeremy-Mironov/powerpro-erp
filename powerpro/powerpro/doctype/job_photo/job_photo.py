import frappe
from frappe.utils import now_datetime
from frappe.model.document import Document


class JobPhoto(Document):
    def before_insert(self):
        self.taken_by = frappe.session.user
        if not self.taken_at:
            self.taken_at = now_datetime()
