# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.reload_doc("core", "doctype", "DocField")

	if nxenv.db.has_column("DocField", "show_days"):
		nxenv.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_days = 1 WHERE show_days = 0
		"""
		)
		nxenv.db.sql_ddl("alter table tabDocField drop column show_days")

	if nxenv.db.has_column("DocField", "show_seconds"):
		nxenv.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_seconds = 1 WHERE show_seconds = 0
		"""
		)
		nxenv.db.sql_ddl("alter table tabDocField drop column show_seconds")

	nxenv.clear_cache(doctype="DocField")
