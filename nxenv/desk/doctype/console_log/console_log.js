// Copyright (c) 2020, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("Console Log", {
	refresh: function (frm) {
		frm.add_custom_button(__("Re-Run in Console"), () => {
			window.localStorage.setItem("system_console_code", frm.doc.script);
			window.localStorage.setItem("system_console_type", frm.doc.type);
			nxenv.set_route("Form", "System Console");
		});
	},
});
