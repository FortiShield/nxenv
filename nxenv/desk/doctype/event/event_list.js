nxenv.listview_settings["Event"] = {
	add_fields: ["starts_on", "ends_on"],
	onload: function () {
		nxenv.route_options = {
			status: "Open",
		};
	},
};
