# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	nxenv.reload_doc("core", "doctype", "system_settings", force=1)
	nxenv.db.set_single_value("System Settings", "password_reset_limit", 3)
