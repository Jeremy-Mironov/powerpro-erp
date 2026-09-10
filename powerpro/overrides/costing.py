import frappe


def _refresh(job):
    if job:
        frappe.enqueue("powerpro.costing.refresh_job_costs", job=job, enqueue_after_commit=True)


def on_change(doc, method=None):
    _refresh(doc.get("pp_job"))


def on_payment(doc, method=None):
    for ref in doc.get("references") or []:
        if ref.reference_doctype == "Sales Invoice":
            _refresh(frappe.db.get_value("Sales Invoice", ref.reference_name, "pp_job"))
