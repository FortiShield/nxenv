# Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import nxenv
from nxenv.model.document import Document


class AboutUsSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from nxenv.types import DF
		from nxenv.website.doctype.about_us_team_member.about_us_team_member import AboutUsTeamMember
		from nxenv.website.doctype.company_history.company_history import CompanyHistory

		company_history: DF.Table[CompanyHistory]
		company_history_heading: DF.Data | None
		company_introduction: DF.TextEditor | None
		footer: DF.TextEditor | None
		page_title: DF.Data | None
		team_members: DF.Table[AboutUsTeamMember]
		team_members_heading: DF.Data | None
		team_members_subtitle: DF.SmallText | None
	# end: auto-generated types

	def on_update(self):
		from nxenv.website.utils import clear_cache

		clear_cache("about")


def get_args():
	obj = nxenv.get_doc("About Us Settings")
	return {"obj": obj}
