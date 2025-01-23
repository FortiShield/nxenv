nxenv.logout = function () {
	nxenv.call({
		method: "logout",
		callback: function (r) {
			if (r.exc) {
				return;
			}
			window.location.href = "/login";
		},
	});
};
