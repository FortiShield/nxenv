nxenv.provide("nxenv.model.user_settings");

$.extend(nxenv.model.user_settings, {
	get: function (doctype) {
		return nxenv
			.call("nxenv.model.utils.user_settings.get", { doctype })
			.then((r) => JSON.parse(r.message || "{}"));
	},
	save: function (doctype, key, value) {
		if (nxenv.session.user === "Guest") return Promise.resolve();

		const old_user_settings = nxenv.model.user_settings[doctype] || {};
		const new_user_settings = $.extend(true, {}, old_user_settings); // deep copy

		if ($.isPlainObject(value)) {
			new_user_settings[key] = new_user_settings[key] || {};
			$.extend(new_user_settings[key], value);
		} else {
			new_user_settings[key] = value;
		}

		const a = JSON.stringify(old_user_settings);
		const b = JSON.stringify(new_user_settings);
		if (a !== b) {
			// update if changed
			return this.update(doctype, new_user_settings);
		}
		return Promise.resolve(new_user_settings);
	},
	remove: function (doctype, key) {
		var user_settings = nxenv.model.user_settings[doctype] || {};
		delete user_settings[key];

		return this.update(doctype, user_settings);
	},
	update: function (doctype, user_settings) {
		if (nxenv.session.user === "Guest") return Promise.resolve();
		return nxenv.call({
			method: "nxenv.model.utils.user_settings.save",
			args: {
				doctype: doctype,
				user_settings: user_settings,
			},
			callback: function (r) {
				nxenv.model.user_settings[doctype] = r.message;
			},
		});
	},
});

nxenv.get_user_settings = function (doctype, key) {
	var settings = nxenv.model.user_settings[doctype] || {};
	if (key) {
		settings = settings[key] || {};
	}
	return settings;
};
