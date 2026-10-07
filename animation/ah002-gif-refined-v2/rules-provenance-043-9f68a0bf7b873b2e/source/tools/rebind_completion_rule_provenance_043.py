"""Stage immutable JSON bindings after restoring historical level43 rules.

All 120 GIFs and all repaired still pixels stay unchanged. This does not decode
or publish GIFs: the final publisher must independently run every existing gate.
Original authoring receipts remain honest records of their render-time inputs.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from build_content_release import canonical, digest, immutable_write
from delivery_variants import load_completion_sources, put_object, read_object
from repair_completion_source_043 import verify_art_only_change


def write_json(path, value):
    immutable_write(path, (json.dumps(value, indent=2) + '\n').encode())


def release(path):
    raw = path.read_bytes()
    if digest(raw) != path.stem:
        raise ValueError('Immutable release filename differs from bytes')
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-index', type=Path, required=True)
    parser.add_argument('--previous-candidate', type=Path, required=True)
    parser.add_argument('--source-repair', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    previous_index, previous_candidate, source, output = (
        value.resolve() for value in (args.previous_index, args.previous_candidate,
                                     args.source_repair, args.output))
    output.mkdir(parents=True, exist_ok=True)
    repair = json.loads((source / 'source-repair-receipt.json').read_bytes())
    corrected_path = Path(repair['repairedCataloguePath'])
    corrected = release(corrected_path)
    root = corrected_path.parent.parent
    sources = load_completion_sources(previous_index)
    prior_path = root / 'releases' / (sources['sourceCatalogueSha256'] + '.json')
    prior = release(prior_path)
    baseline_path = root / 'releases' / (repair['sourceCatalogueSha256'] + '.json')
    baseline = release(baseline_path)
    previous = release(previous_candidate)
    if (prior.get('deliveryContract') != 2 or corrected.get('deliveryContract') != 2
            or previous.get('deliveryContract') != 3
            or repair.get('authoritativeRulesUnchanged') is not True
            or set(sources['levels']) != set(range(1, 121))):
        raise ValueError('Expected the complete repaired set and corrected historical rules')
    candidate = copy.deepcopy(corrected)
    candidate['deliveryContract'] = 3
    index = {'schemaVersion': 1, 'sourceCatalogueSha256': corrected_path.stem, 'levels': {}}
    checks = []
    city_sizes = {}
    sizes = []
    source_delta = []
    for city in candidate['destinations']:
        old_city = next(row for row in prior['destinations'] if row['id'] == city['id'])
        old_candidate_city = next(row for row in previous['destinations'] if row['id'] == city['id'])
        original_city = next(row for row in baseline['destinations'] if row['id'] == city['id'])
        old_package = json.loads(read_object(root, old_city['package']))
        package = json.loads(read_object(root, city['package']))
        original_package = json.loads(read_object(root, original_city['package']))
        if old_candidate_city['package'] != old_city['package']:
            raise ValueError('Prior candidate city does not match its source')
        normalized = copy.deepcopy(package)
        normalized['levels'] = old_package['levels']
        if normalized != old_package:
            raise ValueError('Rule correction changed city artwork assets or metadata')
        for level_id in city['levelIds']:
            key = str(level_id)
            new_level = next(row for row in package['levels'] if row['levelId'] == level_id)
            old_level = next(row for row in old_package['levels'] if row['levelId'] == level_id)
            base_level = next(row for row in original_package['levels'] if row['levelId'] == level_id)
            rules_sha = verify_art_only_change(base_level, new_level)
            if level_id != 43 and new_level != old_level:
                raise ValueError('Unrelated level changed')
            normalized = copy.deepcopy(new_level)
            normalized['pieces'], normalized['geometry'] = old_level['pieces'], old_level['geometry']
            if normalized != old_level:
                raise ValueError('Metadata migration changed rendered art or unrelated fields')
            old_part = json.loads(read_object(root, old_city['delivery']['levels'][key]))
            new_part = json.loads(read_object(root, city['delivery']['levels'][key]))
            normalized = copy.deepcopy(new_part)
            normalized['levels'] = old_part['levels']
            if normalized != old_part or new_part['levels'] != [new_level]:
                raise ValueError('Metadata migration changed the delivered composition')
            old_complete = json.loads(read_object(root, old_candidate_city['delivery']['levels'][key]))
            animation = old_complete.pop('completionAnimation')
            provenance = old_complete.pop('completionProvenance')
            old_complete['deliveryContract'] = 2
            if old_complete != old_part:
                raise ValueError('Prior completion candidate differs from its source')
            row = sources['levels'][level_id]
            image_sha = new_part['assets'][new_level['image']]['sha256']
            raw = row['path'].read_bytes()
            gif_sha = digest(raw)
            expected = {'version': 1, 'levelId': level_id,
                        'sourceCatalogueSha256': prior_path.stem,
                        'sourceImageSha256': image_sha, 'gifSha256': gif_sha}
            if (provenance != expected or row['gifSha256'] != gif_sha
                    or row['sourceImageSha256'] != image_sha or len(raw) > 5_000_000
                    or animation['asset']['sha256'] != gif_sha
                    or read_object(root, animation['asset']) != raw):
                raise ValueError('Reused GIF or source binding differs')
            chunks = animation['asset'].get('chunks', [])
            if chunks and b''.join(read_object(root, chunk) for chunk in chunks) != raw:
                raise ValueError('Retained GIF chunk bytes differ')
            new_part['deliveryContract'] = 3
            new_part['completionAnimation'] = animation
            new_part['completionProvenance'] = dict(expected, sourceCatalogueSha256=corrected_path.stem)
            city['delivery']['levels'][key] = put_object(root, canonical(new_part), 'json', 'application/json')
            index['levels'][key] = {'levelId': level_id,
                                    'path': os.path.relpath(row['path'], output).replace('\\', '/'),
                                    'gifSha256': gif_sha, 'sourceImageSha256': image_sha}
            receipt_path = row['path'].with_suffix('.json')
            receipt = json.loads(receipt_path.read_bytes())
            if (receipt['conformance']['descriptor']['sha256'] != gif_sha
                    or receipt['sourceImageSha256'] != image_sha):
                raise ValueError('Original render receipt differs from the reused GIF')
            checks.append({'levelId': level_id, 'gifSha256': gif_sha,
                           'sourceImageSha256': image_sha, 'immutableRulesSha256': rules_sha,
                           'originalRenderReceiptPath': os.path.relpath(receipt_path, output).replace('\\', '/'),
                           'originalRenderReceiptSha256': digest(receipt_path.read_bytes()),
                           'renderedArtUnchanged': True, 'gifBytesUnchanged': True})
            sizes.append(len(raw))
            city_key = str((level_id - 1) // 20 + 1)
            city_sizes[city_key] = city_sizes.get(city_key, 0) + len(raw)
            if old_level != new_level:
                source_delta.append(level_id)
    if source_delta != [43] or len(checks) != 120:
        raise ValueError('Expected exactly one historical-rule restoration across120 unchanged GIFs')
    raw = canonical(candidate)
    candidate_path = root / 'releases' / (digest(raw) + '.json')
    immutable_write(candidate_path, raw)
    write_json(output / 'completion-index.json', index)
    write_json(output / 'completion-download-summary.json', {
        'count': len(sizes), 'totalBytes': sum(sizes), 'perCityBytes': city_sizes,
        'minimumBytes': min(sizes), 'meanBytes': sum(sizes)/len(sizes), 'maximumBytes': max(sizes),
        'hardCapPerGifBytes': 5_000_000})
    write_json(output / 'rules-provenance-migration.json', {
        'schemaVersion': 1,
        'reason': 'Restore immutable revision3 rule/detail provenance; current artwork measurements remain QA-only.',
        'previousIndexSha256': digest(previous_index.read_bytes()),
        'previousSourceCatalogueSha256': prior_path.stem,
        'newSourceCatalogueSha256': corrected_path.stem,
        'originalRulesCatalogueSha256': baseline_path.stem,
        'previousCandidateSha256': previous_candidate.stem,
        'candidateSha256': candidate_path.stem,
        'candidatePath': str(candidate_path),
        'newIndexSha256': digest((output/'completion-index.json').read_bytes()),
        'sourceRepairReceiptSha256': digest((source/'source-repair-receipt.json').read_bytes()),
        'currentArtworkDetailQA': repair['currentArtworkDetailQA'],
        'toolSha256': digest(Path(__file__).read_bytes()),
        'unchangedGifCount': len(checks), 'levels': checks,
        'priorReceiptsAndImmutableReleasesPreserved': True,
        'newAnimationFramesRendered': False,
        'validationScope': 'Object/chunk hashes, exact rules and art bindings. Final publisher must run strict GIF/native/still gates.',
        'published': False,
    })
    print(json.dumps({'sourceCatalogue': str(corrected_path), 'candidate': str(candidate_path),
                      'index': str(output/'completion-index.json'), 'unchangedGifCount': len(checks)}))


if __name__ == '__main__':
    main()
