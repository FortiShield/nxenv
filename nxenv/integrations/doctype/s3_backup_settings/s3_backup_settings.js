// Copyright (c) 2017, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.ui.form.on("S3 Backup Settings", {
	refresh: function (frm) {
		frm.clear_custom_buttons();
		frm.events.take_backup(frm);
	},

	take_backup: function (frm) {
		if (frm.doc.access_key_id && frm.doc.secret_access_key) {
			frm.add_custom_button(__("Take Backup Now"), function () {
				frm.dashboard.set_headline_alert("S3 Backup Started!");
				nxenv.call({
					method: "nxenv.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_s3",
					callback: function (r) {
						if (!r.exc) {
							nxenv.msgprint(__("S3 Backup complete!"));
							frm.dashboard.clear_headline();
						}
					},
				});
			}).addClass("btn-primary");
		}
	},
});
