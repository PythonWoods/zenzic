# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
"""Zenzic Rule Engine — pluggable, pure-function linting rules.

Architecture
------------
Rules are pure functions: they receive immutable data (file path, line text,
line number) and return a list of :class:`RuleFinding` objects.  No I/O is
permitted inside a rule — this is enforced by the interface contract and
documented clearly.

Two kinds of rules coexist in the same engine:

* **CustomRule** — declared directly in ``zenzic.toml`` as ``[[custom_rules]]``
  entries.  No Python required.  Ideal for project-specific vocabulary checks.
* **BaseRule** subclasses — Python classes registered via the
  ``zenzic.rules`` entry-point group.  For complex, multi-line logic that
  a regex cannot express.

Both kinds are applied through the same :class:`AdaptiveRuleEngine.run` interface so
the scanner only sees one surface.

Rule dependency taxonomy (🔌 Dev 3 — relevant for caching)
-----------------------------------------------------------
Rules divide into two classes based on their input dependencies.  This
determines which cache-key components are required (see
:mod:`zenzic.core.cache`):

**Atomic rules** — depend only on the content of a single file and the
active configuration.  Cache key: ``SHA256(content) + SHA256(config)``.
These cache entries survive VSM changes caused by *other* files.

Examples:

* :class:`CustomRule` — regex applied line-by-line; no cross-file state.
* Any :class:`BaseRule` subclass whose :meth:`check` inspects only ``text``.

**Global rules** — depend on the VSM (routing table) in addition to file
content and configuration.  Cache key:
``SHA256(content) + SHA256(config) + SHA256(vsm_snapshot)``.  These entries
are invalidated whenever *any* file's routing state changes.

Examples:

* :class:`VSMBrokenLinkRule` — validates links against ``vsm[url].status``.
* Any :class:`BaseRule` subclass that overrides :meth:`check_vsm` and
  consults the ``vsm`` or ``anchors_cache`` arguments.

**Cross-file rules** (future) — depend on the content of *other* files, not
just the routing state.  These cannot be cached per-file without a
file-level dependency graph and must be treated as always-invalidated.
No built-in rules of this type exist yet.

Zenzic Way compliance
---------------------
* **Lint the Source:** Rules receive raw Markdown text — never HTML.
* **No Subprocesses:** The rule module does not import or invoke any process.
* **Pure Functions First:** :meth:`BaseRule.check` must be deterministic and
  side-effect-free.  :class:`AdaptiveRuleEngine.run` is also pure (list in, list out).
"""

from __future__ import annotations

import pickle
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from importlib.metadata import EntryPoint

    from zenzic.models.vsm import VSM, Route


# ─── Finding ──────────────────────────────────────────────────────────────────

Severity = Literal["error", "warning", "info"]


@dataclass(slots=True)
class RuleFinding:
    """A single issue found by a rule.

    Attributes:
        file_path: Path to the source file (used for display only).
        line_no: 1-based line number of the offending content.
        rule_id: Identifier of the rule that produced this finding.
        message: Human-readable description of the issue.
        severity: ``"error"``, ``"warning"``, or ``"info"``.
        matched_line: Raw text of the offending line. Populated by
            :class:`CustomRule`; empty string for Python-native rules
            that do not provide line context.
    """

    file_path: Path
    line_no: int
    rule_id: str
    message: str
    severity: Severity = "error"
    matched_line: str = field(default="")

    @property
    def is_error(self) -> bool:
        """Return ``True`` when this finding blocks a passing check."""
        return self.severity == "error"


# ─── Violation (structured finding for VSM-aware rules) ──────────────────────


