"""ERPNext Project is the Job. Field-service rules live here and run through
doc_events (hooks.py), after Project's own validate (ERPNext computes costing
and billing itself: timesheets, purchase invoices, stock entries, sales invoices)."""
import frappe
from frappe import _
from frappe.utils import add_years, cint, flt, now_datetime, today

from powerpro.utils import guard_mirror, settings

COMPLETE_STATES = ("Complete", "Invoiced", "Paid", "Closed", "Under warranty")
NATIVE_STATUS = {"Cancelled": "Cancelled", "On hold": "On hold"}


def validate(doc, method=None):
    guard_mirror(doc, flag="pp_is_mirror")
    if not doc.pp_status:
        doc.pp_status = "Scheduled"
    if doc.pp_parent_project and doc.pp_parent_project == doc.name:
        frappe.throw(_("A job cannot be its own warranty parent"))
    fill_from_property(doc)
    set_owner_approval(doc)
    set_warranty(doc)
    sync_native_status(doc)


def fill_from_property(doc):
    if not doc.pp_property:
        return
    p = frappe.db.get_value("Property", doc.pp_property, ["customer", "latitude", "longitude"], as_dict=True)
    if not p:
        return
    if not doc.customer:
        doc.customer = p.customer
    doc.latitude, doc.longitude = p.latitude, p.longitude


def set_owner_approval(doc):
    threshold = flt(settings().owner_approval_threshold) or 5000
    needs = flt(doc.pp_quoted_total) > threshold or doc.project_type == "Commercial project"
    doc.pp_needs_owner_approval = 1 if needs else 0
    if needs and not doc.pp_owner_approved_on and "PP Owner" in frappe.get_roles():
        doc.pp_owner_approved_by = frappe.session.user
        doc.pp_owner_approved_on = now_datetime()


def set_warranty(doc):
    if doc.pp_status in COMPLETE_STATES:
        if not doc.pp_completed_on:
            doc.pp_completed_on = today()
        doc.pp_warranty_until = add_years(doc.pp_completed_on, cint(settings().warranty_years) or 5)
    if doc.pp_status == "In progress" and doc.pp_needs_owner_approval and not doc.pp_owner_approved_on:
        frappe.throw(_("This job needs owner approval before work starts"))


def sync_native_status(doc):
    """ERPNext's own status field follows the job status (it is read-only in the form)."""
    if doc.pp_status in COMPLETE_STATES:
        doc.status = "Completed"
    elif doc.pp_status in NATIVE_STATUS:
        doc.status = NATIVE_STATUS[doc.pp_status]
    else:
        doc.status = "Open"


# ---- billing: Invoiced / Paid follow the invoices and payments of the job

def on_invoice_change(doc, method=None):
    """Sales Invoice on_submit / on_cancel."""
    if doc.get("project"):
        refresh_billing(doc.project)


def on_payment(doc, method=None):
    """Payment Entry on_submit / on_cancel: outstanding amounts are already updated by then."""
    projects = set()
    for ref in doc.get("references") or []:
        if ref.reference_doctype == "Sales Invoice":
            p = frappe.db.get_value("Sales Invoice", ref.reference_name, "project")
            if p:
                projects.add(p)
    for p in projects:
        refresh_billing(p)


def refresh_billing(project):
    rows = frappe.get_all("Sales Invoice", filters={"project": project, "docstatus": 1},
                          fields=["base_grand_total", "outstanding_amount"])
    billed = sum(flt(r.base_grand_total) for r in rows)
    paid = sum(flt(r.base_grand_total) - flt(r.outstanding_amount) for r in rows)
    current = frappe.db.get_value("Project", project, "pp_status")
    updates = {"pp_paid_total": paid}
    if current in ("Complete", "Invoiced", "Paid"):
        if not rows:
            new = "Complete"
        elif billed > 0 and paid >= billed - 0.005:
            new = "Paid"
        else:
            new = "Invoiced"
        if new != current:
            updates["pp_status"] = new
    frappe.db.set_value("Project", project, updates, update_modified=False)
