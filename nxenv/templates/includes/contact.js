// Copyright (c) 2015, Nxenv Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

nxenv.ready(function () {
	if (nxenv.utils.get_url_arg("subject")) {
		$('[name="subject"]').val(nxenv.utils.get_url_arg("subject"));
	}

	$(".btn-send")
		.off("click")
		.on("click", function () {
			var email = $('[name="email"]').val();
			var message = $('[name="message"]').val();

			if (!(email && message)) {
				nxenv.msgprint(
					'{{ _("Please enter both your email and message so that we can get back to you. Thanks!") }}'
				);
				return false;
			}

			if (!validate_email(email)) {
				nxenv.msgprint(
					'{{ _("You seem to have written your name instead of your email. Please enter a valid email address so that we can get back.") }}'
				);
				$('[name="email"]').focus();
				return false;
			}

			$("#contact-alert").toggle(false);
			nxenv.call({
				type: "POST",
				method: "nxenv.www.contact.send_message",
				args: {
					subject: $('[name="subject"]').val(),
					sender: email,
					message: message,
				},
				callback: function (r) {
					if (!r.exc) {
						nxenv.msgprint(
							'{{ _("Thank you for your message") }}',
							'{{ _("Message Sent") }}'
						);
					}
					$(":input").val("");
				},
			});
		});
});

var msgprint = function (txt) {
	if (txt) $("#contact-alert").html(txt).toggle(true);
};
