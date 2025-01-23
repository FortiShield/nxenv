# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	if not nxenv.db.table_exists("List View Setting"):
		return
	if not nxenv.db.exists("DocType", "List View Setting"):
		return

	nxenv.reload_doc("desk", "doctype", "List View Settings")

	existing_list_view_settings = nxenv.get_all("List View Settings", as_list=True, order_by="modified")
	for list_view_setting in nxenv.get_all(
		"List View Setting",
		fields=["disable_count", "disable_sidebar_stats", "disable_auto_refresh", "name"],
		order_by="modified",
	):
		name = list_view_setting.pop("name")
		if name not in [x[0] for x in existing_list_view_settings]:
			list_view_setting["doctype"] = "List View Settings"
			list_view_settings = nxenv.get_doc(list_view_setting)
			# setting name here is necessary because autoname is set as prompt
			list_view_settings.name = name
			list_view_settings.insert()

	nxenv.delete_doc("DocType", "List View Setting", force=True)
