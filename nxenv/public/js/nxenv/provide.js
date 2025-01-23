// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// provide a namespace
if (!window.nxenv) window.nxenv = {};

nxenv.provide = function (namespace) {
	// docs: create a namespace //
	var nsl = namespace.split(".");
	var parent = window;
	for (var i = 0; i < nsl.length; i++) {
		var n = nsl[i];
		if (!parent[n]) {
			parent[n] = {};
		}
		parent = parent[n];
	}
	return parent;
};

nxenv.provide("locals");
nxenv.provide("nxenv.flags");
nxenv.provide("nxenv.settings");
nxenv.provide("nxenv.utils");
nxenv.provide("nxenv.ui.form");
nxenv.provide("nxenv.modules");
nxenv.provide("nxenv.templates");
nxenv.provide("nxenv.test_data");
nxenv.provide("nxenv.utils");
nxenv.provide("nxenv.model");
nxenv.provide("nxenv.user");
nxenv.provide("nxenv.session");
nxenv.provide("nxenv._messages");
nxenv.provide("locals.DocType");

// for listviews
nxenv.provide("nxenv.listview_settings");
nxenv.provide("nxenv.tour");
nxenv.provide("nxenv.listview_parent_route");

// constants
window.NEWLINE = "\n";
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// API globals
window.cur_frm = null;
