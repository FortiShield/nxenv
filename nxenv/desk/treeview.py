# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv import _


@nxenv.whitelist()
def get_all_nodes(doctype, label, parent, tree_method, **filters):
	"""Recursively gets all data from tree nodes"""

	if "cmd" in filters:
		del filters["cmd"]
	filters.pop("data", None)

	tree_method = nxenv.get_attr(tree_method)

	nxenv.is_whitelisted(tree_method)

	data = tree_method(doctype, parent, **filters)
	out = [dict(parent=label, data=data)]

	if "is_root" in filters:
		del filters["is_root"]
	to_check = [d.get("value") for d in data if d.get("expandable")]

	while to_check:
		parent = to_check.pop()
		data = tree_method(doctype, parent, is_root=False, **filters)
		out.append(dict(parent=parent, data=data))
		for d in data:
			if d.get("expandable"):
				to_check.append(d.get("value"))

	return out


@nxenv.whitelist()
def get_children(doctype, parent="", include_disabled=False, **filters):
	if isinstance(include_disabled, str):
		include_disabled = nxenv.sbool(include_disabled)
	return _get_children(doctype, parent, include_disabled=include_disabled)


def _get_children(doctype, parent="", ignore_permissions=False, include_disabled=False):
	parent_field = "parent_" + nxenv.scrub(doctype)
	filters = [[f"ifnull(`{parent_field}`,'')", "=", parent], ["docstatus", "<", 2]]
	if nxenv.db.has_column(doctype, "disabled") and not include_disabled:
		filters.append(["disabled", "=", False])

	meta = nxenv.get_meta(doctype)

	return nxenv.get_list(
		doctype,
		fields=[
			"name as value",
			"{} as title".format(meta.get("title_field") or "name"),
			"is_group as expandable",
		],
		filters=filters,
		order_by="name",
		ignore_permissions=ignore_permissions,
	)


@nxenv.whitelist()
def add_node():
	args = make_tree_args(**nxenv.form_dict)
	doc = nxenv.get_doc(args)

	doc.save()


def make_tree_args(**kwarg):
	kwarg.pop("cmd", None)

	doctype = kwarg["doctype"]
	parent_field = "parent_" + nxenv.scrub(doctype)

	if kwarg["is_root"] == "false":
		kwarg["is_root"] = False
	if kwarg["is_root"] == "true":
		kwarg["is_root"] = True

	parent = kwarg.get("parent") or kwarg.get(parent_field)
	if doctype != parent:
		kwarg.update({parent_field: parent})

	return nxenv._dict(kwarg)