@dataclass(slots=True)
class Violation:
    """A structured finding produced by a VSM-aware rule.

    This is the richer counterpart to :class:`RuleFinding` for rules that
    operate on the :data:`~zenzic.models.vsm.VSM` rather than on raw line
    text.  Every field is mandatory so the CLI can render a consistent visual
    snippet without any ``None`` guards.

    Violation standard (🎨 Dev 2 specification):

    * ``code``    — Stable machine-readable identifier in the form ``ZXXX``
                    (e.g. ``Z001``).  Used in ``--ignore`` flags and
                    suppressions inside ``zenzic.toml``.
    * ``level``   — ``"error"`` blocks a clean exit; ``"warning"`` is
                    reported but does not fail CI; ``"info"`` is purely
                    informational.
    * ``context`` — The raw Markdown source line that triggered the finding
                    (stripped of leading/trailing whitespace), exactly as it
                    appears in the source file.  Empty string only when the
                    finding is not tied to a specific line (e.g. a
                    file-level structural issue).

    Attributes:
        file_path:  Absolute path of the source file containing the violation.
        line_no:    1-based line number of the offending content.
        code:       Machine-readable violation code (e.g. ``"Z001"``).
        message:    Human-readable description shown in the report.
        level:      Severity — ``"error"``, ``"warning"``, or ``"info"``.
        context:    Raw source line that triggered the violation (stripped).
    """

    file_path: Path
    line_no: int
    code: str
    message: str
    level: Severity = "error"
    context: str = field(default="")

    @property
    def is_error(self) -> bool:
        """``True`` when this violation blocks a passing check."""
        return self.level == "error"

    def as_finding(self) -> RuleFinding:
        """Convert to :class:`RuleFinding` for backwards-compatible engine output."""
        return RuleFinding(
            file_path=self.file_path,
            line_no=self.line_no,
            rule_id=self.code,
            message=self.message,
            severity=self.level,
            matched_line=self.context,
        )


# ─── Abstract base ─────────────────────────────────────────────────────────────


class BaseRule(ABC):
    """Abstract interface for all Zenzic linting rules.

    Subclass this to create a Python-native rule.  Register it via the
    ``zenzic.rules`` entry-point group so Zenzic discovers it automatically::

        # pyproject.toml
        [project.entry-points."zenzic.rules"]
        my_rule = "my_package.rules:MyRule"

    **Contract:**

    * :meth:`check` must be **pure** — no I/O, no global state mutation.
    * :meth:`check` must be **deterministic** — same input always yields same output.
    * Raising an exception inside :meth:`check` is a bug in the rule.  The engine
      catches it and emits a single ``"error"`` finding describing the failure,
      then continues with the next rule.

    **VSM-aware extension:**

    Subclasses that need to validate links against the routing table should
    override :meth:`check_vsm` instead of (or in addition to) :meth:`check`.
    The engine calls :meth:`check_vsm` when a :data:`~zenzic.models.vsm.VSM`
    and ``anchors_cache`` are available, passing all data in-memory so the
    rule never needs to perform I/O.  Rules that do not need VSM data simply
    leave :meth:`check_vsm` as the default no-op.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Stable, unique identifier for this rule (e.g. ``"ZZ001"``).

        Used in output and in ``[[custom_rules]]`` ``id`` fields.
        """

    @abstractmethod
    def check(
        self,
        file_path: Path,
        text: str,
    ) -> list[RuleFinding]:
        """Analyse the raw Markdown content of one file.

        Args:
            file_path: Absolute path to the file (for labelling findings only —
                do **not** read from it; the content is already in *text*).
            text: Complete raw Markdown source of the file.

        Returns:
            A list of :class:`RuleFinding` objects, or an empty list if the
            file passes this rule.
        """

    def check_vsm(
        self,
        file_path: Path,
        text: str,
        vsm: Mapping[str, Route],
        anchors_cache: dict[Path, set[str]],
    ) -> list[Violation]:
        """Analyse a file against the pre-built Virtual Site Map.

        Override this method to write VSM-aware rules.  The default
        implementation is a no-op that returns an empty list, so existing
        ``BaseRule`` subclasses that only implement :meth:`check` continue to
        work without any modification.

        **Pure function contract:**

        * Do **not** call ``open()``, ``Path.exists()``, or any other I/O.
        * Do **not** mutate ``vsm`` or ``anchors_cache``.
        * Every link validation must consult ``vsm`` — a link is valid when
          ``vsm[target_url].status == "REACHABLE"``.

        Args:
            file_path:     Absolute path to the file (labelling only).
            text:          Complete raw Markdown source of the file.
            vsm:           Pre-built :data:`~zenzic.models.vsm.VSM` mapping
                           canonical URL → :class:`~zenzic.models.vsm.Route`.
                           Already populated by the Core before this call;
                           do **not** re-build it inside the rule.
            anchors_cache: Pre-computed mapping of absolute ``Path`` → anchor
                           slug set.  Use this for anchor validation instead
                           of re-parsing file content.

        Returns:
            A list of :class:`Violation` objects, or an empty list.
        """
        return []


