// Copyright (c) 2017, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("Print Style", {
	refresh: function (frm) {
		frm.add_custom_button(__("Print Settings"), () => {
			nxenv.set_route("Form", "Print Settings");
		});
	},
});
