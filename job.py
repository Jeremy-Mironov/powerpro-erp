import frappe
from frappe import _
from frappe.utils import add_years, cint, flt, now_datetime, today
from frappe.model.document import Document
from powerpro.utils import guard_mirror, settings

COMPLETE_STATES = ("Complete", "Invoiced", "Paid", "Closed", "Under warranty")


class Job(Document):
    def validate(self):
        guard_mirror(self)
        if self.parent_job and self.parent_job == self.name:
            frappe.throw(_("A job cannot be its own warranty parent"))
        self.set_owner_approval_flag()
        self.set_warranty()
        self.compute_margin()

    def set_owner_approval_flag(self):
        threshold = flt(settings().owner_approval_threshold) or 5000
        needs = flt(self.quoted_total) > threshold or self.job_type == "Commercial project"
        self.needs_owner_approval = 1 if needs else 0
        if self.needs_owner_approval and not self.owner_approved_on and "PP Owner" in frappe.get_roles():
            self.owner_approved_by = frappe.session.user
            self.owner_approved_on = now_datetime()

    def set_warranty(self):
        if self.status in COMPLETE_STATES:
            if not self.completed_on:
                self.completed_on = today()
            years = cint(settings().warranty_years) or 5
            self.warranty_until = add_years(self.completed_on, years)
        if self.status == "In progress" and self.needs_owner_approval and not self.owner_approved_on:
            frappe.throw(_("This job needs owner approval before work starts"))

    def compute_margin(self):
        self.actual_cost = flt(self.material_cost) + flt(self.direct_purchase_cost) + flt(self.labor_cost)
        revenue = flt(self.invoiced_total) or flt(self.quoted_total)
        self.margin = revenue - flt(self.actual_cost)
        self.margin_pct = (self.margin / revenue * 100) if revenue else 0
