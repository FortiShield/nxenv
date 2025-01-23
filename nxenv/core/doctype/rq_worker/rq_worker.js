// Copyright (c) 2022, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("RQ Worker", {
	refresh: function (frm) {
		// Nothing in this form is supposed to be editable.
		frm.disable_form();
	},
});
