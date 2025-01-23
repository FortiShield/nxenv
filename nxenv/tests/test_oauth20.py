# Copyright (c) 2022, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from werkzeug.test import TestResponse

import nxenv
from nxenv.integrations.oauth2 import encode_params
from nxenv.tests import IntegrationTestCase
from nxenv.tests.test_api import get_test_client, make_request, suppress_stdout
from nxenv.tests.utils import make_test_records

if TYPE_CHECKING:
	from nxenv.integrations.doctype.social_login_key.social_login_key import SocialLoginKey


class NxenvRequestTestCase(IntegrationTestCase):
	@property
	def sid(self) -> str:
		if not getattr(self, "_sid", None):
			from nxenv.auth import CookieManager, LoginManager
			from nxenv.utils import set_request

			set_request(path="/")
			nxenv.local.cookie_manager = CookieManager()
			nxenv.local.login_manager = LoginManager()
			nxenv.local.login_manager.login_as("test@example.com")
			self._sid = nxenv.session.sid

		return self._sid

	def get(self, path: str, params: dict | None = None, **kwargs) -> TestResponse:
		return make_request(
			target=self.TEST_CLIENT.get, args=(path,), kwargs={"data": params, **kwargs}, site=self.site
		)

	def post(self, path, data, **kwargs) -> TestResponse:
		return make_request(
			target=self.TEST_CLIENT.post, args=(path,), kwargs={"data": data, **kwargs}, site=self.site
		)

	def put(self, path, data, **kwargs) -> TestResponse:
		return make_request(
			target=self.TEST_CLIENT.put, args=(path,), kwargs={"data": data, **kwargs}, site=self.site
		)

	def delete(self, path, **kwargs) -> TestResponse:
		return make_request(target=self.TEST_CLIENT.delete, args=(path,), kwargs=kwargs, site=self.site)


