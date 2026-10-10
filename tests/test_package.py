import argparse
from contextlib import redirect_stderr
import importlib.util
from io import StringIO
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('openai_package', ROOT / 'scripts/package_openai.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)

# These are real public addresses used only as serialization fixtures. Tests
# never contact them and do not treat the OpenAI docs MCP as a Telegram server.
REMOTE_URL = 'https://developers.openai.com/mcp'
PRIVACY_URL = 'https://github.com/Kay0k1/telegram-dev'
TERMS_URL = 'https://github.com/Kay0k1/telegram-dev'
DEMO_URL = 'https://www.youtube.com/'
REMOTE_FLAGS = ['--mcp-url', REMOTE_URL, '--privacy-url', PRIVACY_URL,
                '--terms-url', TERMS_URL, '--demo-url', DEMO_URL]


class PackageTests(unittest.TestCase):
    def reject(self, flags):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
            package.parse_args(flags)
        self.assertEqual(failure.exception.code, 2)

    def check_skill_resources_and_icons(self, archive, manifest):
        members = set(archive.namelist())
        for field in ('composerIcon', 'composerIconDark', 'logo', 'logoDark'):
            icon_path = manifest['interface'][field]
            self.assertTrue(icon_path.startswith('./'))
            icon = ET.fromstring(archive.read(icon_path.removeprefix('./')))
            self.assertEqual(icon.attrib['width'], icon.attrib['height'])
            self.assertGreaterEqual(int(icon.attrib['width']), 48)
        for name in members:
            if name.startswith('skills/') and name.endswith('.md'):
                text = archive.read(name).decode('utf-8')
                for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
                    if '://' in target or target.startswith('#'):
                        continue
                    linked = str(PurePosixPath(name).parent / target.split('#')[0])
                    self.assertIn(linked, members, f'{name} references missing {target}')

    def test_skill_only_is_independent_from_bundled_server(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'skill.zip'
            args = package.parse_args(['--skill-only', '--output', str(output)])
            package.build(args)
            with zipfile.ZipFile(output) as archive:
                members = set(archive.namelist())
                manifest = json.loads(archive.read('.codex-plugin/plugin.json'))
                self.assertEqual(manifest['name'], 'telegram-dev-skill')
                self.assertNotIn('mcpServers', manifest)
                self.assertEqual(manifest['interface']['capabilities'], [])
                self.assertNotIn('review', manifest['extensions']['com.openai'])
                self.assertNotIn('.mcp.json', members)
                self.assertNotIn('mcp.json', members)
                self.assertNotIn('telegram_knowledge.py', members)
                self.assertNotIn('privacyPolicyURL', manifest['interface'])
                self.assertTrue({'LICENSE', 'NOTICE', 'README.md', 'skills/telegram-dev/SKILL.md'} <= members)
                self.assertTrue(all(name in {'LICENSE', 'NOTICE', 'README.md', '.codex-plugin/plugin.json'}
                                    or name.startswith(('skills/', 'assets/')) for name in members))
                self.assertIn('browsing', manifest['interface']['longDescription'])
                self.assertIn('браузер', manifest['extensions']['com.openai']['publication']['translations']['ru-RU']['description'])
                readme = archive.read('README.md').decode('utf-8')
                self.assertIn('has not been submitted', readme)
                self.assertLess(readme.index('## Русский'), readme.index('## English'))
                self.assertIn('Встроенного сервера документации', readme)
                self.check_skill_resources_and_icons(archive, manifest)

    def test_remote_archive_preserves_supplied_review_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'remote.zip'
            args = package.parse_args([*REMOTE_FLAGS, '--output', str(output)])
            package.build(args)
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read('.codex-plugin/plugin.json'))
                server = json.loads(archive.read('.mcp.json'))['mcpServers']['telegram-knowledge']
                self.assertEqual(manifest['name'], 'telegram-dev')
                self.assertEqual(manifest['mcpServers'], './.mcp.json')
                self.assertEqual(server['url'], REMOTE_URL)
                self.assertNotIn('command', server)
                self.assertNotIn('telegram_knowledge.py', archive.namelist())
                review = manifest['extensions']['com.openai']['review']
                self.assertEqual(len(review['test_cases']['positive']), 5)
                self.assertEqual(len(review['test_cases']['negative']), 3)
                self.assertEqual(review['demo_recording_url'], DEMO_URL)
                self.assertEqual(manifest['interface']['privacyPolicyURL'], PRIVACY_URL)
                self.assertEqual(manifest['interface']['termsOfServiceURL'], TERMS_URL)
                readme = archive.read('README.md').decode('utf-8')
                self.assertLess(readme.index('## Русский'), readme.index('## English'))
                self.check_skill_resources_and_icons(archive, manifest)

    def test_modes_and_conditional_requirements_prevent_incomplete_archives(self):
        self.reject([])
        self.reject(['--skill-only', '--mcp-url', REMOTE_URL])
        for field, value in [('privacy-url', PRIVACY_URL), ('terms-url', TERMS_URL), ('demo-url', DEMO_URL)]:
            with self.subTest(field=field):
                self.reject(['--skill-only', '--' + field, value])
                flags = REMOTE_FLAGS.copy()
                index = flags.index('--' + field)
                del flags[index:index + 2]
                self.reject(flags)
        self.assertEqual(package.parse_args(['--skill-only']).output.name, 'telegram-dev-skill-openai.zip')
        self.assertEqual(package.parse_args(REMOTE_FLAGS).output.name, 'telegram-dev-openai.zip')

    def test_urls_reject_placeholders_local_hosts_and_credentials(self):
        for url in ['http://developers.openai.com/mcp', 'https://example.com/mcp',
                    'https://YOUR-DOMAIN/mcp', 'https://telegram.invalid/mcp',
                    'https://127.0.0.1/mcp', 'https://10.0.0.1/mcp',
                    'https://user:secret@developers.openai.com/mcp',
                    'https://developers.openai.com/mcp#fragment',
                    'https://developers.openai.com/mcp?token=secret']:
            with self.subTest(url=url), self.assertRaises(argparse.ArgumentTypeError):
                package.public_https(url)
        recording = 'https://www.youtube.com/?gl=US'
        self.assertEqual(package.recording_https(recording), recording)

    def test_incomplete_or_placeholder_input_never_creates_an_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'must-not-exist.zip'
            for field, value in [('demo_url', None), ('mcp_url', 'https://example.com/mcp')]:
                with self.subTest(field=field):
                    args = package.parse_args([*REMOTE_FLAGS, '--output', str(output)])
                    setattr(args, field, value)
                    with self.assertRaises(ValueError):
                        package.build(args)
                    self.assertFalse(output.exists())

    def test_existing_output_is_preserved_and_source_manifest_is_untouched(self):
        source_before = (ROOT / '.codex-plugin/plugin.json').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'keep.zip'
            output.write_bytes(b'existing release')
            args = package.parse_args(['--skill-only', '--output', str(output)])
            with self.assertRaises(FileExistsError):
                package.build(args)
            self.assertEqual(output.read_bytes(), b'existing release')
        self.assertEqual((ROOT / '.codex-plugin/plugin.json').read_bytes(), source_before)


if __name__ == '__main__':
    unittest.main()
