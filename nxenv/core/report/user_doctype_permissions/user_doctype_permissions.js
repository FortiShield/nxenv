// Copyright (c) 2024, Nxenv Technologies and contributors
// For license information, please see license.txt

nxenv.query_reports["User Doctype Permissions"] = {
	filters: [
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
			reqd: 1,
		},
	],
};
