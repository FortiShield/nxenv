nxenv.ui.form.ControlHeading = class ControlHeading extends nxenv.ui.form.ControlHTML {
	get_content() {
		return "<h4>" + __(this.df.label, null, this.df.parent) + "</h4>";
	}
};
