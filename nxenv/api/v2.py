"""REST API v2

This file defines routes and implementation for REST API.

Note:
	- All functions in this file should be treated as "whitelisted" as they are exposed via routes
	- None of the functions present here should be called from python code, their location and
	  internal implementation can change without treating it as "breaking change".
"""

import json
from typing import Any

from werkzeug.routing import Rule

import nxenv
import nxenv.client
from nxenv import _, get_newargs, is_whitelisted
from nxenv.core.doctype.server_script.server_script_utils import get_server_script_map
from nxenv.handler import is_valid_http_method, run_server_script, upload_file

PERMISSION_MAP = {
	"GET": "read",
	"POST": "write",
}


def handle_rpc_call(method: str, doctype: str | None = None):
	from nxenv.modules.utils import load_doctype_module

	if doctype:
		# Expand to run actual method from doctype controller
		module = load_doctype_module(doctype)
		method = module.__name__ + "." + method

	for hook in reversed(nxenv.get_hooks("override_whitelisted_methods", {}).get(method, [])):
		# override using the last hook
		method = hook
		break

	# via server script
	server_script = get_server_script_map().get("_api", {}).get(method)
	if server_script:
		return run_server_script(server_script)

	try:
		method = nxenv.get_attr(method)
	except Exception as e:
		nxenv.throw(_("Failed to get method {0} with {1}").format(method, e))

	is_whitelisted(method)
	is_valid_http_method(method)

	return nxenv.call(method, **nxenv.form_dict)


def login():
	"""Login happens implicitly, this function doesn't do anything."""
	pass


def logout():
	nxenv.local.login_manager.logout()
	nxenv.db.commit()


def read_doc(doctype: str, name: str):
	doc = nxenv.get_doc(doctype, name)
	doc.check_permission("read")
	doc.apply_fieldlevel_read_permissions()
	return doc


def document_list(doctype: str):
	if nxenv.form_dict.get("fields"):
		nxenv.form_dict["fields"] = json.loads(nxenv.form_dict["fields"])

	# set limit of records for nxenv.get_list
	nxenv.form_dict.limit_page_length = nxenv.form_dict.limit or 20
	# evaluate nxenv.get_list
	return nxenv.call(nxenv.client.get_list, doctype, **nxenv.form_dict)


def count(doctype: str) -> int:
	from nxenv.desk.reportview import get_count

	nxenv.form_dict.doctype = doctype

	return get_count()


def create_doc(doctype: str):
	data = nxenv.form_dict
	data.pop("doctype", None)
	return nxenv.new_doc(doctype, **data).insert()


def update_doc(doctype: str, name: str):
	data = nxenv.form_dict

	doc = nxenv.get_doc(doctype, name, for_update=True)
	data.pop("flags", None)
	doc.update(data)
	doc.save()

	# check for child table doctype
	if doc.get("parenttype"):
		nxenv.get_doc(doc.parenttype, doc.parent).save()

	return doc


def delete_doc(doctype: str, name: str):
	nxenv.client.delete_doc(doctype, name)
	nxenv.response.http_status_code = 202
	return "ok"


def get_meta(doctype: str):
	nxenv.only_for("All")
	return nxenv.get_meta(doctype)


def execute_doc_method(doctype: str, name: str, method: str | None = None):
	"""Get a document from DB and execute method on it.

	Use cases:
	- Submitting/cancelling document
	- Triggering some kind of update on a document
	"""
	method = method or nxenv.form_dict.pop("run_method")
	doc = nxenv.get_doc(doctype, name)
	doc.is_whitelisted(method)

	doc.check_permission(PERMISSION_MAP[nxenv.request.method])
	return doc.run_method(method, **nxenv.form_dict)


def run_doc_method(method: str, document: dict[str, Any] | str, kwargs=None):
	"""run a whitelisted controller method on in-memory document.


	This is useful for building clients that don't necessarily encode all the business logic but
	call server side function on object to validate and modify the doc.

	The doc CAN exists in DB too and can write to DB as well if method is POST.
	"""

	if isinstance(document, str):
		document = nxenv.parse_json(document)

	if kwargs is None:
		kwargs = {}

	doc = nxenv.get_doc(document)
	doc._original_modified = doc.modified
	doc.check_if_latest()

	doc.check_permission(PERMISSION_MAP[nxenv.request.method])

	method_obj = getattr(doc, method)
	fn = getattr(method_obj, "__func__", method_obj)
	is_whitelisted(fn)
	is_valid_http_method(fn)

	new_kwargs = get_newargs(fn, kwargs)
	response = doc.run_method(method, **new_kwargs)
	nxenv.response.docs.append(doc)  # send modified document and result both.
	return response


url_rules = [
	# RPC calls
	Rule("/method/login", endpoint=login),
	Rule("/method/logout", endpoint=logout),
	Rule("/method/ping", endpoint=nxenv.ping),
	Rule("/method/upload_file", endpoint=upload_file),
	Rule("/method/<method>", endpoint=handle_rpc_call),
	Rule(
		"/method/run_doc_method",
		methods=["GET", "POST"],
		endpoint=lambda: nxenv.call(run_doc_method, **nxenv.form_dict),
	),
	Rule("/method/<doctype>/<method>", endpoint=handle_rpc_call),
	# Document level APIs
	Rule("/document/<doctype>", methods=["GET"], endpoint=document_list),
	Rule("/document/<doctype>", methods=["POST"], endpoint=create_doc),
	Rule("/document/<doctype>/<path:name>/", methods=["GET"], endpoint=read_doc),
	Rule("/document/<doctype>/<path:name>/", methods=["PATCH", "PUT"], endpoint=update_doc),
	Rule("/document/<doctype>/<path:name>/", methods=["DELETE"], endpoint=delete_doc),
	Rule(
		"/document/<doctype>/<path:name>/method/<method>/",
		methods=["GET", "POST"],
		endpoint=execute_doc_method,
	),
	# Collection level APIs
	Rule("/doctype/<doctype>/meta", methods=["GET"], endpoint=get_meta),
	Rule("/doctype/<doctype>/count", methods=["GET"], endpoint=count),
]
