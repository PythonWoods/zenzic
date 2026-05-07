<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Architecture Overview

This document provides an overview of the system architecture and its key components.

## Core Components

The system is built around three principal layers: the scanner, the validator, and
the adapter. The scanner traverses the documentation directory and collects all
source files. The validator applies check rules to the scanned content. The adapter
translates engine-specific constructs into a format the Core can process uniformly.

## Design Principles

All components depend on the `BaseAdapter` protocol interface, never on concrete
implementations. This ensures the Core remains engine-agnostic — a new documentation
engine can be supported by implementing the adapter protocol alone, with zero changes
to the scanner or validator.
