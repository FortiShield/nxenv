// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.provide("nxenv.pages");
nxenv.provide("nxenv.views");

nxenv.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		this.route = nxenv.get_route();
		this.page_name = nxenv.get_route_str();

		if (this.before_show && this.before_show() === false) return;

		if (nxenv.pages[this.page_name]) {
			nxenv.container.change_to(this.page_name);
			if (this.on_show) {
				this.on_show();
			}
		} else {
			if (this.route[1]) {
				this.make(this.route);
			} else {
				nxenv.show_not_found(this.route);
			}
		}
	}

	make_page(double_column, page_name, sidebar_postition) {
		return nxenv.make_page(double_column, page_name, sidebar_postition);
	}
};

nxenv.make_page = function (double_column, page_name, sidebar_position) {
	if (!page_name) {
		page_name = nxenv.get_route_str();
	}

	const page = nxenv.container.add_page(page_name);

	nxenv.ui.make_app_page({
		parent: page,
		single_column: !double_column,
		sidebar_position: sidebar_position,
		disable_sidebar_toggle: !sidebar_position,
	});

	nxenv.container.change_to(page_name);
	return page;
};
