#compdef bgmi

local pre cur action
local actions bangumi config
local READ_FORMAT WRITE_FORMAT
actions='({{ ' '.join(actions) }})'
bangumi='({{ ' '.join(bangumi) }})'
config='({{ ' '.join(config) }})'
#
READ_FORMAT='(native json markdown markdown_strict haddock latex)'
WRITE_FORMAT='(native json plain markdown markdown_strict s5)'

# _arguments \
#     {-f,-r}'[-f FORMAT, -r FORMAT, Specify input format]: :->reader' \
#     {-t,-w}'[-t FORMAT, -w FORMAT, Specify output format]: :->writer' \
#     {-o,--output}'[-o FILE, --output=FILE, Write output to FILE instead of stdout]' \
#     {-h,--help}'[Show usage message]' \
#     {-v,--version}'[Print version]' \
#     '*:files:_files'

_alternative \
    'writer:writer options:((-t\:"-t FORMAT, -w FORMAT, Specify output format" -w\:"-t FORMAT, -w FORMAT, Specify output format"))'

case "$state" in
    reader )
        _multi_parts ' ' $READ_FORMAT && return 0
        ;;
    writer )
        _multi_parts ' ' $WRITE_FORMAT && return 0
esac

if [[ ${words[(i)-f]} -le ${{'{#words}'}} ]] || [[ ${words[(i)-r]} -le ${{'{#words}'}} ]]
then
    _values 'reader options' \
        '-R[Parse untranslatable HTML codes and LaTeX as raw]' \
        '-S[Produce typographically correct output]' \
        '--filter[Specify an executable to be used as a filter]' \
        '-p[Preserve tabs instead of converting them to spaces]'
fi

if [[ ${words[(i)-t]} -le ${{'{#words}'}} ]] || [[ ${words[(i)-w]} -le ${{'{#words}'}} ]]
then
    _values 'writer options' \
        '-s[Produce output with an appropriate  header  and  footer]' \
        '--template[Use FILE as a custom template for the generated document]' \
        '--toc[Include an automatically generated table of contents]'
fi
