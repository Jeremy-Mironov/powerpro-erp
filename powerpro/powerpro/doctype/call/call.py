import frappe
from frappe.utils import add_days, now_datetime
from frappe.model.document import Document
from powerpro.utils import normalize_e164, find_customer_by_phone, settings


class Call(Document):
    def validate(self):
        self.from_e164 = normalize_e164(self.from_e164)
        self.to_e164 = normalize_e164(self.to_e164)
        self.tracking_number = normalize_e164(self.tracking_number)
        if not self.customer:
            other = self.from_e164 if self.direction == "Inbound" else self.to_e164
            customer, contact = find_customer_by_phone(other)
            self.customer = self.customer or customer
            self.contact = self.contact or contact

    def after_insert(self):
        self.maybe_open_request()

    def on_update(self):
        if self.has_value_changed("status"):
            self.maybe_open_request()

    def maybe_open_request(self):
        s = settings()
        if not s.auto_request_on_missed_call or self.direction != "Inbound":
            return
        if self.status not in ("No answer", "Voicemail") or self.service_request:
            return
        days = s.missed_call_dedupe_days or 7
        existing = frappe.db.get_value("Service Request",
            {"phone_e164": self.from_e164, "status": ("in", ["New", "Contacted", "Visit scheduled"]),
             "creation": (">=", add_days(now_datetime(), -days))}, "name")
        if existing:
            self.db_set("service_request", existing, update_modified=False)
            return
        sr = frappe.get_doc({
            "doctype": "Service Request", "status": "New", "source": "Phone",
            "customer": self.customer, "phone": self.from_e164, "call": self.name,
            "description": f"Missed call on {self.tracking_number or self.to_e164} ({self.status})"
                           + (f"\n\nVoicemail transcript:\n{self.transcript}" if self.transcript else ""),
        })
        sr.flags.ignore_permissions = True
        sr.insert()
        self.db_set("service_request", sr.name, update_modified=False)
