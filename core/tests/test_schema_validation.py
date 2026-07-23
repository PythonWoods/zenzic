# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path

import jsonschema
from typer.testing import CliRunner

from zenzic.main import app


def test_json_output_schema_compliance():
    runner = CliRunner()
    cwd = os.getcwd()
    os.chdir("examples/z120-unknown-html-attr")
    try:
        result = runner.invoke(app, ["check", "all", "--format", "json", "--strict"])
    finally:
        os.chdir(cwd)
    assert result.exit_code != 0

    output = result.stdout
    json_start = output.find("{")
    json_output = json.loads(output[json_start:])

    schema_path = Path("zenzic-output.schema.json")
    with open(schema_path) as f:
        schema = json.load(f)

    jsonschema.validate(instance=json_output, schema=schema)


def test_sarif_output_schema_compliance():
    runner = CliRunner()
    cwd = os.getcwd()
    os.chdir("examples/z205-forbidden-scheme")
    try:
        result = runner.invoke(app, ["check", "all", "--format", "sarif", "--strict"])
    finally:
        os.chdir(cwd)
    assert result.exit_code != 0

    output = result.stdout
    json_start = output.find("{")
    sarif_output = json.loads(output[json_start:])

    schema_path = Path(__file__).parent / "fixtures/sarif-2.1.0-schema.json"
    with open(schema_path) as f:
        sarif_schema = json.load(f)

    jsonschema.validate(instance=sarif_output, schema=sarif_schema)
