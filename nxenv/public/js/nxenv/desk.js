// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

// __('Modules') __('Domains') __('Places') __('Administration') # for translation, don't remove

nxenv.start_app = function () {
	if (!nxenv.Application) return;
	nxenv.assets.check();
	nxenv.provide("nxenv.app");
	nxenv.provide("nxenv.desk");
	nxenv.app = new nxenv.Application();
};

$(document).ready(function () {
	if (!nxenv.utils.supportsES6) {
		nxenv.msgprint({
			indicator: "red",
			title: __("Browser not supported"),
			message: __(
				"Some of the features might not work in your browser. Please update your browser to the latest version."
			),
		});
	}
	nxenv.start_app();
});

nxenv.Application = class Application {
	constructor() {
		this.startup();
	}

	startup() {
		nxenv.realtime.init();
		nxenv.model.init();

		this.load_bootinfo();
		this.load_user_permissions();
		this.make_nav_bar();
		this.make_sidebar();
		this.set_favicon();
		this.set_fullwidth_if_enabled();
		this.add_browser_class();
		this.setup_energy_point_listeners();
		this.setup_copy_doc_listener();
		this.setup_broadcast_listeners();

		nxenv.ui.keys.setup();

		this.setup_theme();

		// page container
		this.make_page_container();
		this.setup_tours();
		this.set_route();

		// trigger app startup
		$(document).trigger("startup");
		$(document).trigger("app_ready");

		this.show_notices();
		this.show_notes();

		if (nxenv.ui.startup_setup_dialog && !nxenv.boot.setup_complete) {
			nxenv.ui.startup_setup_dialog.pre_show();
			nxenv.ui.startup_setup_dialog.show();
		}

		// listen to build errors
		this.setup_build_events();

		if (nxenv.sys_defaults.email_user_password) {
			var email_list = nxenv.sys_defaults.email_user_password.split(",");
			for (var u in email_list) {
				if (email_list[u] === nxenv.user.name) {
					this.set_password(email_list[u]);
				}
			}
		}

		// REDESIGN-TODO: Fix preview popovers
		this.link_preview = new nxenv.ui.LinkPreview();

		nxenv.broadcast.emit("boot", {
			csrf_token: nxenv.csrf_token,
			user: nxenv.session.user,
		});
	}

	make_sidebar() {
		this.sidebar = new nxenv.ui.Sidebar({});
	}

	setup_theme() {
		nxenv.ui.keys.add_shortcut({
			shortcut: "shift+ctrl+g",
			description: __("Switch Theme"),
			action: () => {
				if (nxenv.theme_switcher && nxenv.theme_switcher.dialog.is_visible) {
					nxenv.theme_switcher.hide();
				} else {
					nxenv.theme_switcher = new nxenv.ui.ThemeSwitcher();
					nxenv.theme_switcher.show();
				}
			},
		});

		nxenv.ui.add_system_theme_switch_listener();
		const root = document.documentElement;

		const observer = new MutationObserver(() => {
			nxenv.ui.set_theme();
		});
		observer.observe(root, {
			attributes: true,
			attributeFilter: ["data-theme-mode"],
		});

		nxenv.ui.set_theme();
	}

	setup_tours() {
		if (
			!window.Cypress &&
			nxenv.boot.onboarding_tours &&
			nxenv.boot.user.onboarding_status != null
		) {
			let pending_tours = !nxenv.boot.onboarding_tours.every(
				(tour) => nxenv.boot.user.onboarding_status[tour[0]]?.is_complete
			);
			if (pending_tours && nxenv.boot.onboarding_tours.length > 0) {
				nxenv.require("onboarding_tours.bundle.js", () => {
					nxenv.utils.sleep(1000).then(() => {
						nxenv.ui.init_onboarding_tour();
					});
				});
			}
		}
	}

	show_notices() {
		if (nxenv.boot.messages) {
			nxenv.msgprint(nxenv.boot.messages);
		}

		if (nxenv.user_roles.includes("System Manager")) {
			// delayed following requests to make boot faster
			setTimeout(() => {
				this.show_change_log();
				this.show_update_available();
			}, 1000);
		}

		if (!nxenv.boot.developer_mode) {
			let console_security_message = __(
				"Using this console may allow attackers to impersonate you and steal your information. Do not enter or paste code that you do not understand."
			);
			console.log(`%c${console_security_message}`, "font-size: large");
		}

		nxenv.realtime.on("version-update", function () {
			var dialog = nxenv.msgprint({
				message: __(
					"The application has been updated to a new version, please refresh this page"
				),
				indicator: "green",
				title: __("Version Updated"),
			});
			dialog.set_primary_action(__("Refresh"), function () {
				location.reload(true);
			});
			dialog.get_close_btn().toggle(false);
		});
	}

	set_route() {
		if (nxenv.boot && localStorage.getItem("session_last_route")) {
			nxenv.set_route(localStorage.getItem("session_last_route"));
			localStorage.removeItem("session_last_route");
		} else {
			// route to home page
			nxenv.router.route();
		}
		nxenv.router.on("change", () => {
			$(".tooltip").hide();
		});
	}

	set_password(user) {
		var me = this;
		nxenv.call({
			method: "nxenv.core.doctype.user.user.get_email_awaiting",
			args: {
				user: user,
			},
			callback: function (email_account) {
				email_account = email_account["message"];
				if (email_account) {
					var i = 0;
					if (i < email_account.length) {
						me.email_password_prompt(email_account, user, i);
					}
				}
			},
		});
	}

	email_password_prompt(email_account, user, i) {
		var me = this;
		const email_id = email_account[i]["email_id"];
		let d = new nxenv.ui.Dialog({
			title: __("Password missing in Email Account"),
			fields: [
				{
					fieldname: "password",
					fieldtype: "Password",
					label: __(
						"Please enter the password for: <b>{0}</b>",
						[email_id],
						"Email Account"
					),
					reqd: 1,
				},
				{
					fieldname: "submit",
					fieldtype: "Button",
					label: __("Submit", null, "Submit password for Email Account"),
				},
			],
		});
		d.get_input("submit").on("click", function () {
			//setup spinner
			d.hide();
			var s = new nxenv.ui.Dialog({
				title: __("Checking one moment"),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "checking",
					},
				],
			});
			s.fields_dict.checking.$wrapper.html('<i class="fa fa-spinner fa-spin fa-4x"></i>');
			s.show();
			nxenv.call({
				method: "nxenv.email.doctype.email_account.email_account.set_email_password",
				args: {
					email_account: email_account[i]["email_account"],
					password: d.get_value("password"),
				},
				callback: function (passed) {
					s.hide();
					d.hide(); //hide waiting indication
					if (!passed["message"]) {
						nxenv.show_alert(
							{ message: __("Login Failed please try again"), indicator: "error" },
							5
						);
						me.email_password_prompt(email_account, user, i);
					} else {
						if (i + 1 < email_account.length) {
							i = i + 1;
							me.email_password_prompt(email_account, user, i);
						}
					}
				},
			});
		});
		d.show();
	}
	load_bootinfo() {
		if (nxenv.boot) {
			this.setup_workspaces();
			nxenv.model.sync(nxenv.boot.docs);
			this.check_metadata_cache_status();
			this.set_globals();
			this.sync_pages();
			nxenv.router.setup();
			this.setup_moment();
			if (nxenv.boot.print_css) {
				nxenv.dom.set_style(nxenv.boot.print_css, "print-style");
			}
			nxenv.user.name = nxenv.boot.user.name;
			nxenv.router.setup();
		} else {
			this.set_as_guest();
		}
	}

	setup_workspaces() {
		nxenv.modules = {};
		nxenv.workspaces = {};
		nxenv.boot.allowed_workspaces = nxenv.boot.sidebar_pages.pages;

		for (let page of nxenv.boot.allowed_workspaces || []) {
			nxenv.modules[page.module] = page;
			nxenv.workspaces[nxenv.router.slug(page.name)] = page;
		}
	}

	load_user_permissions() {
		nxenv.defaults.load_user_permission_from_boot();

		nxenv.realtime.on(
			"update_user_permissions",
			nxenv.utils.debounce(() => {
				nxenv.defaults.update_user_permissions();
			}, 500)
		);
	}

	check_metadata_cache_status() {
		if (nxenv.boot.metadata_version != localStorage.metadata_version) {
			nxenv.assets.clear_local_storage();
			nxenv.assets.init_local_storage();
		}
	}

	set_globals() {
		nxenv.session.user = nxenv.boot.user.name;
		nxenv.session.logged_in_user = nxenv.boot.user.name;
		nxenv.session.user_email = nxenv.boot.user.email;
		nxenv.session.user_fullname = nxenv.user_info().fullname;

		nxenv.user_defaults = nxenv.boot.user.defaults;
		nxenv.user_roles = nxenv.boot.user.roles;
		nxenv.sys_defaults = nxenv.boot.sysdefaults;

		nxenv.ui.py_date_format = nxenv.boot.sysdefaults.date_format
			.replace("dd", "%d")
			.replace("mm", "%m")
			.replace("yyyy", "%Y");
		nxenv.boot.user.last_selected_values = {};
	}
	sync_pages() {
		// clear cached pages if timestamp is not found
		if (localStorage["page_info"]) {
			nxenv.boot.allowed_pages = [];
			var page_info = JSON.parse(localStorage["page_info"]);
			$.each(nxenv.boot.page_info, function (name, p) {
				if (!page_info[name] || page_info[name].modified != p.modified) {
					delete localStorage["_page:" + name];
				}
				nxenv.boot.allowed_pages.push(name);
			});
		} else {
			nxenv.boot.allowed_pages = Object.keys(nxenv.boot.page_info);
		}
		localStorage["page_info"] = JSON.stringify(nxenv.boot.page_info);
	}
	set_as_guest() {
		nxenv.session.user = "Guest";
		nxenv.session.user_email = "";
		nxenv.session.user_fullname = "Guest";

		nxenv.user_defaults = {};
		nxenv.user_roles = ["Guest"];
		nxenv.sys_defaults = {};
	}
	make_page_container() {
		if ($("#body").length) {
			$(".splash").remove();
			nxenv.temp_container = $("<div id='temp-container' style='display: none;'>").appendTo(
				"body"
			);
			nxenv.container = new nxenv.views.Container();
		}
	}
	make_nav_bar() {
		// toolbar
		if (nxenv.boot && nxenv.boot.home_page !== "setup-wizard") {
			nxenv.nxenv_toolbar = new nxenv.ui.toolbar.Toolbar();
		}
	}
	logout() {
		var me = this;
		me.logged_out = true;
		return nxenv.call({
			method: "logout",
			callback: function (r) {
				if (r.exc) {
					return;
				}
				me.redirect_to_login();
			},
		});
	}
	handle_session_expired() {
		nxenv.app.redirect_to_login();
	}
	redirect_to_login() {
		window.location.href = `/login?redirect-to=${encodeURIComponent(
			window.location.pathname + window.location.search
		)}`;
	}
	set_favicon() {
		var link = $('link[type="image/x-icon"]').remove().attr("href");
		$('<link rel="shortcut icon" href="' + link + '" type="image/x-icon">').appendTo("head");
		$('<link rel="icon" href="' + link + '" type="image/x-icon">').appendTo("head");
	}
	trigger_primary_action() {
		// to trigger change event on active input before triggering primary action
		$(document.activeElement).blur();
		// wait for possible JS validations triggered after blur (it might change primary button)
		setTimeout(() => {
			if (window.cur_dialog && cur_dialog.display && !cur_dialog.is_minimized) {
				// trigger primary
				cur_dialog.get_primary_btn().trigger("click");
			} else if (cur_frm && cur_frm.page.btn_primary.is(":visible")) {
				cur_frm.page.btn_primary.trigger("click");
			} else if (nxenv.container.page.save_action) {
				nxenv.container.page.save_action();
			}
		}, 100);
	}

	show_change_log() {
		var me = this;
		let change_log = nxenv.boot.change_log;

		// nxenv.boot.change_log = [{
		// 	"change_log": [
		// 		[<version>, <change_log in markdown>],
		// 		[<version>, <change_log in markdown>],
		// 	],
		// 	"description": "ERP made simple",
		// 	"title": "ERPNext",
		// 	"version": "12.2.0"
		// }];

		if (
			!Array.isArray(change_log) ||
			!change_log.length ||
			window.Cypress ||
			cint(nxenv.boot.sysdefaults.disable_change_log_notification)
		) {
			return;
		}

		// Iterate over changelog
		var change_log_dialog = nxenv.msgprint({
			message: nxenv.render_template("change_log", { change_log: change_log }),
			title: __("Updated To A New Version 🎉"),
			wide: true,
		});
		change_log_dialog.keep_open = true;
		change_log_dialog.custom_onhide = function () {
			nxenv.call({
				method: "nxenv.utils.change_log.update_last_known_versions",
			});
			me.show_notes();
		};
	}

	show_update_available() {
		if (!nxenv.boot.has_app_updates) return;
		nxenv.xcall("nxenv.utils.change_log.show_update_popup");
	}

	add_browser_class() {
		$("html").addClass(nxenv.utils.get_browser().name.toLowerCase());
	}

	set_fullwidth_if_enabled() {
		nxenv.ui.toolbar.set_fullwidth_if_enabled();
	}

	show_notes() {
		var me = this;
		if (nxenv.boot.notes.length) {
			nxenv.boot.notes.forEach(function (note) {
				if (!note.seen || note.notify_on_every_login) {
					var d = nxenv.msgprint({ message: note.content, title: note.title });
					d.keep_open = true;
					d.custom_onhide = function () {
						note.seen = true;

						// Mark note as read if the Notify On Every Login flag is not set
						if (!note.notify_on_every_login) {
							nxenv.call({
								method: "nxenv.desk.doctype.note.note.mark_as_seen",
								args: {
									note: note.name,
								},
							});
						}

						// next note
						me.show_notes();
					};
				}
			});
		}
	}

	setup_build_events() {
		if (nxenv.boot.developer_mode) {
			nxenv.require("build_events.bundle.js");
		}
	}

	setup_energy_point_listeners() {
		nxenv.realtime.on("energy_point_alert", (message) => {
			nxenv.show_alert(message);
		});
	}

	setup_copy_doc_listener() {
		$("body").on("paste", (e) => {
			try {
				let pasted_data = nxenv.utils.get_clipboard_data(e);
				let doc = JSON.parse(pasted_data);
				if (doc.doctype) {
					e.preventDefault();
					const sleep = nxenv.utils.sleep;

					nxenv.dom.freeze(__("Creating {0}", [doc.doctype]) + "...");
					// to avoid abrupt UX
					// wait for activity feedback
					sleep(500).then(() => {
						let res = nxenv.model.with_doctype(doc.doctype, () => {
							let newdoc = nxenv.model.copy_doc(doc);
							newdoc.__newname = doc.name;
							delete doc.name;
							newdoc.idx = null;
							newdoc.__run_link_triggers = false;
							nxenv.set_route("Form", newdoc.doctype, newdoc.name);
							nxenv.dom.unfreeze();
						});
						res && res.fail?.(nxenv.dom.unfreeze);
					});
				}
			} catch (e) {
				//
			}
		});
	}

	/// Setup event listeners for events across browser tabs / web workers.
	setup_broadcast_listeners() {
		// booted in another tab -> refresh csrf to avoid invalid requests.
		nxenv.broadcast.on("boot", ({ csrf_token, user }) => {
			if (user && user != nxenv.session.user) {
				nxenv.msgprint({
					message: __(
						"You've logged in as another user from another tab. Refresh this page to continue using system."
					),
					title: __("User Changed"),
					primary_action: {
						label: __("Refresh"),
						action: () => {
							window.location.reload();
						},
					},
				});
				return;
			}

			if (csrf_token) {
				// If user re-logged in then their other tabs won't be usable without this update.
				nxenv.csrf_token = csrf_token;
			}
		});
	}

	setup_moment() {
		moment.updateLocale("en", {
			week: {
				dow: nxenv.datetime.get_first_day_of_the_week_index(),
			},
		});
		moment.locale("en");
		moment.user_utc_offset = moment().utcOffset();
		if (nxenv.boot.timezone_info) {
			moment.tz.add(nxenv.boot.timezone_info);
		}
	}
};

nxenv.get_module = function (m, default_module) {
	var module = nxenv.modules[m] || default_module;
	if (!module) {
		return;
	}

	if (module._setup) {
		return module;
	}

	if (!module.label) {
		module.label = m;
	}

	if (!module._label) {
		module._label = __(module.label);
	}

	module._setup = true;

	return module;
};
