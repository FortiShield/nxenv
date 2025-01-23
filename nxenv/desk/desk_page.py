# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


@nxenv.whitelist()
def get(name):
	"""
	Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = nxenv.get_doc("Page", name)
	if page.is_permitted():
		page.load_assets()
		docs = nxenv._dict(page.as_dict())
		if getattr(page, "_dynamic_page", None):
			docs["_dynamic_page"] = 1

		return docs
	else:
		nxenv.response["403"] = 1
		raise nxenv.PermissionError("No read permission for Page %s" % (page.title or name))


@nxenv.whitelist(allow_guest=True)
def getpage():
	"""
	Load the page from `nxenv.form` and send it via `nxenv.response`
	"""
	page = nxenv.form_dict.get("name")
	doc = get(page)

	nxenv.response.docs.append(doc)
