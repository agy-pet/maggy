# bash completion for maggy
_maggy() {
    local cur prev pet_cmds sl_cmds cmds i cmd
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    pet_cmds="on off toggle theme blink mood motion side name preview"
    sl_cmds="on off toggle show hide render"
    cmds="setup uninstall status $pet_cmds pet statusline config doctor update version help"
    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=($(compgen -W "$cmds --version --help" -- "$cur")); return
    fi
    # `maggy pet <cmd>` is the same as `maggy <cmd>`.
    i=1
    if [ "${COMP_WORDS[1]}" = "pet" ]; then
        if [ "$COMP_CWORD" -eq 2 ]; then COMPREPLY=($(compgen -W "$pet_cmds" -- "$cur")); return; fi
        i=2
    elif [ "${COMP_WORDS[1]}" = "statusline" ]; then
        if [ "$COMP_CWORD" -eq 2 ]; then COMPREPLY=($(compgen -W "$sl_cmds" -- "$cur")); return; fi
        case "${COMP_WORDS[2]}" in
            show|hide) COMPREPLY=($(compgen -W "model context quota workspace git effort all" -- "$cur")) ;;
            on|off|toggle|enable|disable) COMPREPLY=($(compgen -W "--settings" -- "$cur")) ;;
        esac
        return
    fi
    cmd="${COMP_WORDS[i]}"
    local pos=$((COMP_CWORD - i))
    case "$cmd" in
        theme) COMPREPLY=($(compgen -W "auto default xmas" -- "$cur")) ;;
        blink|mood|motion) COMPREPLY=($(compgen -W "on off toggle" -- "$cur")) ;;
        side) COMPREPLY=($(compgen -W "left right toggle" -- "$cur")) ;;
        config)
            case "$pos" in
                1) COMPREPLY=($(compgen -W "show get set reset path" -- "$cur")) ;;
                2) COMPREPLY=($(compgen -W "name theme blink mood pet motion side hide" -- "$cur")) ;;
            esac ;;
        preview)
            if [ "$prev" = "--theme" ]; then COMPREPLY=($(compgen -W "default xmas" -- "$cur"))
            else COMPREPLY=($(compgen -W "working tool_use initializing idle reviewing error --theme --name --once --width" -- "$cur")); fi ;;
        setup|install)
            if [ "$prev" = "--theme" ]; then COMPREPLY=($(compgen -W "auto default xmas" -- "$cur"))
            elif [ "$prev" = "--side" ]; then COMPREPLY=($(compgen -W "left right" -- "$cur"))
            else COMPREPLY=($(compgen -W "--settings --force --padding --stack --no-stack --theme --name --no-blink --no-mood --no-pet --no-motion --side" -- "$cur")); fi ;;
        uninstall) COMPREPLY=($(compgen -W "--settings --purge" -- "$cur")) ;;
        status) COMPREPLY=($(compgen -W "--settings --quiet" -- "$cur")) ;;
        name) COMPREPLY=($(compgen -W "--reset" -- "$cur")) ;;
    esac
}
complete -F _maggy maggy
