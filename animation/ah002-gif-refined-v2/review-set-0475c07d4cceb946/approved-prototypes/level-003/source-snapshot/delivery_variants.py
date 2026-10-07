"""Immutable checked images, verified chunks and per-level rules (contracts 1/2/3).

Original city packages and PNGs remain available for older binaries and save validation.
This module only writes a candidate; publication still runs the existing content gates.
"""
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import json
from pathlib import Path
import re

from PIL import Image

from build_content_release import canonical, digest, immutable_write, MAX_OBJECT_BYTES

DELIVERY_CONTRACT = 2
GIF_DELIVERY_CONTRACT = 3
CHUNK_BYTES = 512 * 1024
MAX_LEVEL_BYTES = 1024 * 1024
MAX_READY_BYTES = 12 * 1024 * 1024
MAX_DECODED_BYTES = 64 * 1024 * 1024
OBJECT = re.compile(r"objects/([a-f0-9]{64})\.(json|png|webp|gif|bin)\Z")


def load_completion_sources(path):
    """Bound authoring receipts; relative GIF paths belong to this index."""
    path = Path(path)
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate completion GIF level ID")
            result[key] = value
        return result
    value = json.loads(path.read_bytes(), object_pairs_hook=unique_pairs)
    if (not isinstance(value, dict) or set(value) != {"schemaVersion", "sourceCatalogueSha256", "levels"}
            or type(value["schemaVersion"]) is not int or value["schemaVersion"] != 1
            or not isinstance(value["levels"], dict) or not value["levels"]
            or not re.fullmatch(r"[a-f0-9]{64}", str(value["sourceCatalogueSha256"]))):
        raise ValueError("Completion GIF sources require a bound authoring index")
    result = copy.deepcopy(value)
    result["levels"] = {}
    for key, receipt in value["levels"].items():
        if (not re.fullmatch(r"[1-9][0-9]*", key) or not isinstance(receipt, dict)
                or set(receipt) != {"levelId", "path", "gifSha256", "sourceImageSha256"}
                or type(receipt["levelId"]) is not int or receipt["levelId"] != int(key)
                or not isinstance(receipt["path"], str) or not receipt["path"]
                or any(not re.fullmatch(r"[a-f0-9]{64}", str(receipt[name])) for name in ("gifSha256", "sourceImageSha256"))):
            raise ValueError("Invalid completion GIF authoring receipt")
        source = Path(receipt["path"])
        result["levels"][int(key)] = dict(receipt, path=source if source.is_absolute() else path.parent / source)
    return result


def _completion_provenance(level_id, catalogue_sha, image_sha, gif_sha):
    return dict(version=1, levelId=level_id, sourceCatalogueSha256=catalogue_sha,
                sourceImageSha256=image_sha, gifSha256=gif_sha)


def _verified_provenance(root, part, destination, source_catalogues):
    value = part.get("completionProvenance")
    level = part["levels"][0]
    asset = part["completionAnimation"]["asset"]
    image_sha = part["assets"][level["image"]]["sha256"]
    if (not isinstance(value, dict) or type(value.get("version")) is not int or type(value.get("levelId")) is not int
            or not re.fullmatch(r"[a-f0-9]{64}", str(value.get("sourceCatalogueSha256")))
            or value != _completion_provenance(level["levelId"], value["sourceCatalogueSha256"], image_sha, asset["sha256"])):
        raise ValueError("Completion GIF provenance does not bind this level, still image and GIF")
    sha = value["sourceCatalogueSha256"]
    if sha not in source_catalogues:
        source = Path(root) / "releases" / (sha + ".json")
        with source.open("rb") as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024 or digest(raw) != sha:
            raise ValueError("Completion source catalogue integrity mismatch")
        original = json.loads(raw)
        if original.get("deliveryContract") != 2 or original.get("imagePolicy") != "composed-v1":
            raise ValueError("Completion source catalogue must retain delivery2 stills")
        source_catalogues[sha] = original
    previous = next((city for city in source_catalogues[sha]["destinations"] if city["id"] == destination["id"]), None)
    if previous is None or previous["package"] != destination["package"]:
        raise ValueError("Completion source city does not match this package")
    descriptor = previous["delivery"]["levels"].get(str(level["levelId"]))
    if descriptor is None:
        raise ValueError("Completion source level is absent")
    original_part = json.loads(read_object(root, descriptor))
    bound_stills = {key: item for key, item in part.items() if key not in ("completionAnimation", "completionProvenance")}
    bound_stills["deliveryContract"] = 2
    if original_part != bound_stills:
        raise ValueError("Completion provenance changed the original level or still descriptors")


