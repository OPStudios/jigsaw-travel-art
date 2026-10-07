"""Bind119 unchanged GIFs and repaired43 to a new immutable source catalogue.

Writes a new index and migration proof; prior GIFs, receipts and indexes stay intact.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from build_content_release import digest, immutable_write
from delivery_variants import read_object


def write_json(path, data):
    immutable_write(path, (json.dumps(data, indent=2) + '\n').encode())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous-set', type=Path, required=True)
    p.add_argument('--source-repair', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    previous, source, output = (v.resolve() for v in (args.previous_set, args.source_repair, args.output))
    repair = json.loads((source / 'source-repair-receipt.json').read_bytes())
    catalogue = Path(repair['repairedCataloguePath'])
    root = catalogue.parent.parent
    old_catalogue = root / 'releases' / (repair['sourceCatalogueSha256'] + '.json')
    before_manifest = json.loads(old_catalogue.read_bytes())
    after_manifest = json.loads(catalogue.read_bytes())
    prior_index_raw = (previous / 'index.json').read_bytes()
    prior = json.loads(prior_index_raw)
    if prior['sourceCatalogueSha256'] != digest(old_catalogue.read_bytes()):
        raise ValueError('Previous index is not bound to the inspected source catalogue')
    if digest(catalogue.read_bytes()) != repair['repairedSourceCatalogueSha256']:
        raise ValueError('Repaired catalogue identity changed')
    if set(prior['levels']) != {str(n) for n in range(1, 121)}:
        raise ValueError('Expected a complete120-level previous index')
    current = {'schemaVersion': 1, 'sourceCatalogueSha256': digest(catalogue.read_bytes()), 'levels': {}}
    evidence = []
    sizes = []
    city_totals = {}
    repaired = json.loads((output / 'level-043.json').read_bytes())
    for level in range(1, 121):
        key = str(level)
        prior_row = prior['levels'][key]
        prior_path = (previous / prior_row['path']).resolve()
        if digest(prior_path.read_bytes()) != prior_row['gifSha256']:
            raise ValueError('Previous GIF changed: ' + key)
        old_city = next(c for c in before_manifest['destinations'] if level in c['levelIds'])
        new_city = next(c for c in after_manifest['destinations'] if level in c['levelIds'])
        old_descriptor = old_city['delivery']['levels'][key]
        new_descriptor = new_city['delivery']['levels'][key]
        old_part = json.loads(read_object(root, old_descriptor))
        new_part = json.loads(read_object(root, new_descriptor))
        old_image = old_part['assets'][old_part['levels'][0]['image']]['sha256']
        new_image = new_part['assets'][new_part['levels'][0]['image']]['sha256']
        if old_image != prior_row['sourceImageSha256']:
            raise ValueError('Previous GIF composition binding differs: ' + key)
        if level != 43:
            if old_descriptor != new_descriptor or old_part != new_part or old_image != new_image:
                raise ValueError('Unchanged GIF would be rebound to different artwork: ' + key)
            path, gif_sha = prior_path, prior_row['gifSha256']
            original_receipt = previous / f'level-{level:03d}.json'
            evidence.append({'levelId': level, 'gifSha256': gif_sha, 'sourceImageSha256': new_image,
                             'levelPackageSha256': new_descriptor['sha256'], 'stillAndLevelMetadataIdentical': True,
                             'originalReceiptPath': os.path.relpath(original_receipt, output).replace('\\', '/'),
                             'originalReceiptSha256': digest(original_receipt.read_bytes())})
        else:
            path = output / 'level-043.gif'
            gif_sha = digest(path.read_bytes())
            if (repaired['sourceCatalogueSha256'] != current['sourceCatalogueSha256']
                    or repaired['sourceImageSha256'] != new_image
                    or repaired['conformance']['descriptor']['sha256'] != gif_sha
                    or repaired.get('openVisualDefects')):
                raise ValueError('The repaired GIF is not bound to its repaired still')
        current['levels'][key] = {'levelId': level, 'path': os.path.relpath(path, output).replace('\\', '/'),
                                  'gifSha256': gif_sha, 'sourceImageSha256': new_image}
        size = path.stat().st_size
        if size > 5_000_000:
            raise ValueError('GIF budget exceeded: ' + key)
        sizes.append(size)
        city = str((level - 1) // 20 + 1)
        city_totals[city] = city_totals.get(city, 0) + size
    index_path = output / 'completion-index.json'
    write_json(index_path, current)
    proof = {'schemaVersion': 1, 'change': 'Coordinated level43 source and GIF repair only',
             'previousIndexSha256': digest(prior_index_raw), 'newIndexSha256': digest(index_path.read_bytes()),
             'previousCatalogueSha256': digest(old_catalogue.read_bytes()),
             'newCatalogueSha256': current['sourceCatalogueSha256'],
             'unchangedGifCount': len(evidence), 'unchanged': evidence,
             'repairedLevel': current['levels']['43'], 'previousAll120GifBytesPreserved': True,
             'priorAuthoringReceiptsUnmodified': True, 'rebindToolSha256': digest(Path(__file__).read_bytes()),
             'published': False}
    write_json(output / 'catalogue-rebinding.json', proof)
    write_json(output / 'completion-download-summary.json',
               {'count': len(sizes), 'totalBytes': sum(sizes), 'perCityBytes': city_totals,
                'minimumBytes': min(sizes), 'meanBytes': sum(sizes) / len(sizes), 'maximumBytes': max(sizes),
                'hardCapPerGifBytes': 5_000_000})
    print(json.dumps({'index': str(index_path), 'indexSha256': proof['newIndexSha256'],
                      'unchangedGifCount': len(evidence), 'repairedGifSha256': current['levels']['43']['gifSha256']}))


if __name__ == '__main__':
    main()
