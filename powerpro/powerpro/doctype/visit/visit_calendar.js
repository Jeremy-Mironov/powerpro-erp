frappe.views.calendar["Visit"] = {
    field_map: {
        start: "starts_at",
        end: "ends_at",
        id: "name",
        title: "title",
        status: "status",
        allDay: "allDay"
    },
    fields: ["name", "title", "starts_at", "ends_at", "status"],
    order_by: "starts_at",
    get_css_class(data) {
        return {
            "Planned": "blue", "En route": "orange", "On site": "orange", "Done": "green",
            "No access": "red", "Rescheduled": "gray", "Cancelled": "red"
        }[data.status] || "blue";
    }
};
