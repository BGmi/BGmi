# 以pandoc的名字保存下面的程序
_bgmi() {
    local pre cur opts

    COMPREPLY=()
    #pre="$3"
    #cur="$2"
    pre=${COMP_WORDS[COMP_CWORD-1]}
    cur=${COMP_WORDS[COMP_CWORD]}
    opts="-f -r -t -w -o --output -v --version -h --help"
    case "$cur" in
    -* )
        COMPREPLY=( $( compgen -W "$opts" -- $cur ) )
    esac
}
complete -F _bgmi bgmi