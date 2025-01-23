nxenv.pages["backups"].on_page_load = function (wrapper) {
	var page = nxenv.ui.make_app_page({
		parent: wrapper,
		title: __("Download Backups"),
		single_column: true,
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		nxenv.set_route("Form", "System Settings");
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		nxenv.call({
			method: "nxenv.desk.page.backups.backups.schedule_files_backup",
			args: { user_email: nxenv.session.user_email },
		});
	});

	page.add_inner_button(__("Get Backup Encryption Key"), function () {
		if (nxenv.user.has_role("System Manager")) {
			nxenv.verify_password(function () {
				nxenv.call({
					method: "nxenv.utils.backups.get_backup_encryption_key",
					callback: function (r) {
						nxenv.msgprint({
							title: __("Backup Encryption Key"),
							message: __(r.message),
							indicator: "blue",
						});
					},
				});
			});
		} else {
			nxenv.msgprint({
				title: __("Error"),
				message: __("System Manager privileges required."),
				indicator: "red",
			});
		}
	});

	nxenv.breadcrumbs.add("Setup");

	$(nxenv.render_template("backups")).appendTo(page.body.addClass("no-border"));
};
