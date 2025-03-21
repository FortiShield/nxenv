// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.breadcrumbs = {
	all: {},

	preferred: {
		File: "",
		Dashboard: "Customization",
		"Dashboard Chart": "Customization",
		"Dashboard Chart Source": "Customization",
	},

	module_map: {
		Core: "Settings",
		Email: "Settings",
		Custom: "Settings",
		Workflow: "Settings",
		Printing: "Settings",
		Setup: "Settings",
		Automation: "Tools",
	},

	set_doctype_module(doctype, module) {
		localStorage["preferred_breadcrumbs:" + doctype] = module;
	},

	get_doctype_module(doctype) {
		return localStorage["preferred_breadcrumbs:" + doctype];
	},

	add(module, doctype, type) {
		let obj;
		if (typeof module === "object") {
			obj = module;
		} else {
			obj = {
				module: module,
				doctype: doctype,
				type: type,
			};
		}
		this.all[nxenv.breadcrumbs.current_page()] = obj;
		this.update();
	},

	current_page() {
		return nxenv.get_route_str();
	},

	update() {
		var breadcrumbs = this.all[nxenv.breadcrumbs.current_page()];

		this.clear();
		if (!breadcrumbs) return this.toggle(false);

		if (breadcrumbs.type === "Custom") {
			this.set_custom_breadcrumbs(breadcrumbs);
		} else {
			// workspace
			this.set_workspace_breadcrumb(breadcrumbs);

			// form / print
			let view = nxenv.get_route()[0];
			view = view ? view.toLowerCase() : null;
			if (breadcrumbs.doctype && ["print", "form"].includes(view)) {
				this.set_list_breadcrumb(breadcrumbs);
				this.set_form_breadcrumb(breadcrumbs, view);
			} else if (breadcrumbs.doctype && view === "list") {
				this.set_list_breadcrumb(breadcrumbs);
			} else if (breadcrumbs.doctype && view == "dashboard-view") {
				this.set_list_breadcrumb(breadcrumbs);
				this.set_dashboard_breadcrumb(breadcrumbs);
			}
		}

		if (
			breadcrumbs.workspace &&
			nxenv.workspace_map[breadcrumbs.workspace]?.app &&
			nxenv.workspace_map[breadcrumbs.workspace]?.app != nxenv.current_app
		) {
			let app = nxenv.workspace_map[breadcrumbs.workspace].app;
			nxenv.app.sidebar.apps_switcher.set_current_app(app);
		}

		this.toggle(true);
	},

	set_custom_breadcrumbs(breadcrumbs) {
		this.append_breadcrumb_element(breadcrumbs.route, breadcrumbs.label);
	},

	append_breadcrumb_element(route, label) {
		const el = document.createElement("li");
		const a = document.createElement("a");
		a.href = route;
		a.innerText = label;
		el.appendChild(a);
		this.$breadcrumbs.append(el);
	},

	get last_route() {
		return nxenv.route_history.slice(-2)[0];
	},

	set_workspace_breadcrumb(breadcrumbs) {
		// get preferred module for breadcrumbs, based on history and module

		if (!breadcrumbs.workspace) {
			this.set_workspace(breadcrumbs);
		}

		if (!breadcrumbs.workspace) {
			return;
		}

		if (
			breadcrumbs.module_info &&
			(breadcrumbs.module_info.blocked ||
				!nxenv.visible_modules.includes(breadcrumbs.module_info.module))
		) {
			return;
		}

		this.append_breadcrumb_element(
			`/app/${nxenv.router.slug(breadcrumbs.workspace)}`,
			__(breadcrumbs.workspace)
		);
	},

	set_workspace(breadcrumbs) {
		// try and get module from doctype or other settings
		// then get the workspace for that module

		this.setup_modules();
		var from_module = this.get_doctype_module(breadcrumbs.doctype);

		if (from_module) {
			breadcrumbs.module = from_module;
		} else if (this.preferred[breadcrumbs.doctype] !== undefined) {
			// get preferred module for breadcrumbs
			breadcrumbs.module = this.preferred[breadcrumbs.doctype];
		}

		// guess from last route
		if (this.last_route?.[0] == "Workspaces") {
			let last_workspace = this.last_route[1];

			if (
				breadcrumbs.module &&
				nxenv.boot.module_wise_workspaces[breadcrumbs.module]?.includes(last_workspace)
			) {
				breadcrumbs.workspace = last_workspace;
			}
		} else {
			// choose from __workspaces
			const doctype_meta = nxenv.get_meta(breadcrumbs.doctype);
			if (doctype_meta?.__workspaces?.length) {
				breadcrumbs.workspace = doctype_meta.__workspaces[0];
			}

			if (breadcrumbs.module) {
				if (this.module_map[breadcrumbs.module]) {
					breadcrumbs.module = this.module_map[breadcrumbs.module];
				}

				breadcrumbs.module_info = nxenv.get_module(breadcrumbs.module);

				// set workspace
				if (
					breadcrumbs.module_info &&
					nxenv.boot.module_wise_workspaces[breadcrumbs.module]
				) {
					breadcrumbs.workspace =
						nxenv.boot.module_wise_workspaces[breadcrumbs.module][0];
				}
			}
		}
	},

	set_list_breadcrumb(breadcrumbs) {
		const doctype = breadcrumbs.doctype;
		const doctype_meta = nxenv.get_meta(doctype);
		if (
			(doctype === "User" && !nxenv.user.has_role("System Manager")) ||
			doctype_meta?.issingle
		) {
			// no user listview for non-system managers and single doctypes
		} else {
			let route;
			const doctype_route = nxenv.router.slug(nxenv.router.doctype_layout || doctype);
			if (doctype_meta?.is_tree) {
				let view = nxenv.model.user_settings[doctype].last_view || "Tree";
				route = `${doctype_route}/view/${view}`;
			} else {
				route = doctype_route;
			}
			this.append_breadcrumb_element(`/app/${route}`, __(doctype));
		}
	},

	set_form_breadcrumb(breadcrumbs, view) {
		const doctype = breadcrumbs.doctype;
		let docname = nxenv.get_route().slice(2).join("/");
		let docname_title;
		if (docname.startsWith("new-" + doctype.toLowerCase().replace(/ /g, "-"))) {
			docname_title = __("New {0}", [__(doctype)]);
		} else {
			docname_title = __(docname);
		}
		let form_route = `/app/${nxenv.router.slug(doctype)}/${encodeURIComponent(docname)}`;
		this.append_breadcrumb_element(form_route, docname_title);

		if (view === "form") {
			let last_crumb = this.$breadcrumbs.find("li").last();
			last_crumb.addClass("disabled");
			last_crumb.css("cursor", "copy");
			last_crumb.click((event) => {
				event.stopImmediatePropagation();
				nxenv.utils.copy_to_clipboard(last_crumb.text());
			});
		}
	},

	set_dashboard_breadcrumb(breadcrumbs) {
		const doctype = breadcrumbs.doctype;
		const docname = nxenv.get_route()[1];
		let dashboard_route = `/app/${nxenv.router.slug(doctype)}/${docname}`;
		$(`<li><a href="${dashboard_route}">${__(docname)}</a></li>`).appendTo(this.$breadcrumbs);
	},

	setup_modules() {
		if (!nxenv.visible_modules) {
			nxenv.visible_modules = $.map(nxenv.boot.allowed_workspaces, (m) => {
				return m.module;
			});
		}
	},

	rename(doctype, old_name, new_name) {
		var old_route_str = ["Form", doctype, old_name].join("/");
		var new_route_str = ["Form", doctype, new_name].join("/");
		this.all[new_route_str] = this.all[old_route_str];
		delete nxenv.breadcrumbs.all[old_route_str];
		this.update();
	},

	clear() {
		this.$breadcrumbs = $("#navbar-breadcrumbs").empty();
	},

	toggle(show) {
		if (show) {
			$("body").addClass("no-breadcrumbs");
		} else {
			$("body").removeClass("no-breadcrumbs");
		}
	},
};
