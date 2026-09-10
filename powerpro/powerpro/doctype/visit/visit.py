import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, time_diff_in_hours
from frappe.model.document import Document
from powerpro.utils import guard_mirror


class Visit(Document):
    def validate(self):
        guard_mirror(self)
        self.fill_from_links()
        if self.check_in and self.check_out:
            if get_datetime(self.check_out) < get_datetime(self.check_in):
                frappe.throw(_("Check-out cannot be before check-in"))
            self.duration_hours = time_diff_in_hours(self.check_out, self.check_in)
        if self.customer_signature and not self.signed_at:
            self.signed_at = now_datetime()
        if self.status == "Done" and not self.check_out:
            self.check_out = now_datetime()

    def fill_from_links(self):
        if self.job:
            customer, prop = frappe.db.get_value("Job", self.job, ["customer", "property"])
            self.customer, self.property = customer, prop
        if self.van:
            self.warehouse = frappe.db.get_value("Van", self.van, "warehouse")
        for row in self.crew or []:
            if row.employee and not row.employee_name:
                row.employee_name = frappe.db.get_value("Employee", row.employee, "employee_name")
