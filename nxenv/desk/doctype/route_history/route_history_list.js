nxenv.listview_settings["Route History"] = {
	onload: function (listview) {
		nxenv.require("logtypes.bundle.js", () => {
			nxenv.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};
