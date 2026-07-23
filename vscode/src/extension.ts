// SPDX-FileCopyrightText: 2026 PythonWoods
//
// SPDX-License-Identifier: Apache-2.0

import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    Executable
} from 'vscode-languageclient/node';

// A4 fix: typed as | undefined — initialized in activate(), disposed via subscriptions.
let client: LanguageClient | undefined;
let statusBarItem: vscode.StatusBarItem | undefined;
// A2 fix: guard flag prevents concurrent restart calls.
let restarting = false;

const MIN_CORE_VERSION = '0.23.3';

/**
 * Safely resolve the Zenzic executable path with cross-platform fallback logic.
 * Order of precedence:
 * 1. Explicit user/workspace setting (zenzic.executablePath containing path separator or absolute)
 * 2. System $PATH
 * 3. Standard user binary fallback directories (~/.local/bin, ~/.cargo/bin, ~/.uv/bin) via os.homedir()
 */
export async function resolveExecutablePath(cmd: string): Promise<string | undefined> {
    const isWindows = process.platform === 'win32';
    const exts = isWindows ? ['.exe', '.cmd', '.bat', ''] : [''];

    const checkPath = async (p: string): Promise<string | undefined> => {
        for (const ext of exts) {
            try {
                await fs.promises.access(p + ext, fs.constants.X_OK);
                return p + ext;
            } catch {
                // Ignore and try next extension or path
            }
        }
        return undefined;
    };

    if (path.isAbsolute(cmd) || cmd.includes(path.sep) || (isWindows && cmd.includes('/'))) {
        return await checkPath(cmd);
    }

    const home = os.homedir();
    const systemPaths = (process.env.PATH || '').split(path.delimiter);
    const fallbackPaths = home
        ? [
            path.join(home, '.local', 'bin'),
            path.join(home, '.cargo', 'bin'),
            path.join(home, '.uv', 'bin')
        ]
        : [];

    const searchDirs = [...systemPaths, ...fallbackPaths];
    for (const dir of searchDirs) {
        if (!dir) continue;
        const fullPath = path.join(dir, cmd);
        const resolved = await checkPath(fullPath);
        if (resolved) {
            return resolved;
        }
    }
    return undefined;
}

/**
 * Compare two SemVer strings (MAJOR.MINOR.PATCH).
 * Returns > 0 if v1 > v2, < 0 if v1 < v2, and 0 if v1 === v2.
 */
export function compareSemver(v1: string, v2: string): number {
    const parse = (v: string) => {
        const match = v.match(/^(\d+)\.(\d+)\.(\d+)/);
        if (!match) {
            throw new Error(`Invalid SemVer format: '${v}'`);
        }
        return [parseInt(match[1], 10), parseInt(match[2], 10), parseInt(match[3], 10)];
    };

    const [major1, minor1, patch1] = parse(v1);
    const [major2, minor2, patch2] = parse(v2);

    if (major1 !== major2) { return major1 - major2; }
    if (minor1 !== minor2) { return minor1 - minor2; }
    return patch1 - patch2;
}

export interface CoreVersionCheckResult {
    status: 'ok' | 'outdated' | 'not_found' | 'error';
    version?: string;
    error?: string;
}

/**
 * Safely verify the core binary version via execFile (preventing shell injection)
 * and compare against MIN_CORE_VERSION.
 */
export async function checkCoreVersion(executablePath: string): Promise<CoreVersionCheckResult> {
    const cp = await import('child_process');
    return new Promise((resolve) => {
        cp.execFile(executablePath, ['--version'], { encoding: 'utf-8' }, (err, stdout, stderr) => {
            if (err) {
                if ((err as { code?: string }).code === 'ENOENT') {
                    return resolve({ status: 'not_found', error: `Binary not found at '${executablePath}'` });
                }
                return resolve({
                    status: 'error',
                    error: err.message || stderr || 'Failed to execute zenzic --version'
                });
            }

            const output = (stdout || '').trim() || (stderr || '').trim();
            const match = output.match(/(\d+\.\d+\.\d+)/);
            if (!match) {
                return resolve({
                    status: 'error',
                    error: `Could not parse version from output: '${output}'`
                });
            }

            const foundVersion = match[1];
            try {
                if (compareSemver(foundVersion, MIN_CORE_VERSION) < 0) {
                    return resolve({
                        status: 'outdated',
                        version: foundVersion
                    });
                }
                return resolve({
                    status: 'ok',
                    version: foundVersion
                });
            } catch (cmpErr: unknown) {
                const msg = cmpErr instanceof Error ? cmpErr.message : String(cmpErr);
                return resolve({ status: 'error', error: msg });
            }
        });
    });
}

