"""Packaging must not replace a usable extension with mismatched map resources."""
import json
from pathlib import Path

import pytest

from scripts import build_extension


@pytest.mark.parametrize('asset', [None, {'schema_version': 1, 'cache_key': 'stale', 'topics': []}])
def test_invalid_layout_preserves_existing_package(tmp_path, monkeypatch, asset):
    destination = tmp_path / 'dist' / 'otherwise-extension'
    destination.mkdir(parents=True)
    marker = destination / 'working-package.txt'
    marker.write_text('keep')
    (tmp_path / 'extension').mkdir()
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data' / 'topics.json').write_text(json.dumps([
        {'topic': 'Gardening', 'domain': 'Home', 'description': 'Original description'}
    ]))
    if asset is not None:
        (tmp_path / 'data' / 'galaxy-layout.json').write_text(json.dumps(asset))
    monkeypatch.setattr(build_extension, 'ROOT', tmp_path)
    monkeypatch.setattr(build_extension, 'DESTINATION', destination)
    with pytest.raises((ValueError, FileNotFoundError)):
        build_extension.build()
    assert marker.read_text() == 'keep'
