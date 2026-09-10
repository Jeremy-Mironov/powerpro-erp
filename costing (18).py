import frappe
from frappe.utils import flt


def _sum(doctype, filters, field):
    return flt(frappe.db.get_value(doctype, filters, f"sum({field})") or 0)


@frappe.whitelist()
def refresh_job_costs(job):
    """Recompute actuals on a Job from submitted ERPNext documents that carry pp_job."""
    frappe.has_permission("Job", "write", throw=True)
    material = _sum("Stock Entry", {"docstatus": 1, "pp_job": job, "purpose": "Material Issue"}, "total_outgoing_value")
    direct = _sum("Purchase Invoice", {"docstatus": 1, "pp_job": job, "is_return": 0}, "base_grand_total")
    labor = _sum("Timesheet", {"docstatus": 1, "pp_job": job}, "total_costing_amount")
    invoiced = _sum("Sales Invoice", {"docstatus": 1, "pp_job": job, "is_return": 0}, "base_grand_total")
    outstanding = _sum("Sales Invoice", {"docstatus": 1, "pp_job": job, "is_return": 0}, "outstanding_amount")
    paid = invoiced - outstanding

    quoted = flt(frappe.db.get_value("Job", job, "quoted_total"))
    actual = material + direct + labor
    revenue = invoiced or quoted
    margin = revenue - actual
    values = {
        "material_cost": material,
        "direct_purchase_cost": direct,
        "labor_cost": labor,
        "actual_cost": actual,
        "invoiced_total": invoiced,
        "paid_total": paid,
        "margin": margin,
        "margin_pct": (margin / revenue * 100) if revenue else 0,
    }
    frappe.db.set_value("Job", job, values, update_modified=False)
    return values
