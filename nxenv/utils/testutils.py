# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import nxenv


def add_custom_field(doctype, fieldname, fieldtype="Data", options=None):
	nxenv.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"options": options,
		}
	).insert()


def clear_custom_fields(doctype):
	nxenv.db.delete("Custom Field", {"dt": doctype})
	nxenv.clear_cache(doctype=doctype)
