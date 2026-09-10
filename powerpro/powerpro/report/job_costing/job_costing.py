import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    conditions = {}
    for key in ("status", "customer", "job_type", "lead_tech"):
        if filters.get(key):
            conditions[key] = filters[key]
    if filters.get("from_date"):
        conditions["scheduled_start"] = (">=", filters["from_date"])
    columns = [
        {"label": _("Job"), "fieldname": "name", "fieldtype": "Link", "options": "Job", "width": 140},
        {"label": _("Title"), "fieldname": "title", "fieldtype": "Data", "width": 220},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": _("Type"), "fieldname": "job_type", "fieldtype": "Data", "width": 120},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Quoted"), "fieldname": "quoted_total", "fieldtype": "Currency", "width": 110},
        {"label": _("Invoiced"), "fieldname": "invoiced_total", "fieldtype": "Currency", "width": 110},
        {"label": _("Paid"), "fieldname": "paid_total", "fieldtype": "Currency", "width": 110},
        {"label": _("Materials"), "fieldname": "material_cost", "fieldtype": "Currency", "width": 110},
        {"label": _("Direct purchases"), "fieldname": "direct_purchase_cost", "fieldtype": "Currency", "width": 120},
        {"label": _("Labor"), "fieldname": "labor_cost", "fieldtype": "Currency", "width": 110},
        {"label": _("Actual cost"), "fieldname": "actual_cost", "fieldtype": "Currency", "width": 110},
        {"label": _("Margin"), "fieldname": "margin", "fieldtype": "Currency", "width": 110},
        {"label": _("Margin %"), "fieldname": "margin_pct", "fieldtype": "Percent", "width": 90},
    ]
    rows = frappe.get_all(
        "Job", filters=conditions, order_by="scheduled_start desc",
        fields=[c["fieldname"] for c in columns],
    )
    return columns, rows
