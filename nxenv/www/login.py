# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE


from urllib.parse import urlparse

import nxenv
import nxenv.utils
from nxenv import _
from nxenv.apps import get_default_path
from nxenv.auth import LoginManager
from nxenv.core.doctype.navbar_settings.navbar_settings import get_app_logo
from nxenv.rate_limiter import rate_limit
from nxenv.utils import cint, get_url
from nxenv.utils.data import escape_html
from nxenv.utils.html_utils import get_icon_html
from nxenv.utils.jinja import guess_is_path
from nxenv.utils.oauth import get_oauth2_authorize_url, get_oauth_keys, redirect_post_login
from nxenv.utils.password import get_decrypted_password
from nxenv.website.utils import get_home_page

no_cache = True


def get_context(context):
	redirect_to = nxenv.local.request.args.get("redirect-to")
	redirect_to = sanitize_redirect(redirect_to)

	if nxenv.session.user != "Guest":
		if not redirect_to:
			if nxenv.session.data.user_type == "Website User":
				redirect_to = get_default_path() or get_home_page()
			else:
				redirect_to = get_default_path() or "/app"

		if redirect_to != "login":
			nxenv.local.flags.redirect_location = redirect_to
			raise nxenv.Redirect

	context.no_header = True
	context.for_test = "login.html"
	context["title"] = "Login"
	context["hide_login"] = True  # dont show login link on login page again.
	context["provider_logins"] = []
	context["disable_signup"] = cint(nxenv.get_website_settings("disable_signup"))
	context["show_footer_on_login"] = cint(nxenv.get_website_settings("show_footer_on_login"))
	context["disable_user_pass_login"] = cint(nxenv.get_system_settings("disable_user_pass_login"))
	context["logo"] = get_app_logo()
	context["app_name"] = (
		nxenv.get_website_settings("app_name") or nxenv.get_system_settings("app_name") or _("Nxenv")
	)

	signup_form_template = nxenv.get_hooks("signup_form_template")
	if signup_form_template and len(signup_form_template):
		path = signup_form_template[-1]
		if not guess_is_path(path):
			path = nxenv.get_attr(signup_form_template[-1])()
	else:
		path = "nxenv/templates/signup.html"

	if path:
		context["signup_form_template"] = nxenv.get_template(path).render()

	providers = nxenv.get_all(
		"Social Login Key",
		filters={"enable_social_login": 1},
		fields=["name", "client_id", "base_url", "provider_name", "icon"],
		order_by="name",
	)

	for provider in providers:
		client_secret = get_decrypted_password(
			"Social Login Key", provider.name, "client_secret", raise_exception=False
		)
		if not client_secret:
			continue

		icon = None
		if provider.icon:
			if provider.provider_name == "Custom":
				icon = get_icon_html(provider.icon, small=True)
			else:
				icon = f"<img src={escape_html(provider.icon)!r} alt={escape_html(provider.provider_name)!r}>"

		if provider.client_id and provider.base_url and get_oauth_keys(provider.name):
			context.provider_logins.append(
				{
					"name": provider.name,
					"provider_name": provider.provider_name,
					"auth_url": get_oauth2_authorize_url(provider.name, redirect_to),
					"icon": icon,
				}
			)
			context["social_login"] = True

	if cint(nxenv.db.get_value("LDAP Settings", "LDAP Settings", "enabled")):
		from nxenv.integrations.doctype.ldap_settings.ldap_settings import LDAPSettings

		context["ldap_settings"] = LDAPSettings.get_ldap_client_settings()

	login_label = [_("Email")]

	if nxenv.utils.cint(nxenv.get_system_settings("allow_login_using_mobile_number")):
		login_label.append(_("Mobile"))

	if nxenv.utils.cint(nxenv.get_system_settings("allow_login_using_user_name")):
		login_label.append(_("Username"))

	context["login_label"] = f" {_('or')} ".join(login_label)

	context["login_with_email_link"] = nxenv.get_system_settings("login_with_email_link")

	return context


@nxenv.whitelist(allow_guest=True)
def login_via_token(login_token: str):
	sid = nxenv.cache.get_value(f"login_token:{login_token}", expires=True)
	if not sid:
		nxenv.respond_as_web_page(_("Invalid Request"), _("Invalid Login Token"), http_status_code=417)
		return

	nxenv.local.form_dict.sid = sid
	nxenv.local.login_manager = LoginManager()

	redirect_post_login(
		desk_user=nxenv.db.get_value("User", nxenv.session.user, "user_type") == "System User"
	)


@nxenv.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60 * 60)
def send_login_link(email: str):
	if not nxenv.get_system_settings("login_with_email_link"):
		return

	expiry = nxenv.get_system_settings("login_with_email_link_expiry") or 10
	link = _generate_temporary_login_link(email, expiry)

	app_name = (
		nxenv.get_website_settings("app_name") or nxenv.get_system_settings("app_name") or _("Nxenv")
	)

	subject = _("Login To {0}").format(app_name)

	nxenv.sendmail(
		subject=subject,
		recipients=email,
		template="login_with_email_link",
		args={"link": link, "minutes": expiry, "app_name": app_name},
		now=True,
	)


def _generate_temporary_login_link(email: str, expiry: int):
	assert isinstance(email, str)

	if not nxenv.db.exists("User", email):
		nxenv.throw(_("User with email address {0} does not exist").format(email), nxenv.DoesNotExistError)
	key = nxenv.generate_hash()
	nxenv.cache.set_value(f"one_time_login_key:{key}", email, expires_in_sec=expiry * 60)

	return get_url(f"/api/method/nxenv.www.login.login_via_key?key={key}")


def get_login_with_email_link_ratelimit() -> int:
	return nxenv.get_system_settings("rate_limit_email_link_login") or 5


@nxenv.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=get_login_with_email_link_ratelimit, seconds=60 * 60)
def login_via_key(key: str):
	cache_key = f"one_time_login_key:{key}"
	email = nxenv.cache.get_value(cache_key)

	if email:
		nxenv.cache.delete_value(cache_key)
		nxenv.local.login_manager.login_as(email)

		redirect_post_login(
			desk_user=nxenv.db.get_value("User", nxenv.session.user, "user_type") == "System User"
		)
	else:
		nxenv.respond_as_web_page(
			_("Not Permitted"),
			_("The link you trying to login is invalid or expired."),
			http_status_code=403,
			indicator_color="red",
		)


def sanitize_redirect(redirect: str | None) -> str | None:
	"""Only allow redirect on same domain.

	Allowed redirects:
	- Same host e.g. https://nxenv.localhost/path
	- Just path e.g. /app
	"""
	if not redirect:
		return redirect

	parsed_redirect = urlparse(redirect)
	if not parsed_redirect.netloc:
		return redirect

	parsed_request_host = urlparse(nxenv.local.request.url)
	if parsed_request_host.netloc == parsed_redirect.netloc:
		return redirect

	return None