def _completion_metadata(asset):
    return dict(version=1, asset=asset, frameCount=75, frameDelayMs=40, durationMs=3000, playCount=1)


def _verified_completion(root, value, results):
    from completion_gif import validate as validate_gif
    if not isinstance(value, dict) or set(value) != set(_completion_metadata({})):
        raise ValueError("Invalid completion GIF metadata")
    for key, expected in _completion_metadata({}).items():
        if key != "asset" and (type(value[key]) is not int or value[key] != expected):
            raise ValueError("Invalid completion GIF timing or version")
    asset = value["asset"]
    if not isinstance(asset, dict) or set(asset) - {"path", "sha256", "bytes", "mediaType", "width", "height", "chunks"}:
        raise ValueError("Invalid completion GIF descriptor")
    from completion_gif import MAX_BYTES
    if type(asset.get("bytes")) is not int or not 14 <= asset["bytes"] <= MAX_BYTES:
        raise ValueError("Completion GIF exceeds 5,000,000-byte budget")
    if any(type(asset.get(axis)) is not int or asset[axis] < 1 for axis in ("width", "height")):
        raise ValueError("Invalid completion GIF dimensions")
    if asset.get("mediaType") != "image/gif" or not str(asset.get("path", "")).endswith(".gif"):
        raise ValueError("Completion GIF media type mismatch")
    raw = read_object(root, asset)
    key = asset["sha256"]
    if key not in results:
        results[key] = validate_gif(raw)
    result = results[key]
    if {k: v for k, v in asset.items() if k != "chunks"} != result["descriptor"]:
        raise ValueError("Completion GIF descriptor differs from decoded file")
    chunks = asset.get("chunks", [])
    if not isinstance(chunks, list) or len(chunks) > 10 or (len(raw) > CHUNK_BYTES and not chunks):
        raise ValueError("Missing bounded completion GIF resume chunks")
    assembled = bytearray()
    for chunk in chunks:
        if (not isinstance(chunk, dict) or set(chunk) != {"path", "sha256", "bytes", "mediaType"}
                or type(chunk.get("bytes")) is not int or not 0 < chunk["bytes"] <= CHUNK_BYTES
                or chunk.get("mediaType") != "application/octet-stream" or not str(chunk.get("path", "")).endswith(".bin")):
            raise ValueError("Invalid completion GIF resume chunk")
        assembled.extend(read_object(root, chunk))
    if chunks and assembled != raw:
        raise ValueError("Completion GIF chunk assembly mismatch")
    return result


