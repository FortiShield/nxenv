// Copyright (c) 2016, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("Email Queue", {
	refresh: function (frm) {
		if (["Not Sent", "Partially Sent"].includes(frm.doc.status)) {
			let button = frm.add_custom_button("Send Now", function () {
				nxenv.call({
					method: "nxenv.email.doctype.email_queue.email_queue.send_now",
					args: {
						name: frm.doc.name,
					},
					btn: button,
					callback: function () {
						frm.reload_doc();
						if (cint(nxenv.sys_defaults.suspend_email_queue)) {
							nxenv.show_alert(
								__(
									"Email queue is currently suspended. Resume to automatically send emails."
								)
							);
						}
					},
				});
			});
		} else if (frm.doc.status == "Error") {
			frm.add_custom_button("Retry Sending", function () {
				frm.call({
					method: "nxenv.email.doctype.email_queue.email_queue.retry_sending",
					args: {
						queues: [frm.doc.name],
					},
					callback: function () {
						frm.reload_doc();
						nxenv.show_alert({
							message: __(
								"Status Updated. The email will be picked up in the next scheduled run."
							),
							indicator: "green",
						});
					},
				});
			});
		}
	},
});