class TestOAuth20(NxenvRequestTestCase):
	site = nxenv.local.site

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_test_records("User")

		cls.form_header = {"content-type": "application/x-www-form-urlencoded"}
		cls.scope = "all openid"
		cls.redirect_uri = "http://localhost"

		# Set Nxenv server URL reqired for id_token generation
		nxenv_login_key: SocialLoginKey = nxenv.new_doc("Social Login Key")
		nxenv_login_key.get_social_login_provider("Nxenv", initialize=True)
		nxenv_login_key.base_url = nxenv.utils.get_url()
		nxenv_login_key.enable_social_login = 0
		nxenv_login_key.insert(ignore_if_duplicate=True)
		nxenv.db.commit()

	def setUp(self):
		self.TEST_CLIENT = get_test_client()
		self.oauth_client = nxenv.new_doc("OAuth Client")
		self.oauth_client.update(
			{
				"app_name": "_Test OAuth Client",
				"client_secret": "test_client_secret",
				"default_redirect_uri": "http://localhost",
				"docstatus": 0,
				"doctype": "OAuth Client",
				"grant_type": "Authorization Code",
				"name": "test_client_id",
				"redirect_uris": "http://localhost",
				"response_type": "Code",
				"scopes": "all openid",
				"skip_authorization": 1,
			}
		)
		self.oauth_client.insert()

		self.client_id = self.oauth_client.get("client_id")
		self.client_secret = self.oauth_client.get("client_secret")

	def tearDown(self):
		self.oauth_client.delete(force=True)
		nxenv.db.rollback()

	def test_invalid_login(self):
		with suppress_stdout():
			self.assertFalse(check_valid_openid_response(client=self))

	def test_login_using_authorization_code(self):
		update_client_for_auth_code_grant(self.client_id)

		# Go to Authorize url
		self.TEST_CLIENT.set_cookie(key="sid", value=self.sid)
		resp = self.get(
			"/api/method/nxenv.integrations.oauth2.authorize",
			{
				"client_id": self.client_id,
				"scope": self.scope,
				"response_type": "code",
				"redirect_uri": self.redirect_uri,
			},
			follow_redirects=True,
		)
		query = parse_qs(resp.request.environ["QUERY_STRING"])
		auth_code = query.get("code")[0]

		# Request for bearer token
		token_response = self.post(
			"/api/method/nxenv.integrations.oauth2.get_token",
			headers=self.form_header,
			data={
				"grant_type": "authorization_code",
				"code": auth_code,
				"redirect_uri": self.redirect_uri,
				"client_id": self.client_id,
				"scope": self.scope,
			},
		)

		# Parse bearer token json
		bearer_token = token_response.json

		self.assertTrue(bearer_token.get("access_token"))
		self.assertTrue(bearer_token.get("expires_in"))
		self.assertTrue(bearer_token.get("id_token"))
		self.assertTrue(bearer_token.get("refresh_token"))
		self.assertTrue(bearer_token.get("scope"))
		self.assertTrue(bearer_token.get("token_type") == "Bearer")
		self.assertTrue(
			check_valid_openid_response(access_token=bearer_token.get("access_token"), client=self)
		)

		decoded_token = self.decode_id_token(bearer_token.get("id_token"))
		self.assertEqual(decoded_token["email"], "test@example.com")

	def test_login_using_authorization_code_with_pkce(self):
		update_client_for_auth_code_grant(self.client_id)

		# Go to Authorize url
		self.TEST_CLIENT.set_cookie(key="sid", value=self.sid)
		resp = self.get(
			"/api/method/nxenv.integrations.oauth2.authorize",
			{
				"client_id": self.client_id,
				"scope": self.scope,
				"response_type": "code",
				"redirect_uri": self.redirect_uri,
				"code_challenge_method": "S256",
				"code_challenge": "21XaP8MJjpxCMRxgEzBP82sZ73PRLqkyBUta1R309J0",
			},
			follow_redirects=True,
		)

		# Get authorization code from redirected URL
		query = parse_qs(resp.request.environ["QUERY_STRING"])
		auth_code = query.get("code")[0]

		# Request for bearer token
		token_response = self.post(
			"/api/method/nxenv.integrations.oauth2.get_token",
			headers=self.form_header,
			data={
				"grant_type": "authorization_code",
				"code": auth_code,
				"redirect_uri": self.redirect_uri,
				"client_id": self.client_id,
				"scope": self.scope,
				"code_verifier": "420",
			},
		)

		# Parse bearer token json
		bearer_token = token_response.json

		self.assertTrue(bearer_token.get("access_token"))
		self.assertTrue(bearer_token.get("id_token"))

		decoded_token = self.decode_id_token(bearer_token.get("id_token"))
		self.assertEqual(decoded_token["email"], "test@example.com")

	def test_revoke_token(self):
		client = nxenv.get_doc("OAuth Client", self.client_id)
		client.grant_type = "Authorization Code"
		client.response_type = "Code"
		client.save()
		nxenv.db.commit()

		# Go to Authorize url
		self.TEST_CLIENT.set_cookie(key="sid", value=self.sid)
		resp = self.get(
			"/api/method/nxenv.integrations.oauth2.authorize",
			{
				"client_id": self.client_id,
				"scope": self.scope,
				"response_type": "code",
				"redirect_uri": self.redirect_uri,
			},
			follow_redirects=True,
		)

		# Get authorization code from redirected URL
		query = parse_qs(resp.request.environ["QUERY_STRING"])
		auth_code = query.get("code")[0]

		# Request for bearer token
		token_response = self.post(
			"/api/method/nxenv.integrations.oauth2.get_token",
			headers=self.form_header,
			data={
				"grant_type": "authorization_code",
				"code": auth_code,
				"redirect_uri": self.redirect_uri,
				"client_id": self.client_id,
			},
		)

		# Parse bearer token json
		bearer_token = token_response.json

		# Revoke Token
		revoke_token_response = self.post(
			"/api/method/nxenv.integrations.oauth2.revoke_token",
			headers=self.form_header,
			data={"token": bearer_token.get("access_token")},
		)

		self.assertTrue(revoke_token_response.status_code == 200)

		# Check revoked token
		self.assertFalse(
			check_valid_openid_response(access_token=bearer_token.get("access_token"), client=self)
		)

	def test_resource_owner_password_credentials_grant(self):
		client = nxenv.get_doc("OAuth Client", self.client_id)
		client.grant_type = "Authorization Code"
		client.response_type = "Code"
		client.save()
		nxenv.db.commit()

		# Request for bearer token
		token_response = self.post(
			"/api/method/nxenv.integrations.oauth2.get_token",
			data={
				"grant_type": "password",
				"username": "test@example.com",
				"password": "Eastern_43A1W",
				"client_id": self.client_id,
				"scope": self.scope,
			},
			headers=self.form_header,
		)

		# Parse bearer token json
		bearer_token = token_response.json

		# Check token for valid response
		self.assertTrue(
			check_valid_openid_response(access_token=bearer_token.get("access_token"), client=self)
		)

	def test_login_using_implicit_token(self):
		oauth_client = nxenv.get_doc("OAuth Client", self.client_id)
		oauth_client.grant_type = "Implicit"
		oauth_client.response_type = "Token"
		oauth_client.save()
		oauth_client_before = oauth_client.get_doc_before_save()
		nxenv.db.commit()

		session = requests.Session()
		login(session)

		redirect_destination = None

		# Go to Authorize url
		try:
			session.get(
				get_full_url("/api/method/nxenv.integrations.oauth2.authorize"),
				params=encode_params(
					{
						"client_id": self.client_id,
						"scope": self.scope,
						"response_type": "token",
						"redirect_uri": self.redirect_uri,
					}
				),
			)
		except requests.exceptions.ConnectionError as ex:
			redirect_destination = ex.request.url

		response_dict = parse_qs(urlparse(redirect_destination).fragment)

		self.assertTrue(response_dict.get("access_token"))
		self.assertTrue(response_dict.get("expires_in"))
		self.assertTrue(response_dict.get("scope"))
		self.assertTrue(response_dict.get("token_type"))
		self.assertTrue(check_valid_openid_response(response_dict.get("access_token")[0]))
		oauth_client.delete(force=True)
		oauth_client_before.insert()
		nxenv.db.commit()

	def test_openid_code_id_token(self):
		update_client_for_auth_code_grant(self.client_id)
		nonce = nxenv.generate_hash()

		# Go to Authorize url
		self.TEST_CLIENT.set_cookie(key="sid", value=self.sid)
		resp = self.get(
			"/api/method/nxenv.integrations.oauth2.authorize",
			{
				"client_id": self.client_id,
				"scope": self.scope,
				"response_type": "code",
				"redirect_uri": self.redirect_uri,
				"nonce": nonce,
			},
			follow_redirects=True,
		)

		# Get authorization code from redirected URL
		query = parse_qs(resp.request.environ["QUERY_STRING"])
		auth_code = query.get("code")[0]

		# Request for bearer token
		token_response = self.post(
			"/api/method/nxenv.integrations.oauth2.get_token",
			headers=self.form_header,
			data=encode_params(
				{
					"grant_type": "authorization_code",
					"code": auth_code,
					"redirect_uri": self.redirect_uri,
					"client_id": self.client_id,
					"scope": self.scope,
				}
			),
		)

		# Parse bearer token json
		bearer_token = token_response.json

		payload = self.decode_id_token(bearer_token.get("id_token"))
		self.assertEqual(payload["email"], "test@example.com")

		self.assertTrue(payload.get("nonce") == nonce)

	def decode_id_token(self, id_token):
		import jwt

		return jwt.decode(
			id_token,
			audience=self.client_id,
			key=self.client_secret,
			algorithms=["HS256"],
			options={"verify_signature": True, "require": ["exp", "iat", "aud"]},
		)


def check_valid_openid_response(access_token=None, client: "NxenvRequestTestCase" = None):
	"""Return True for valid response."""
	# Use token in header
	headers = {}
	URL = "/api/method/nxenv.integrations.oauth2.openid_profile"

	if access_token:
		headers["Authorization"] = f"Bearer {access_token}"

	# check openid for email test@example.com
	if client:
		openid_response = client.get(URL, headers=headers)
	else:
		openid_response = requests.get(get_full_url(URL), headers=headers)

	return openid_response.status_code == 200


def login(session):
	session.post(get_full_url("/api/method/login"), data={"usr": "test@example.com", "pwd": "Eastern_43A1W"})


def get_full_url(endpoint):
	"""Turn '/endpoint' into 'http://127.0.0.1:8000/endpoint'."""
	return urljoin(nxenv.utils.get_url(), endpoint)


def update_client_for_auth_code_grant(client_id):
	client = nxenv.get_doc("OAuth Client", client_id)
	client.grant_type = "Authorization Code"
	client.response_type = "Code"
	client.save()
	nxenv.db.commit()
	return client
