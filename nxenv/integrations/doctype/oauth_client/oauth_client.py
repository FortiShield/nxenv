# Copyright (c) 2015, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv import _
from nxenv.model.document import Document
from nxenv.permissions import SYSTEM_USER_ROLE


class OAuthClient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.integrations.doctype.oauth_client_role.oauth_client_role import OAuthClientRole
		from nxenv.types import DF

		allowed_roles: DF.TableMultiSelect[OAuthClientRole]
		app_name: DF.Data
		client_id: DF.Data | None
		client_secret: DF.Data | None
		default_redirect_uri: DF.Data
		grant_type: DF.Literal["Authorization Code", "Implicit"]
		redirect_uris: DF.Text | None
		response_type: DF.Literal["Code", "Token"]
		scopes: DF.Text
		skip_authorization: DF.Check
		user: DF.Link | None
	# end: auto-generated types

	def validate(self):
		self.client_id = self.name
		if not self.client_secret:
			self.client_secret = nxenv.generate_hash(length=10)
		self.validate_grant_and_response()
		self.add_default_role()

	def validate_grant_and_response(self):
		if (self.grant_type == "Authorization Code" and self.response_type != "Code") or (
			self.grant_type == "Implicit" and self.response_type != "Token"
		):
			nxenv.throw(
				_(
					"Combination of Grant Type (<code>{0}</code>) and Response Type (<code>{1}</code>) not allowed"
				).format(self.grant_type, self.response_type)
			)

	def add_default_role(self):
		if not self.allowed_roles:
			self.append("allowed_roles", {"role": SYSTEM_USER_ROLE})

	def user_has_allowed_role(self) -> bool:
		"""Returns true if session user is allowed to use this client."""
		allowed_roles = {d.role for d in self.allowed_roles}
		return bool(allowed_roles & set(nxenv.get_roles()))