# ─── CustomRule (TOML-driven) ──────────────────────────────────────────────────


@dataclass
class CustomRule(BaseRule):
    """A regex-based rule declared in ``[[custom_rules]]`` inside ``zenzic.toml``.

    Each entry in the ``[[custom_rules]]`` array maps directly to one
    ``CustomRule`` instance.  The pattern is applied line-by-line.

    TOML example::

        [[custom_rules]]
        id = "ZZ-NOINTERNAL"
        pattern = "internal\\.corp\\.example\\.com"
        message = "Internal hostname must not appear in public documentation."
        severity = "error"

        [[custom_rules]]
        id = "ZZ-NODRAFT"
        pattern = "(?i)\\bDRAFT\\b"
        message = "Remove DRAFT marker before publishing."
        severity = "warning"

    Attributes:
        id: Rule identifier, surfaced in findings as ``rule_id``.
        pattern: Regular-expression string applied to each non-blank line.
        message: Human-readable explanation shown in the finding.
        severity: ``"error"`` (default), ``"warning"``, or ``"info"``.
    """

    id: str
    pattern: str
    message: str
    severity: Severity = "error"
    _compiled: re.Pattern[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(
                f"CustomRule '{self.id}': invalid regex pattern {self.pattern!r} — {exc}"
            ) from exc

    @property
    def rule_id(self) -> str:
        return self.id

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        """Apply the pattern line-by-line to *text*."""
        findings: list[RuleFinding] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if self._compiled.search(line):
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=lineno,
                        rule_id=self.id,
                        message=self.message,
                        severity=self.severity,
                        matched_line=line,
                    )
                )
        return findings


# ─── AdaptiveRuleEngine ───────────────────────────────────────────────────────


def _assert_pickleable(rule: BaseRule) -> None:
    """Raise :class:`PluginContractError` if *rule* cannot be pickled.

    Called at engine construction time (eager validation) so that a
    non-serialisable rule is rejected before the first file is scanned,
    not inside a worker process mid-run.

    Args:
        rule: A :class:`BaseRule` instance to validate.

    Raises:
        PluginContractError: When ``pickle.dumps(rule)`` raises any error.
    """
    from zenzic.core.exceptions import PluginContractError  # deferred: avoid circular import

    try:
        pickle.dumps(rule)
    except Exception as exc:  # noqa: BLE001
        raise PluginContractError(
            f"Rule '{rule.rule_id}' ({type(rule).__qualname__}) is not serialisable "
            f"and cannot be used with the AdaptiveRuleEngine.\n"
            f"  Cause: {type(exc).__name__}: {exc}\n"
            f"  Fix: ensure the rule class is defined at module level (not inside a "
            f"function or closure) and that all instance attributes are pickleable.",
        ) from exc


