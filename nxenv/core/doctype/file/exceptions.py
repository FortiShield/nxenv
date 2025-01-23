import nxenv


class MaxFileSizeReachedError(nxenv.ValidationError):
	pass


class FolderNotEmpty(nxenv.ValidationError):
	pass


class FileTypeNotAllowed(nxenv.ValidationError):
	pass


from nxenv.exceptions import *
