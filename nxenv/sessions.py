# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
"""
Boot session from cache or build

Session bootstraps info needed by common client side activities including
permission, homepage, default variables, system defaults etc
"""

import json
from urllib.parse import unquote

import redis

import nxenv
import nxenv.defaults
import nxenv.model.meta
import nxenv.translate
import nxenv.utils
from nxenv import _
from nxenv.apps import get_apps, get_default_path, is_desk_apps
from nxenv.cache_manager import clear_user_cache, reset_metadata_version
from nxenv.query_builder import Order
from nxenv.utils import cint, cstr, get_assets_json
from nxenv.utils.change_log import has_app_update_notifications
from nxenv.utils.data import add_to_date


@nxenv.whitelist()
def clear():
	nxenv.local.session_obj.update(force=True)
	nxenv.local.db.commit()
	clear_user_cache(nxenv.session.user)
	nxenv.response["message"] = _("Cache Cleared")


def clear_sessions(user=None, keep_current=False, force=False):
	"""Clear other sessions of the current user. Called at login / logout

	:param user: user name (default: current user)
	:param keep_current: keep current session (default: false)
	:param force: triggered by the user (default false)
	"""

	reason = "Logged In From Another Session"
	if force:
		reason = "Force Logged out by the user"

	for sid in get_sessions_to_clear(user, keep_current, force):
		delete_session(sid, reason=reason)


def get_sessions_to_clear(user=None, keep_current=False, force=False):
	"""Return sessions of the current user. Called at login / logout.

	:param user: user name (default: current user)
	:param keep_current: keep current session (default: false)
	:param force: ignore simultaneous sessions count, log the user out of all except current (default: false)
	"""
	if not user:
		user = nxenv.session.user

	offset = 0
	if not force and user == nxenv.session.user:
		simultaneous_sessions = nxenv.db.get_value("User", user, "simultaneous_sessions") or 1
		offset = simultaneous_sessions

	session = nxenv.qb.DocType("Sessions")
	session_id = nxenv.qb.from_(session).where(session.user == user)
	if keep_current:
		if not force:
			offset = max(0, offset - 1)
		session_id = session_id.where(session.sid != nxenv.session.sid)

	query = (
		session_id.select(session.sid).offset(offset).limit(100).orderby(session.lastupdate, order=Order.desc)
	)

	return query.run(pluck=True)


def delete_session(sid=None, user=None, reason="Session Expired"):
	from nxenv.core.doctype.activity_log.feed import logout_feed

	if nxenv.flags.read_only:
		# This isn't manually initiated logout, most likely user's cookies were expired in such case
		# we should just ignore it till database is back up again.
		return

	if sid and not user:
		table = nxenv.qb.DocType("Sessions")
		user_details = nxenv.qb.from_(table).where(table.sid == sid).select(table.user).run(as_dict=True)
		if user_details:
			user = user_details[0].get("user")

	logout_feed(user, reason)
	nxenv.db.delete("Sessions", {"sid": sid})
	nxenv.db.commit()

	nxenv.cache.hdel("session", sid)


def clear_all_sessions(reason=None):
	"""This effectively logs out all users"""
	nxenv.only_for("Administrator")
	if not reason:
		reason = "Deleted All Active Session"
	for sid in nxenv.qb.from_("Sessions").select("sid").run(pluck=True):
		delete_session(sid, reason=reason)


def get_expired_sessions():
	"""Return list of expired sessions."""

	sessions = nxenv.qb.DocType("Sessions")
	return (
		nxenv.qb.from_(sessions).select(sessions.sid).where(sessions.lastupdate < get_expired_threshold())
	).run(pluck=True)


def clear_expired_sessions():
	"""This function is meant to be called from scheduler"""
	for sid in get_expired_sessions():
		delete_session(sid, reason="Session Expired")


