nxenv.listview_settings["Notification Log"] = {
	onload: function (listview) {
		nxenv.require("logtypes.bundle.js", () => {
			nxenv.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};
