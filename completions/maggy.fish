# fish completion for maggy
function __maggy_themes
    printf '%s\n' default xmas halloween cny
    set -l dir (set -q XDG_CONFIG_HOME; and echo $XDG_CONFIG_HOME; or echo ~/.config)/maggy/themes
    for f in $dir/*.json
        basename $f .json
    end
end
set -l pet_cmds on off toggle theme blink mood motion stretch side name preview
set -l sl_cmds on off toggle show hide render enable disable
set -l cmds setup uninstall status $pet_cmds pet statusline config stats doctor update version help
complete -c maggy -f

# top level (pet commands work without the `pet` prefix)
set -l top "not __fish_seen_subcommand_from $cmds"
complete -c maggy -n $top -a setup -d 'hook Maggy into agy statusLine'
complete -c maggy -n $top -a uninstall -d 'remove Maggy from agy statusLine'
complete -c maggy -n $top -a status -d 'show setup and a sample'
complete -c maggy -n $top -a pet -d 'pet commands (prefix optional)'
complete -c maggy -n $top -a statusline -d 'statusline commands'
complete -c maggy -n $top -a config -d 'show, get or set config'
complete -c maggy -n $top -a stats -d 'tasks, busy time and streaks'
complete -c maggy -n $top -a doctor -d 'check the setup'
complete -c maggy -n $top -a update -d 'upgrade to the latest version'
complete -c maggy -n $top -a version -d 'print the version'

# pet commands, at the top level or after `pet`
set -l petpos "not __fish_seen_subcommand_from $cmds; or begin; __fish_seen_subcommand_from pet; and not __fish_seen_subcommand_from $pet_cmds; end"
complete -c maggy -n $petpos -a on -d 'show the logo'
complete -c maggy -n $petpos -a off -d 'hide the logo'
complete -c maggy -n $petpos -a toggle -d 'show or hide the logo'
complete -c maggy -n $petpos -a theme -d 'show or switch the theme'
complete -c maggy -n $petpos -a blink -d 'idle twinkling on/off'
complete -c maggy -n $petpos -a mood -d 'mood caption on/off'
complete -c maggy -n $petpos -a motion -d 'animation on/off'
complete -c maggy -n $petpos -a stretch -d 'stretch reminder on/off/minutes'
complete -c maggy -n $petpos -a side -d 'logo left or right'
complete -c maggy -n $petpos -a name -d 'show or rename your pet'
complete -c maggy -n $petpos -a preview -d 'watch Maggy dance'

# statusline commands
set -l slpos "__fish_seen_subcommand_from statusline; and not __fish_seen_subcommand_from $sl_cmds"
complete -c maggy -n $slpos -a on -d 'turn the statusline on'
complete -c maggy -n $slpos -a off -d 'turn the statusline off'
complete -c maggy -n $slpos -a toggle -d 'turn the statusline on or off'
complete -c maggy -n $slpos -a show -d 'show statusline segments'
complete -c maggy -n $slpos -a hide -d 'hide statusline segments'
complete -c maggy -n $slpos -a render -d 'render from agy JSON on stdin'
complete -c maggy -n "__fish_seen_subcommand_from statusline; and __fish_seen_subcommand_from show hide" -a 'model context quota workspace git effort stats all'

complete -c maggy -n "__fish_seen_subcommand_from theme" -a 'auto list (__maggy_themes)'
complete -c maggy -n "__fish_seen_subcommand_from stretch" -a 'on off toggle 30 45 60'
complete -c maggy -n "__fish_seen_subcommand_from blink mood motion" -a 'on off toggle'
complete -c maggy -n "__fish_seen_subcommand_from side" -a 'left right toggle'
complete -c maggy -n "__fish_seen_subcommand_from config" -a 'show get set reset path name theme blink mood pet motion side hide stretch stretch_after stats'
complete -c maggy -n "__fish_seen_subcommand_from preview" -a 'working tool_use initializing idle reviewing error stretch'
complete -c maggy -n "__fish_seen_subcommand_from preview" -l theme -xa '(__maggy_themes)'
complete -c maggy -n "__fish_seen_subcommand_from preview" -l name -x
complete -c maggy -n "__fish_seen_subcommand_from preview" -l once
complete -c maggy -n "__fish_seen_subcommand_from stats" -a 'today week month year all'
complete -c maggy -n "__fish_seen_subcommand_from stats" -a web -d 'open the dashboard'
complete -c maggy -n "__fish_seen_subcommand_from stats" -a on -d 'start counting (default)'
complete -c maggy -n "__fish_seen_subcommand_from stats" -a off -d 'stop counting, keep saved stats'
complete -c maggy -n "__fish_seen_subcommand_from stats" -a toggle -d 'start or stop counting'
complete -c maggy -n "__fish_seen_subcommand_from stats" -a reset -d 'delete saved stats (needs --yes)'
complete -c maggy -n "__fish_seen_subcommand_from stats" -a path -d 'print where stats are saved'
complete -c maggy -n "__fish_seen_subcommand_from stats" -l days -x
complete -c maggy -n "__fish_seen_subcommand_from stats" -l json
complete -c maggy -n "__fish_seen_subcommand_from stats" -l yes
complete -c maggy -n "__fish_seen_subcommand_from setup" -l settings -r
complete -c maggy -n "__fish_seen_subcommand_from setup" -l force
complete -c maggy -n "__fish_seen_subcommand_from setup" -l padding -x
complete -c maggy -n "__fish_seen_subcommand_from setup" -l stack
complete -c maggy -n "__fish_seen_subcommand_from setup" -l no-stack
complete -c maggy -n "__fish_seen_subcommand_from setup" -l theme -xa 'auto (__maggy_themes)'
complete -c maggy -n "__fish_seen_subcommand_from setup" -l name -x
complete -c maggy -n "__fish_seen_subcommand_from setup" -l no-blink
complete -c maggy -n "__fish_seen_subcommand_from setup" -l no-mood
complete -c maggy -n "__fish_seen_subcommand_from setup" -l no-pet
complete -c maggy -n "__fish_seen_subcommand_from setup" -l no-motion
complete -c maggy -n "__fish_seen_subcommand_from setup" -l side -xa 'left right'
complete -c maggy -n "__fish_seen_subcommand_from setup" -l no-stretch
complete -c maggy -n "__fish_seen_subcommand_from uninstall" -l purge
complete -c maggy -n "__fish_seen_subcommand_from status" -s q -l quiet
complete -c maggy -n "__fish_seen_subcommand_from name" -l reset
complete -c maggy -n "__fish_seen_subcommand_from stats" -l out -r
complete -c maggy -n "__fish_seen_subcommand_from stats" -l no-open
