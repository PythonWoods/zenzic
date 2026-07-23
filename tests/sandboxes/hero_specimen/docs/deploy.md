<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Deployment Guide

Follow these steps to deploy your application to the production
environment. This guide covers prerequisites, host configuration,
environment setup, container orchestration, and the final verification
checklist that must be completed before any traffic is routed to the
new instances.

## Prerequisites

Ensure your environment matches the baseline configuration described
in the infrastructure runbook. You will need access to the deployment
pipeline, valid SSH credentials, and a working copy of the latest
release artefacts from the CI build.

## Host Configuration

Review the host configuration before deployment:

[Host Config](../../../../etc/shadow)

Verify the target environment against the security checklist before
applying any changes to production infrastructure.