def with_completion_gifs(root, manifest, sources, *, report=None):
    """Add GIFs to a verified contract2 candidate without reencoding its stills."""
    from completion_gif import validate as validate_gif, MAX_BYTES
    if manifest.get("deliveryContract") != 2 or manifest.get("imagePolicy") != "composed-v1":
        raise ValueError("Completion GIFs require the unchanged composed-v1 delivery2 stills")
    expected = {int(level_id) for city in manifest["destinations"] for level_id in city["levelIds"]}
    source_sha = digest(canonical(manifest))
    if (not isinstance(sources, dict) or set(sources) != {"schemaVersion", "sourceCatalogueSha256", "levels"}
            or type(sources["schemaVersion"]) is not int or sources["schemaVersion"] != 1
            or sources["sourceCatalogueSha256"] != source_sha or not isinstance(sources["levels"], dict)
            or any(type(key) is not int for key in sources["levels"]) or set(sources["levels"]) != expected):
        raise ValueError("Completion GIF source map must cover every level exactly")
    validate(root, manifest)
    immutable_write(Path(root) / "releases" / (source_sha + ".json"), canonical(manifest))
    candidate = copy.deepcopy(manifest)
    candidate["deliveryContract"] = GIF_DELIVERY_CONTRACT
    cache = {}
    for destination in candidate["destinations"]:
        for key, package in list(destination["delivery"]["levels"].items()):
            part = json.loads(read_object(root, package))
            receipt = sources["levels"][int(key)]
            image_sha = part["assets"][part["levels"][0]["image"]]["sha256"]
            if (not isinstance(receipt, dict) or set(receipt) != {"levelId", "path", "gifSha256", "sourceImageSha256"}
                    or type(receipt["levelId"]) is not int or receipt["levelId"] != int(key)
                    or receipt["sourceImageSha256"] != image_sha
                    or not re.fullmatch(r"[a-f0-9]{64}", str(receipt["gifSha256"]))):
                raise ValueError("Completion GIF authoring receipt does not match this level")
            source = Path(receipt["path"]).resolve()
            if source not in cache:
                with source.open("rb") as stream:
                    raw = stream.read(MAX_BYTES + 1)
                checked = validate_gif(raw)
                asset = put_object(root, raw, "gif", "image/gif")
                asset.update(width=checked["descriptor"]["width"], height=checked["descriptor"]["height"])
                if len(raw) > CHUNK_BYTES:
                    asset["chunks"] = [put_object(root, raw[start:start + CHUNK_BYTES], "bin", "application/octet-stream")
                                       for start in range(0, len(raw), CHUNK_BYTES)]
                cache[source] = _completion_metadata(asset)
            if cache[source]["asset"]["sha256"] != receipt["gifSha256"]:
                raise ValueError("Completion GIF differs from its authoring receipt")
            part["deliveryContract"] = GIF_DELIVERY_CONTRACT
            part["completionAnimation"] = copy.deepcopy(cache[source])
            part["completionProvenance"] = _completion_provenance(int(key), source_sha, image_sha, receipt["gifSha256"])
            raw = canonical(part)
            if len(raw) > MAX_LEVEL_BYTES:
                raise ValueError("Per-level metadata budget exceeded")
            destination["delivery"]["levels"][key] = put_object(root, raw, "json", "application/json")
    raw = canonical(candidate)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Catalogue size outside client limit")
    # Do not expose a release pointer until all GIFs, stills and budgets pass.
    validate(root, candidate, report=report)
    path = Path(root) / "releases" / (digest(raw) + ".json")
    immutable_write(path, raw)
    return path


def read_object(root, item):
    match = OBJECT.fullmatch(item.get("path", ""))
    if not match or match[1] != item.get("sha256"):
        raise ValueError("Unsafe delivery object")
    if type(item.get("bytes")) is not int or not 0 < item["bytes"] <= MAX_OBJECT_BYTES:
        raise ValueError("Delivery object size outside budget")
    with (Path(root) / item["path"]).open("rb") as stream:
        raw = stream.read(item["bytes"] + 1)
    if len(raw) != item["bytes"] or digest(raw) != item["sha256"]:
        raise ValueError("Delivery object integrity mismatch")
    return raw


def put_object(root, raw, extension, media_type):
    if not 0 < len(raw) <= MAX_OBJECT_BYTES:
        raise ValueError("Delivery object size outside budget")
    sha = digest(raw)
    path = f"objects/{sha}.{extension}"
    immutable_write(Path(root) / path, raw)
    return {"path": path, "sha256": sha, "bytes": len(raw), "mediaType": media_type}


def image_variant(root, item, *, policy=None, protected=False):
    raw = read_object(root, item)
    with Image.open(io.BytesIO(raw)) as original:
        if original.format != "PNG" or original.size != (item["width"], item["height"]):
            raise ValueError("Invalid source image")
        if not all(0 < n <= 4096 for n in original.size):
            raise ValueError("Image dimensions outside decode budget")
        if policy is not None:
            from image_compression import POLICY, compress
            if policy != POLICY:
                raise ValueError("Unsupported image compression policy")
            encoded, extension, _ = compress(raw, protected=protected)
        else:
            output = io.BytesIO()
            original.save(output, format="WEBP", lossless=True, method=6, exact=True)
            encoded, extension = output.getvalue(), "webp"
            with Image.open(io.BytesIO(encoded)) as decoded:
                if original.convert("RGBA").tobytes() != decoded.convert("RGBA").tobytes():
                    raise ValueError("Lossless encoding changed pixels")
    # Some tiny art compresses better as PNG. Never increase delivery size.
    value = put_object(root, encoded, extension, "image/" + extension) if len(encoded) < len(raw) else copy.deepcopy(item)
    value.update(width=item["width"], height=item["height"])
    if value["bytes"] > CHUNK_BYTES:
        body = read_object(root, value)
        value["chunks"] = [put_object(root, body[start:start + CHUNK_BYTES], "bin", "application/octet-stream")
                           for start in range(0, len(body), CHUNK_BYTES)]
    return value


