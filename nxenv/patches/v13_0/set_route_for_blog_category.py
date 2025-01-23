import nxenv


def execute():
	categories = nxenv.get_list("Blog Category")
	for category in categories:
		doc = nxenv.get_doc("Blog Category", category["name"])
		doc.set_route()
		doc.save()
