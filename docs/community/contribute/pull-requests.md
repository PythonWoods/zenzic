---
icon: lucide/git-pull-request-create
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Pull requests

The process and requirements we describe below serve as important guardrails
that are essential to running an Open Source project and help us prevent wasted
effort and ensure the integrity of the codebase.

## Local development setup

Clone the repository and install Zenzic in editable mode so that your local
changes are reflected immediately without reinstalling.

=== ":simple-astral: uv (recommended)"

    ```bash
    git clone https://github.com/PythonWoods/zenzic.git
    cd zenzic
    uv venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    uv pip install -e .
    ```

    [`uv`](https://docs.astral.sh/uv/) resolves dependencies significantly faster than pip and produces
    a reproducible environment via `uv.lock`. Preferred for all development work.

=== ":simple-pypi: pip"

    ```bash
    git clone https://github.com/PythonWoods/zenzic.git
    cd zenzic
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -e .
    ```

With an editable install, the `zenzic` binary on your `PATH` always runs the
source you are working on. Validate the repository's own documentation at any
time:

```bash
zenzic check all            # all six checks
zenzic check references     # includes custom [[custom_rules]] evaluation
pytest                      # full test suite
```

!!! note "End users vs contributors"

    **End users** run `uvx zenzic check all` — no clone, no install, zero
    friction. That is the entry point documented in the user-facing guides.

    **Contributors** clone the repo and install editably as shown above.
    The `zenzic` binary in your activated virtual environment is what you want
    — not `uvx`, which would download the published PyPI version.

## Before you start

Before you start work on a pull request (PR), we need you to open an issue and
discuss it with us so we know what you are working on and so we can agree on the
approach to take. This prevents you from spending time on a feature that may not
align with the project's goals. You then reference the issue number in your PR
to link back to our discussion.

## Styles and linting

It is important that your edits produce clean commits that can be reviewed
quickly and without distractions caused by spurious diffs. The project uses the
following styling and linting tools:

| Language | Tool   | Notes                       |
| :------- | :----- | :---------------------------|
| Python   | [ruff] | Linting and code formatting |
| Python   | [mypy] | Type checking               |

  [ruff]: https://docs.astral.sh/ruff/
  [mypy]: https://www.mypy-lang.org/

We also use an [.editorconfig] file that configures compatible editors to behave
consistently for tasks like removing trailing whitespace or applying indentation
styles.

  [.editorconfig]: https://editorconfig.org/

## Verified commits

To ensure the integrity of our project, we require [verified commits] that are
cryptographically signed. Follow the instructions on GitHub for using [gpg],
[ssh], or [s/mime] keypairs.

  [verified commits]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification
  [gpg]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#gpg-commit-signature-verification
  [ssh]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#ssh-commit-signature-verification
  [s/mime]: https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification#smime-commit-signature-verification

## Developer certificate of origin

To ensure the legal integrity of our project, we require all contributors to
_sign off_ on their commits, thus accepting the Developer Certificate of Origin.
This certifies that you have the right to submit the code under the project's
license.

Add a `Signed-off-by` line to every commit using the `-s` flag:

```bash
git commit -s -m "<type>: <summary> (#<issue number>)"
```

## Use of Generative AI

AI-assisted coding can be useful, but the unreflected inclusion of AI-generated
code can also do great harm. By signing off on commits, you attest that you have
either written all the code yourself or have thoroughly reviewed and fully
understood any generated code.

Code contributions that contain obviously AI-generated code that you cannot
fully explain to us will be rejected.

## Commit message standards

We follow the [Conventional Commits] specification. Each commit message must
follow this structure:

```text
<type>: <summary description> (#<issue number>)

Signed-off-by: ...
```

  [Conventional Commits]: https://www.conventionalcommits.org/

<figure markdown>

| Type          | Description                                    |
| :------------ | :--------------------------------------------- |
| `feat`        | Implements a new feature                       |
| `fix`         | Fixes a bug                                    |
| `perf`        | Improves performance                           |
| `refactor`    | Improves code without changing behavior        |
| `build`       | Makes changes to the build or CI system        |
| `docs`        | Adds or improves documentation                 |
| `style`       | Makes stylistic changes only (e.g. whitespace) |
| `test`        | Adds or improves tests                         |
| `chore`       | Updates build process, prepares releases, etc. |

  <figcaption>Accepted commit types</figcaption>
</figure>
