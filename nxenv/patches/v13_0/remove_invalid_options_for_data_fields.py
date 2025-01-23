# Copyright (c) 2022, Nxenv and Contributors
# License: MIT. See LICENSE


import nxenv
from nxenv.model import data_field_options


def execute():
	custom_field = nxenv.qb.DocType("Custom Field")
	(
		nxenv.qb.update(custom_field)
		.set(custom_field.options, None)
		.where((custom_field.fieldtype == "Data") & (custom_field.options.notin(data_field_options)))
	).run()
