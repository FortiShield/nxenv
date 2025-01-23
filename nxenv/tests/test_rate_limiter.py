# Copyright (c) 2020, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import time

from werkzeug.wrappers import Response

import nxenv
import nxenv.rate_limiter
from nxenv.rate_limiter import RateLimiter
from nxenv.tests import IntegrationTestCase
from nxenv.utils import cint


class TestRateLimiter(IntegrationTestCase):
	def test_apply_with_limit(self):
		nxenv.conf.rate_limit = {"window": 86400, "limit": 1}
		nxenv.rate_limiter.apply()

		self.assertTrue(hasattr(nxenv.local, "rate_limiter"))
		self.assertIsInstance(nxenv.local.rate_limiter, RateLimiter)

		nxenv.cache.delete(nxenv.local.rate_limiter.key)
		delattr(nxenv.local, "rate_limiter")

	def test_apply_without_limit(self):
		nxenv.conf.rate_limit = None
		nxenv.rate_limiter.apply()

		self.assertFalse(hasattr(nxenv.local, "rate_limiter"))

	def test_respond_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		nxenv.conf.rate_limit = {"window": 86400, "limit": 0.01}
		self.assertRaises(nxenv.TooManyRequestsError, nxenv.rate_limiter.apply)
		nxenv.rate_limiter.update()

		response = nxenv.rate_limiter.respond()

		self.assertIsInstance(response, Response)
		self.assertEqual(response.status_code, 429)

		headers = nxenv.local.rate_limiter.headers()
		self.assertIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertIn("X-RateLimit-Limit", headers)
		self.assertIn("X-RateLimit-Remaining", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"]) <= 86400)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 0)

		nxenv.cache.delete(limiter.key)
		nxenv.cache.delete(nxenv.local.rate_limiter.key)
		delattr(nxenv.local, "rate_limiter")

	def test_respond_under_limit(self):
		nxenv.conf.rate_limit = {"window": 86400, "limit": 0.01}
		nxenv.rate_limiter.apply()
		nxenv.rate_limiter.update()
		response = nxenv.rate_limiter.respond()
		self.assertEqual(response, None)

		nxenv.cache.delete(nxenv.local.rate_limiter.key)
		delattr(nxenv.local, "rate_limiter")

	def test_headers_under_limit(self):
		nxenv.conf.rate_limit = {"window": 86400, "limit": 0.01}
		nxenv.rate_limiter.apply()
		nxenv.rate_limiter.update()
		headers = nxenv.local.rate_limiter.headers()
		self.assertNotIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"] < 86400))
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 10000)

		nxenv.cache.delete(nxenv.local.rate_limiter.key)
		delattr(nxenv.local, "rate_limiter")

	def test_reject_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.01, 86400)
		self.assertRaises(nxenv.TooManyRequestsError, limiter.apply)

		nxenv.cache.delete(limiter.key)

	def test_do_not_reject_under_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.02, 86400)
		self.assertEqual(limiter.apply(), None)

		nxenv.cache.delete(limiter.key)

	def test_update_method(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		self.assertEqual(limiter.duration, cint(nxenv.cache.get(limiter.key)))

		nxenv.cache.delete(limiter.key)

	def test_window_expires(self):
		limiter = RateLimiter(1000, 1)
		self.assertTrue(nxenv.cache.exists(limiter.key, shared=True))
		limiter.update()
		self.assertTrue(nxenv.cache.exists(limiter.key, shared=True))
		time.sleep(1.1)
		self.assertFalse(nxenv.cache.exists(limiter.key, shared=True))
		nxenv.cache.delete(limiter.key)
