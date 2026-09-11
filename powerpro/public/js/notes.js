// PowerPro field notes: one panel on Customer / Property / Project / Visit forms showing the
// notes inherited down the chain (customer -> property -> project -> visit), filtered by role.
frappe.provide("powerpro.notes");

powerpro.notes.render = function (frm, links) {
    if (frm.is_new()) return;
    const args = {};
    ["customer", "property", "project", "visit"].forEach((k) => { if (links[k]) args[k] = links[k]; });
    if (!Object.keys(args).length) return;
    frappe.call({ method: "powerpro.notes.get_notes", args, callback: (r) => {
        const notes = r.message || [];
        const body = frm.dashboard.add_section(powerpro.notes.html(notes, frm.doctype), __("Field notes") + (notes.length ? ` (${notes.length})` : ""));
        body.find(".pp-note-add").on("click", () => powerpro.notes.add(frm, links));
        body.find(".pp-note-open").on("click", function () { frappe.set_route("Form", "Field Note", $(this).data("name")); });
        frm.dashboard.show();
    }});
};

powerpro.notes.html = function (notes, doctype) {
    const badge = (t, cls) => `<span class="indicator-pill ${cls} pp-badge">${frappe.utils.escape_html(t)}</span>`;
    const typeColor = { "Access & safety": "red", "Customer preference": "blue", "Site condition": "orange", "Handoff": "purple", "Billing": "green", "General": "gray" };
    let rows = notes.map((n) => {
        const scope = n.scope !== doctype ? badge(`${__(n.scope)}: ${n.scope_name}`, "gray") : "";
        const pin = n.pinned ? `<span title="${__("Pinned")}">📌</span> ` : "";
        const vis = n.visibility !== "Everyone" ? badge(__(n.visibility), "yellow") : "";
        const when = frappe.datetime.prettyDate(n.creation);
        return `<div class="pp-note">
            <div class="pp-note-head">${pin}${badge(__(n.note_type), typeColor[n.note_type] || "gray")} ${vis} ${scope}
              <span class="text-muted small pp-note-meta">${frappe.utils.escape_html(n.author_name || "")} · ${frappe.utils.escape_html(n.author_role || "")} · ${when}</span>
              <a class="pp-note-open small" data-name="${n.name}" href="javascript:void(0)">${__("open")}</a></div>
            ${n.title ? `<div class="pp-note-title">${frappe.utils.escape_html(n.title)}</div>` : ""}
            <div class="pp-note-body">${n.content || ""}</div>
            ${n.image ? `<div><img src="${n.image}" class="pp-note-img"></div>` : ""}
        </div>`;
    }).join("");
    if (!rows) rows = `<div class="text-muted">${__("No notes yet")}</div>`;
    return `<style>
        .pp-note{padding:8px 0;border-bottom:1px solid var(--border-color)} .pp-note:last-child{border-bottom:0}
        .pp-note-head{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:4px}
        .pp-note-meta{margin-left:auto} .pp-note-title{font-weight:600;margin:2px 0}
        .pp-note-body p{margin:0 0 4px} .pp-note-img{max-height:160px;border-radius:6px;margin-top:6px}
        .pp-badge{font-size:11px}
    </style>
    <div class="pp-notes">${rows}</div>
    <div style="margin-top:8px"><button class="btn btn-xs btn-default pp-note-add">${__("Add note")}</button></div>`;
};

powerpro.notes.add = function (frm, links) {
    const d = new frappe.ui.Dialog({
        title: __("New field note"),
        fields: [
            { fieldname: "note_type", fieldtype: "Select", label: __("Type"), reqd: 1, default: "General",
              options: ["General", "Access & safety", "Customer preference", "Site condition", "Handoff", "Billing"] },
            { fieldname: "visibility", fieldtype: "Select", label: __("Visible to"), reqd: 1, default: "Everyone",
              options: powerpro.notes.levels() },
            { fieldname: "pinned", fieldtype: "Check", label: __("Pinned (always on top)") },
            { fieldname: "content", fieldtype: "Small Text", label: __("Note"), reqd: 1 },
            { fieldname: "image", fieldtype: "Attach Image", label: __("Photo") },
        ],
        primary_action_label: __("Save"),
        primary_action: (v) => {
            const doc = Object.assign({ doctype: "Field Note" }, v);
            ["customer", "property", "project", "visit"].forEach((k) => { if (links[k]) doc[k] = links[k]; });
            frappe.db.insert(doc).then(() => { d.hide(); frm.reload_doc(); });
        },
    });
    d.show();
};

powerpro.notes.levels = function () {
    if (frappe.user.has_role(["PP Owner", "System Manager"]) || frappe.session.user === "Administrator") return ["Everyone", "Office", "Owner"];
    if (frappe.user.has_role(["PP Dispatcher", "PP Estimator", "PP Shop", "PP Bookkeeper", "PP Integration"])) return ["Everyone", "Office"];
    return ["Everyone"];
};