def get():
	"""get session boot info"""
	from nxenv.boot import get_bootinfo
	from nxenv.desk.doctype.note.note import get_unseen_notes
	from nxenv.utils.change_log import get_change_log

	bootinfo = None
	if not getattr(nxenv.conf, "disable_session_cache", None):
		# check if cache exists
		bootinfo = nxenv.cache.hget("bootinfo", nxenv.session.user)
		if bootinfo:
			bootinfo["from_cache"] = 1
			bootinfo["user"]["recent"] = json.dumps(nxenv.cache.hget("user_recent", nxenv.session.user))

	if not bootinfo:
		# if not create it
		bootinfo = get_bootinfo()
		nxenv.cache.hset("bootinfo", nxenv.session.user, bootinfo)
		try:
			nxenv.cache.ping()
		except redis.exceptions.ConnectionError:
			message = _("Redis cache server not running. Please contact Administrator / Tech support")
			if "messages" in bootinfo:
				bootinfo["messages"].append(message)
			else:
				bootinfo["messages"] = [message]

		# check only when clear cache is done, and don't cache this
		if nxenv.local.request:
			bootinfo["change_log"] = get_change_log()

	bootinfo["metadata_version"] = nxenv.client_cache.get_value("metadata_version")
	if not bootinfo["metadata_version"]:
		bootinfo["metadata_version"] = reset_metadata_version()

	bootinfo.notes = get_unseen_notes()
	bootinfo.assets_json = get_assets_json()
	bootinfo.read_only = bool(nxenv.flags.read_only)

	for hook in nxenv.get_hooks("extend_bootinfo"):
		nxenv.get_attr(hook)(bootinfo=bootinfo)

	bootinfo["lang"] = nxenv.translate.get_user_lang()
	bootinfo["disable_async"] = nxenv.conf.disable_async

	bootinfo["setup_complete"] = cint(nxenv.get_system_settings("setup_complete"))
	bootinfo["apps_data"] = {
		"apps": get_apps() or [],
		"is_desk_apps": 1 if bool(is_desk_apps(get_apps())) else 0,
		"default_path": get_default_path() or "",
	}

	bootinfo["desk_theme"] = nxenv.get_cached_value("User", nxenv.session.user, "desk_theme") or "Light"
	bootinfo["user"]["impersonated_by"] = nxenv.session.data.get("impersonated_by")
	bootinfo["navbar_settings"] = nxenv.client_cache.get_doc("Navbar Settings")
	bootinfo.has_app_updates = has_app_update_notifications()

	return bootinfo


@nxenv.whitelist()
def get_boot_assets_json():
	return get_assets_json()


def get_csrf_token():
	if not nxenv.local.session.data.csrf_token:
		generate_csrf_token()

	return nxenv.local.session.data.csrf_token


def generate_csrf_token():
	nxenv.local.session.data.csrf_token = nxenv.generate_hash()
	if not nxenv.flags.in_test:
		nxenv.local.session_obj.update(force=True)


