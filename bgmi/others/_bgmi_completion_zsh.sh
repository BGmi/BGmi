_bgmi(){

    local  BANGUMI_LIST
    BANGUMI_LIST='({{' '.join(bangumi)}})'

    {% for action, opts in actions_and_opts.items() %}
    local {{ action }}
    {{ action }}='({{ ' '.join([x['dest']for x in opts]) }})'    {% end %}


    _alternative \
{% for action, opts in actions_and_opts.items() %}        '{{action}}:{{action}} options:(({% for opt in opts %}{{opt['dest']}}\:"{{opt.get('help',opt['dest'])}}" {% end %}))' \
{% end %}


    case "$state" in
        reader )
            _multi_parts ' ' $READ_FORMAT && return 0
        ;;
        writer )
            _multi_parts ' ' $WRITE_FORMAT && return 0
        ;;
        bangumi )
            _multi_parts ' ' $BANGUMI_LIST && return 0

            ;;
            update )
            _multi_parts ' ' $update && return 0

            ;;
            filter )
            _multi_parts ' ' $filter && return 0

            ;;
            config )
            COMPREPLY=( $( compgen -W "$config" -- $cur ) )
            return 0

            ;;
            cal )
            local opts
            opts="{{' '.join([x['dest'] for x in actions_and_opts['cal']])}}"
            _multi_parts ' ' $opts && return 0


            ;;
            source )
            local opts
            opts="{{' '.join([x['dest'] for x in actions_and_opts['source']])}}"
            _multi_parts ' ' $opts && return 0

            ;;
            search )
            local opts
            opts="{{' '.join([x['dest'] for x in actions_and_opts['search']])}}"
            _multi_parts ' ' $opts && return 0

            ;;
            download )
            local opts
            opts="{{' '.join([x['dest'] for x in actions_and_opts['download']])}}"
            _multi_parts ' ' $opts && return 0

    esac
    
    
    # if [[ ${words[(i)-f]} -le ${{'{#words}'}} ]] || [[ ${words[(i)-r]} -le ${{'{#words}'}} ]]
    # then
    #     _values 'reader options' \
    #     '-R[Parse untranslatable HTML codes and LaTeX as raw]' \
    #     '-S[Produce typographically correct output]' \
    #     '--filter[Specify an executable to be used as a filter]' \
    #     '-p[Preserve tabs instead of converting them to spaces]'
    # fi
    
    # if [[ ${words[(i)-t]} -le ${{'{#words}'}} ]] || [[ ${words[(i)-w]} -le ${{'{#words}'}} ]]
    # then
    #     _values 'writer options' \
    #     '-s[Produce output with an appropriate  header  and  footer]' \
    #     '--template[Use FILE as a custom template for the generated document]' \
    #     '--toc[Include an automatically generated table of contents]'
    # fi
}

compdef _bgmi bgmi
