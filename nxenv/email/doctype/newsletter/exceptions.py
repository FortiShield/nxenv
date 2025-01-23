# Copyright (c) 2021, Nxenv Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE

from nxenv.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass
