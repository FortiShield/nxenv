class InvalidBranchException(Exception):
	pass


class InvalidRemoteException(Exception):
	pass


class PatchError(Exception):
	pass


class CommandFailedError(Exception):
	pass


class NxcliNotFoundError(Exception):
	pass


class ValidationError(Exception):
	pass


class AppNotInstalledError(ValidationError):
	pass


class CannotUpdateReleaseNxcli(ValidationError):
	pass


class FeatureDoesNotExistError(CommandFailedError):
	pass

class VersionNotFound(Exception):
	pass
