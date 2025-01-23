nxenv.listview_settings["Dashboard"] = {
	button: {
		show(doc) {
			return doc.name;
		},
		get_label() {
			return nxenv.utils.icon("dashboard-list", "sm");
		},
		get_description(doc) {
			return __("View {0}", [`${doc.name}`]);
		},
		action(doc) {
			nxenv.set_route("dashboard-view", doc.name);
		},
	},
};
