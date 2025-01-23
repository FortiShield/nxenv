// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// License: See license.txt

nxenv.ui.form.on("Currency", {
	refresh(frm) {
		frm.set_intro("");
		if (!frm.doc.enabled) {
			frm.set_intro(__("This Currency is disabled. Enable to use in transactions"));
		}
	},
});
