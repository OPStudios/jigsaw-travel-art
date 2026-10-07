"""Immutable, source-coordinated repair of level 43's detached rosemary stem.

Moves the original painted cutout only. No redraw, old-object replacement,
geometry regeneration, publication, or modification of the other 119 levels.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw

from build_content_release import canonical, digest, immutable_write
from delivery_variants import (animation_images, composition_descriptor, level_sources,
                               put_object, read_object)
from image_compression import composite, decode, validate_animation, validate_image
from verify_mixed_geometry import vertices_bytes

REPO = Path(__file__).resolve().parents[1]
LEVEL = 43
OFFSET = (-15, 7)
ART_KEYS = ('image', 'artRevision', 'paintedAnimation')


def verify_art_only_change(before, after):
    """Artwork cannot rewrite rule/replay or historical geometry provenance."""
    before_rules = {key: value for key, value in before.items() if key not in ART_KEYS}
    after_rules = {key: value for key, value in after.items() if key not in ART_KEYS}
    if before_rules != after_rules:
        raise ValueError('Source repair changed immutable rules or gameplay metadata')
    return digest(canonical(before_rules))


def png_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG', compress_level=9)
    return stream.getvalue()


def write_json(path, value):
    immutable_write(path, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalogue', type=Path, required=True)
    p.add_argument('--art-root', type=Path, required=True)
    p.add_argument('--previous-set', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--godot', type=Path, required=True)
    args = p.parse_args()
    catalogue, art, previous, output = (v.resolve() for v in
                                      (args.catalogue, args.art_root, args.previous_set, args.output))
    output.mkdir(parents=True, exist_ok=True)
    root = catalogue.parent.parent
    catalogue_raw = catalogue.read_bytes()
    if digest(catalogue_raw) != catalogue.stem:
        raise ValueError('Source catalogue filename and exact bytes differ')
    old_manifest = json.loads(catalogue_raw)
    if old_manifest.get('deliveryContract') != 2 or old_manifest.get('imagePolicy') != 'composed-v1':
        raise ValueError('Expected the reviewed composed-v1 source catalogue')
    manifest = copy.deepcopy(old_manifest)
    city = next(c for c in manifest['destinations'] if LEVEL in c['levelIds'])
    old_city = copy.deepcopy(city)
    original = json.loads(read_object(root, city['package']))
    old_original = copy.deepcopy(original)
    level = next(row for row in original['levels'] if row['levelId'] == LEVEL)
    old_level = copy.deepcopy(level)
    delivery = json.loads(read_object(root, city['delivery']['levels'][str(LEVEL)]))
    old_delivery = copy.deepcopy(delivery)
    old_image = level['image']
    master_descriptor = original['assets'][old_image]
    images = {s: decode(read_object(root, original['assets'][s])) for s in level_sources(level)[1:]}
    master = decode(read_object(root, master_descriptor))
    if composite(level, images).tobytes() != master.tobytes():
        raise ValueError('Original master does not reproduce its source composition')
    if master.size != (1280, 1600):
        raise ValueError('Inspected original coordinate system changed')
    part = level['paintedAnimation']['parts'][1]
    if part['rect'] != [0.7078125, 0.124375, 0.0671875, 0.109375]:
        raise ValueError('The inspected original rosemary placement changed')
    part['rect'][0] += OFFSET[0] / master.width
    part['rect'][1] += OFFSET[1] / master.height
    repaired = composite(level, images)
    repaired_raw = png_bytes(repaired)
    new_master = put_object(root, repaired_raw, 'png', 'image/png')
    new_master.update(width=master.width, height=master.height)
    level['image'] = f"res://assets/art/ah002-contact-v1/043/{new_master['sha256'][:12]}-picture.png"
    level['artRevision'] = 'ah002-contact-v1'
    del original['assets'][old_image]
    original['assets'][level['image']] = new_master

    # Measure the repaired art for QA only. Piece detail affects exact Hint/Sort
    # ordering and replay; detailSource records the original geometry authoring.
    # Neither may change in an art-only revision, even if current ranks match.
    request = {'levels': [copy.deepcopy(level)], 'sources': {str(LEVEL): {
        'path': str(root / new_master['path']), 'sha256': new_master['sha256'],
        'resource': level['image'], 'width': master.width, 'height': master.height}}}
    request_path = output / 'detail-request.json'
    result_path = output / 'detail-result.json'
    write_json(request_path, request)
    if result_path.exists():
        raise ValueError('Choose a clean repair output; never replace existing detail proof')
    proc = subprocess.run([str(args.godot.resolve()), '--headless', '--path', str(REPO),
                           '--script', 'tools/recompute_mixed_detail.gd', '--',
                           str(request_path), str(result_path)], cwd=REPO,
                          capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    log = proc.stdout + proc.stderr
    immutable_write(output / 'detail.log', log.encode())
    if proc.returncode or any(x in log for x in ['ERROR:', 'SCRIPT ERROR:', 'Parse Error:']):
        raise ValueError('Repaired image detail recalculation failed: ' + log[-2000:])
    measured = json.loads(result_path.read_bytes())['levels'][0]
    if len(measured['pieces']) != len(level['pieces']):
        raise ValueError('Image detail recalculation changed piece count')
    if vertices_bytes(measured['pieces']) != vertices_bytes(old_level['pieces']):
        raise ValueError('QA measurement changed geometry')
    rule_fingerprint = verify_art_only_change(old_level, level)
    detail_qa = {
        'purpose': 'Current repaired-art measurements only; not authoritative gameplay or replay data.',
        'source': measured['geometry']['detailSource'],
        'requestSha256': digest(request_path.read_bytes()),
        'resultSha256': digest(result_path.read_bytes()),
        'measuredPieceDetails': [{'pieceIndex': index, 'detail': piece['detail']}
                                 for index, piece in enumerate(measured['pieces'])],
        'authoritativePieceDetailsPreserved': True,
        'historicalGeometryDetailSourcePreserved': old_level['geometry']['detailSource'],
    }
    if detail_qa['source']['sha256'] != new_master['sha256']:
        raise ValueError('QA measurement is not bound to the repaired master')

    city['package'] = put_object(root, canonical(original), 'json', 'application/json')
    delivery['levels'] = [copy.deepcopy(level)]
    del delivery['assets'][old_image]
    delivery['assets'][level['image']] = composition_descriptor(level, delivery['assets'], new_master)
    city['delivery']['levels'][str(LEVEL)] = put_object(root, canonical(delivery), 'json', 'application/json')
    manifest_raw = canonical(manifest)
    repaired_catalogue = root / 'releases' / (digest(manifest_raw) + '.json')
    immutable_write(repaired_catalogue, manifest_raw)

    # Existing still-compression gates apply unchanged to the repaired picture.
    originals = animation_images(root, level, original['assets'])
    delivered = animation_images(root, level, delivery['assets'])
    still_metrics = validate_image(originals[level['image']], delivered[level['image']])
    animation_metrics = validate_animation(level, originals, delivered)
    source_still = delivered[level['image']]
    immutable_write(output / 'repaired-delivered-still.png', png_bytes(source_still))
    immutable_write(output / 'repaired-master.png', repaired_raw)
    board = Image.new('RGB', (840, 560), '#ece3d1')
    draw = ImageDraw.Draw(board)
    for column, (title, image) in enumerate([('Original source contact', master), ('Repaired source contact', repaired)]):
        crop = image.crop((885, 310, 1025, 445)).convert('RGB').resize((420, 405), Image.Resampling.NEAREST)
        board.paste(crop, (column * 420, 30))
        draw.text((column * 420 + 10, 10), title, fill='#241f18')
    draw.text((12, 455), 'Only the existing rosemary moves (-15,+7) pixels in the 1280x1600 master.', fill='#241f18')
    draw.text((12, 477), 'Its cut stem overlaps the existing branch stub; source pixels are unchanged.', fill='#241f18')
    immutable_write(output / 'contact-before-after.png', png_bytes(board))

    # Preserve an art revision; never mutate the original approved source folder.
    profiles = json.loads((previous / 'profiles-final.json').read_bytes())
    profile = profiles['levels'][str(LEVEL)]
    old_authoring_path = art / profile['authoring']
    old_authoring = old_authoring_path.read_bytes()
    spec = json.loads(old_authoring)
    authored = spec['parts'][1]
    authored['rect'] = copy.deepcopy(part['rect'])
    authored['sourcePixelRect'][0] += OFFSET[0]
    authored['sourcePixelRect'][1] += OFFSET[1]
    authored['anchor']['point'] = [v + OFFSET[a] for a, v in enumerate(authored['anchor']['point'])]
    revision = art / 'scenes/ah002-contact-repairs/level-043-v1'
    repair = {'levelId': LEVEL, 'part': 2, 'translationMasterPx': list(OFFSET),
              'originalMasterSha256': master_descriptor['sha256'], 'repairedMasterSha256': new_master['sha256'],
              'originalAuthoringSha256': digest(old_authoring), 'oldRect': old_level['paintedAnimation']['parts'][1]['rect'],
              'newRect': part['rect'], 'targetContactMasterPx': [932, 380],
              'method': 'Translate unchanged painted cutout onto the existing branch; coordinated still and GIF.',
              'sourcePixelsRepainted': False, 'geometryVerticesUnchanged': True}
    spec['sourceRepair'] = repair
    authored_raw = (json.dumps(spec, indent=2, ensure_ascii=False) + '\n').encode()
    immutable_write(revision / 'master.png', repaired_raw)
    immutable_write(revision / 'authoring.portable.json', authored_raw)
    write_json(revision / 'repair.json', repair)
    old_profile_authoring = profile['authoring']
    profile['authoring'] = (revision / 'authoring.portable.json').relative_to(art).as_posix()
    profile['openVisualDefects'] = []
    profile['resolvedSourceDefect'] = repair
    profile['parts'][1]['rect'] = copy.deepcopy(part['rect'])
    profile['parts'][1]['reason'] = 'The repaired rosemary joins the original branch stub in both still and GIF; keep that contact stationary.'
    for row in profiles['sourceAuthoring']:
        if row['path'] == old_profile_authoring:
            row.update(path=profile['authoring'], sha256=digest(authored_raw))
    profiles['sourceRepair'] = repair
    write_json(output / 'profiles-repaired.json', profiles)

    unchanged = []
    for prior_city, next_city in zip(old_manifest['destinations'], manifest['destinations']):
        prior_package = json.loads(read_object(root, prior_city['package']))
        next_package = json.loads(read_object(root, next_city['package']))
        for before, after in zip(prior_package['levels'], next_package['levels']):
            ident = before['levelId']
            if ident == LEVEL:
                continue
            if before != after or prior_city['delivery']['levels'][str(ident)] != next_city['delivery']['levels'][str(ident)]:
                raise ValueError('Unrelated level metadata changed: ' + str(ident))
            unchanged.append(ident)
    if len(unchanged) != 119:
        raise ValueError('Expected exactly119 unchanged levels')
    proof = {'schemaVersion': 1, 'repair': repair, 'sourceCatalogueSha256': digest(catalogue_raw),
             'repairedSourceCatalogueSha256': digest(manifest_raw), 'repairedCataloguePath': str(repaired_catalogue),
             'originalCityPackage': old_city['package'], 'repairedCityPackage': city['package'],
             'oldSourceImageSha256': old_delivery['assets'][old_image]['sha256'],
             'newSourceImageSha256': delivery['assets'][level['image']]['sha256'],
             'unchangedLevelIds': unchanged, 'geometryVerticesSha256': digest(vertices_bytes(level['pieces'])),
             'immutableRulesSha256': rule_fingerprint, 'authoritativeRulesUnchanged': True,
             'currentArtworkDetailQA': detail_qa,
             'stillCompressionMetrics': still_metrics, 'animationCompressionMetrics': animation_metrics,
             'repairToolSha256': digest(Path(__file__).read_bytes()), 'oldImmutableObjectsPreserved': True,
             'published': False}
    write_json(output / 'source-repair-receipt.json', proof)
    print(json.dumps({'catalogue': str(repaired_catalogue), 'profiles': str(output / 'profiles-repaired.json'),
                      'unchangedLevels': len(unchanged), 'newSourceImageSha256': proof['newSourceImageSha256']}))


if __name__ == '__main__':
    main()
