"""Install MCP + skill into one chosen project, preserving existing settings."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import tomlkit

ROOT = Path(__file__).resolve().parents[1]


def install(agent, project):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError('Project directory must already exist')
    layout = {
        'codex': ('.codex/config.toml', '.agents/skills/telegram-dev'),
        'claude': ('.mcp.json', '.claude/skills/telegram-dev'),
        'cursor': ('.cursor/mcp.json', '.cursor/skills/telegram-dev'),
    }
    config_name, skill_name = layout[agent]
    config = project / config_name
    skill = project / skill_name
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    command = {'command': sys.executable, 'args': [str(ROOT / 'telegram_knowledge.py'), 'serve']}
    # Parse before writing anything: malformed config is reported, never replaced.
    if agent == 'codex':
        data = tomlkit.parse(config.read_text()) if config.exists() else tomlkit.document()
        if 'mcp_servers' not in data:
            data['mcp_servers'] = tomlkit.table()
        if 'telegram-knowledge' in data['mcp_servers']:
            raise ValueError('telegram-knowledge is already configured; inspect/update its existing entry instead of overwriting it')
        data['mcp_servers']['telegram-knowledge'] = command
        content = tomlkit.dumps(data)
    else:
        data = json.loads(config.read_text()) if config.exists() else {}
        servers = data.setdefault('mcpServers', {})
        if 'telegram-knowledge' in servers:
            raise ValueError('telegram-knowledge is already configured; inspect/update its existing entry instead of overwriting it')
        servers['telegram-knowledge'] = {'type': 'stdio', **command}
        content = json.dumps(data, indent=2) + '\n'
    if skill.exists():
        raise ValueError(f'Skill already exists: {skill}; inspect it before replacing')
    config.parent.mkdir(parents=True, exist_ok=True)
    if config.exists():
        shutil.copy2(config, config.with_name(config.name + '.backup-' + stamp))
    skill.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'skills/telegram-dev', skill)
    pending = config.with_name(config.name + '.telegram-dev-' + stamp)
    try:
        pending.write_text(content)
        pending.replace(config)
    except Exception:
        shutil.rmtree(skill)
        pending.unlink(missing_ok=True)
        raise
    return {'config': str(config), 'skill': str(skill), 'restart': 'Open a new agent session and enable/trust the project MCP connection if prompted.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', required=True, choices=['codex', 'claude', 'cursor'])
    parser.add_argument('--project', required=True)
    args = parser.parse_args()
    print(json.dumps(install(args.agent, args.project), indent=2))
