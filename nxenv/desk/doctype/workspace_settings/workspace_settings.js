// Copyright (c) 2024, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("Workspace Settings", {
	setup(frm) {
		frm.hide_full_form_button = true;
		frm.docfields = [];
		frm.workspace_map = {};
		let workspace_visibilty = JSON.parse(frm.doc.workspace_visibility_json || "{}");

		// build fields from workspaces
		let cnt = 0,
			column_added = false;
		for (let page of nxenv.boot.allowed_workspaces) {
			if (page.public) {
				frm.workspace_map[page.name] = page;
				cnt++;
				frm.docfields.push({
					fieldtype: "Check",
					fieldname: page.name,
					hidden: !nxenv.boot.app_data_map[nxenv.current_app].workspaces.includes(
						page.title
					),
					label: page.title + (page.parent_page ? ` (${page.parent_page})` : ""),
					initial_value: workspace_visibilty[page.name] !== 0, // not set is also visible
				});
			}
		}

		nxenv.temp = frm;
	},
	validate(frm) {
		frm.doc.workspace_visibility_json = JSON.stringify(frm.dialog.get_values());
		frm.doc.workspace_setup_completed = 1;
	},
	after_save(frm) {
		// reload page to show latest sidebar
		nxenv.app.sidebar.reload();
	},
});