def level_sources(level):
    animation = level["paintedAnimation"]
    return [level["image"], animation["background"], *[p["source"] for p in animation["parts"]]]


def readiness_budget(raw, assets, completion=None):
    ready_bytes = len(raw) + sum({item["path"]: item["bytes"] for item in assets.values()}.values())
    decoded_bytes = sum({item["sha256"]: item["width"] * item["height"] * 4 for item in assets.values()}.values())
    additional_wire = 0
    if completion is not None:
        from completion_gif import budget_bytes, MAX_BYTES
        asset = completion["asset"]
        ready_bytes += asset["bytes"]
        decoded_bytes += budget_bytes(asset["width"], asset["height"], asset["bytes"])
        additional_wire = MAX_BYTES
    if ready_bytes > MAX_READY_BYTES + additional_wire or decoded_bytes > MAX_DECODED_BYTES:
        raise ValueError("Per-level readiness budget exceeded")
    return decoded_bytes


def protected_source(level, source):
    return (source in {p["source"] for p in level["paintedAnimation"]["parts"]}
            or source.endswith(("/flag.png", "/stamp.png")))


def animation_images(root, level, assets):
    from image_compression import decode, composite
    result = {source: decode(read_object(root, assets[source])) for source in level_sources(level)
              if assets[source].get("mediaType") != "image/composite"}
    if assets[level["image"]].get("mediaType") == "image/composite":
        result[level["image"]] = composite(level, result)
    return result


def composition_descriptor(level, assets, original):
    animation = level["paintedAnimation"]
    recipe = dict(version=1, background=assets[animation["background"]],
                  parts=[dict(asset=assets[p["source"]], rect=p["rect"]) for p in animation["parts"]])
    sha = digest(canonical(recipe))
    return dict(path="compositions/" + sha + ".rgba", sha256=sha, bytes=0, mediaType="image/composite",
                width=original["width"], height=original["height"], composition=recipe)


