"""Measure a literal AH002 GIF against the unchanged compressed-delivery gates.

This is the original full-resolution feasibility measurement, not a content
publisher. The subsequent actual-GIF requirement caps each file at 5,000,000
bytes; this historical prototype does not meet that cap.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from pathlib import Path
from PIL import Image
from image_compression import quality, acceptable, MAX_PUZZLE_BYTES
SIZE=(1128,1350)

def verified(root, item):
    path=root/item["path"]
    raw=path.read_bytes()
    if len(raw)!=item["bytes"] or hashlib.sha256(raw).hexdigest()!=item["sha256"]:
        raise ValueError("Immutable content identity mismatch: "+str(path))
    return path

def measure(catalogue, level_id, output):
    raw=catalogue.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=catalogue.stem:
        raise ValueError("Catalogue filename must equal its SHA256")
    catalog=json.loads(raw); root=catalogue.parent.parent
    if catalog.get("deliveryContract")!=2 or catalog.get("imagePolicy")!="composed-v1":
        raise ValueError("Expected the published compressed layer contract")
    payload=None
    for city in catalog["destinations"]:
        item=city["delivery"]["levels"].get(str(level_id))
        if item:
            payload=json.loads(verified(root,item).read_bytes()); break
    if payload is None: raise ValueError("Level not found")
    level=payload["levels"][0]; animation=level["paintedAnimation"]
    if level["levelId"]!=level_id or len(animation["parts"])!=5:
        raise ValueError("Expected exactly five authored parts")
    background=Image.open(verified(root,payload["assets"][animation["background"]])).convert("RGBA").resize(SIZE,Image.Resampling.LANCZOS)
    parts=[]
    for part in animation["parts"]:
        image=Image.open(verified(root,payload["assets"][part["source"]])).convert("RGBA")
        image=image.resize((round(part["rect"][2]*SIZE[0]),round(part["rect"][3]*SIZE[1])),Image.Resampling.LANCZOS)
        parts.append((part,image))
    output.mkdir(parents=True,exist_ok=True)
    frames=[]; metrics={}; started=time.monotonic()
    for index in range(75):
        phase=index/74; zoom=1+.05*phase*phase*(3-2*phase)
        image=background.copy()
        for part,cutout in parts:
            dx=part["axis"][0]*part["amplitude"]*3*math.sin(phase*math.tau)/zoom
            dy=part["axis"][1]*part["amplitude"]*3*math.sin(phase*math.tau)/zoom
            at=(round(part["rect"][0]*SIZE[0]+dx),round(part["rect"][1]*SIZE[1]+dy))
            image.alpha_composite(cutout,at)
        image=image.transform(SIZE,Image.Transform.AFFINE,(1/zoom,0,SIZE[0]/2*(1-1/zoom),0,1/zoom,SIZE[1]/2*(1-1/zoom)),Image.Resampling.BICUBIC).convert("RGB")
        quantized=image.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.FLOYDSTEINBERG)
        if index in (0,19,37,56,74):
            values=quality(image,quantized)
            metrics[str(index)]={**values,"passesComposedV1":acceptable(values)}
        # WEBP sources may carry loop metadata: GIF must not inherit it.
        quantized.info.clear(); frames.append(quantized)
    path=output/("level-%03d-completion.gif"%level_id)
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=40,optimize=True,disposal=1)
    with Image.open(path) as image:
        delays=[]
        for index in range(image.n_frames):
            image.seek(index);delays.append(image.info.get("duration"))
        verification=dict(dimensions=list(image.size),frames=image.n_frames,delaysMs=sorted(set(delays)),durationMs=sum(delays),loop=image.info.get("loop","not present: play once"))
    if verification!={"dimensions":[1128,1350],"frames":75,"delaysMs":[40],"durationMs":3000,"loop":"not present: play once"}:
        raise ValueError("GIF does not meet exact frame/timing specification")
    result=dict(prototypeLevel=level_id,catalogueSha256=catalogue.stem,gifBytes=path.stat().st_size,gifSha256=hashlib.sha256(path.read_bytes()).hexdigest(),generationSeconds=round(time.monotonic()-started,2),verification=verification,paletteQualityAgainstDeliveredLayers=metrics,twoDecodedRGBAFramesBytes=SIZE[0]*SIZE[1]*4*2,all75DecodedRGBAFramesBytes=SIZE[0]*SIZE[1]*4*75,composedV1PuzzleLimitBytes=MAX_PUZZLE_BYTES)
    (output/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue",type=Path)
    parser.add_argument("--level",type=int,default=1)
    parser.add_argument("--output",type=Path,default=Path("reports/ah002/gif-feasibility"))
    args=parser.parse_args()
    print(json.dumps(measure(args.catalogue,args.level,args.output),indent=2))