class AdaptiveRuleEngine:
    """Applies a collection of :class:`BaseRule` instances to a Markdown file.

    The engine is stateless after construction — :meth:`run` is a pure
    function that maps ``(path, text)`` to a list of findings.

    All registered rules are validated for pickle-serializability at
    construction time (**eager validation**).  This ensures that any rule
    incompatible with multiprocessing is rejected immediately — before the
    first file is scanned — rather than failing silently inside a worker
    process.

    Usage::

        engine = AdaptiveRuleEngine(rules)
        findings = engine.run(Path("docs/guide.md"), text)

    Args:
        rules: Iterable of :class:`BaseRule` (or :class:`CustomRule`) instances
            to apply.  Order is preserved in the output.

    Raises:
        PluginContractError: If any rule fails the eager pickle validation.
    """

    def __init__(self, rules: Sequence[BaseRule]) -> None:
        for rule in rules:
            _assert_pickleable(rule)
        self._rules = rules

    def __bool__(self) -> bool:
        """Return ``True`` when the engine has at least one rule."""
        return bool(self._rules)

    def run(self, file_path: Path, text: str) -> list[RuleFinding]:
        """Run all rules against *text* and return consolidated findings.

        Exceptions raised inside individual rules are caught and converted to
        a single ``"error"`` finding with ``rule_id="RULE-ENGINE-ERROR"`` so
        that one faulty plugin cannot abort the scan of the entire docs tree.

        Args:
            file_path: Path to the file being checked (labelling only).
            text: Raw Markdown content of the file.

        Returns:
            Flat list of :class:`RuleFinding` objects from all rules,
            in rule-definition order.
        """
        findings: list[RuleFinding] = []
        for rule in self._rules:
            try:
                findings.extend(rule.check(file_path, text))
            except Exception as exc:  # noqa: BLE001
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=0,
                        rule_id="RULE-ENGINE-ERROR",
                        message=(
                            f"Rule '{rule.rule_id}' raised an unexpected exception: "
                            f"{type(exc).__name__}: {exc}"
                        ),
                        severity="error",
                    )
                )
        return findings

    def run_vsm(
        self,
        file_path: Path,
        text: str,
        vsm: VSM,
        anchors_cache: dict[Path, set[str]],
    ) -> list[RuleFinding]:
        """Run VSM-aware rules against *text* and the pre-built routing table.

        Calls :meth:`BaseRule.check_vsm` on every rule that overrides it.
        Converts the resulting :class:`Violation` objects to :class:`RuleFinding`
        for a uniform output type.  Exceptions are caught and wrapped exactly as
        in :meth:`run`.

        Args:
            file_path:     Absolute path to the file (labelling only).
            text:          Raw Markdown content.
            vsm:           Pre-built VSM (canonical URL → Route).
            anchors_cache: Pre-computed anchor slug sets.

        Returns:
            Flat list of :class:`RuleFinding` from all VSM-aware rules.
        """
        findings: list[RuleFinding] = []
        for rule in self._rules:
            try:
                violations = rule.check_vsm(file_path, text, vsm, anchors_cache)
                findings.extend(v.as_finding() for v in violations)
            except Exception as exc:  # noqa: BLE001
                findings.append(
                    RuleFinding(
                        file_path=file_path,
                        line_no=0,
                        rule_id="RULE-ENGINE-ERROR",
                        message=(
                            f"Rule '{rule.rule_id}' raised an unexpected exception "
                            f"in check_vsm: {type(exc).__name__}: {exc}"
                        ),
                        severity="error",
                    )
                )
        return findings


# ─── VSMBrokenLinkRule ────────────────────────────────────────────────────────


# Inline links: [text](url) and images ![alt](url)
_INLINE_LINK_RE = re.compile(r"!?\[[^\[\]]*\]\(([^)]+)\)")
# Fenced code block fence marker
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


