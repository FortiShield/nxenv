nxenv.ui.form.on("User", {
	setup: function (frm) {
		frm.set_query("default_workspace", () => {
			return {
				filters: {
					for_user: ["in", [null, nxenv.session.user]],
					title: ["!=", "Welcome Workspace"],
				},
			};
		});
	},
	before_load: function (frm) {
		let update_tz_options = function () {
			frm.fields_dict.time_zone.set_data(nxenv.all_timezones);
		};

		if (!nxenv.all_timezones) {
			nxenv.call({
				method: "nxenv.core.doctype.user.user.get_timezones",
				callback: function (r) {
					nxenv.all_timezones = r.message.timezones;
					update_tz_options();
				},
			});
		} else {
			update_tz_options();
		}
	},

	time_zone: function (frm) {
		if (frm.doc.time_zone && frm.doc.time_zone.startsWith("Etc")) {
			frm.set_df_property(
				"time_zone",
				"description",
				__("Note: Etc timezones have their signs reversed.")
			);
		}
	},

	role_profiles: function (frm) {
		if (frm.doc.role_profiles && frm.doc.role_profiles.length) {
			frm.roles_editor.disable = 1;
			frm.call("populate_role_profile_roles").then(() => {
				frm.roles_editor.show();
			});
		} else {
			frm.roles_editor.disable = 0;
			frm.roles_editor.show();
		}
	},

	module_profile: function (frm) {
		if (frm.doc.module_profile) {
			nxenv.call({
				method: "nxenv.core.doctype.user.user.get_module_profile",
				args: {
					module_profile: frm.doc.module_profile,
				},
				callback: function (data) {
					frm.set_value("block_modules", []);
					$.each(data.message || [], function (i, v) {
						let d = frm.add_child("block_modules");
						d.module = v.module;
					});
					frm.module_editor && frm.module_editor.show();
				},
			});
		}
	},

	onload: function (frm) {
		frm.can_edit_roles = has_access_to_edit_user();

		if (frm.is_new() && frm.roles_editor) {
			frm.roles_editor.reset();
		}

		if (
			frm.can_edit_roles &&
			!frm.is_new() &&
			["System User", "Website User"].includes(frm.doc.user_type)
		) {
			if (!frm.roles_editor) {
				const role_area = $('<div class="role-editor">').appendTo(
					frm.fields_dict.roles_html.wrapper
				);

				frm.roles_editor = new nxenv.RoleEditor(
					role_area,
					frm,
					frm.doc.role_profiles && frm.doc.role_profiles.length ? 1 : 0
				);

				if (frm.doc.user_type == "System User") {
					var module_area = $("<div>").appendTo(frm.fields_dict.modules_html.wrapper);
					frm.module_editor = new nxenv.ModuleEditor(frm, module_area);
				}
			} else {
				frm.roles_editor.show();
			}
		}
	},
	refresh: function (frm) {
		let doc = frm.doc;

		nxenv.xcall("nxenv.apps.get_apps").then((r) => {
			let apps = r?.map((r) => r.name) || [];
			frm.set_df_property("default_app", "options", [" ", ...apps]);
		});

		if (frm.is_new()) {
			frm.set_value("time_zone", nxenv.sys_defaults.time_zone);
		}

		if (
			["System User", "Website User"].includes(frm.doc.user_type) &&
			!frm.is_new() &&
			!frm.roles_editor &&
			frm.can_edit_roles
		) {
			frm.reload_doc();
			return;
		}

		frm.toggle_display(["sb1", "sb3", "modules_access"], false);
		frm.trigger("setup_impersonation");

		if (!frm.is_new()) {
			if (has_access_to_edit_user()) {
				frm.add_custom_button(
					__("Set User Permissions"),
					function () {
						nxenv.route_options = {
							user: doc.name,
						};
						nxenv.set_route("List", "User Permission");
					},
					__("Permissions")
				);

				frm.add_custom_button(
					__("View Permitted Documents"),
					() =>
						nxenv.set_route("query-report", "Permitted Documents For User", {
							user: frm.doc.name,
						}),
					__("Permissions")
				);

				frm.add_custom_button(
					__("View Doctype Permissions"),
					() =>
						nxenv.set_route("query-report", "User Doctype Permissions", {
							user: frm.doc.name,
						}),
					__("Permissions")
				);

				frm.toggle_display(["sb1", "sb3", "modules_access"], true);
			}

			frm.add_custom_button(
				__("Reset Password"),
				function () {
					nxenv.call({
						method: "nxenv.core.doctype.user.user.reset_password",
						args: {
							user: frm.doc.name,
						},
					});
				},
				__("Password")
			);

			if (nxenv.user.has_role("System Manager")) {
				nxenv.db.get_single_value("LDAP Settings", "enabled").then((value) => {
					if (value === 1 && frm.doc.name != "Administrator") {
						frm.add_custom_button(
							__("Reset LDAP Password"),
							function () {
								const d = new nxenv.ui.Dialog({
									title: __("Reset LDAP Password"),
									fields: [
										{
											label: __("New Password"),
											fieldtype: "Password",
											fieldname: "new_password",
											reqd: 1,
										},
										{
											label: __("Confirm New Password"),
											fieldtype: "Password",
											fieldname: "confirm_password",
											reqd: 1,
										},
										{
											label: __("Logout All Sessions"),
											fieldtype: "Check",
											fieldname: "logout_sessions",
										},
									],
									primary_action: (values) => {
										d.hide();
										if (values.new_password !== values.confirm_password) {
											nxenv.throw(__("Passwords do not match!"));
										}
										nxenv.call(
											"nxenv.integrations.doctype.ldap_settings.ldap_settings.reset_password",
											{
												user: frm.doc.email,
												password: values.new_password,
												logout: values.logout_sessions,
											}
										);
									},
								});
								d.show();
							},
							__("Password")
						);
					}
				});
			}

			if (
				cint(nxenv.boot.sysdefaults.enable_two_factor_auth) &&
				(nxenv.session.user == doc.name || nxenv.user.has_role("System Manager"))
			) {
				frm.add_custom_button(
					__("Reset OTP Secret"),
					function () {
						nxenv.call({
							method: "nxenv.twofactor.reset_otp_secret",
							args: {
								user: frm.doc.name,
							},
						});
					},
					__("Password")
				);
			}

			frm.trigger("enabled");

			if (frm.roles_editor && frm.can_edit_roles) {
				frm.roles_editor.disable =
					frm.doc.role_profiles && frm.doc.role_profiles.length ? 1 : 0;
				frm.roles_editor.show();
			}

			frm.module_editor && frm.module_editor.show();

			if (nxenv.session.user == doc.name) {
				// update display settings
				if (doc.user_image) {
					nxenv.boot.user_info[nxenv.session.user].image = nxenv.utils.get_file_link(
						doc.user_image
					);
				}
			}
		}
		if (frm.doc.user_emails && nxenv.model.can_create("Email Account")) {
			var found = 0;
			for (var i = 0; i < frm.doc.user_emails.length; i++) {
				if (frm.doc.email == frm.doc.user_emails[i].email_id) {
					found = 1;
				}
			}
			if (!found) {
				frm.add_custom_button(__("Create User Email"), function () {
					if (!frm.doc.email) {
						nxenv.msgprint(__("Email is mandatory to create User Email"));
						return;
					}
					frm.events.create_user_email(frm);
				});
			}
		}

		if (nxenv.route_flags.unsaved === 1) {
			delete nxenv.route_flags.unsaved;
			for (let i = 0; i < frm.doc.user_emails.length; i++) {
				frm.doc.user_emails[i].idx = frm.doc.user_emails[i].idx + 1;
			}
			frm.dirty();
		}
		frm.trigger("time_zone");
	},
	validate: function (frm) {
		if (frm.roles_editor) {
			frm.roles_editor.set_roles_in_table();
		}
	},
	enabled: function (frm) {
		var doc = frm.doc;
		if (!frm.is_new() && has_access_to_edit_user()) {
			frm.toggle_display(["sb1", "sb3", "modules_access"], doc.enabled);
			frm.set_df_property("enabled", "read_only", 0);
		}

		if (frm.doc.name !== "Administrator") {
			frm.toggle_enable("email", frm.is_new());
		}
	},
	create_user_email: function (frm) {
		nxenv.call({
			method: "nxenv.core.doctype.user.user.has_email_account",
			args: {
				email: frm.doc.email,
			},
			callback: function (r) {
				if (!Array.isArray(r.message) || !r.message.length) {
					nxenv.route_options = {
						email_id: frm.doc.email,
						awaiting_password: 1,
						enable_incoming: 1,
					};
					nxenv.model.with_doctype("Email Account", function (doc) {
						doc = nxenv.model.get_new_doc("Email Account");
						nxenv.route_flags.linked_user = frm.doc.name;
						nxenv.route_flags.delete_user_from_locals = true;
						nxenv.set_route("Form", "Email Account", doc.name);
					});
				} else {
					nxenv.route_flags.create_user_account = frm.doc.name;
					nxenv.set_route("Form", "Email Account", r.message[0]["name"]);
				}
			},
		});
	},
	generate_keys: function (frm) {
		nxenv.call({
			method: "nxenv.core.doctype.user.user.generate_keys",
			args: {
				user: frm.doc.name,
			},
			callback: function (r) {
				if (r.message) {
					nxenv.msgprint(__("Save API Secret: {0}", [r.message.api_secret]));
					frm.reload_doc();
				}
			},
		});
	},
	after_save: function (frm) {
		/**
		 * Checks whether the effective value has changed.
		 *
		 * @param {Array.<string>} - Tuple with new override, previous override,
		 *   and optionally fallback.
		 * @returns {boolean} - Whether the resulting value has effectively changed
		 */
		const has_effectively_changed = ([new_override, prev_override, fallback = undefined]) => {
			const prev_effective = prev_override || fallback;
			const new_effective = new_override || fallback;
			return new_override !== undefined && prev_effective !== new_effective;
		};

		const doc = frm.doc;
		const boot = nxenv.boot;
		const attr_tuples = [
			[doc.language, boot.user.language, boot.sysdefaults.language],
			[doc.time_zone, boot.time_zone.user, boot.time_zone.system],
			[doc.desk_theme, boot.user.desk_theme], // No system default.
		];

		if (doc.name === nxenv.session.user && attr_tuples.some(has_effectively_changed)) {
			nxenv.msgprint(__("Refreshing..."));
			window.location.reload();
		}
	},
	setup_impersonation: function (frm) {
		if (
			nxenv.session.user === "Administrator" &&
			frm.doc.name != "Administrator" &&
			!frm.is_new()
		) {
			frm.add_custom_button(__("Impersonate"), () => {
				if (frm.doc.restrict_ip) {
					nxenv.msgprint({
						message:
							"There's IP restriction for this user, you can not impersonate as this user.",
						title: "IP restriction is enabled",
					});
					return;
				}
				nxenv.prompt(
					[
						{
							fieldname: "reason",
							fieldtype: "Small Text",
							label: "Reason for impersonating",
							description: __("Note: This will be shared with user."),
							reqd: 1,
						},
					],
					(values) => {
						nxenv
							.xcall("nxenv.core.doctype.user.user.impersonate", {
								user: frm.doc.name,
								reason: values.reason,
							})
							.then(() => window.location.reload());
					},
					__("Impersonate as {0}", [frm.doc.name]),
					__("Confirm")
				);
			});
		}
	},
});

nxenv.ui.form.on("User Email", {
	email_account(frm, cdt, cdn) {
		let child_row = locals[cdt][cdn];
		nxenv.model.get_value("Email Account", child_row.email_account, "auth_method", (value) => {
			child_row.used_oauth = value.auth_method === "OAuth";
			frm.refresh_field("user_emails", cdn, "used_oauth");
		});
	},
});

function has_access_to_edit_user() {
	return has_common(nxenv.user_roles, get_roles_for_editing_user());
}

function get_roles_for_editing_user() {
	return (
		nxenv
			.get_meta("User")
			.permissions.filter((perm) => perm.permlevel >= 1 && perm.write)
			.map((perm) => perm.role) || ["System Manager"]
	);
}
