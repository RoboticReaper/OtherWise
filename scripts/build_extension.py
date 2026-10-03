"""Build a self-contained unpacked Chrome extension and a distributable ZIP."""
from pathlib import Path
import json
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DESTINATION = ROOT / 'dist' / 'otherwise-extension'


def build():
    from galaxy import validate_layout

    source = json.loads((ROOT / 'data' / 'topics.json').read_text())
    layout_path = ROOT / 'data' / 'galaxy-layout.json'
    if not layout_path.exists():
        raise FileNotFoundError('Generate the public Galaxy layout with scripts/build_galaxy.py before packaging.')
    layout = json.loads(layout_path.read_text())
    validate_layout(layout, source)
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    shutil.copytree(ROOT / 'extension', DESTINATION,
                    ignore=shutil.ignore_patterns('tests', '*.test.js', '.DS_Store'))
    catalog = [{'id': row['topic'], 'topic': row['topic'], 'domain': row['domain'],
                'description': row['description']} for row in source]
    (DESTINATION / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, separators=(',', ':')))
    shutil.copyfile(layout_path, DESTINATION / 'galaxy-layout.json')
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
