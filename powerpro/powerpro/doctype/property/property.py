from frappe.model.document import Document
from powerpro.utils import guard_mirror


class Property(Document):
    def validate(self):
        guard_mirror(self)
        self.title = ", ".join([x for x in [self.address_line, self.city] if x])
