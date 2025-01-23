nxenv.listview_settings["RQ Job"] = {
	hide_name_column: true,

	onload(listview) {
		if (!has_common(nxenv.user_roles, ["Administrator", "System Manager"])) return;

		listview.page.add_inner_button(
			__("Remove Failed Jobs"),
			() => {
				nxenv.confirm(__("Are you sure you want to remove all failed jobs?"), () => {
					nxenv.xcall("nxenv.core.doctype.rq_job.rq_job.remove_failed_jobs");
				});
			},
			__("Actions")
		);

		nxenv.xcall("nxenv.utils.scheduler.get_scheduler_status").then(({ status }) => {
			if (status === "active") {
				listview.page.set_indicator(__("Scheduler: Active"), "green");
			} else {
				listview.page.set_indicator(__("Scheduler: Inactive"), "red");
				listview.page.add_inner_button(
					__("Enable Scheduler"),
					() => {
						nxenv.confirm(__("Are you sure you want to re-enable scheduler?"), () => {
							nxenv
								.xcall("nxenv.utils.scheduler.activate_scheduler")
								.then(() => {
									nxenv.show_alert(__("Enabled Scheduler"));
								})
								.catch((e) => {
									nxenv.show_alert({
										message: __("Failed to enable scheduler: {0}", e),
										indicator: "error",
									});
								});
						});
					},
					__("Actions")
				);
			}
		});

		setInterval(() => {
			if (listview.list_view_settings.disable_auto_refresh) {
				return;
			}

			const route = nxenv.get_route() || [];
			if (route[0] != "List" || "RQ Job" != route[1]) {
				return;
			}

			listview.refresh();
		}, 15000);
	},
};
