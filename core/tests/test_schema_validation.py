# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path

import jsonschema
from typer.testing import CliRunner

from zenzic.main import app


def _get_repo_root() -> Path:
    tests_dir = Path(__file__).resolve().parent
    if (tests_dir.parent.parent / "examples").is_dir():
        return tests_dir.parent.parent
    return tests_dir.parent


def test_json_output_schema_compliance():
    runner = CliRunner()
    repo_root = _get_repo_root()
    example_dir = repo_root / "examples/z120-unknown-html-attr"
    cwd = os.getcwd()
    os.chdir(example_dir)
    try:
        result = runner.invoke(app, ["check", "all", "--format", "json", "--strict"])
    finally:
        os.chdir(cwd)
    assert result.exit_code != 0

    output = result.stdout
    json_start = output.find("{")
    json_output = json.loads(output[json_start:])

    schema_path = repo_root / "zenzic-output.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    jsonschema.validate(instance=json_output, schema=schema)


def test_sarif_output_schema_compliance():
    runner = CliRunner()
    repo_root = _get_repo_root()
    example_dir = repo_root / "examples/z205-forbidden-scheme"
    cwd = os.getcwd()
    os.chdir(example_dir)
    try:
        result = runner.invoke(app, ["check", "all", "--format", "sarif", "--strict"])
    finally:
        os.chdir(cwd)
    assert result.exit_code != 0

    output = result.stdout
    json_start = output.find("{")
    sarif_output = json.loads(output[json_start:])

    tests_dir = Path(__file__).resolve().parent
    schema_path = tests_dir / "fixtures/sarif-2.1.0-schema.json"
    with open(schema_path) as f:
        sarif_schema = json.load(f)

    jsonschema.validate(instance=sarif_output, schema=sarif_schema)
