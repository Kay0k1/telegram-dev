"""Install MCP + skill into one chosen project, preserving existing settings."""
import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

import tomlkit

ROOT = Path(__file__).resolve().parents[1]
MARKER = '.telegram-dev-install.json'
LAYOUT = {
    'codex': ('.codex/config.toml', '.agents/skills/telegram-dev'),
    'claude': ('.mcp.json', '.claude/skills/telegram-dev'),
    'cursor': ('.cursor/mcp.json', '.cursor/skills/telegram-dev'),
}


def file_hashes(directory):
    hashes = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Skill contains a symbolic link; review it before updating: {path}')
        if path.is_file() and path.relative_to(directory).as_posix() != MARKER:
            hashes[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def read_ownership(skill, agent, config_name):
    marker = skill / MARKER
    if not marker.is_file() or marker.is_symlink():
        raise ValueError('Existing skill has no Telegram Dev ownership manifest. For a legacy install, '
                         'back up and remove its skill directory and telegram-knowledge MCP entry, then install again.')
    try:
        metadata = json.loads(marker.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError('The Telegram Dev ownership manifest is invalid; review the installation manually') from exc
    if (not isinstance(metadata, dict) or metadata.get('schema_version') != 1
            or metadata.get('agent') != agent or metadata.get('config') != config_name
            or not isinstance(metadata.get('files'), dict) or not isinstance(metadata.get('connection'), dict)
            or not isinstance(metadata.get('source_root'), str)):
        raise ValueError('The Telegram Dev ownership manifest does not match this installation')
    if file_hashes(skill) != metadata['files']:
        raise ValueError('Installed Telegram Dev skill has local changes, added files or removed files. '
                         'Back up and resolve those changes before --update; no files were overwritten.')
    return metadata


def install(agent, project, update=False):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError('Project directory must already exist')
    if agent not in LAYOUT:
        raise ValueError('Unknown agent')
    config_name, skill_name = LAYOUT[agent]
    config = project / config_name
    skill = project / skill_name
    if skill.is_symlink() or config.is_symlink():
        raise ValueError('Skill/config uses a symbolic link; review this installation manually')
    if update:
        if not skill.is_dir():
            raise ValueError('No existing Telegram Dev skill to update; install without --update first')
        ownership = read_ownership(skill, agent, config_name)
    else:
        ownership = None
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    command = {'command': sys.executable, 'args': [str(ROOT / 'telegram_knowledge.py'), 'serve']}
    connection = command if agent == 'codex' else {'type': 'stdio', **command}
    # Parse before writing anything: malformed config is reported, never replaced.
    if agent == 'codex':
        data = tomlkit.parse(config.read_text(encoding='utf-8')) if config.exists() else tomlkit.document()
        if 'mcp_servers' not in data:
            data['mcp_servers'] = tomlkit.table()
        servers = data['mcp_servers']
    else:
        data = json.loads(config.read_text(encoding='utf-8')) if config.exists() else {}
        if not isinstance(data, dict):
            raise ValueError('Agent config must be a JSON object')
        servers = data.setdefault('mcpServers', {})
    if not isinstance(servers, Mapping):
        raise ValueError('MCP server configuration must be a table/object')
    existing = servers.get('telegram-knowledge')
    if update:
        if (not isinstance(existing, Mapping)
                or any(existing.get(key) != value for key, value in ownership['connection'].items())
                or any(key not in ownership['connection'] for key in connection)):
            raise ValueError('telegram-knowledge MCP connection no longer matches the managed installation. '
                             'Review the connection manually; --update will not overwrite it.')
        # Preserve user settings such as env and timeouts attached to this connection.
        for key, value in connection.items():
            existing[key] = value
    else:
        if 'telegram-knowledge' in servers:
            raise ValueError('telegram-knowledge is already configured; inspect/update its existing entry instead of overwriting it')
        if skill.exists():
            raise ValueError(f'Skill already exists: {skill}; inspect it before replacing')
        servers['telegram-knowledge'] = connection
    content = tomlkit.dumps(data) if agent == 'codex' else json.dumps(data, indent=2) + '\n'
    version = tomlkit.parse((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    source = ROOT / 'skills/telegram-dev'
    if not (source / 'SKILL.md').is_file():
        raise ValueError('The source checkout has no Telegram Dev SKILL.md')
    source_files = file_hashes(source)
    config.parent.mkdir(parents=True, exist_ok=True)
    skill.parent.mkdir(parents=True, exist_ok=True)
    stage = skill.with_name('.telegram-dev-stage-' + stamp)
    # Keep backups outside agent discovery directories so they cannot load as duplicate skills.
    skill_backup = project / '.telegram-dev-backups' / (agent + '-' + stamp) / 'skill' if update else None
    config_backup = config.with_name(config.name + '.backup-' + stamp) if config.exists() else None
    pending = config.with_name(config.name + '.telegram-dev-' + stamp)
    promoted = old_moved = False
    try:
        shutil.copytree(source, stage)
        if file_hashes(stage) != source_files:
            raise ValueError('Source skill changed during installation; retry after the source checkout is stable')
        metadata = {
            'schema_version': 1, 'version': str(version), 'source_root': str(ROOT),
            'agent': agent, 'config': config_name, 'connection': connection,
            'files': source_files,
        }
        (stage / MARKER).write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
        pending.write_text(content, encoding='utf-8')
        if config_backup:
            shutil.copy2(config, config_backup)
        if update:
            skill_backup.parent.mkdir(parents=True, exist_ok=True)
            skill.replace(skill_backup)
            old_moved = True
        stage.replace(skill)
        promoted = True
        pending.replace(config)
    except Exception:
        if promoted:
            shutil.rmtree(skill)
        if old_moved:
            skill_backup.replace(skill)
        if skill_backup and skill_backup.parent.exists() and not any(skill_backup.parent.iterdir()):
            skill_backup.parent.rmdir()
        if stage.exists():
            shutil.rmtree(stage)
        pending.unlink(missing_ok=True)
        raise
    return {
        'config': str(config), 'skill': str(skill), 'version': str(version), 'updated': update,
        'backups': [str(path) for path in (config_backup, skill_backup) if path],
        'restart': 'Open a new agent session and enable/trust the project MCP connection if prompted.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', required=True, choices=['codex', 'claude', 'cursor'])
    parser.add_argument('--project', required=True)
    parser.add_argument('--update', action='store_true', help='Update an unchanged installation created by this installer')
    args = parser.parse_args()
    try:
        result = install(args.agent, args.project, update=args.update)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
