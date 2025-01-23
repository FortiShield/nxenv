import nxenv
from nxenv.utils import cint

no_cache = 1


def get_context(context):
	nxenv.db.commit()  # nosemgrep
	context = nxenv._dict()
	context.boot = get_boot()
	return context


def get_boot():
	return nxenv._dict(
		{
			"site_name": nxenv.local.site,
			"read_only_mode": nxenv.flags.read_only,
			"csrf_token": nxenv.sessions.get_csrf_token(),
			"setup_complete": cint(nxenv.get_system_settings("setup_complete")),
		}
	)
