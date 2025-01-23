nxenv.provide("nxenv.model");
nxenv.provide("nxenv.utils");

/**
 * Opens the Website Meta Tag form if it exists for {route}
 * or creates a new doc and opens the form
 */
nxenv.utils.set_meta_tag = function (route) {
	nxenv.db.exists("Website Route Meta", route).then((exists) => {
		if (exists) {
			nxenv.set_route("Form", "Website Route Meta", route);
		} else {
			// new doc
			const doc = nxenv.model.get_new_doc("Website Route Meta");
			doc.__newname = route;
			nxenv.set_route("Form", doc.doctype, doc.name);
		}
	});
};
