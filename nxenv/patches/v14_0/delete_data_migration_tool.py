# Copyright (c) 2022, Nxenv Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import nxenv


def execute():
	doctypes = nxenv.get_all("DocType", {"module": "Data Migration", "custom": 0}, pluck="name")
	for doctype in doctypes:
		nxenv.delete_doc("DocType", doctype, ignore_missing=True)

	nxenv.delete_doc("Module Def", "Data Migration", ignore_missing=True, force=True)
