// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

if (nxenv.require) {
	nxenv.require("file_uploader.bundle.js");
} else {
	nxenv.ready(function () {
		nxenv.require("file_uploader.bundle.js");
	});
}
