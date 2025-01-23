// Copyright (c) 2024, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("Role Replication", {
	refresh(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Replicate"), ($btn) => {
			$btn.text(__("Replicating..."));
			nxenv.run_serially([
				() => nxenv.dom.freeze("Replicating..."),
				() => frm.call("replicate_role"),
				() => nxenv.dom.unfreeze(),
				() => nxenv.msgprint(__("Replication completed.")),
				() => $btn.text(__("Replicate")),
			]);
		});
	},
});
