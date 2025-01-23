// Copyright (c) 2022, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("RQ Job", {
	refresh: function (frm) {
		// Nothing in this form is supposed to be editable.
		frm.disable_form();
		frm.dashboard.set_headline_alert(
			__("This is a virtual doctype and data is cleared periodically.")
		);

		if (["started", "queued"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Force Stop job"), () => {
				nxenv.confirm(
					__(
						"This will terminate the job immediately and might be dangerous, are you sure? "
					),
					() => {
						nxenv
							.xcall("nxenv.core.doctype.rq_job.rq_job.stop_job", {
								job_id: frm.doc.name,
							})
							.then((r) => {
								nxenv.show_alert(__("Job Stopped Successfully"));
								frm.reload_doc();
							});
					}
				);
			});
		}
	},
});
