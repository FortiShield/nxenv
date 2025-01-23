# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import functools
import gc
import logging
import os
import re

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import ClosingIterator

import nxenv
import nxenv.api
import nxenv.handler
import nxenv.monitor
import nxenv.rate_limiter
import nxenv.recorder
import nxenv.utils.response
from nxenv import _
from nxenv.auth import SAFE_HTTP_METHODS, UNSAFE_HTTP_METHODS, HTTPRequest, validate_auth
from nxenv.middlewares import StaticDataMiddleware
from nxenv.utils import CallbackManager, cint, get_site_name
from nxenv.utils.data import escape_html
from nxenv.utils.error import log_error, log_error_snapshot
from nxenv.website.page_renderers.error_page import ErrorPage
from nxenv.website.serve import get_response

_site = None
_sites_path = os.environ.get("SITES_PATH", ".")


# If gc.freeze is done then importing modules before forking allows us to share the memory
import gettext

import babel
import babel.messages
import bleach
import num2words
import pydantic

import nxenv.boot
import nxenv.client
import nxenv.core.doctype.file.file
import nxenv.core.doctype.user.user
import nxenv.database.mariadb.database  # Load database related utils
import nxenv.database.query
import nxenv.desk.desktop  # workspace
import nxenv.desk.form.save
import nxenv.model.db_query
import nxenv.query_builder
import nxenv.utils.background_jobs  # Enqueue is very common
import nxenv.utils.data  # common utils
import nxenv.utils.jinja  # web page rendering
import nxenv.utils.jinja_globals
import nxenv.utils.redis_wrapper  # Exact redis_wrapper
import nxenv.utils.safe_exec
import nxenv.utils.typing_validations  # any whitelisted method uses this
import nxenv.website.path_resolver  # all the page types and resolver
import nxenv.website.router  # Website router
import nxenv.website.website_generator  # web page doctypes

# end: module pre-loading


def after_response_wrapper(app):
	"""Wrap a WSGI application to call after_response hooks after we have responded.

	This is done to reduce response time by deferring expensive tasks."""

	@functools.wraps(app)
	def application(environ, start_response):
		return ClosingIterator(
			app(environ, start_response),
			(
				nxenv.rate_limiter.update,
				nxenv.recorder.dump,
				nxenv.request.after_response.run,
				nxenv.destroy,
			),
		)

	return application


@after_response_wrapper
@Request.application
def application(request: Request):
	response = None

	try:
		rollback = True

		init_request(request)

		validate_auth()

		if request.method == "OPTIONS":
			response = Response()

		elif nxenv.form_dict.cmd:
			from nxenv.deprecation_dumpster import deprecation_warning

			deprecation_warning(
				"unknown",
				"v17",
				f"{nxenv.form_dict.cmd}: Sending `cmd` for RPC calls is deprecated, call REST API instead `/api/method/cmd`",
			)
			nxenv.handler.handle()
			response = nxenv.utils.response.build_response("json")

		elif request.path.startswith("/api/"):
			response = nxenv.api.handle(request)

		elif request.path.startswith("/backups"):
			response = nxenv.utils.response.download_backup(request.path)

		elif request.path.startswith("/private/files/"):
			response = nxenv.utils.response.download_private_file(request.path)

		elif request.method in ("GET", "HEAD", "POST"):
			response = get_response()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = sync_database(rollback)

	finally:
		# Important note:
		# this function *must* always return a response, hence any exception thrown outside of
		# try..catch block like this finally block needs to be handled appropriately.

		if rollback and request.method in UNSAFE_HTTP_METHODS and nxenv.db:
			nxenv.db.rollback()

		try:
			run_after_request_hooks(request, response)
		except Exception:
			# We can not handle exceptions safely here.
			nxenv.logger().error("Failed to run after request hook", exc_info=True)

	log_request(request, response)
	process_response(response)

	return response


def run_after_request_hooks(request, response):
	if not getattr(nxenv.local, "initialised", False):
		return

	for after_request_task in nxenv.get_hooks("after_request"):
		nxenv.call(after_request_task, response=response, request=request)


def init_request(request):
	nxenv.local.request = request
	nxenv.local.request.after_response = CallbackManager()

	nxenv.local.is_ajax = nxenv.get_request_header("X-Requested-With") == "XMLHttpRequest"

	site = _site or request.headers.get("X-Nxenv-Site-Name") or get_site_name(request.host)
	nxenv.init(site, sites_path=_sites_path, force=True)

	if not (nxenv.local.conf and nxenv.local.conf.db_name):
		# site does not exist
		raise NotFound

	if nxenv.local.conf.maintenance_mode:
		nxenv.connect()
		if nxenv.local.conf.allow_reads_during_maintenance:
			setup_read_only_mode()
		else:
			raise nxenv.SessionStopped("Session Stopped")
	else:
		nxenv.connect(set_admin_as_user=False)
	if request.path.startswith("/api/method/upload_file"):
		from nxenv.core.api.file import get_max_file_size

		request.max_content_length = get_max_file_size()
	else:
		request.max_content_length = cint(nxenv.local.conf.get("max_file_size")) or 25 * 1024 * 1024
	make_form_dict(request)

	if request.method != "OPTIONS":
		nxenv.local.http_request = HTTPRequest()

	for before_request_task in nxenv.get_hooks("before_request"):
		nxenv.call(before_request_task)


