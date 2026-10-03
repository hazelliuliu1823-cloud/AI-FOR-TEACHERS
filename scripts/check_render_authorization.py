#!/usr/bin/env python3
"""Renderer entry guard: refuse planning, stale or altered manifests."""
import argparse
import json
from pathlib import Path

from compile_render_manifest import compile_manifest, digest


def check(root, manifest):
    if manifest.get('render_allowed') is not True or manifest.get('eligibility') != 'validated_for_render':
        raise ValueError('Manifest is not eligible for rendering')
    raw = {k: v for k, v in manifest.items() if k != 'manifest_digest'}
    if manifest.get('manifest_digest') != digest(raw):
        raise ValueError('Manifest content changed after compilation')
    current = compile_manifest(root)
    if current['input_digest'] != manifest.get('input_digest'):
        raise ValueError('Project/evidence/decision inputs changed; recompile before rendering')
    if current['manifest_digest'] != manifest['manifest_digest']:
        raise ValueError('Manifest differs from the current validated execution')
    return {'status': 'pass', 'render_allowed': True, 'playback_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_directory', type=Path)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        print(json.dumps(check(args.project_directory, manifest), ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'status': 'fail', 'render_allowed': False, 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
