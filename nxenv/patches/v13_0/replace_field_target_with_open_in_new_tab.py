import nxenv


def execute():
	doctype = "Top Bar Item"
	if not nxenv.db.table_exists(doctype) or not nxenv.db.has_column(doctype, "target"):
		return

	nxenv.reload_doc("website", "doctype", "top_bar_item")
	nxenv.db.set_value(doctype, {"target": 'target = "_blank"'}, "open_in_new_tab", 1)
