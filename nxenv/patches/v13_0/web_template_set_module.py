# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	"""Set default module for standard Web Template, if none."""
	nxenv.reload_doc("website", "doctype", "Web Template Field")
	nxenv.reload_doc("website", "doctype", "web_template")

	standard_templates = nxenv.get_list("Web Template", {"standard": 1})
	for template in standard_templates:
		doc = nxenv.get_doc("Web Template", template.name)
		if not doc.module:
			doc.module = "Website"
			doc.save()