export async function activate(context: vscode.ExtensionContext) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = '$(sync~spin) Zenzic: Starting';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    const startServer = async () => {
        const config = vscode.workspace.getConfiguration('zenzic');
        const executablePath = config.get<string>('executablePath') || 'zenzic';

        const resolvedPath = await resolveExecutablePath(executablePath);

        if (!resolvedPath) {
            statusBarItem!.text = '$(error) Zenzic: Not Found';
            statusBarItem!.tooltip = `Executable not found: '${executablePath}'. Run: uv tool install zenzic`;
            const action = await vscode.window.showErrorMessage(
                `Zenzic binary not found: '${executablePath}'. ` +
                `Install the core engine via 'uv tool install zenzic' or configure 'zenzic.executablePath'.`,
                'Install with uv',
                'Open Docs'
            );
            if (action === 'Install with uv') {
                const terminal = vscode.window.createTerminal('Zenzic Setup');
                terminal.show();
                terminal.sendText('uv tool install zenzic', false);
            } else if (action === 'Open Docs') {
                vscode.env.openExternal(vscode.Uri.parse(
                    'https://github.com/PythonWoods/zenzic-vscode#requirements'
                ));
            }
            return;
        }

        // Enforce Core Version Handshake (>= MIN_CORE_VERSION) before starting LSP client
        const versionResult = await checkCoreVersion(resolvedPath);
        if (versionResult.status === 'not_found') {
            statusBarItem!.text = '$(error) Zenzic: Not Found';
            statusBarItem!.tooltip = `Zenzic binary not found at '${resolvedPath}'`;
            vscode.window.showErrorMessage(
                `Zenzic binary not found at '${resolvedPath}'. Please install it via 'uv tool install zenzic' or configure 'zenzic.executablePath'.`
            );
            return;
        }

        if (versionResult.status === 'outdated') {
            statusBarItem!.text = '$(error) Zenzic: Outdated Core';
            statusBarItem!.tooltip = `Zenzic Core v${MIN_CORE_VERSION} or higher required (found v${versionResult.version})`;
            const action = await vscode.window.showErrorMessage(
                `Zenzic extension requires Zenzic Core v${MIN_CORE_VERSION} or higher. ` +
                `Found v${versionResult.version}. Please update the global binary or configure 'zenzic.executablePath'.`,
                'Update with uv',
                'Configure Path',
                'Open Docs'
            );
            if (action === 'Update with uv') {
                const terminal = vscode.window.createTerminal('Zenzic Update');
                terminal.show();
                terminal.sendText('uv tool install --force zenzic', false);
            } else if (action === 'Configure Path') {
                vscode.commands.executeCommand('workbench.action.openSettings', 'zenzic.executablePath');
            } else if (action === 'Open Docs') {
                vscode.env.openExternal(vscode.Uri.parse(
                    'https://github.com/PythonWoods/zenzic-vscode#requirements'
                ));
            }
            return;
        }

        if (versionResult.status === 'error') {
            statusBarItem!.text = '$(error) Zenzic: Version Error';
            statusBarItem!.tooltip = `Failed to verify Zenzic Core version: ${versionResult.error}`;
            vscode.window.showErrorMessage(
                `Could not verify Zenzic Core version: ${versionResult.error}`
            );
            return;
        }

        const run: Executable = {
            command: resolvedPath,
            args: ['lsp']
        };


        // A5: debug config is intentionally identical to run. This extension is a
        // thin client: server-side debugging is done by attaching directly to the
        // zenzic process, not through a dedicated debug launcher.
        const serverOptions: ServerOptions = { run, debug: run };

        const outputChannel = vscode.window.createOutputChannel('Zenzic Language Server', { log: true });

        const clientOptions: LanguageClientOptions = {
            documentSelector: [
                { scheme: 'file', language: 'markdown', pattern: '**/*.{md,mdx,markdown}' },
                { scheme: 'file', language: 'mdx', pattern: '**/*.{md,mdx,markdown}' },
                { scheme: 'untitled', language: 'markdown' },
                { scheme: 'untitled', language: 'mdx' }
            ],
            outputChannel
        };

        client = new LanguageClient(
            'zenzicLanguageServer',
            'Zenzic Language Server',
            serverOptions,
            clientOptions
        );

        try {
            await client.start();
            statusBarItem!.text = '$(check) Zenzic: Running';
            statusBarItem!.tooltip = 'Zenzic Language Server is running';
        } catch (err: unknown) {
            // A1 fix: err is unknown; narrow to Error before accessing .message to
            // avoid producing "Error: undefined" when a non-Error value is thrown.
            const message = err instanceof Error ? err.message : String(err);
            statusBarItem!.text = '$(error) Zenzic: Error';
            statusBarItem!.tooltip = 'Zenzic Language Server failed to start';
            vscode.window.showErrorMessage(
                `Failed to start Zenzic LSP. Please ensure zenzic is installed ` +
                `(e.g., 'uv tool install zenzic') or set the correct path in ` +
                `'zenzic.executablePath'. Error: ${message}`
            );
        }
    };

    const restartServer = async () => {
        // A2 fix: idempotent guard — if a restart is already in flight, ignore the
        // duplicate call instead of spawning a second concurrent LSP client.
        if (restarting) { return; }
        restarting = true;
        try {
            statusBarItem!.text = '$(sync~spin) Zenzic: Restarting';
            if (client) {
                await client.stop();
                client = undefined;
            }
            await startServer();
        } finally {
            restarting = false;
        }
    };

    const stopServer = async () => {
        if (client) {
            statusBarItem!.text = '$(sync~spin) Zenzic: Stopping';
            await client.stop();
            client = undefined;
            statusBarItem!.text = '$(stop-circle) Zenzic: Stopped';
            statusBarItem!.tooltip = 'Zenzic Language Server is stopped';
        }
    };

    context.subscriptions.push(
        vscode.commands.registerCommand('zenzic.restartServer', restartServer),
        vscode.commands.registerCommand('zenzic.startServer', startServer),
        vscode.commands.registerCommand('zenzic.stopServer', stopServer)
    );

    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (e) => {
            if (e.affectsConfiguration('zenzic.executablePath')) {
                await restartServer();
            }
        })
    );

    await startServer();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    // A3 fix: swallow rejection from stop() — the server process may have already
    // exited (e.g., crashed), in which case stop() rejects with a benign error.
    return client.stop().catch(() => { /* server already stopped */ });
}
