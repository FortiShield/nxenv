# Copyright (c) 2018, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def execute():
	signatures = nxenv.db.get_list("User", {"email_signature": ["!=", ""]}, ["name", "email_signature"])
	nxenv.reload_doc("core", "doctype", "user")
	for d in signatures:
		signature = d.get("email_signature")
		signature = signature.replace("\n", "<br>")
		signature = "<div>" + signature + "</div>"
		nxenv.db.set_value("User", d.get("name"), "email_signature", signature)
