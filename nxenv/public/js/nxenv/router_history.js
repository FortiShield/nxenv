nxenv.route_history_queue = [];
const routes_to_skip = ["Form", "social", "setup-wizard", "recorder"];

const save_routes = nxenv.utils.debounce(() => {
	if (nxenv.session.user === "Guest") return;
	const routes = nxenv.route_history_queue;
	if (!routes.length) return;

	nxenv.route_history_queue = [];

	nxenv
		.xcall("nxenv.desk.doctype.route_history.route_history.deferred_insert", {
			routes: routes,
		})
		.catch(() => {
			nxenv.route_history_queue.concat(routes);
		});
}, 10000);

nxenv.router.on("change", () => {
	const route = nxenv.get_route();
	if (is_route_useful(route)) {
		nxenv.route_history_queue.push({
			creation: nxenv.datetime.now_datetime(),
			route: nxenv.get_route_str(),
		});

		save_routes();
	}
});

function is_route_useful(route) {
	if (!route[1]) {
		return false;
	} else if ((route[0] === "List" && !route[2]) || routes_to_skip.includes(route[0])) {
		return false;
	} else {
		return true;
	}
}
