# Contributing

If you want to add an issue or pull request, please ensure that the [existing issues](https://github.com/BGmi/bgmi/issues?utf8=✓&q=) don't already cover your question or contribution.

To get started contributing code to the `BGmi`:

## Installation

We recommend using [`virtualenv`](https://virtualenv.readthedocs.org/en/latest/) to isolate dependencies for development.
This guide assumes that you have already created and activated a virtualenv for this project.

Ensure that you have the latest version of pip installed:
```
pip install -U pip
```

Clone the repository (alternatively, if you plan on making a pull request and are not in the `BGmi` organization, use the [github page](https://github.com/BGmi/BGmi) to create your own fork)

```
git clone git@github.com:BGmi/BGmi.git
cd BGmi
```

Install all dev requirements

```
pip install -r requirements/dev.txt
```

Install `pre-commit` hooks

```
pre-commit install
```

And finally create a separate branch to begin work

```
git checkout -b feature/my-new-feature
```

## Submitting Pull Requests

Pull requests are welcomed! We'd like to review the design and implementation as early as
possible so please submit the pull request even if it's not 100%.
Let us know the purpose of the change and list the remaining items which need to be
addressed before merging.
Finally, PR's should include unit tests and documentation where appropriate.
Make sure passed all tests in CI.

## code style

code should be formatted by`isort` and `yapf`, which config are included in [`setup.cfg`](../setup.cfg).

Lint by `flake8`, which config is also included in [`setup.cfg`](../setup.cfg).
