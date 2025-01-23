# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import nxenv


def execute():
	nxenv.reload_doc("website", "doctype", "web_form_list_column")
	nxenv.reload_doctype("Web Form")

	for web_form in nxenv.get_all("Web Form", fields=["*"]):
		if web_form.allow_multiple and not web_form.show_list:
			nxenv.db.set_value("Web Form", web_form.name, "show_list", True)
