// PowerPro: maps without an API — the map view is OpenStreetMap (built into Frappe), navigation
// opens Google Maps in the browser / phone app by street address, which is exact at the door
// (our stored coordinates come from a free street-level geocoder and can be tens of meters off).
frappe.provide("powerpro.geo");

powerpro.geo.address_of = (p) =>
    [p.address_line, p.city, `${p.state || ""} ${p.zip_code || ""}`.trim()].filter(Boolean).join(", ");

powerpro.geo.url = (mode, dest) => {
    const q = encodeURIComponent(dest);
    return mode === "dir"
        ? `https://www.google.com/maps/dir/?api=1&destination=${q}`
        : `https://www.google.com/maps/search/?api=1&query=${q}`;
};

// Navigate to a Property. The tab is opened synchronously inside the click (phone browsers block
// windows opened after an async call), then pointed at the directions once the address arrives.
powerpro.geo.navigate = (property, lat, lng) => {
    const fallback = lat && lng ? `${lat},${lng}` : "";
    const tab = window.open("about:blank", "_blank");
    const go = (dest) => {
        const url = powerpro.geo.url("dir", dest);
        if (tab) tab.location = url; else window.open(url);
    };
    if (!property) return go(fallback);
    frappe.db.get_value("Property", property, ["address_line", "city", "state", "zip_code"])
        .then((r) => go(powerpro.geo.address_of(r.message || {}) || fallback))
        .catch(() => go(fallback));
};
