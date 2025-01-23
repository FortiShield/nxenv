nxenv.ui.AppsSwitcher = class AppsSwitcher {
	constructor(sidebar) {
		this.drop_down_state = false;
		this.sidebar_wrapper = sidebar.wrapper;
		this.sidebar = sidebar;
		this.setup_app_switcher();
	}

	setup_app_switcher() {
		this.app_switcher_menu = $(".app-switcher-menu");
		$(".app-switcher-dropdown").on("click", () => {
			this.app_switcher_menu.toggleClass("hidden");
		});

		// hover out of the sidebar  move this to sidebar.js
		this.sidebar_wrapper.find(".body-sidebar").on("mouseleave", () => {
			this.app_switcher_menu.addClass("hidden");

			// hide any expanded menus as they leave a blank space in the sidebar
			this.sidebar_wrapper.find(".drop-icon[data-state='opened'").click();
		});
	}
	create_app_data_map() {
		nxenv.boot.app_data_map = {};
		for (var app of nxenv.boot.app_data) {
			nxenv.boot.app_data_map[app.app_name] = app;
			if (app.workspaces?.length) {
				this.add_app_item(app);
			}
		}
	}
	populate_apps_menu() {
		this.add_private_app();

		this.add_website_select();
		this.add_settings_select();
		this.setup_select_app();
	}

	add_app_item(app) {
		$(`<div class="app-item" data-app-name="${app.app_name}"
			data-app-route="${app.app_route}">
			<a>
				<div class="sidebar-item-icon">
					<img
						class="app-logo"
						src="${app.app_logo_url}"
						alt="${__("App Logo")}"
					>
				</div>
				<span class="app-item-title">${app.app_title}</span>
			</a>
		</div>`).appendTo(this.app_switcher_menu);
	}

	add_private_app() {
		let private_pages = this.sidebar.all_pages.filter((p) => p.public === 0);
		if (private_pages.length === 0) return;

		const app = {
			app_name: "private",
			app_title: __("My Workspaces"),
			app_route: "/app/private",
			app_logo_url: "/assets/nxenv/images/nxenv-framework-logo.svg",
			workspaces: private_pages,
		};

		nxenv.boot.app_data_map["private"] = app;
		$(`<div class="divider"></div>`).prependTo(this.app_switcher_menu);
		$(`<div class="app-item" data-app-name="${app.app_name}"
			data-app-route="${app.app_route}">
			<a>
				<div class="sidebar-item-icon">
					<img
						class="app-logo"
						src="${app.app_logo_url}"
						alt="${__("App Logo")}"
					>
				</div>
				<span class="app-item-title">${app.app_title}</span>
			</a>
		</div>`).prependTo(this.app_switcher_menu);
	}

	setup_select_app() {
		this.app_switcher_menu.find(".app-item").on("click", (e) => {
			let item = $(e.delegateTarget);
			let route = item.attr("data-app-route");
			this.app_switcher_menu.toggleClass("hidden");

			if (item.attr("data-app-name") == "settings") {
				nxenv.quick_edit("Workspace Settings");
				return;
			}
			if (route.startsWith("/app/private")) {
				this.set_current_app("private");
				let ws = Object.values(nxenv.workspace_map).find((ws) => ws.public === 0);
				route += "/" + nxenv.router.slug(ws.title);
				nxenv.set_route(route);
			} else if (route.startsWith("/app")) {
				nxenv.set_route(route);
				this.set_current_app(item.attr("data-app-name"));
			} else {
				// new page
				window.open(route);
			}
		});
	}
	// refactor them into one single function
	add_website_select() {
		$(`<div class="divider"></div>`).appendTo(this.app_switcher_menu);
		this.add_app_item(
			{
				app_name: "website",
				app_title: __("Website"),
				app_route: "/",
				app_logo_url: "/assets/nxenv/images/web.svg",
			},
			this.app_switcher_menu
		);
	}

	add_settings_select() {
		$(`<div class="divider"></div>`).appendTo(this.app_switcher_menu);
		this.add_app_item({
			app_name: "settings",
			app_title: __("Settings"),
			app_logo_url: "/assets/nxenv/images/settings-gear.svg",
		});
		let settings_item = this.app_switcher_menu.children().last();
	}

	set_current_app(app) {
		if (!app) {
			console.warn("set_current_app: app not defined");
			return;
		}
		let app_data = nxenv.boot.app_data_map[app] || nxenv.boot.app_data_map["nxenv"];

		this.sidebar_wrapper
			.find(".app-switcher-dropdown .sidebar-item-icon img")
			.attr("src", app_data.app_logo_url);
		this.sidebar_wrapper
			.find(".app-switcher-dropdown .sidebar-item-label")
			.html(app_data.app_title);

		$(".navbar-brand .app-logo").attr("src", app_data.app_logo_url);

		if (nxenv.current_app === app) return;
		nxenv.current_app = app;

		// re-render the sidebar
		nxenv.app.sidebar.make_sidebar();
	}
};
