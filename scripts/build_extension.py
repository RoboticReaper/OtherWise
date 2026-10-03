"""Build a self-contained unpacked Chrome extension and a distributable ZIP."""
from pathlib import Path
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'dist' / 'otherwise-extension'


def build():
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    shutil.copytree(ROOT / 'extension', DESTINATION,
                    ignore=shutil.ignore_patterns('tests', '*.test.js', '.DS_Store'))
    source = json.loads((ROOT / 'data' / 'topics.json').read_text())
    catalog = [{'id': row['topic'], 'topic': row['topic'], 'domain': row['domain'],
                'description': row['description']} for row in source]
    (DESTINATION / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, separators=(',', ':')))
    readme = ROOT / 'docs' / 'extension-guide.md'
    if readme.exists():
        shutil.copyfile(readme, DESTINATION / 'INSTALL.md')
    archive = ROOT / 'dist' / 'OtherWise-extension.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        for path in sorted(DESTINATION.rglob('*')):
            if path.is_file():
                output.write(path, path.relative_to(DESTINATION.parent))
    print(f'Built {len(catalog):,} local topics: {DESTINATION}')
    print(f'Install archive: {archive}')
    return DESTINATION, archive


if __name__ == '__main__':
    build()
