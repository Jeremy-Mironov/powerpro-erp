import frappe
from frappe.model.document import Document
from powerpro.utils import guard_mirror
from powerpro.geo import geocode_property, territory_for_county

ADDRESS_FIELDS = ("address_line", "city", "state", "zip_code")


class Property(Document):
    def validate(self):
        guard_mirror(self)
        self.title = ", ".join([x for x in [self.address_line, self.city] if x])
        retry = not (self.latitude and self.longitude) and (self.geocode_status or "") in ("", "NO_KEY", "REQUEST_FAILED")
        if self.address_changed() or retry:
            geocode_property(self)
        if self.county and not self.territory:
            self.territory = territory_for_county(self.county, self.state)

    def address_changed(self):
        if self.is_new():
            return True
        before = self.get_doc_before_save()
        return any((before.get(f) or "") != (self.get(f) or "") for f in ADDRESS_FIELDS) if before else True

    def on_update(self):
        """Keep coordinates on open jobs and visits in sync with the property."""
        before = self.get_doc_before_save()
        if before and before.latitude == self.latitude and before.longitude == self.longitude:
            return
        coords = {"latitude": self.latitude, "longitude": self.longitude}
        for name in frappe.get_all("Project", filters={"pp_property": self.name, "status": ("!=", "Completed")}, pluck="name"):
            frappe.db.set_value("Project", name, coords, update_modified=False)
        for name in frappe.get_all("Visit", filters={"property": self.name, "status": ("in", ["Planned", "En route", "On site"])}, pluck="name"):
            frappe.db.set_value("Visit", name, coords, update_modified=False)
