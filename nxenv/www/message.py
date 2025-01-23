# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv.utils import strip_html_tags
from nxenv.utils.html_utils import clean_html

no_cache = 1


def get_context(context):
	message_context = nxenv._dict()
	if hasattr(nxenv.local, "message"):
		message_context["header"] = nxenv.local.message_title
		message_context["title"] = strip_html_tags(nxenv.local.message_title)
		message_context["message"] = nxenv.local.message
		if hasattr(nxenv.local, "message_success"):
			message_context["success"] = nxenv.local.message_success

	elif nxenv.local.form_dict.id:
		message_id = nxenv.local.form_dict.id
		key = f"message_id:{message_id}"
		message = nxenv.cache.get_value(key, expires=True)
		if message:
			message_context.update(message.get("context", {}))
			if message.get("http_status_code"):
				nxenv.local.response["http_status_code"] = message["http_status_code"]

	if not message_context.title:
		message_context.title = clean_html(nxenv.form_dict.title)

	if not message_context.message:
		message_context.message = clean_html(nxenv.form_dict.message)

	return message_context