def _extract_inline_links_with_lines(text: str) -> list[tuple[str, int, str]]:
    """Return ``(url, 1-based-lineno, raw_line)`` for every inline Markdown link.

    Skips fenced code blocks and inline code spans.  Pure function — no I/O.

    Args:
        text: Raw Markdown content.

    Returns:
        List of ``(url, line_number, raw_line)`` in document order.
    """
    results: list[tuple[str, int, str]] = []
    in_block = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not in_block:
            if _FENCE_RE.match(stripped):
                in_block = True
                continue
        else:
            if _FENCE_RE.match(stripped):
                in_block = False
            continue
        clean = re.sub(r"`[^`]+`", lambda m: " " * len(m.group()), line)
        for m in _INLINE_LINK_RE.finditer(clean):
            raw = m.group(1).strip()
            if not raw:
                continue
            url = re.sub(r"""\s+["'].*$""", "", raw).strip()
            if url:
                results.append((url, lineno, line.strip()))
    return results


class VSMBrokenLinkRule(BaseRule):
    """VSM-aware broken link detector (🔌 Dev 3).

    Validates every inline Markdown link against the pre-built Virtual Site Map
    instead of the filesystem.  A link is valid when its target URL appears in
    the VSM with status ``REACHABLE`` (including Ghost Routes auto-generated by
    ``reconfigure_material``).

    **Why VSM, not filesystem:**
    The filesystem tells you *whether* a file exists.  The VSM tells you
    *whether the build engine will serve it*.  A file can exist on disk and be
    ``ORPHAN_BUT_EXISTING`` — it will never be served.  Linking to it is a
    broken link from the user's perspective, even though the file is present.

    **Pure function contract (Zenzic Way):**

    * No ``open()``, no ``Path.exists()``, no I/O of any kind in
      :meth:`check_vsm`.
    * :meth:`check` is a no-op — this rule only makes sense with a VSM.
      Without routing context, link reachability cannot be determined.

    Rule code: ``Z001``
    """

    # Schemes we skip — not navigable internal links
    _SKIP_SCHEMES = frozenset(
        (
            "http://",
            "https://",
            "mailto:",
            "data:",
            "ftp:",
            "tel:",
            "javascript:",
            "irc:",
            "xmpp://",
        )
    )

    @property
    def rule_id(self) -> str:
        return "Z001"

    def check(self, file_path: Path, text: str) -> list[RuleFinding]:
        """No-op: VSMBrokenLinkRule requires VSM context — use check_vsm."""
        return []

    def check_vsm(
        self,
        file_path: Path,
        text: str,
        vsm: Mapping[str, Route],
        anchors_cache: dict[Path, set[str]],
    ) -> list[Violation]:
        """Validate all inline links in *text* against the VSM.

        For each inline link:

        1. Skip external URLs and non-navigable schemes.
        2. Skip bare fragment-only links (``#anchor``).
        3. For relative paths, compute the canonical URL using the same
           clean-URL logic the build engines use (``/page/``).
        4. Look up the URL in the VSM.  If absent or not ``REACHABLE``,
           emit a :class:`Violation` with code ``Z001``.

        Args:
            file_path:     Absolute path of the file being checked.
            text:          Raw Markdown source.
            vsm:           Pre-built VSM (canonical URL → Route).
            anchors_cache: Not used by this rule (kept for interface
                           compatibility).

        Returns:
            List of :class:`Violation` for every link whose target is absent
            from the VSM or not ``REACHABLE``.
        """
        violations: list[Violation] = []

        for url, lineno, raw_line in _extract_inline_links_with_lines(text):
            # Skip non-navigable schemes and bare fragments
            if url == "#" or any(url.startswith(s) for s in self._SKIP_SCHEMES):
                continue
            if url.startswith("#"):
                continue  # same-page anchor — handled separately

            # Compute the canonical URL this link would resolve to.
            # We apply the standard clean-URL transformation:
            #   guide/index.md  → /guide/
            #   guide/install.md → /guide/install/
            # Paths without .md suffix (e.g. "guide/install") are also handled.
            target_url = self._to_canonical_url(url)
            if target_url is None:
                continue

            route = vsm.get(target_url)
            if route is None:
                violations.append(
                    Violation(
                        file_path=file_path,
                        line_no=lineno,
                        code=self.rule_id,
                        message=(
                            f"'{url}' resolves to '{target_url}' which is not in the "
                            "Virtual Site Map — the target file may not exist"
                        ),
                        level="error",
                        context=raw_line,
                    )
                )
            elif route.status == "ORPHAN_BUT_EXISTING":
                violations.append(
                    Violation(
                        file_path=file_path,
                        line_no=lineno,
                        code="Z002",
                        message=(
                            f"'{url}' resolves to '{target_url}' which exists on disk "
                            f"but is not in the site navigation (ORPHAN_LINK). "
                            "Readers cannot reach this page via the nav tree."
                        ),
                        level="warning",
                        context=raw_line,
                    )
                )
            elif route.status not in ("REACHABLE",):
                violations.append(
                    Violation(
                        file_path=file_path,
                        line_no=lineno,
                        code=self.rule_id,
                        message=(
                            f"'{url}' resolves to '{target_url}' which has VSM status "
                            f"'{route.status}' — the page exists but is not reachable "
                            "via site navigation (UNREACHABLE_LINK)"
                        ),
                        level="error",
                        context=raw_line,
                    )
                )

        return violations

    @staticmethod
    def _to_canonical_url(href: str) -> str | None:
        """Convert a relative Markdown href to a canonical URL string.

        Applies the standard MkDocs / Zensical clean-URL rule:
        ``page.md`` → ``/page/``, ``dir/index.md`` → ``/dir/``.
        Returns ``None`` for hrefs that cannot be converted to a meaningful
        canonical URL (e.g. bare query strings, empty paths).

        Pure: no I/O, no Path.exists().

        Args:
            href: Raw href extracted from a Markdown link, already stripped of
                any title portion.

        Returns:
            Canonical URL string (leading and trailing ``/``), or ``None``.
        """
        from urllib.parse import unquote, urlsplit

        parsed = urlsplit(href)
        path = unquote(parsed.path.replace("\\", "/")).rstrip("/")
        if not path:
            return None

        # Strip .md suffix if present
        if path.endswith(".md"):
            path = path[:-3]

        # index is the directory itself
        parts = [p for p in path.split("/") if p]
        if not parts:
            return "/"
        if parts[-1] == "index":
            parts = parts[:-1]
        if not parts:
            return "/"

        return "/" + "/".join(parts) + "/"


