# Waspid AI OS
"""Waspid command-line interface.

A lightweight, cross-platform entry point for operating a Waspid
deployment. Uses only the standard library at import time so that
``waspid version``/``waspid doctor`` work even when optional server
dependencies are missing.

Provider API keys added via ``waspid provider add`` are stored in
``~/.waspid/waspid.env`` (the directory name is kept for
compatibility with the upstream agent SDK) and exported into the
environment by ``waspid start``, where LiteLLM picks them up.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

STATE_DIR = Path(os.environ.get('OH_PERSISTENCE_DIR', Path.home() / '.waspid'))
ENV_FILE = STATE_DIR / 'waspid.env'

# Provider id -> environment variable LiteLLM (or the server) reads.
PROVIDERS: dict[str, str] = {
    'openai': 'OPENAI_API_KEY',
    'anthropic': 'ANTHROPIC_API_KEY',
    'gemini': 'GEMINI_API_KEY',
    'grok': 'XAI_API_KEY',
    'openrouter': 'OPENROUTER_API_KEY',
    'deepseek': 'DEEPSEEK_API_KEY',
    'ollama': 'OLLAMA_BASE_URL',
    'azure': 'AZURE_API_KEY',
    'bedrock': 'AWS_ACCESS_KEY_ID',
}


def _repo_root() -> Path | None:
    """Best-effort location of a Waspid source checkout (for dev/build)."""
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / 'Makefile').exists() and (candidate / 'frontend').exists():
        return candidate
    return None


def _read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                values[key.strip()] = value.strip()
    return values


def _write_env_file(values: dict[str, str]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lines = ['# Waspid provider credentials. Managed by `waspid provider`.']
    lines += [f'{k}={v}' for k, v in sorted(values.items())]
    ENV_FILE.write_text('\n'.join(lines) + '\n')
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass


def cmd_version(_: argparse.Namespace) -> int:
    try:
        from waspid.version import get_version

        print(f'Waspid {get_version()}')
    except Exception:
        print('Waspid (version unavailable — package not fully installed)')
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    for key, value in _read_env_file().items():
        os.environ.setdefault(key, value)
    try:
        import uvicorn
    except ImportError:
        print(
            'uvicorn is not installed. Run `waspid build` (or `make build`) first.',
            file=sys.stderr,
        )
        return 1
    print(f'Starting Waspid on http://{args.host}:{args.port}')
    uvicorn.run('waspid.app_server.app:app', host=args.host, port=args.port)
    return 0


def _run_make(target: str, *extra: str) -> int:
    root = _repo_root()
    if root is None:
        print(
            f'`waspid {target}` requires a Waspid source checkout '
            '(Makefile not found).',
            file=sys.stderr,
        )
        return 1
    if shutil.which('make') is None:
        print('`make` is not installed.', file=sys.stderr)
        return 1
    return subprocess.call(['make', target, *extra], cwd=root)


def cmd_dev(_: argparse.Namespace) -> int:
    return _run_make('run')


def cmd_build(_: argparse.Namespace) -> int:
    return _run_make('build')


def cmd_update(_: argparse.Namespace) -> int:
    root = _repo_root()
    if root is None:
        print('`waspid update` requires a git checkout of Waspid.', file=sys.stderr)
        return 1
    code = subprocess.call(['git', 'pull', '--ff-only'], cwd=root)
    if code == 0:
        print('Updated. Run `waspid build` to rebuild dependencies and frontend.')
    return code


def cmd_deploy(args: argparse.Namespace) -> int:
    root = _repo_root()
    if root is None:
        print('`waspid deploy` requires a Waspid source checkout.', file=sys.stderr)
        return 1
    compose = ['docker', 'compose']
    if shutil.which('docker') is None:
        print('Docker is not installed.', file=sys.stderr)
        return 1
    cmd = compose + ['up', '--build']
    if args.detach:
        cmd.append('-d')
    return subprocess.call(cmd, cwd=root)


def cmd_doctor(_: argparse.Namespace) -> int:
    failures = 0

    def check(label: str, ok: bool, hint: str = '') -> None:
        nonlocal failures
        mark = 'ok' if ok else 'MISSING'
        print(f'  [{mark:>7}] {label}' + (f' — {hint}' if not ok and hint else ''))
        if not ok:
            failures += 1

    print('Waspid doctor')
    print('System:')
    check(
        f'Python {sys.version_info.major}.{sys.version_info.minor}',
        (3, 12) <= sys.version_info[:2] < (3, 14),
        'Python >= 3.12 and < 3.14 required',
    )
    check('node', shutil.which('node') is not None, 'install Node.js 22+')
    check('npm', shutil.which('npm') is not None, 'install npm')
    check('docker', shutil.which('docker') is not None, 'needed for sandboxed agents')
    check('make', shutil.which('make') is not None, 'needed for dev/build commands')

    print('Server:')
    try:
        import uvicorn  # noqa: F401

        check('python dependencies', True)
    except ImportError:
        check('python dependencies', False, 'run `make build`')
    root = _repo_root()
    if root is not None:
        check(
            'frontend build',
            (root / 'frontend' / 'build').exists(),
            'run `waspid build`',
        )

    print('Providers:')
    saved = _read_env_file()
    configured = [
        provider
        for provider, env_key in PROVIDERS.items()
        if env_key in saved or os.environ.get(env_key)
    ]
    check(
        'at least one provider key',
        bool(configured),
        'run `waspid provider add <provider> <key>` or use the Settings UI',
    )
    if configured:
        print(f'    configured: {", ".join(configured)}')

    print('No problems found.' if failures == 0 else f'{failures} problem(s) found.')
    return 0 if failures == 0 else 1


def cmd_provider_list(_: argparse.Namespace) -> int:
    saved = _read_env_file()
    print(f'{"PROVIDER":<12} {"ENV VAR":<22} STATUS')
    for provider, env_key in PROVIDERS.items():
        if env_key in saved:
            status = 'configured (waspid.env)'
        elif os.environ.get(env_key):
            status = 'configured (environment)'
        else:
            status = '-'
        print(f'{provider:<12} {env_key:<22} {status}')
    print('\nKeys can also be configured per-user in the Settings UI.')
    return 0


def cmd_provider_add(args: argparse.Namespace) -> int:
    provider = args.provider.lower()
    if provider not in PROVIDERS:
        print(
            f'Unknown provider {provider!r}. Supported: {", ".join(PROVIDERS)}',
            file=sys.stderr,
        )
        return 1
    values = _read_env_file()
    values[PROVIDERS[provider]] = args.api_key
    _write_env_file(values)
    print(f'Saved {PROVIDERS[provider]} to {ENV_FILE}')
    print('It will be exported automatically by `waspid start`.')
    return 0


def cmd_provider_remove(args: argparse.Namespace) -> int:
    provider = args.provider.lower()
    if provider not in PROVIDERS:
        print(f'Unknown provider {provider!r}.', file=sys.stderr)
        return 1
    values = _read_env_file()
    if values.pop(PROVIDERS[provider], None) is None:
        print(f'{provider} is not configured in {ENV_FILE}.')
        return 0
    _write_env_file(values)
    print(f'Removed {provider} from {ENV_FILE}.')
    return 0


def _open_ui(path: str, port: int) -> int:
    import webbrowser

    url = f'http://localhost:{port}{path}'
    print(f'Opening {url}')
    webbrowser.open(url)
    return 0


def cmd_agents(args: argparse.Namespace) -> int:
    return _open_ui('/agents', args.port)


def cmd_workflows(args: argparse.Namespace) -> int:
    return _open_ui('/workflows', args.port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='waspid',
        description='Waspid — enterprise AI workforce operating system.',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('version', help='Print the Waspid version').set_defaults(
        func=cmd_version
    )

    start = sub.add_parser('start', help='Start the Waspid server')
    start.add_argument('--host', default='127.0.0.1')
    start.add_argument('--port', type=int, default=3000)
    start.set_defaults(func=cmd_start)

    sub.add_parser(
        'dev', help='Run backend and frontend in development mode (make run)'
    ).set_defaults(func=cmd_dev)
    sub.add_parser(
        'build', help='Install dependencies and build the frontend (make build)'
    ).set_defaults(func=cmd_build)
    sub.add_parser('doctor', help='Check the local environment').set_defaults(
        func=cmd_doctor
    )
    sub.add_parser('update', help='Update a git checkout of Waspid').set_defaults(
        func=cmd_update
    )

    deploy = sub.add_parser('deploy', help='Deploy with Docker Compose')
    deploy.add_argument('-d', '--detach', action='store_true')
    deploy.set_defaults(func=cmd_deploy)

    provider = sub.add_parser('provider', help='Manage LLM provider credentials')
    provider_sub = provider.add_subparsers(dest='provider_command', required=True)
    provider_sub.add_parser('list', help='List providers').set_defaults(
        func=cmd_provider_list
    )
    add = provider_sub.add_parser('add', help='Save a provider API key')
    add.add_argument('provider', help=f'One of: {", ".join(PROVIDERS)}')
    add.add_argument('api_key')
    add.set_defaults(func=cmd_provider_add)
    remove = provider_sub.add_parser('remove', help='Remove a provider API key')
    remove.add_argument('provider')
    remove.set_defaults(func=cmd_provider_remove)

    agents = sub.add_parser('agents', help='Open the agents dashboard')
    agents.add_argument('--port', type=int, default=3000)
    agents.set_defaults(func=cmd_agents)

    workflows = sub.add_parser('workflows', help='Open the workflows dashboard')
    workflows.add_argument('--port', type=int, default=3000)
    workflows.set_defaults(func=cmd_workflows)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