class Session:
	__slots__ = ("_update_in_cache", "data", "full_name", "sid", "time_diff", "user", "user_type")

	def __init__(self, user, resume=False, full_name=None, user_type=None):
		self.sid = cstr(
			nxenv.form_dict.pop("sid", None) or unquote(nxenv.request.cookies.get("sid", "Guest"))
		)
		self.user = user
		self.user_type = user_type
		self.full_name = full_name
		self.data = nxenv._dict({"data": nxenv._dict({})})
		self.time_diff = None
		self._update_in_cache = False

		# set local session
		nxenv.local.session = self.data

		if resume:
			self.resume()

		else:
			if self.user:
				self.validate_user()
				self.start()

	def validate_user(self):
		if not nxenv.get_cached_value("User", self.user, "enabled"):
			nxenv.throw(
				_("User {0} is disabled. Please contact your System Manager.").format(self.user),
				nxenv.ValidationError,
			)

	def start(self):
		"""start a new session"""
		# generate sid
		if self.user == "Guest":
			sid = "Guest"
		else:
			sid = nxenv.generate_hash()

		self.data.user = self.user
		self.sid = self.data.sid = sid
		self.data.data.user = self.user
		self.data.data.session_ip = nxenv.local.request_ip
		if self.user != "Guest":
			self.data.data.update(
				{
					"last_updated": nxenv.utils.now(),
					"session_expiry": get_expiry_period(),
					"full_name": self.full_name,
					"user_type": self.user_type,
				}
			)

		# insert session
		if self.user != "Guest":
			self.insert_session_record()

			# update user
			user = nxenv.get_doc("User", self.data["user"])
			user_doctype = nxenv.qb.DocType("User")
			(
				nxenv.qb.update(user_doctype)
				.set(user_doctype.last_login, nxenv.utils.now())
				.set(user_doctype.last_ip, nxenv.local.request_ip)
				.set(user_doctype.last_active, nxenv.utils.now())
				.where(user_doctype.name == self.data["user"])
			).run()

			user.run_notifications("before_change")
			user.run_notifications("on_update")
			nxenv.db.commit()

	def insert_session_record(self):
		Sessions = nxenv.qb.DocType("Sessions")
		now = nxenv.utils.now()

		(
			nxenv.qb.into(Sessions)
			.columns(Sessions.sessiondata, Sessions.user, Sessions.lastupdate, Sessions.sid, Sessions.status)
			.insert(
				(
					nxenv.as_json(self.data["data"], indent=None, separators=(",", ":")),
					self.data["user"],
					now,
					self.data["sid"],
					"Active",
				)
			)
		).run()
		nxenv.cache.hset("session", self.data.sid, self.data)

	def resume(self):
		"""non-login request: load a session"""
		import nxenv
		from nxenv.auth import validate_ip_address

		data = self.get_session_record()

		if data:
			self.data.update({"data": data, "user": data.user, "sid": self.sid})
			self.user = data.user
			validate_ip_address(self.user)
		else:
			self.start_as_guest()

		if self.sid != "Guest":
			nxenv.local.lang = nxenv.translate.get_user_lang(self.data.user)

	def get_session_record(self):
		"""get session record, or return the standard Guest Record"""
		from nxenv.auth import clear_cookies

		r = self.get_session_data()

		if not r:
			nxenv.response["session_expired"] = 1
			clear_cookies()
			self.sid = "Guest"
			r = self.get_session_data()

		return r

	def get_session_data(self):
		if self.sid == "Guest":
			return nxenv._dict({"user": "Guest"})

		data = self.get_session_data_from_cache()
		if not data:
			self._update_in_cache = True
			data = self.get_session_data_from_db()
		return data

	def get_session_data_from_cache(self):
		data = nxenv.cache.hget("session", self.sid)
		if data:
			data = nxenv._dict(data)
			session_data = data.get("data", {})

			# set user for correct timezone
			self.time_diff = nxenv.utils.time_diff_in_seconds(
				nxenv.utils.now(), session_data.get("last_updated")
			)
			expiry = get_expiry_in_seconds(session_data.get("session_expiry"))

			if self.time_diff > expiry:
				self._delete_session()
				data = None

		return data and data.data

	def get_session_data_from_db(self):
		sessions = nxenv.qb.DocType("Sessions")

		record = (
			nxenv.qb.from_(sessions)
			.select(sessions.user, sessions.sessiondata)
			.where(sessions.sid == self.sid)
			.where(sessions.lastupdate > get_expired_threshold())
		).run()

		if record:
			data = nxenv.parse_json(record[0][1] or "{}")
			data.user = record[0][0]
		else:
			self._delete_session()
			data = None

		return data

	def _delete_session(self):
		delete_session(self.sid, reason="Session Expired")

	def start_as_guest(self):
		"""all guests share the same 'Guest' session"""
		self.user = "Guest"
		self.start()

	def update(self, force=False):
		"""extend session expiry"""

		if nxenv.session.user == "Guest":
			return

		now = nxenv.utils.now_datetime()

		# update session in db
		last_updated = self.data.data.last_updated
		time_diff = nxenv.utils.time_diff_in_seconds(now, last_updated) if last_updated else None

		# database persistence is secondary, don't update it too often
		updated_in_db = False
		if (
			force or (time_diff is None) or (time_diff > 600) or self._update_in_cache
		) and not nxenv.flags.read_only:
			self.data.data.last_updated = now
			self.data.data.lang = str(nxenv.lang)

			Sessions = nxenv.qb.DocType("Sessions")
			# update sessions table
			(
				nxenv.qb.update(Sessions)
				.where(Sessions.sid == self.data["sid"])
				.set(
					Sessions.sessiondata,
					nxenv.as_json(self.data["data"], indent=None, separators=(",", ":")),
				)
				.set(Sessions.lastupdate, now)
			).run()

			nxenv.db.set_value("User", nxenv.session.user, "last_active", now, update_modified=False)

			nxenv.db.commit()
			updated_in_db = True
			nxenv.cache.hset("session", self.sid, self.data)

		return updated_in_db

	def set_impersonsated(self, original_user):
		self.data.data.impersonated_by = original_user
		# Forcefully flush session
		self.update(force=True)


def get_expiry_period_for_query():
	if nxenv.db.db_type == "postgres":
		return get_expiry_period()
	else:
		return get_expiry_in_seconds()


def get_expiry_in_seconds(expiry=None):
	if not expiry:
		expiry = get_expiry_period()

	parts = expiry.split(":")
	return (cint(parts[0]) * 3600) + (cint(parts[1]) * 60) + cint(parts[2])


def get_expired_threshold():
	"""Get cutoff time before which all sessions are considered expired."""

	now = nxenv.utils.now()
	expiry_in_seconds = get_expiry_in_seconds()

	return add_to_date(now, seconds=-expiry_in_seconds, as_string=True)


def get_expiry_period():
	exp_sec = nxenv.get_system_settings("session_expiry") or "240:00:00"

	# incase seconds is missing
	if len(exp_sec.split(":")) == 2:
		exp_sec = exp_sec + ":00"

	return exp_sec
