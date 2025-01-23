# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import nxenv
from nxenv import _


@nxenv.whitelist()
def update_event(args, field_map):
	"""Updates Event (called via calendar) based on passed `field_map`"""
	args = nxenv._dict(json.loads(args))
	field_map = nxenv._dict(json.loads(field_map))
	w = nxenv.get_doc(args.doctype, args.name)
	w.set(field_map.start, args[field_map.start])
	w.set(field_map.end, args.get(field_map.end))
	w.save()


def get_event_conditions(doctype, filters=None):
	"""Return SQL conditions with user permissions and filters for event queries."""
	from nxenv.desk.reportview import get_filters_cond

	if not nxenv.has_permission(doctype):
		nxenv.throw(_("Not Permitted"), nxenv.PermissionError)

	return get_filters_cond(doctype, filters, [], with_match_conditions=True)


@nxenv.whitelist()
def get_events(doctype, start, end, field_map, filters=None, fields=None):
	field_map = nxenv._dict(json.loads(field_map))
	fields = nxenv.parse_json(fields)

	doc_meta = nxenv.get_meta(doctype)
	for d in doc_meta.fields:
		if d.fieldtype == "Color":
			field_map.update({"color": d.fieldname})

	filters = json.loads(filters) if filters else []

	if not fields:
		fields = [field_map.start, field_map.end, field_map.title, "name"]

	if field_map.color:
		fields.append(field_map.color)

	start_date = "ifnull({}, '0001-01-01 00:00:00')".format(field_map.start)
	end_date = "ifnull({}, '2199-12-31 00:00:00')".format(field_map.end)

	filters += [
		[doctype, start_date, "<=", end],
		[doctype, end_date, ">=", start],
	]
	fields = list({field for field in fields if field})
	return nxenv.get_list(doctype, fields=fields, filters=filters)
