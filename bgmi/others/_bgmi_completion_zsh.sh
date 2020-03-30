_bgmi(){

   # local  BANGUMI_LIST
   # BANGUMI_LIST='({{' '.join(bangumi)}})'

{#
    {% for action, opts in actions_and_opts.items() %}
    local {{ action }}
    {{ action }}='({{ ' '.join([x['dest'] for x in opts]) }})'    {% end %}
#}

    if [[ ${{'{#words}'}} -le 2 ]]
            then
        _alternative \
            'action:action options:(({% for action, opts in actions_and_opts.items() %}{{action}}\:"{{helper[action]}}" {% end %}))'
    fi

{% for action , opts in actions_and_opts.items() %}{% if opts %}
    if [[ ${words[(i){{action}}]} -le ${{'{#words}'}} ]]
        then
        # _arguments \
            # {-t,-w}'[-t FORMAT, -w FORMAT, Specify output format]'
        _alternative \
        '{{action}}:{{action}} options:(({% for opt in opts %}{% if isinstance(opt['dest'], string_types) %}{{opt['dest'] }}\:"{{opt['kwargs'].get('help','')}}" {% elif isinstance(opt['dest'], list) %}{% for ar in opt['dest'] %}{{ar}}\:"{{opt['kwargs'].get('help','')}}" {% end %}{% end %}{% end %}))'
    fi
{% end %}{% end %}
}

compdef _bgmi bgmi

#usage: eval "$(bgmi complete)"
#if you are using windows, cygwin or babun, try `eval "$(bgmi complete|dos2unix)"`
