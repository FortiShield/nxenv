# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import nxenv
from nxenv import _
from nxenv.rate_limiter import rate_limit
from nxenv.website.doctype.blog_settings.blog_settings import get_like_limit
from nxenv.website.utils import clear_cache


@nxenv.whitelist(allow_guest=True)
@rate_limit(key="reference_name", limit=get_like_limit, seconds=60 * 60)
def like(reference_doctype, reference_name, like, route=""):
	like = nxenv.parse_json(like)
	ref_doc = nxenv.get_doc(reference_doctype, reference_name)
	if ref_doc.disable_likes == 1:
		return

	if like:
		liked = add_like(reference_doctype, reference_name)
	else:
		liked = delete_like(reference_doctype, reference_name)

	# since likes are embedded in the page, clear the web cache
	if route:
		clear_cache(route)

	if like and ref_doc.enable_email_notification:
		ref_doc_title = ref_doc.get_title()
		subject = _("Like on {0}: {1}").format(reference_doctype, ref_doc_title)
		content = _("You have received a ❤️ like on your blog post")
		message = f"<p>{content} <b>{ref_doc_title}</b></p>"
		message = message + "<p><a href='{}/{}#likes' style='font-size: 80%'>{}</a></p>".format(
			nxenv.utils.get_request_site_address(), ref_doc.route, _("View Blog Post")
		)

		# notify creator
		nxenv.sendmail(
			recipients=nxenv.db.get_value("User", ref_doc.owner, "email") or ref_doc.owner,
			subject=subject,
			message=message,
			reference_doctype=ref_doc.doctype,
			reference_name=ref_doc.name,
		)

	return liked


def add_like(reference_doctype, reference_name):
	user = nxenv.session.user

	like = nxenv.new_doc("Comment")
	like.comment_type = "Like"
	like.comment_email = user
	like.reference_doctype = reference_doctype
	like.reference_name = reference_name
	like.content = "Liked by: " + user
	if user == "Guest":
		like.ip_address = nxenv.local.request_ip
	like.save(ignore_permissions=True)
	return True


def delete_like(reference_doctype, reference_name):
	user = nxenv.session.user

	filters = {
		"comment_type": "Like",
		"comment_email": user,
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
	}

	if user == "Guest":
		filters["ip_address"] = nxenv.local.request_ip

	nxenv.db.delete("Comment", filters)
	return False
