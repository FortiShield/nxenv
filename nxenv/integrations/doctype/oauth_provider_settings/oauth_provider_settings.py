# Copyright (c) 2015, Nxenv Technologies and contributors
# License: MIT. See LICENSE

import nxenv
from nxenv import _
from nxenv.model.document import Document


class OAuthProviderSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF

		skip_authorization: DF.Literal["Force", "Auto"]
	# end: auto-generated types

	pass


def get_oauth_settings():
	"""Return OAuth settings."""
	return nxenv._dict(
		{"skip_authorization": nxenv.db.get_single_value("OAuth Provider Settings", "skip_authorization")}
	)
