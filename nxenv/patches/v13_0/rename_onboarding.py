# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	if nxenv.db.exists("DocType", "Onboarding"):
		nxenv.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
