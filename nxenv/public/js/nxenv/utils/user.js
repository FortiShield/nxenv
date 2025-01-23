nxenv.user_info = function (uid) {
	if (!uid) uid = nxenv.session.user;

	let user_info;
	if (!(nxenv.boot.user_info && nxenv.boot.user_info[uid])) {
		user_info = { fullname: uid || "Unknown" };
	} else {
		user_info = nxenv.boot.user_info[uid];
	}

	user_info.abbr = nxenv.get_abbr(user_info.fullname);
	user_info.color = nxenv.get_palette(user_info.fullname);

	return user_info;
};

nxenv.update_user_info = function (user_info) {
	for (let user in user_info) {
		if (nxenv.boot.user_info[user]) {
			Object.assign(nxenv.boot.user_info[user], user_info[user]);
		} else {
			nxenv.boot.user_info[user] = user_info[user];
		}
	}
};

nxenv.provide("nxenv.user");

$.extend(nxenv.user, {
	name: "Guest",
	full_name: function (uid) {
		return uid === nxenv.session.user
			? __(
					"You",
					null,
					"Name of the current user. For example: You edited this 5 hours ago."
			  )
			: nxenv.user_info(uid).fullname;
	},
	image: function (uid) {
		return nxenv.user_info(uid).image;
	},
	abbr: function (uid) {
		return nxenv.user_info(uid).abbr;
	},
	has_role: function (rl) {
		if (typeof rl == "string") rl = [rl];
		for (var i in rl) {
			if ((nxenv.boot ? nxenv.boot.user.roles : ["Guest"]).indexOf(rl[i]) != -1) return true;
		}
	},
	get_desktop_items: function () {
		// hide based on permission
		var modules_list = $.map(nxenv.boot.allowed_modules, function (icon) {
			var m = icon.module_name;
			var type = nxenv.modules[m] && nxenv.modules[m].type;

			if (nxenv.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if (nxenv.boot.user.allow_modules.indexOf(m) != -1 || nxenv.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if (nxenv.boot.allowed_pages.indexOf(nxenv.modules[m].link) != -1) ret = m;
			} else if (type === "list") {
				if (nxenv.model.can_read(nxenv.modules[m]._doctype)) ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if (nxenv.user.has_role("System Manager") || nxenv.user.has_role("Administrator"))
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_report_manager: function () {
		return nxenv.user.has_role(["Administrator", "System Manager", "Report Manager"]);
	},

	get_formatted_email: function (email) {
		var fullname = nxenv.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = "";

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl("%(quote)s%(fullname)s%(quote)s <%(email)s>", {
				fullname: fullname,
				email: email,
				quote: quote,
			});
		}
	},

	get_emails: () => {
		return Object.keys(nxenv.boot.user_info).map((key) => nxenv.boot.user_info[key].email);
	},

	/* Normally nxenv.user is an object
	 * having properties and methods.
	 * But in the following case
	 *
	 * if (nxenv.user === 'Administrator')
	 *
	 * nxenv.user will cast to a string
	 * returning nxenv.user.name
	 */
	toString: function () {
		return this.name;
	},
});

nxenv.session_alive = true;
$(document).bind("mousemove", function () {
	if (nxenv.session_alive === false) {
		$(document).trigger("session_alive");
	}
	nxenv.session_alive = true;
	if (nxenv.session_alive_timeout) clearTimeout(nxenv.session_alive_timeout);
	nxenv.session_alive_timeout = setTimeout("nxenv.session_alive=false;", 30000);
});
