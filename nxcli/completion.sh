_nxcli_completion() {
    # Complete commands using click bashcomplete
    COMPREPLY=( $( COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _NXCLI_COMPLETE=complete $1 ) )
    if [ -d "sites" ]; then
        # Also add nxenv commands if present

        # nxcli_helper.py expects to be executed from "sites" directory
        cd sites

        # All nxenv commands are subcommands under "nxcli nxenv"
        # Nxenv is only installed in virtualenv "env" so use appropriate python executable
        COMPREPLY+=( $( COMP_WORDS="nxcli nxenv "${COMP_WORDS[@]:1} \
                        COMP_CWORD=$(($COMP_CWORD+1)) \
                        _NXCLI_COMPLETE=complete ../env/bin/python ../apps/nxenv/nxenv/utils/nxcli_helper.py ) )

        # If the word before the current cursor position in command typed so far is "--site" then only list sites
        if [ ${COMP_WORDS[COMP_CWORD-1]} == "--site" ]; then
            COMPREPLY=( $( ls -d ./*/site_config.json | cut -f 2 -d "/" | xargs echo ) )
        fi

        # Get out of sites directory now
        cd ..
    fi
    return 0
}

# Only support bash and zsh
if [ -n "$BASH" ] ; then
    complete -F _nxcli_completion -o default nxcli;
elif [ -n "$ZSH_VERSION" ]; then
    # Use zsh in bash compatibility mode
    autoload bashcompinit
    bashcompinit
    complete -F _nxcli_completion -o default nxcli;
fi
