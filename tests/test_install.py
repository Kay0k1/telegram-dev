import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import tomlkit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def source_copy(self, destination):
        source = Path(destination)
        shutil.copytree(ROOT / 'skills/telegram-dev', source / 'skills/telegram-dev')
        (source / 'pyproject.toml').write_text('[project]\nversion = "0.3.0-test"\n', encoding='utf-8')
        (source / 'telegram_knowledge.py').write_text('# test release\n', encoding='utf-8')
        return source

    def read_config(self, agent, config):
        text = config.read_text(encoding='utf-8')
        return tomlkit.parse(text) if agent == 'codex' else json.loads(text)

    def write_config(self, agent, config, data):
        text = tomlkit.dumps(data) if agent == 'codex' else json.dumps(data, indent=2) + '\n'
        config.write_text(text, encoding='utf-8')

    def test_all_agents_preserve_existing_settings(self):
        for agent, filename in [('codex', '.codex/config.toml'), ('claude', '.mcp.json'), ('cursor', '.cursor/mcp.json')]:
            with self.subTest(agent=agent), tempfile.TemporaryDirectory(prefix='telegram project ') as folder:
                project = Path(folder)
                config = project / filename
                config.parent.mkdir(parents=True, exist_ok=True)
                original = '# retain this comment\n[mcp_servers.other]\ncommand = "existing"\n' if agent == 'codex' else json.dumps({'mcpServers': {'other': {'command': 'existing'}}})
                config.write_text(original, encoding='utf-8')
                result = installer.install(agent, project)
                data = self.read_config(agent, config)
                servers = data['mcp_servers' if agent == 'codex' else 'mcpServers']
                self.assertEqual(servers['other']['command'], 'existing')
                self.assertIn('telegram-knowledge', servers)
                self.assertTrue(Path(result['skill'], 'references/buttons-and-custom-emoji.md').is_file())
                self.assertTrue(Path(result['skill'], installer.MARKER).is_file())
                backups = list(config.parent.glob(config.name + '.backup-*'))
                self.assertEqual(backups[0].read_text(encoding='utf-8'), original)
                before = config.read_text(encoding='utf-8')
                with self.assertRaises(ValueError):
                    installer.install(agent, project)
                self.assertEqual(config.read_text(encoding='utf-8'), before)

    def test_invalid_existing_config_is_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / '.mcp.json').write_text('{bad json', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError):
                installer.install('claude', p)
            self.assertEqual((p / '.mcp.json').read_text(encoding='utf-8'), '{bad json')
            self.assertFalse((p / '.claude').exists())

    def test_update_refreshes_skill_and_preserves_settings_for_all_agents(self):
        for agent, (config_name, _skill_name) in installer.LAYOUT.items():
            with self.subTest(agent=agent), tempfile.TemporaryDirectory() as folder:
                source = self.source_copy(Path(folder) / 'release')
                project = Path(folder) / 'project'
                project.mkdir()
                with patch.object(installer, 'ROOT', source):
                    first = installer.install(agent, project)
                    skill = Path(first['skill'])
                    original_skill = (skill / 'SKILL.md').read_bytes()
                    config = project / config_name
                    data = self.read_config(agent, config)
                    servers = data['mcp_servers' if agent == 'codex' else 'mcpServers']
                    servers['other'] = {'command': 'preserve-other'}
                    servers['telegram-knowledge']['env'] = {'CUSTOM': 'preserve'}
                    data['custom_setting'] = 'preserve-top-level'
                    self.write_config(agent, config, data)
                    original_config = config.read_bytes()
                    (source / 'skills/telegram-dev/SKILL.md').write_bytes(original_skill + b'\nNew release instructions.\n')
                    (source / 'skills/telegram-dev/references/new-feature.md').write_text('New feature', encoding='utf-8')
                    (source / 'skills/telegram-dev/references/buttons-and-custom-emoji.md').unlink()
                    updated = installer.install(agent, project, update=True)
                self.assertTrue(updated['updated'])
                self.assertIn(b'New release instructions', (skill / 'SKILL.md').read_bytes())
                self.assertTrue((skill / 'references/new-feature.md').is_file())
                self.assertFalse((skill / 'references/buttons-and-custom-emoji.md').exists())
                changed_data = self.read_config(agent, config)
                changed_servers = changed_data['mcp_servers' if agent == 'codex' else 'mcpServers']
                self.assertEqual(changed_data['custom_setting'], 'preserve-top-level')
                self.assertEqual(changed_servers['other']['command'], 'preserve-other')
                self.assertEqual(changed_servers['telegram-knowledge']['env']['CUSTOM'], 'preserve')
                backups = [Path(item) for item in updated['backups']]
                self.assertEqual(next(item for item in backups if item.is_file()).read_bytes(), original_config)
                self.assertEqual((next(item for item in backups if item.is_dir()) / 'SKILL.md').read_bytes(), original_skill)
                marker = json.loads((skill / installer.MARKER).read_text(encoding='utf-8'))
                self.assertEqual(marker['version'], '0.3.0-test')
                self.assertEqual(marker['files'], installer.file_hashes(skill))

    def test_update_refuses_local_edits_added_files_and_deleted_files(self):
        for change in ('edit', 'add', 'delete', 'nested-marker'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                project = Path(folder)
                first = installer.install('claude', project)
                skill = Path(first['skill'])
                if change == 'edit':
                    (skill / 'SKILL.md').write_text('my customized skill', encoding='utf-8')
                elif change == 'add':
                    (skill / 'my-notes.md').write_text('keep my notes', encoding='utf-8')
                elif change == 'delete':
                    (skill / 'SKILL.md').unlink()
                else:
                    (skill / 'references' / installer.MARKER).write_text('{}', encoding='utf-8')
                before_files = installer.file_hashes(skill)
                before_config = (project / '.mcp.json').read_bytes()
                with self.assertRaisesRegex(ValueError, 'local changes'):
                    installer.install('claude', project, update=True)
                self.assertEqual(installer.file_hashes(skill), before_files)
                self.assertEqual((project / '.mcp.json').read_bytes(), before_config)
                self.assertFalse(list(project.rglob('*.backup-*')))

    def test_update_refuses_changed_mcp_connection_and_legacy_installs(self):
        for change in ('connection', 'legacy'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                project = Path(folder)
                first = installer.install('cursor', project)
                skill = Path(first['skill'])
                config = Path(first['config'])
                if change == 'legacy':
                    (skill / installer.MARKER).unlink()
                else:
                    data = self.read_config('cursor', config)
                    data['mcpServers']['telegram-knowledge']['command'] = 'my-custom-command'
                    self.write_config('cursor', config, data)
                before = config.read_bytes()
                hashes = installer.file_hashes(skill)
                expected = 'legacy install' if change == 'legacy' else 'managed installation'
                with self.assertRaisesRegex(ValueError, expected):
                    installer.install('cursor', project, update=True)
                self.assertEqual(config.read_bytes(), before)
                self.assertEqual(installer.file_hashes(skill), hashes)

    def test_owned_install_can_update_after_source_and_python_move(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / 'project'
            project.mkdir()
            source = self.source_copy(Path(folder) / 'old release')
            with patch.object(installer, 'ROOT', source):
                first = installer.install('claude', project)
            moved = Path(folder) / 'new release'
            source.rename(moved)
            with patch.object(installer, 'ROOT', moved), patch.object(installer.sys, 'executable', '/new/python'):
                installer.install('claude', project, update=True)
            data = self.read_config('claude', Path(first['config']))
            server = data['mcpServers']['telegram-knowledge']
            self.assertEqual(server['command'], '/new/python')
            self.assertEqual(server['args'][0], str(moved / 'telegram_knowledge.py'))
            marker = json.loads((Path(first['skill']) / installer.MARKER).read_text(encoding='utf-8'))
            self.assertEqual(marker['source_root'], str(moved))

    def test_config_write_failure_rolls_back_skill_update(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / 'project'
            project.mkdir()
            source = self.source_copy(Path(folder) / 'release')
            with patch.object(installer, 'ROOT', source):
                first = installer.install('codex', project)
                skill, config = Path(first['skill']), Path(first['config'])
                before_files = installer.file_hashes(skill)
                before_marker = (skill / installer.MARKER).read_bytes()
                before_config = config.read_bytes()
                (source / 'skills/telegram-dev/SKILL.md').write_text('new upstream skill', encoding='utf-8')
                original_replace = Path.replace

                def fail_config_replace(path, target):
                    if Path(target) == config:
                        raise OSError('simulated config replacement failure')
                    return original_replace(path, target)

                with patch.object(Path, 'replace', fail_config_replace):
                    with self.assertRaisesRegex(OSError, 'simulated'):
                        installer.install('codex', project, update=True)
            self.assertEqual(installer.file_hashes(skill), before_files)
            self.assertEqual((skill / installer.MARKER).read_bytes(), before_marker)
            self.assertEqual(config.read_bytes(), before_config)
            self.assertFalse(list(skill.parent.glob('.telegram-dev-stage-*')))
            self.assertFalse(list(config.parent.glob(config.name + '.telegram-dev-*')))
