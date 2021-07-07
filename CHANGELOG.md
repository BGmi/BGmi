# Changelog

## [2.2.2](https://github.com/BGmi/BGmi/compare/2.2.1...2.2.2) - 2021-07-07

### Bug Fixes

- **downloader**: remove unexpected debug message
- **transmission**: make sure torrent will start downloading when adding

### Code Refactoring

- add qbittorrent rpc library to deps-prod

## [2.2.1](https://github.com/BGmi/BGmi/compare/2.2.0...2.2.1) - 2021-04-27

### Bug Fixes

- filter function on bangumi.moe ([#266](https://github.com/BGmi/BGmi/issues/266))
- episode parser ([#265](https://github.com/BGmi/BGmi/issues/265))

## [2.2.0](https://github.com/BGmi/BGmi/compare/2.1.4...2.2.0) - 2021-04-18

### Features

- **downloader**: add qbittorrent downloader ([#259](https://github.com/BGmi/BGmi/issues/259))

### Bug Fixes

- episode parsing ([#249](https://github.com/BGmi/BGmi/issues/249))
- parse episode with E prefix in brackets
- **config**: always read config file as utf-8 ([#257](https://github.com/BGmi/BGmi/issues/257))
- **update**: catch network error when fetching bangumi info ([#254](https://github.com/BGmi/BGmi/issues/254))

## [2.1.4](https://github.com/BGmi/BGmi/compare/2.1.3...2.1.4) - 2021-02-08

### Bug Fixes

- bgmi search for mikan,dmhy ([#244](https://github.com/BGmi/BGmi/issues/244))
- update bangumi info when updating
- retry http requests on error
- **mikan**: fetch full episode list of mikan source ([#237](https://github.com/BGmi/BGmi/issues/237))
- **mikan**: retry on http error
- **mikan**: handle server instability response
- **script**: remove deprecated imp module

### Code Refactoring

- reduce dict
- move cover downloader to controller
- drop py3.5 support
- remove some utils from `BaseWebsite`
- **cli**: use `wcwidth` to count bangumi name length
- **downloader**: migrate driver to transmission-rpc
- **internal**: migrate attrs to pydantic
- **mikan**: readability improvement
- **mikan**: remove debug code
- **mikan**: debug message
- **script**: replace deprecated api load_module

### Features

- **cli**: enable color in bash and zsh on windows
- don't fetch all bangumi info when show calendar
- allow `Unknown` as bangumi update_time

### BREAKING CHANGE

python3.5 has reached its EOL, so bump required python version to 3.6

## [2.1.3](https://github.com/BGmi/BGmi/compare/2.1.2...2.1.3) (2020-03-19)

### Bug Fixes

- bangumi name as part of other bangumi can be searched now ([7fd3a23](https://github.com/BGmi/BGmi/commit/7fd3a2314a054bef83d8f4cb90a769988af1c98a)), closes [#225](https://github.com/BGmi/BGmi/issues/225)

## [2.1.2](https://github.com/BGmi/BGmi/compare/2.1.1...2.1.2) (2020-01-02)

### Bug Fixes

- **front**: python3.8 windows asyncio ([7d53bf9](https://github.com/BGmi/BGmi/commit/7d53bf9084030c00f566300f719e5ff1a7e0a1f1)), closes [#217](https://github.com/BGmi/BGmi/issues/217)

## [2.1.1](https://github.com/BGmi/BGmi/compare/2.1.0-beta...2.1.1) (2019-04-24)

### Bug Fixes

- mikan parser error ([1842cc1](https://github.com/BGmi/BGmi/commit/1842cc18c1a303b893be803729f7f2046822af50))

## [2.1.0-beta](https://github.com/BGmi/BGmi/compare/2.0.6...2.1.0-beta) (2018-10-07)

### Features

- gen nginx.conf ([120eeec](https://github.com/BGmi/BGmi/commit/120eeec50e7550086ceaaf3ae7342f103074818f))
- fuzzy search for bangumi name ([f1a61c7](https://github.com/BGmi/BGmi/commit/f1a61c7fa253be64e725f31b6a962e30c799f6e0))
- **download delege**: deluge ([c42a407](https://github.com/BGmi/BGmi/commit/c42a407d2c693b5c2f7741f962129dab11d8c1b3))
