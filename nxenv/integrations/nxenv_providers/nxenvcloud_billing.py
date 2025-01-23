import requests

import nxenv
from nxenv import _


def get_base_url():
	url = "https://nxenvcloud.com"
	if nxenv.conf.developer_mode and nxenv.conf.get("saas_billing_base_url"):
		url = nxenv.conf.get("saas_billing_base_url")
	return url


def get_site_name():
	site_name = nxenv.local.site
	if nxenv.conf.developer_mode and nxenv.conf.get("saas_billing_site_name"):
		site_name = nxenv.conf.get("saas_billing_site_name")
	return site_name


def get_headers():
	# check if user is system manager
	if nxenv.get_roles(nxenv.session.user).count("System Manager") == 0:
		nxenv.throw(_("You are not allowed to access this resource"))

	# check if communication secret is set
	if not nxenv.conf.get("fc_communication_secret"):
		nxenv.throw(_("Communication secret not set"))

	return {
		"X-Site-Token": nxenv.conf.get("fc_communication_secret"),
		"X-Site": get_site_name(),
	}


@nxenv.whitelist()
def get_token_and_base_url():
	request = requests.post(
		f"{get_base_url()}/api/method/press.saas.api.auth.generate_access_token",
		headers=get_headers(),
	)
	if request.status_code == 200:
		return {
			"base_url": get_base_url(),
			"token": request.json()["message"],
		}
	else:
		nxenv.throw(_("Failed to generate access token"))


@nxenv.whitelist()
def is_access_token_valid(token):
	headers = {"Content-Type": "application/json"}
	request = requests.post(
		f"{get_base_url()}/api/method/press.saas.api.auth.is_access_token_valid",
		headers,
		json={token},
	)
	return request.json()["message"]


@nxenv.whitelist()
def current_site_info():
	request = requests.post(f"{get_base_url()}/api/method/press.saas.api.site.info", headers=get_headers())
	if request.status_code == 200:
		return request.json().get("message")
	else:
		nxenv.throw(_("Failed to get site info"))


@nxenv.whitelist()
def api(method, data=None):
	if data is None:
		data = {}
	request = requests.post(
		f"{get_base_url()}/api/method/press.saas.api.{method}",
		headers=get_headers(),
		json=data,
	)
	if request.status_code == 200:
		return request.json().get("message")
	else:
		nxenv.throw(_("Failed while calling API {0}", method))


@nxenv.whitelist()
def is_fc_site():
	is_system_manager = nxenv.get_roles(nxenv.session.user).count("System Manager")
	setup_completed = nxenv.get_system_settings("setup_complete")
	return is_system_manager and setup_completed and nxenv.conf.get("fc_communication_secret")


# login to nxenv cloud dashboard
@nxenv.whitelist()
def send_verification_code():
	request = requests.post(
		f"{get_base_url()}/api/method/press.api.developer.saas.request_login_to_fc",
		headers=get_headers(),
		json={"domain": get_site_name()},
	)
	if request.status_code == 200:
		return request.json().get("message")
	else:
		nxenv.throw(_("Failed to request login to Nxenv Cloud"))


@nxenv.whitelist()
def verify_and_login(verification_code: str):
	request = requests.post(
		f"{get_base_url()}/api/method/press.api.developer.saas.validate_login_to_fc",
		headers=get_headers(),
		json={"domain": get_site_name(), "otp": verification_code},
	)

	if request.status_code == 200:
		return {
			"base_url": get_base_url(),
			"login_token": request.json()["login_token"],
		}
	else:
		nxenv.throw(_("Invalid Code. Please try again."))