def build(root, manifest, workers=2, *, policy=None, report=None):
    if manifest.get("contentContract") != 3 or manifest.get("deliveryContract", 0) != 0:
        raise ValueError("Delivery variants require an original contract 3 catalogue")
    candidate = copy.deepcopy(manifest)
    candidate["deliveryContract"] = DELIVERY_CONTRACT if policy is not None else 1
    if policy is not None:
        from image_compression import POLICY
        if policy != POLICY:
            raise ValueError("Unsupported image compression policy")
        candidate["imagePolicy"] = policy
    packages = [json.loads(read_object(root, d["package"])) for d in manifest["destinations"]]
    unique = {item["sha256"]: item for p in packages for item in p["assets"].values()}
    if policy is not None:
        needed = {p["assets"][s]["sha256"] for p in packages for level in p["levels"]
                  for s in level_sources(level)[1:]}
        needed.update(p["presentation"][key]["sha256"] for p in packages for key in ("postcard", "flag", "stamp", "banner"))
        unique = {sha: item for sha, item in unique.items() if sha in needed}
    protected = {p["assets"][s]["sha256"] for p in packages for level in p["levels"]
                 for s in p["assets"] if protected_source(level, s)}
    with ThreadPoolExecutor(max_workers=max(1, min(int(workers), 4))) as pool:
        print(f"Encoding {len(unique)} unique images (policy={policy or 'lossless'})", flush=True)
        variants = dict(zip(unique, pool.map(lambda item: image_variant(root, item, policy=policy,
                             protected=item["sha256"] in protected), unique.values())))
    fallbacks = []
    if policy is not None:
        from image_compression import validate_animation
        # Independent encodes can differ at the transition/edge. Prefer exact art
        # for the affected level if the complete animation cannot pass the gate.
        for payload in packages:
            print(f"Checking animation quality: {payload['cityId']}", flush=True)
            for level in payload["levels"]:
                assets = {s: variants[item["sha256"]] for s, item in payload["assets"].items() if item["sha256"] in variants}
                assets[level["image"]] = composition_descriptor(level, assets, payload["assets"][level["image"]])
                try:
                    validate_animation(level, animation_images(root, level, payload["assets"]),
                                       animation_images(root, level, assets))
                except ValueError as error:
                    for source in (level["paintedAnimation"]["background"],):
                        old = payload["assets"][source]
                        variants[old["sha256"]] = image_variant(root, old)
                    fallbacks.append({"level": level["levelId"], "reason": str(error)})
    for destination, payload in zip(candidate["destinations"], packages):
        presentation = copy.deepcopy(payload["presentation"])
        for key in ("postcard", "flag", "stamp", "banner"):
            presentation[key] = variants[presentation[key]["sha256"]]
        levels = {}
        for level in payload["levels"]:
            assets = {s: variants[payload["assets"][s]["sha256"]] for s in level_sources(level)[1 if policy is not None else 0:]}
            if policy is not None:
                assets[level["image"]] = composition_descriptor(level, assets, payload["assets"][level["image"]])
            for key in ("postcard", "flag", "stamp", "banner"):
                assets[f"res://assets/art/cities/{destination['id']}/{key}.png"] = presentation[key]
            retained = {revision: [entry for entry in entries if entry["levelId"] == level["levelId"]]
                        for revision, entries in payload.get("retainedLayouts", {}).items()}
            part = dict(schemaVersion=2, deliveryContract=candidate["deliveryContract"], contentContract=3,
                        geometryRevision=payload["geometryRevision"], cityId=destination["id"],
                        levels=[level], assets=assets, presentation=presentation, retainedLayouts=retained)
            raw = canonical(part)
            if len(raw) > MAX_LEVEL_BYTES:
                raise ValueError("Per-level delivery budget exceeded")
            readiness_budget(raw, assets)
            levels[str(level["levelId"])] = put_object(root, raw, "json", "application/json")
        destination["delivery"] = {"levels": levels, "presentation": presentation}
    raw = canonical(candidate)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Catalogue size outside client limit")
    path = Path(root) / "releases" / (digest(raw) + ".json")
    immutable_write(path, raw)
    print("Validating complete candidate and download budgets", flush=True)
    validate(root, candidate, report=report)
    if report is not None:
        report["animation_lossless_fallbacks"] = fallbacks
    return path


