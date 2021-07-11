{{ if .Unreleased.CommitGroups -}}
{{ range .Unreleased.CommitGroups -}}

### {{ .Title }}

{{ range .Commits -}}

- {{ if .Scope }}**{{ .Scope }}**: {{ end }}{{ .Subject }}
  {{ end }}
  {{ end -}}
  {{- if .Unreleased.NoteGroups -}}
  {{ range .Unreleased.NoteGroups -}}

### {{ .Title -}}

{{ range .Notes }}
{{ .Body }}
{{ end -}}
{{ end -}}
{{ end }}

## [commits]({{ .Info.RepositoryURL }}/compare/{{ $latest := index .Versions 0 }}{{ $latest.Tag.Name }}...HEAD)

{{ end -}}
