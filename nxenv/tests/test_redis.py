import functools
from unittest.mock import patch

import redis

import nxenv
from nxenv.tests import IntegrationTestCase
from nxenv.utils import get_nxcli_id
from nxenv.utils.background_jobs import get_redis_conn
from nxenv.utils.redis_queue import RedisQueue


def version_tuple(version):
	return tuple(map(int, (version.split("."))))


def skip_if_redis_version_lt(version):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			conn = get_redis_conn()
			redis_version = conn.execute_command("info")["redis_version"]
			if version_tuple(redis_version) < version_tuple(version):
				return
			return func(*args, **kwargs)

		return wrapper

	return decorator


class TestRedisAuth(IntegrationTestCase):
	@skip_if_redis_version_lt("6.0")
	@patch.dict(nxenv.conf, {"nxcli_id": "test_nxcli", "use_rq_auth": False})
	def test_rq_gen_acllist(self):
		"""Make sure that ACL list is genrated"""
		acl_list = RedisQueue.gen_acl_list()
		self.assertEqual(acl_list[1]["nxcli"][0], get_nxcli_id())

	@skip_if_redis_version_lt("6.0")
	@patch.dict(nxenv.conf, {"nxcli_id": "test_nxcli", "use_rq_auth": False})
	def test_adding_redis_user(self):
		acl_list = RedisQueue.gen_acl_list()
		username, password = acl_list[1]["nxcli"]
		conn = get_redis_conn()

		conn.acl_deluser(username)
		_ = RedisQueue(conn).add_user(username, password)
		self.assertTrue(conn.acl_getuser(username))
		conn.acl_deluser(username)

	@skip_if_redis_version_lt("6.0")
	@patch.dict(nxenv.conf, {"nxcli_id": "test_nxcli", "use_rq_auth": False})
	def test_rq_namespace(self):
		"""Make sure that user can access only their respective namespace."""
		# Current nxcli ID
		nxcli_id = nxenv.conf.get("nxcli_id")
		conn = get_redis_conn()
		conn.set("rq:queue:test_nxcli1:abc", "value")
		conn.set(f"rq:queue:{nxcli_id}:abc", "value")

		# Create new Redis Queue user
		tmp_nxcli_id = "test_nxcli1"
		username, password = tmp_nxcli_id, "password1"
		conn.acl_deluser(username)
		nxenv.conf.update({"nxcli_id": tmp_nxcli_id})
		_ = RedisQueue(conn).add_user(username, password)
		test_nxcli1_conn = RedisQueue.get_connection(username, password)

		self.assertEqual(test_nxcli1_conn.get("rq:queue:test_nxcli1:abc"), b"value")

		# User should not be able to access queues apart from their nxcli queues
		with self.assertRaises(redis.exceptions.NoPermissionError):
			test_nxcli1_conn.get(f"rq:queue:{nxcli_id}:abc")

		nxenv.conf.update({"nxcli_id": nxcli_id})
		conn.acl_deluser(username)
