// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.views.ReportFactory = class ReportFactory extends nxenv.views.Factory {
	make(route) {
		const _route = ["List", route[1], "Report"];

		if (route[2]) {
			// custom report
			_route.push(route[2]);
		}

		nxenv.set_route(_route);
	}
};
