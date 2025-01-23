import nxenv

NXENV_CLOUD_DOMAINS = ("nxenv.cloud", "erpnext.com", "nxenvhr.com")


def on_nxenvcloud() -> bool:
	"""Returns true if running on Nxenv Cloud.


	Useful for modifying few features for better UX."""
	return nxenv.local.site.endswith(NXENV_CLOUD_DOMAINS)
