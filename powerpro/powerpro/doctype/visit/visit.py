import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, time_diff_in_hours
from frappe.model.document import Document
from powerpro.utils import guard_mirror, settings


class Visit(Document):
    def validate(self):
        guard_mirror(self)
        self.fill_from_project()
        self.set_window()
        if self.van and not self.warehouse:
            self.warehouse = frappe.db.get_value("Van", self.van, "warehouse")
        if self.check_in and self.check_out:
            if get_datetime(self.check_out) < get_datetime(self.check_in):
                frappe.throw(_("Check-out cannot be before check-in"))
            self.duration_hours = time_diff_in_hours(self.check_out, self.check_in)
        if self.customer_signature and not self.signed_at:
            self.signed_at = now_datetime()
        if self.status == "Done" and not self.check_out:
            self.check_out = now_datetime()
        for row in self.crew or []:
            if row.employee and not row.employee_name:
                row.employee_name = frappe.db.get_value("Employee", row.employee, "employee_name")

    def fill_from_project(self):
        if not self.project:
            return
        p = frappe.db.get_value("Project", self.project,
                                ["customer", "project_name", "pp_property", "latitude", "longitude"], as_dict=True)
        if not p:
            return
        self.customer = p.customer
        self.property = p.pp_property
        self.latitude, self.longitude = p.latitude, p.longitude
        self.title = " · ".join([x for x in [p.customer, p.project_name] if x])

    def set_window(self):
        if not self.visit_date:
            return
        s = settings()
        start = self.window_start or s.default_window_start or "08:00:00"
        end = self.window_end or s.default_window_end or "17:00:00"
        self.starts_at = f"{self.visit_date} {start}"
        self.ends_at = f"{self.visit_date} {end}"