def validate(root, manifest, *, report=None):
    contract = manifest.get("deliveryContract", 0)
    if type(contract) is not int or contract not in (0, 1, 2, 3):
        raise ValueError("Unsupported delivery capability")
    if contract == 0:
        if "imagePolicy" in manifest or any("delivery" in d for d in manifest["destinations"]):
            raise ValueError("Unadvertised delivery capability")
        return []
    policy = manifest.get("imagePolicy")
    if (policy is not None) != (contract in (2, 3)):
        raise ValueError("Compression policy requires delivery capability 2 or 3")
    if policy is not None:
        from image_compression import POLICY, validate_image, validate_animation, MAX_READY_BYTES as COMPRESSED_READY_BYTES, MAX_PUZZLE_BYTES, MAX_AVERAGE_BYTES
        if policy != POLICY:
            raise ValueError("Unsupported image compression policy")
    items = {}
    validated_pairs = set()
    measurements, animations, readiness = {}, {}, []
    delivered_images, metadata, still_metadata = {}, {}, {}
    completions, completion_levels, delivered_gifs, source_catalogues = {}, {}, {}, {}
    still_readiness, decoded_readiness = [], []
    from completion_gif import MAX_BYTES as MAX_GIF_BYTES
    for city_index, destination in enumerate(manifest["destinations"]):
        original = json.loads(read_object(root, destination["package"]))
        delivery = destination.get("delivery", {})
        if set(delivery.get("levels", {})) != set(map(str, destination["levelIds"])):
            raise ValueError("Missing or unexpected level partition")
        for level in original["levels"]:
            descriptor = delivery["levels"][str(level["levelId"])]
            raw = read_object(root, descriptor)
            if len(raw) > MAX_LEVEL_BYTES:
                raise ValueError("Per-level metadata budget exceeded")
            part = json.loads(raw)
            expected_retained = {r: [x for x in entries if x["levelId"] == level["levelId"]]
                                 for r, entries in original.get("retainedLayouts", {}).items()}
            if (part.get("schemaVersion") != 2 or part.get("deliveryContract") != contract
                    or part.get("contentContract") != 3 or part.get("geometryRevision") != original["geometryRevision"]
                    or part.get("cityId") != destination["id"] or part.get("levels") != [level]
                    or part.get("retainedLayouts") != expected_retained
                    or part.get("presentation") != delivery.get("presentation")):
                raise ValueError("Partition changed gameplay or saved layouts")
            completion = part.get("completionAnimation")
            if contract == 3:
                _verified_completion(root, completion, completions)
                _verified_provenance(root, part, destination, source_catalogues)
                asset = completion["asset"]
                if asset["path"] in items and items[asset["path"]] != asset:
                    raise ValueError("Inconsistent shared completion GIF descriptor")
                items[asset["path"]] = asset
                items.update((chunk["path"], chunk) for chunk in asset.get("chunks", []))
                delivered_gifs[asset["sha256"]] = asset["bytes"]
                completion_levels[str(level["levelId"])] = asset["sha256"]
            elif "completionAnimation" in part or "completionProvenance" in part:
                raise ValueError("Unadvertised completion GIF capability")
            sources = set(level_sources(level)) | {f"res://assets/art/cities/{destination['id']}/{k}.png"
                                                  for k in ("postcard", "flag", "stamp", "banner")}
            if set(part.get("assets", {})) != sources:
                raise ValueError("Partition asset closure mismatch")
            for key in ("country", "fact", "source"):
                if part["presentation"].get(key) != original["presentation"].get(key):
                    raise ValueError("Presentation text changed")
            for key in ("postcard", "flag", "stamp", "banner"):
                if part["assets"][f"res://assets/art/cities/{destination['id']}/{key}.png"] != part["presentation"][key]:
                    raise ValueError("Presentation alias mismatch")
            screen_assets = dict(part["assets"])
            # AH002: after the native first-three-city exception, the previous
            # arrival painting is also retained behind the current screen.
            if city_index >= 4:
                previous = manifest["destinations"][city_index-1]
                screen_assets["previous_arrival"] = previous["delivery"]["presentation"]["postcard"]
            still_raw = canonical({key: value for key, value in part.items() if key not in ("completionAnimation", "completionProvenance")}) if completion else raw
            readiness_budget(still_raw, screen_assets)
            decoded_readiness.append(readiness_budget(raw, screen_assets, completion))
            ready = len(still_raw) + sum({v["path"]: v["bytes"] for v in screen_assets.values()}.values())
            if policy is not None and ready > COMPRESSED_READY_BYTES:
                raise ValueError("Compressed per-level readiness budget exceeded")
            puzzle_bytes = len(still_raw) + sum({part["assets"][s]["path"]:part["assets"][s]["bytes"] for s in level_sources(level)}.values())
            if policy is not None and puzzle_bytes > MAX_PUZZLE_BYTES:
                raise ValueError("Compressed puzzle readiness budget exceeded")
            still_readiness.append(ready)
            if completion:
                addition = completion["asset"]["bytes"] + len(raw) - len(still_raw)
                if ready + addition > COMPRESSED_READY_BYTES + MAX_GIF_BYTES:
                    raise ValueError("GIF combined screen readiness budget exceeded")
                if puzzle_bytes + addition > MAX_PUZZLE_BYTES + MAX_GIF_BYTES:
                    raise ValueError("GIF combined puzzle readiness budget exceeded")
                ready += addition
            readiness.append(ready)
            metadata[descriptor["sha256"]] = len(raw)
            still_metadata[descriptor["sha256"]] = len(still_raw)
            items[descriptor["path"]] = descriptor
            for source, item in part["assets"].items():
                old = original["assets"][source]
                if item["width"] != old["width"] or item["height"] != old["height"]:
                    raise ValueError("Image geometry changed")
                if item.get("mediaType") == "image/composite":
                    if policy is None or source != level["image"] or item != composition_descriptor(level, part["assets"], old):
                        raise ValueError("Invalid puzzle composition")
                    continue
                if policy is not None and source == level["image"]:
                    raise ValueError("Compressed puzzle must reuse its animation layers")
                if item["path"] in items and item != items[item["path"]]:
                    raise ValueError("Inconsistent shared image descriptor")
                protected = protected_source(level, source)
                pair = (old["sha256"], item["sha256"], protected)
                if pair not in validated_pairs:
                    body = read_object(root, item)
                    with Image.open(io.BytesIO(body)) as image, Image.open(io.BytesIO(read_object(root, old))) as master:
                        expected_format = {"image/png": "PNG", "image/webp": "WEBP"}.get(item.get("mediaType"))
                        if image.size != (item["width"],item["height"]) or image.size != master.size or image.format != expected_format:
                            raise ValueError("Delivery image changed pixels or format")
                        if policy is None:
                            if image.convert("RGBA").tobytes() != master.convert("RGBA").tobytes():
                                raise ValueError("Delivery image changed pixels or format")
                        else:
                            if len(body) > old["bytes"]:
                                raise ValueError("Compression increased delivery size")
                            metrics = validate_image(master, image, protected=protected)
                            measurements[old["sha256"]] = dict(source_bytes=old["bytes"], bytes=len(body),
                                delivered_sha256=item["sha256"], path=item["path"],
                                rgba_sha256=digest(image.convert("RGBA").tobytes()), protected=protected, **metrics)
                    validated_pairs.add(pair)
                if item["path"] not in items:
                    body = read_object(root, item)
                    chunks = item.get("chunks", [])
                    if len(chunks) > 64 or (len(body) > CHUNK_BYTES and not chunks):
                        raise ValueError("Missing bounded resume chunks")
                    if chunks:
                        if any(c["bytes"] > CHUNK_BYTES or not c["path"].endswith(".bin") for c in chunks):
                            raise ValueError("Invalid resume chunk")
                        if b"".join(read_object(root, c) for c in chunks) != body:
                            raise ValueError("Chunk assembly mismatch")
                        items.update((c["path"], c) for c in chunks)
                    items[item["path"]] = item
                delivered_images[item["sha256"]] = item["bytes"]
            if policy is not None:
                originals = animation_images(root, level, original["assets"])
                delivered = animation_images(root, level, part["assets"])
                validate_image(originals[level["image"]], delivered[level["image"]])
                animations[str(level["levelId"])] = validate_animation(level, originals, delivered)
    still_unique_bytes = sum(delivered_images.values()) + sum(still_metadata.values())
    unique_bytes = sum(delivered_images.values()) + sum(metadata.values()) + sum(delivered_gifs.values())
    if policy is not None and still_unique_bytes > MAX_AVERAGE_BYTES * len(readiness):
        raise ValueError("Compressed catalogue average budget exceeded")
    if contract == 3 and unique_bytes > (MAX_AVERAGE_BYTES + MAX_GIF_BYTES) * len(readiness):
        raise ValueError("GIF combined catalogue average budget exceeded")
    if report is not None:
        report.update(policy=policy, images=measurements, animations=animations,
                      unique_image_bytes=sum(delivered_images.values()), metadata_bytes=sum(metadata.values()),
                      unique_payload_bytes=unique_bytes, levels=len(readiness), max_ready_bytes=max(readiness, default=0),
                      max_still_ready_bytes=max(still_readiness, default=0), max_decoded_bytes=max(decoded_readiness, default=0))
        if contract == 3:
            report.update(completion_gifs=completions, completion_levels=completion_levels,
                          unique_gif_bytes=sum(delivered_gifs.values()), still_payload_bytes=still_unique_bytes,
                          completion_source_catalogues=sorted(source_catalogues))
    return list(items.values())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--lossless", action="store_true", help="Reproduce the original exact-pixel delivery format")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--completion-gifs", type=Path, help="Bound authoring index for immutable delivery3 completion GIFs")
    args = parser.parse_args()
    from image_compression import POLICY
    report = {}
    source = json.loads(args.manifest.read_bytes())
    root = args.manifest.parent.parent
    if args.completion_gifs and args.lossless:
        parser.error("Completion GIF delivery preserves composed-v1 stills; --lossless is a retained format")
    if args.completion_gifs and source.get("deliveryContract") == 2:
        path = args.manifest
    else:
        path = build(root, source, args.workers, policy=None if args.lossless else POLICY, report=report)
    if args.completion_gifs:
        path = with_completion_gifs(root, json.loads(path.read_bytes()), load_completion_sources(args.completion_gifs), report=report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(dict(manifest_sha256=path.stem, **report), indent=2) + "\n")
    print(path)
