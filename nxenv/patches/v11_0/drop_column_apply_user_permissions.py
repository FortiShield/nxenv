import nxenv


def execute():
	column = "apply_user_permissions"
	to_remove = ["DocPerm", "Custom DocPerm"]

	for doctype in to_remove:
		if nxenv.db.table_exists(doctype):
			if column in nxenv.db.get_table_columns(doctype):
				nxenv.db.sql(f"alter table `tab{doctype}` drop column {column}")

	nxenv.reload_doc("core", "doctype", "docperm", force=True)
	nxenv.reload_doc("core", "doctype", "custom_docperm", force=True)
