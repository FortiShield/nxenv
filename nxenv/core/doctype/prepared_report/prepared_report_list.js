nxenv.listview_settings["Prepared Report"] = {
	onload: function (list_view) {
		nxenv.require("logtypes.bundle.js", () => {
			nxenv.utils.logtypes.show_log_retention_message(list_view.doctype);
		});
	},
};
