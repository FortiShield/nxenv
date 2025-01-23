nxenv.pages["user-profile"].on_page_load = function (wrapper) {
	nxenv.require("user_profile_controller.bundle.js", () => {
		let user_profile = new nxenv.ui.UserProfile(wrapper);
		user_profile.show();
	});
};
