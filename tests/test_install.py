import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import tomlkit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_all_agents_preserve_existing_settings(self):
        for agent, filename in [('codex', '.codex/config.toml'), ('claude', '.mcp.json'), ('cursor', '.cursor/mcp.json')]:
            with self.subTest(agent=agent), tempfile.TemporaryDirectory(prefix='telegram project ') as folder:
                project = Path(folder)
                config = project / filename
                config.parent.mkdir(parents=True, exist_ok=True)
                original = '# retain this comment\n[mcp_servers.other]\ncommand = "existing"\n' if agent == 'codex' else json.dumps({'mcpServers': {'other': {'command': 'existing'}}})
                config.write_text(original)
                result = installer.install(agent, project)
                data = tomlkit.parse(config.read_text()) if agent == 'codex' else json.loads(config.read_text())
                servers = data['mcp_servers' if agent == 'codex' else 'mcpServers']
                self.assertEqual(servers['other']['command'], 'existing')
                self.assertIn('telegram-knowledge', servers)
                self.assertTrue(Path(result['skill'], 'references/buttons-and-custom-emoji.md').is_file())
                backups = list(config.parent.glob(config.name + '.backup-*'))
                self.assertEqual(backups[0].read_text(), original)
                before = config.read_text()
                with self.assertRaises(ValueError):
                    installer.install(agent, project)
                self.assertEqual(config.read_text(), before)

    def test_invalid_existing_config_is_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / '.mcp.json').write_text('{bad json')
            with self.assertRaises(json.JSONDecodeError):
                installer.install('claude', p)
            self.assertEqual((p / '.mcp.json').read_text(), '{bad json')
            self.assertFalse((p / '.claude').exists())