def setup_read_only_mode():
	"""During maintenance_mode reads to DB can still be performed to reduce downtime. This
	function sets up read only mode

	- Setting global flag so other pages, desk and database can know that we are in read only mode.
	- Setup read only database access either by:
	    - Connecting to read replica if one exists
	    - Or setting up read only SQL transactions.
	"""
	nxenv.flags.read_only = True

	# If replica is available then just connect replica, else setup read only transaction.
	if nxenv.conf.read_from_replica:
		nxenv.connect_replica()
	else:
		nxenv.db.begin(read_only=True)


def log_request(request, response):
	if hasattr(nxenv.local, "conf") and nxenv.local.conf.enable_nxenv_logger:
		nxenv.logger("nxenv.web", allow_site=nxenv.local.site).info(
			{
				"site": get_site_name(request.host),
				"remote_addr": getattr(request, "remote_addr", "NOTFOUND"),
				"pid": os.getpid(),
				"user": getattr(nxenv.local.session, "user", "NOTFOUND"),
				"base_url": getattr(request, "base_url", "NOTFOUND"),
				"full_path": getattr(request, "full_path", "NOTFOUND"),
				"method": getattr(request, "method", "NOTFOUND"),
				"scheme": getattr(request, "scheme", "NOTFOUND"),
				"http_status_code": getattr(response, "status_code", "NOTFOUND"),
			}
		)


def process_response(response: Response):
	if not response:
		return

	# cache control
	# read: https://simonhearne.com/2022/caching-header-best-practices/
	if nxenv.local.response.can_cache:
		# default: 5m (client), 3h (allow stale resources for this long if upstream is down)
		response.headers.setdefault("Cache-Control", "private,max-age=300,stale-while-revalidate=10800")
	else:
		response.headers.setdefault("Cache-Control", "no-store,no-cache,must-revalidate,max-age=0")

	# Set cookies, only if response is non-cacheable to avoid proxy cache invalidation
	if hasattr(nxenv.local, "cookie_manager") and not nxenv.local.response.can_cache:
		nxenv.local.cookie_manager.flush_cookies(response=response)

	# rate limiter headers
	if hasattr(nxenv.local, "rate_limiter"):
		response.headers.extend(nxenv.local.rate_limiter.headers())

	if trace_id := nxenv.monitor.get_trace_id():
		response.headers.extend({"X-Nxenv-Request-Id": trace_id})

	# CORS headers
	if hasattr(nxenv.local, "conf"):
		set_cors_headers(response)


def set_cors_headers(response):
	if not (
		(allowed_origins := nxenv.conf.allow_cors)
		and (request := nxenv.local.request)
		and (origin := request.headers.get("Origin"))
	):
		return

	if allowed_origins != "*":
		if not isinstance(allowed_origins, list):
			allowed_origins = [allowed_origins]

		if origin not in allowed_origins:
			return

	cors_headers = {
		"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Origin": origin,
		"Vary": "Origin",
	}

	# only required for preflight requests
	if request.method == "OPTIONS":
		cors_headers["Access-Control-Allow-Methods"] = request.headers.get("Access-Control-Request-Method")

		if allowed_headers := request.headers.get("Access-Control-Request-Headers"):
			cors_headers["Access-Control-Allow-Headers"] = allowed_headers

		# allow browsers to cache preflight requests for upto a day
		if not nxenv.conf.developer_mode:
			cors_headers["Access-Control-Max-Age"] = "86400"

	response.headers.extend(cors_headers)


def make_form_dict(request: Request):
	import json

	request_data = request.get_data(as_text=True)
	if request_data and request.is_json:
		args = json.loads(request_data)
	else:
		args = {}
		args.update(request.args or {})
		args.update(request.form or {})

	if isinstance(args, dict):
		nxenv.local.form_dict = nxenv._dict(args)
		# _ is passed by $.ajax so that the request is not cached by the browser. So, remove _ from form_dict
		nxenv.local.form_dict.pop("_", None)
	elif isinstance(args, list):
		nxenv.local.form_dict["data"] = args
	else:
		nxenv.throw(_("Invalid request arguments"))


