set shell := ["bash", "-c"]

# just — developer workflow for zenzic-vscode.
#
# Quick reference:
#   just verify          — lint + tsc (pre-push gate)
#   just release <part>  — bump version (patch|minor|major)
#   just release-dry <p> — dry-run bump, no file writes
#   just pin-core <ver>  — realign Zenzic Core pin in README + RELEASE.md
#   just pin-core-dry    — show what pin-core would change (no writes)
#   just versions        — show extension version and pinned core version
#   just clean           — remove generated artefacts (out/, *.vsix, .tsbuildinfo)

verify:
	npm run lint
	npx tsc --noEmit
	command -v reuse > /dev/null 2>&1 && reuse lint || echo "reuse not installed — skipping REUSE lint"

release part:
	#!/usr/bin/env bash
	set -euo pipefail
	case "{{ part }}" in
		patch|minor|major) ;;
		*) echo "Invalid part '{{ part }}'. Use patch|minor|major"; exit 2 ;;
	esac
	uvx --from "bump-my-version==1.2.6" bump-my-version bump {{ part }}

release-dry part *args:
	#!/usr/bin/env bash
	set -euo pipefail
	_short=false
	for _arg in {{args}}; do [[ "$_arg" == "--short" ]] && _short=true; done
	if $_short; then
		uvx --from "bump-my-version==1.2.6" bump-my-version bump {{part}} --dry-run --allow-dirty --verbose 2>&1 \
			| grep -E 'current version|New version will be|Dry run'
	else
		uvx --from "bump-my-version==1.2.6" bump-my-version bump {{part}} --dry-run --allow-dirty --verbose
	fi

# Show the current extension version and the pinned Zenzic Core version
versions:
	#!/usr/bin/env bash
	set -euo pipefail
	PINNED=$(grep -oP '\*\*Pinned Core\*\* \| `zenzic>=\K[0-9.]+' RELEASE.md)
	EXT_MIN=$(grep -oP "const MIN_CORE_VERSION = '\K[0-9.]+" src/extension.ts)
	echo "extension:   $(uvx --from 'bump-my-version==1.2.6' bump-my-version show current_version)"
	echo "core-pinned: $PINNED (RELEASE.md)"
	echo "min-core-ts: $EXT_MIN (src/extension.ts)"

# Realign the Zenzic Core pin in README.md, RELEASE.md, and src/extension.ts.
# Usage: just pin-core <version>
pin-core version:
	#!/usr/bin/env bash
	set -euo pipefail
	if [[ ! "{{version}}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		echo "Invalid version '{{version}}'. Use MAJOR.MINOR.PATCH"
		exit 2
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "Working tree is not clean. Commit or stash changes before pin-core."
		exit 3
	fi
	echo "Aligning Zenzic Core pin to {{version}}..."
	sed -i 's/uv tool install zenzic==[0-9.]*/uv tool install zenzic=={{version}}/g' README.md
	sed -i 's/pip install zenzic==[0-9.]*/pip install zenzic=={{version}}/g' README.md
	sed -i 's/| \*\*Pinned Core\*\* | .* |/| **Pinned Core** | `zenzic>={{version}}` |/' RELEASE.md
	sed -i "s/const MIN_CORE_VERSION = '[0-9.]*';/const MIN_CORE_VERSION = '{{version}}';/g" src/extension.ts
	git add README.md RELEASE.md src/extension.ts
	git commit -S -s -m "chore(deps): pin zenzic core to {{version}}"

# Simulate a Zenzic Core pin realignment and print the diff without writing files.
# Usage: just pin-core-dry <version>
pin-core-dry version:
	#!/usr/bin/env bash
	set -euo pipefail
	if [[ ! "{{version}}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
		echo "Invalid version '{{version}}'. Use MAJOR.MINOR.PATCH"
		exit 2
	fi
	echo "==> Dry-run: changes that 'just pin-core {{version}}' would apply"
	echo ""
	echo "--- README.md ---"
	grep -n 'zenzic==[0-9.]*' README.md \
		| sed 's/zenzic==[0-9.]*/zenzic=={{version}}/' || echo "  (no occurrences)"
	echo ""
	echo "--- RELEASE.md ---"
	grep -n 'Pinned Core' RELEASE.md \
		| sed 's/zenzic>=[0-9.]*/zenzic>={{version}}/' || echo "  (no occurrences)"
	echo ""
	echo "--- src/extension.ts ---"
	grep -n "MIN_CORE_VERSION = '[0-9.]*';" src/extension.ts \
		| sed "s/MIN_CORE_VERSION = '[0-9.]*';/MIN_CORE_VERSION = '{{version}}';/" || echo "  (no occurrences)"

# Remove generated artefacts
clean:
	rm -rf out/ .tsbuildinfo
	find . -maxdepth 1 -name '*.vsix' -delete
