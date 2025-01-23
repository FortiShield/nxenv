# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	"""Enable all the existing Client script"""

	nxenv.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