def handle_exception(e):
	response = None
	http_status_code = getattr(e, "http_status_code", 500)
	accept_header = nxenv.get_request_header("Accept") or ""
	respond_as_json = (
		nxenv.get_request_header("Accept") and (nxenv.local.is_ajax or "application/json" in accept_header)
	) or (nxenv.local.request.path.startswith("/api/") and not accept_header.startswith("text"))

	if not nxenv.session.user:
		# If session creation fails then user won't be unset. This causes a lot of code that
		# assumes presence of this to fail. Session creation fails => guest or expired login
		# usually.
		nxenv.session.user = "Guest"

	if respond_as_json:
		# handle ajax responses first
		# if the request is ajax, send back the trace or error message
		response = nxenv.utils.response.report_error(http_status_code)

	elif isinstance(e, nxenv.SessionStopped):
		response = nxenv.utils.response.handle_session_stopped()

	elif (
		http_status_code == 500
		and (nxenv.db and isinstance(e, nxenv.db.InternalError))
		and (nxenv.db and (nxenv.db.is_deadlocked(e) or nxenv.db.is_timedout(e)))
	):
		http_status_code = 508

	elif http_status_code == 401:
		response = ErrorPage(
			http_status_code=http_status_code,
			title=_("Session Expired"),
			message=_("Your session has expired, please login again to continue."),
		).render()

	elif http_status_code == 403:
		response = ErrorPage(
			http_status_code=http_status_code,
			title=_("Not Permitted"),
			message=_("You do not have enough permissions to complete the action"),
		).render()

	elif http_status_code == 404:
		response = ErrorPage(
			http_status_code=http_status_code,
			title=_("Not Found"),
			message=_("The resource you are looking for is not available"),
		).render()

	elif http_status_code == 429:
		response = nxenv.rate_limiter.respond()

	else:
		response = ErrorPage(
			http_status_code=http_status_code, title=_("Server Error"), message=_("Uncaught Exception")
		).render()

	if e.__class__ == nxenv.AuthenticationError:
		if hasattr(nxenv.local, "login_manager"):
			nxenv.local.login_manager.clear_cookies()

	if http_status_code >= 500 or nxenv.conf.developer_mode:
		log_error_snapshot(e)

	if nxenv.conf.get("developer_mode") and not respond_as_json:
		# don't fail silently for non-json response errors
		print(nxenv.get_traceback())

	return response


def sync_database(rollback: bool) -> bool:
	# if HTTP method would change server state, commit if necessary
	if nxenv.db and (nxenv.local.flags.commit or nxenv.local.request.method in UNSAFE_HTTP_METHODS):
		nxenv.db.commit()
		rollback = False
	elif nxenv.db:
		nxenv.db.rollback()
		rollback = False

	# update session
	if session := getattr(nxenv.local, "session_obj", None):
		if session.update():
			rollback = False

	return rollback


# Always initialize sentry SDK if the DSN is sent
if sentry_dsn := os.getenv("NXENV_SENTRY_DSN"):
	import sentry_sdk
	from sentry_sdk.integrations.argv import ArgvIntegration
	from sentry_sdk.integrations.atexit import AtexitIntegration
	from sentry_sdk.integrations.dedupe import DedupeIntegration
	from sentry_sdk.integrations.excepthook import ExcepthookIntegration
	from sentry_sdk.integrations.modules import ModulesIntegration
	from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

	from nxenv.utils.sentry import NxenvIntegration, before_send

	integrations = [
		AtexitIntegration(),
		ExcepthookIntegration(),
		DedupeIntegration(),
		ModulesIntegration(),
		ArgvIntegration(),
	]

	experiments = {}
	kwargs = {}

	if os.getenv("ENABLE_SENTRY_DB_MONITORING"):
		integrations.append(NxenvIntegration())
		experiments["record_sql_params"] = True

	if tracing_sample_rate := os.getenv("SENTRY_TRACING_SAMPLE_RATE"):
		kwargs["traces_sample_rate"] = float(tracing_sample_rate)
		application = SentryWsgiMiddleware(application)

	if profiling_sample_rate := os.getenv("SENTRY_PROFILING_SAMPLE_RATE"):
		kwargs["profiles_sample_rate"] = float(profiling_sample_rate)

	sentry_sdk.init(
		dsn=sentry_dsn,
		before_send=before_send,
		attach_stacktrace=True,
		release=nxenv.__version__,
		auto_enabling_integrations=False,
		default_integrations=False,
		integrations=integrations,
		_experiments=experiments,
		**kwargs,
	)


def serve(
	port=8000,
	profile=False,
	no_reload=False,
	no_threading=False,
	site=None,
	sites_path=".",
	proxy=False,
):
	global application, _site, _sites_path
	_site = site
	_sites_path = sites_path

	from werkzeug.serving import run_simple

	if profile or os.environ.get("USE_PROFILER"):
		application = ProfilerMiddleware(application, sort_by=("cumtime", "calls"))

	if not os.environ.get("NO_STATICS"):
		application = application_with_statics()

	if proxy or os.environ.get("USE_PROXY"):
		application = ProxyFix(application, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

	application.debug = True
	application.config = {"SERVER_NAME": "127.0.0.1:8000"}

	log = logging.getLogger("werkzeug")
	log.propagate = False

	in_test_env = os.environ.get("CI")
	if in_test_env:
		log.setLevel(logging.ERROR)

	run_simple(
		"0.0.0.0",
		int(port),
		application,
		exclude_patterns=["test_*"],
		use_reloader=False if in_test_env else not no_reload,
		use_debugger=not in_test_env,
		use_evalex=not in_test_env,
		threaded=not no_threading,
	)


def application_with_statics():
	global application, _sites_path

	application = SharedDataMiddleware(application, {"/assets": str(os.path.join(_sites_path, "assets"))})

	application = StaticDataMiddleware(application, {"/files": str(os.path.abspath(_sites_path))})

	return application
