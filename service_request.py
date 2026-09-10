import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.model.document import Document
from powerpro.utils import guard_mirror, normalize_e164


class ServiceRequest(Document):
    def validate(self):
        guard_mirror(self)
        self.phone_e164 = normalize_e164(self.phone)
        if self.status in ("Lost", "Not qualified") and not self.lost_reason:
            frappe.throw(_("Please give a reason for {0}").format(self.status))
        if self.status == "Contacted" and not self.first_response_at:
            self.first_response_at = now_datetime()
        if self.job and self.status not in ("Converted",):
            self.status = "Converted"
