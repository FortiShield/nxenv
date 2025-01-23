import nxenv


def execute():
	nxenv.reload_doc("core", "doctype", "doctype_link")
	nxenv.reload_doc("core", "doctype", "doctype_action")
	nxenv.reload_doc("core", "doctype", "doctype")
	nxenv.model.delete_fields({"DocType": ["hide_heading", "image_view", "read_only_onload"]}, delete=1)

	nxenv.db.delete("Property Setter", {"property": "read_only_onload"})
