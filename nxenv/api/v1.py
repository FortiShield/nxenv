import json

from werkzeug.routing import Rule

import nxenv
from nxenv import _
from nxenv.utils.data import sbool


def document_list(doctype: str):
	if nxenv.form_dict.get("fields"):
		nxenv.form_dict["fields"] = json.loads(nxenv.form_dict["fields"])

	# set limit of records for nxenv.get_list
	nxenv.form_dict.setdefault(
		"limit_page_length",
		nxenv.form_dict.limit or nxenv.form_dict.limit_page_length or 20,
	)

	# convert strings to native types - only as_dict and debug accept bool
	for param in ["as_dict", "debug"]:
		param_val = nxenv.form_dict.get(param)
		if param_val is not None:
			nxenv.form_dict[param] = sbool(param_val)

	# evaluate nxenv.get_list
	return nxenv.call(nxenv.client.get_list, doctype, **nxenv.form_dict)


def handle_rpc_call(method: str):
	import nxenv.handler

	method = method.split("/")[0]  # for backward compatiblity

	nxenv.form_dict.cmd = method
	return nxenv.handler.handle()


def create_doc(doctype: str):
	data = get_request_form_data()
	data.pop("doctype", None)
	return nxenv.new_doc(doctype, **data).insert()


def update_doc(doctype: str, name: str):
	data = get_request_form_data()

	doc = nxenv.get_doc(doctype, name, for_update=True)
	if "flags" in data:
		del data["flags"]

	doc.update(data)
	doc.save()

	# check for child table doctype
	if doc.get("parenttype"):
		nxenv.get_doc(doc.parenttype, doc.parent).save()

	return doc


def delete_doc(doctype: str, name: str):
	# TODO: child doc handling
	nxenv.delete_doc(doctype, name, ignore_missing=False)
	nxenv.response.http_status_code = 202
	return "ok"


def read_doc(doctype: str, name: str):
	# Backward compatiblity
	if "run_method" in nxenv.form_dict:
		return execute_doc_method(doctype, name)

	doc = nxenv.get_doc(doctype, name)
	doc.check_permission("read")
	doc.apply_fieldlevel_read_permissions()
	return doc


def execute_doc_method(doctype: str, name: str, method: str | None = None):
	method = method or nxenv.form_dict.pop("run_method")
	doc = nxenv.get_doc(doctype, name)
	doc.is_whitelisted(method)

	if nxenv.request.method == "GET":
		doc.check_permission("read")
		return doc.run_method(method, **nxenv.form_dict)

	elif nxenv.request.method == "POST":
		doc.check_permission("write")
		return doc.run_method(method, **nxenv.form_dict)


def get_request_form_data():
	if nxenv.form_dict.data is None:
		data = nxenv.safe_decode(nxenv.request.get_data())
	else:
		data = nxenv.form_dict.data

	try:
		return nxenv.parse_json(data)
	except ValueError:
		return nxenv.form_dict


url_rules = [
	Rule("/method/<path:method>", endpoint=handle_rpc_call),
	Rule("/resource/<doctype>", methods=["GET"], endpoint=document_list),
	Rule("/resource/<doctype>", methods=["POST"], endpoint=create_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["GET"], endpoint=read_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["PUT"], endpoint=update_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["DELETE"], endpoint=delete_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["POST"], endpoint=execute_doc_method),
]
