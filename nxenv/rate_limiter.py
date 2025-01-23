# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import time
from collections.abc import Callable
from functools import wraps

from werkzeug.wrappers import Response

import nxenv
from nxenv import _
from nxenv.utils import cint


def apply():
	rate_limit = nxenv.conf.rate_limit
	if rate_limit:
		nxenv.local.rate_limiter = RateLimiter(rate_limit["limit"], rate_limit["window"])
		nxenv.local.rate_limiter.apply()


def update():
	if hasattr(nxenv.local, "rate_limiter"):
		nxenv.local.rate_limiter.update()


def respond():
	if hasattr(nxenv.local, "rate_limiter"):
		return nxenv.local.rate_limiter.respond()


class RateLimiter:
	__slots__ = (
		"counter",
		"duration",
		"end",
		"key",
		"limit",
		"rejected",
		"remaining",
		"reset",
		"spent",
		"start",
		"window",
		"window_number",
	)

	def __init__(self, limit, window):
		self.limit = int(limit * 1000000)
		self.window = window

		self.start = time.time()

		self.window_number, self.spent = divmod(int(self.start), self.window)
		self.key = nxenv.cache.make_key(f"rate-limit-counter-{self.window_number}")
		self.counter = cint(nxenv.cache.get(self.key))
		if not self.counter:
			# This is the first request in this window
			nxenv.cache.incrby(self.key, 0)
			nxenv.cache.expire(self.key, self.window)

		self.remaining = max(self.limit - self.counter, 0)
		self.reset = self.window - self.spent

		self.end = None
		self.duration = None
		self.rejected = False

	def apply(self):
		if self.counter > self.limit:
			self.rejected = True
			self.reject()

	def reject(self):
		raise nxenv.TooManyRequestsError

	def update(self):
		self.record_request_end()
		nxenv.cache.incrby(self.key, self.duration)

	def headers(self):
		self.record_request_end()
		headers = {
			"X-RateLimit-Reset": self.reset,
			"X-RateLimit-Limit": self.limit,
			"X-RateLimit-Remaining": self.remaining,
		}
		if self.rejected:
			headers["Retry-After"] = self.reset

		return headers

	def record_request_end(self):
		if self.end is not None:
			return
		self.end = time.time()
		self.duration = int((self.end - self.start) * 1000000)

	def respond(self):
		if self.rejected:
			return Response(_("Too Many Requests"), status=429)


def rate_limit(
	key: str | None = None,
	limit: int | Callable = 5,
	seconds: int = 24 * 60 * 60,
	methods: str | list = "ALL",
	ip_based: bool = True,
):
	"""Decorator to rate limit an endpoint.

	This will limit Number of requests per endpoint to `limit` within `seconds`.
	Uses redis cache to track request counts.

	:param key: Key is used to identify the requests uniqueness (Optional)
	:param limit: Maximum number of requests to allow with in window time
	:type limit: Callable or Integer
	:param seconds: window time to allow requests
	:param methods: Limit the validation for these methods.
	        `ALL` is a wildcard that applies rate limit on all methods.
	:type methods: string or list or tuple
	:param ip_based: flag to allow ip based rate-limiting
	:type ip_based: Boolean

	Return: a decorator function that limit the number of requests per endpoint
	"""

	def ratelimit_decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			# Do not apply rate limits if method is not opted to check
			if not nxenv.request or (
				methods != "ALL" and nxenv.request.method and nxenv.request.method.upper() not in methods
			):
				return fn(*args, **kwargs)

			_limit = limit() if callable(limit) else limit

			ip = nxenv.local.request_ip if ip_based is True else None

			user_key = nxenv.form_dict.get(key, "")

			identity = None

			if key and ip_based:
				identity = ":".join([ip, user_key])

			identity = identity or ip or user_key

			if not identity:
				nxenv.throw(_("Either key or IP flag is required."))

			cache_key = nxenv.cache.make_key(f"rl:{nxenv.form_dict.cmd}:{identity}")

			value = nxenv.cache.get(cache_key)
			if not value:
				nxenv.cache.setex(cache_key, seconds, 0)

			value = nxenv.cache.incrby(cache_key, 1)
			if value > _limit:
				nxenv.throw(
					_("You hit the rate limit because of too many requests. Please try after sometime."),
					nxenv.RateLimitExceededError,
				)

			return fn(*args, **kwargs)

		return wrapper

	return ratelimit_decorator
