# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	if not nxenv.db.table_exists("Data Import"):
		return

	meta = nxenv.get_meta("Data Import")
	# if Data Import is the new one, return early
	if meta.fields[1].fieldname == "import_type":
		return

	nxenv.db.sql("DROP TABLE IF EXISTS `tabData Import Legacy`")
	nxenv.rename_doc("DocType", "Data Import", "Data Import Legacy")
	nxenv.db.commit()
	nxenv.db.sql("DROP TABLE IF EXISTS `tabData Import`")
	nxenv.rename_doc("DocType", "Data Import Beta", "Data Import")
