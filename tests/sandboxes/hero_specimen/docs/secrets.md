<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Environment Variables

Configure the following environment variables before starting the
application. Each variable controls a specific aspect of the runtime
behaviour, from authentication providers to storage backends and
logging verbosity levels for the monitoring subsystem.

## AWS Credentials

The access key below authenticates against the cloud storage backend.
Ensure the associated IAM policy grants only the minimum required
permissions for the deployment bucket.

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
```
