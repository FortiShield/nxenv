# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from contextlib import suppress

import nxenv
from nxenv import _
from nxenv.rate_limiter import rate_limit
from nxenv.utils import validate_email_address

sitemap = 1


def get_context(context):
	doc = nxenv.get_doc("Contact Us Settings", "Contact Us Settings")

	if doc.query_options:
		query_options = [opt.strip() for opt in doc.query_options.replace(",", "\n").split("\n") if opt]
	else:
		query_options = ["Sales", "Support", "General"]

	out = {"query_options": query_options, "parents": [{"name": _("Home"), "route": "/"}]}
	out.update(doc.as_dict())

	return out


@nxenv.whitelist(allow_guest=True)
@rate_limit(limit=1000, seconds=60 * 60)
def send_message(sender, message, subject="Website Query"):
	sender = validate_email_address(sender, throw=True)

	with suppress(nxenv.OutgoingEmailError):
		if forward_to_email := nxenv.db.get_single_value("Contact Us Settings", "forward_to_email"):
			nxenv.sendmail(recipients=forward_to_email, reply_to=sender, content=message, subject=subject)

		reply = _(
			"""Thank you for reaching out to us. We will get back to you at the earliest.


Your query:

{0}"""
		).format(message)
		nxenv.sendmail(
			recipients=sender,
			content=f"<div style='white-space: pre-wrap'>{reply}</div>",
			subject=_("We've received your query!"),
		)

	# for clearing outgoing email error message
	nxenv.clear_last_message()

	system_language = nxenv.db.get_single_value("System Settings", "language")
	# add to to-do ?
	nxenv.get_doc(
		doctype="Communication",
		sender=sender,
		subject=_("New Message from Website Contact Page", system_language),
		sent_or_received="Received",
		content=message,
		status="Open",
	).insert(ignore_permissions=True)