# ─── Plugin discovery ─────────────────────────────────────────────────────────


@dataclass(slots=True)
class PluginRuleInfo:
    """Metadata about a discovered plugin rule.

    Attributes:
        rule_id:    The stable identifier returned by :attr:`BaseRule.rule_id`.
        class_name: Fully qualified class name (``module.ClassName``).
        source:     Entry-point name (e.g. ``"broken-links"``).
        origin:     Distribution name that registered the rule, or
                    ``"zenzic"`` for core rules.
    """

    rule_id: str
    class_name: str
    source: str
    origin: str


class PluginRegistry:
    """Registry wrapper around ``importlib.metadata`` entry-points.

    Provides read-only discovery for the CLI and explicit rule loading for the
    scanner.  Discovery is best-effort; loading configured plugins is strict.
    """

    def __init__(self, group: str = "zenzic.rules") -> None:
        self._group = group

    def _entry_points(self) -> list[EntryPoint]:
        """Return sorted entry-points for the configured group."""
        from importlib.metadata import entry_points

        return sorted(entry_points(group=self._group), key=lambda ep: ep.name)

    def list_rules(self) -> list[PluginRuleInfo]:
        """Discover all plugin rules as metadata for CLI inspection."""
        results: list[PluginRuleInfo] = []
        for ep in self._entry_points():
            try:
                cls = ep.load()
                instance = cls()
                if not isinstance(instance, BaseRule):
                    continue
            except Exception:  # noqa: BLE001
                continue
            dist_name = ep.dist.name if ep.dist is not None else "zenzic"
            results.append(
                PluginRuleInfo(
                    rule_id=instance.rule_id,
                    class_name=f"{cls.__module__}.{cls.__qualname__}",
                    source=ep.name,
                    origin=dist_name,
                )
            )
        if not any(r.source == "broken-links" for r in results):
            results.append(
                PluginRuleInfo(
                    rule_id=VSMBrokenLinkRule().rule_id,
                    class_name=f"{VSMBrokenLinkRule.__module__}.{VSMBrokenLinkRule.__qualname__}",
                    source="broken-links",
                    origin="zenzic",
                )
            )
        # Keep ordering deterministic regardless of fallback insertion order.
        results.sort(key=lambda r: r.source)
        return results

    def load_core_rules(self) -> list[BaseRule]:
        """Load core rules registered by the ``zenzic`` distribution."""
        core_eps = [
            ep for ep in self._entry_points() if ep.dist is not None and ep.dist.name == "zenzic"
        ]
        loaded = [self._load_entry_point(ep) for ep in core_eps]
        if not any(rule.rule_id == "Z001" for rule in loaded):
            loaded.append(VSMBrokenLinkRule())
        return loaded

    def load_selected_rules(self, plugin_ids: Sequence[str]) -> list[BaseRule]:
        """Load only the configured plugin IDs from the entry-point group.

        Args:
            plugin_ids: Entry-point names declared in ``config.plugins``.

        Raises:
            PluginContractError: If a configured plugin is missing or invalid.
        """
        from zenzic.core.exceptions import PluginContractError  # deferred: avoid circular import

        requested: list[str] = []
        seen: set[str] = set()
        for pid in plugin_ids:
            cleaned = pid.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                requested.append(cleaned)
        if not requested:
            return []

        eps_by_name = {ep.name: ep for ep in self._entry_points()}
        if "broken-links" in requested and "broken-links" not in eps_by_name:
            requested = [pid for pid in requested if pid != "broken-links"]
            return [VSMBrokenLinkRule(), *self.load_selected_rules(requested)]

        missing = sorted(set(requested) - set(eps_by_name))
        if missing:
            raise PluginContractError(
                "Configured plugin rule IDs were not found in the 'zenzic.rules' "
                f"entry-point group: {', '.join(missing)}"
            )

        loaded: list[BaseRule] = []
        for pid in requested:
            loaded.append(self._load_entry_point(eps_by_name[pid]))
        return loaded

    @staticmethod
    def _load_entry_point(ep: EntryPoint) -> BaseRule:
        """Load and instantiate one entry-point as a :class:`BaseRule`."""
        from zenzic.core.exceptions import PluginContractError  # deferred: avoid circular import

        try:
            cls = ep.load()
            instance = cls()
        except Exception as exc:  # noqa: BLE001
            raise PluginContractError(
                f"Failed to load plugin rule '{ep.name}': {type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(instance, BaseRule):
            raise PluginContractError(
                f"Plugin rule '{ep.name}' must instantiate a BaseRule, got "
                f"{type(instance).__qualname__}."
            )
        return instance


def list_plugin_rules() -> list[PluginRuleInfo]:
    """Return metadata for every rule registered in the ``zenzic.rules`` group.

    Iterates over all entry points in the ``zenzic.rules``
    ``importlib.metadata`` group, loads each class, instantiates it (using
    a no-argument constructor), and captures its :attr:`BaseRule.rule_id`.
    Entry points that cannot be loaded or instantiated are skipped — discovery
    is best-effort and must never crash the CLI.

    Returns:
        Sorted list of :class:`PluginRuleInfo`, ordered by ``source`` name.
    """
    return PluginRegistry().list_rules()
