## Usage

- Updating

To update the nxcli CLI tool, depending on your method of installation, you may use

    pip3 install -U nxenv-nxcli

To backup, update all apps and sites on your nxcli, you may use

    nxcli update

To manually update the nxcli, run `nxcli update` to update all the apps, run
patches, build JS and CSS files and restart supervisor (if configured to).

You can also run the parts of the nxcli selectively.

`nxcli update --pull` will only pull changes in the apps

`nxcli update --patch` will only run database migrations in the apps

`nxcli update --build` will only build JS and CSS files for the nxcli

`nxcli update --nxcli` will only update the nxcli utility (this project)

`nxcli update --requirements` will only update all dependencies (Python + Node) for the apps available in current nxcli

- Create a new nxcli

  The init command will create a nxcli directory with nxenv framework installed. It will be setup for periodic backups and auto updates once a day.

      nxcli init nxenv-nxcli && cd nxenv-nxcli

- Add a site

  Nxenv apps are run by nxenv sites and you will have to create at least one site. The new-site command allows you to do that.

      nxcli new-site site1.local

- Add apps

  The get-app command gets remote nxenv apps from a remote git repository and installs them. Example: [erpnext](https://github.com/nxenv/erpnext)

      nxcli get-app erpnext https://github.com/nxenv/erpnext

- Install apps

  To install an app on your new site, use the nxcli `install-app` command.

      nxcli --site site1.local install-app erpnext

- Start nxcli

  To start using the nxcli, use the `nxcli start` command

      nxcli start

  To login to Nxenv / ERPNext, open your browser and go to `[your-external-ip]:8000`, probably `localhost:8000`

  The default username is "Administrator" and password is what you set when you created the new site.

- Setup Manager

## What it does

    	nxcli setup manager

1. Create new site nxcli-manager.local
2. Gets the `nxcli_manager` app from https://github.com/nxenv/nxcli_manager if it doesn't exist already
3. Installs the nxcli_manager app on the site nxcli-manager.local
