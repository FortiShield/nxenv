# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv


def sendmail_to_system_managers(subject, content):
	nxenv.sendmail(recipients=get_system_managers(), subject=subject, content=content)


@nxenv.whitelist()
def get_contact_list(txt, page_length=20, extra_filters: str | None = None) -> list[dict]:
	"""Return email ids for a multiselect field."""
	if extra_filters:
		extra_filters = nxenv.parse_json(extra_filters)

	filters = [
		["Contact Email", "email_id", "is", "set"],
	]
	if extra_filters:
		filters.extend(extra_filters)

	fields = ["first_name", "middle_name", "last_name", "company_name"]
	contacts = nxenv.get_list(
		"Contact",
		fields=["full_name", "`tabContact Email`.email_id"],
		filters=filters,
		or_filters=[[field, "like", f"%{txt}%"] for field in fields]
		+ [["Contact Email", "email_id", "like", f"%{txt}%"]],
		limit_page_length=page_length,
	)

	# The multiselect field will store the `label` as the selected value.
	# The `value` is just used as a unique key to distinguish between the options.
	# https://github.com/nxenv/nxenv/blob/6c6a89bcdd9454060a1333e23b855d0505c9ebc2/nxenv/public/js/nxenv/form/controls/autocomplete.js#L29-L35
	return [
		nxenv._dict(
			value=d.email_id,
			label=d.email_id,
			description=d.full_name,
		)
		for d in contacts
	]


def get_system_managers():
	return nxenv.db.sql_list(
		"""select parent FROM `tabHas Role`
		WHERE role='System Manager'
		AND parent!='Administrator'
		AND parent IN (SELECT email FROM tabUser WHERE enabled=1)"""
	)


@nxenv.whitelist()
def relink(name, reference_doctype=None, reference_name=None):
	nxenv.db.sql(
		"""update
			`tabCommunication`
		set
			reference_doctype = %s,
			reference_name = %s,
			status = "Linked"
		where
			communication_type = "Communication" and
			name = %s""",
		(reference_doctype, reference_name, name),
	)


@nxenv.whitelist()
@nxenv.validate_and_sanitize_search_inputs
def get_communication_doctype(doctype, txt, searchfield, start, page_len, filters):
	user_perms = nxenv.utils.user.UserPermissions(nxenv.session.user)
	user_perms.build_permissions()
	can_read = user_perms.can_read
	from nxenv.modules import load_doctype_module

	com_doctypes = []
	if len(txt) < 2:
		for name in nxenv.get_hooks("communication_doctypes"):
			try:
				module = load_doctype_module(name, suffix="_dashboard")
				if hasattr(module, "get_data"):
					for i in module.get_data()["transactions"]:
						com_doctypes += i["items"]
			except ImportError:
				pass
	else:
		com_doctypes = [
			d[0] for d in nxenv.db.get_values("DocType", {"issingle": 0, "istable": 0, "hide_toolbar": 0})
		]

	return [[dt] for dt in com_doctypes if txt.lower().replace("%", "") in dt.lower() and dt in can_read]
