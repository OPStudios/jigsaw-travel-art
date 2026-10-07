"""Bounded refined GIF authoring; immutable source snapshots and no publication."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, math, subprocess, tempfile, time, sys, shutil
from pathlib import Path
from PIL import Image, __version__ as PILLOW_VERSION
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parent
sys.path.insert(0,str(TOOLS/"prototypes"/"completion_gif"))
from encode_sample import source_animation, read_source, SIZE
sys.path.insert(0,str(HERE))
from actions import smooth
from rigs import prepare
from completion_gif import validate_file
from delivery_variants import composition_descriptor
from image_compression import quality


def sha(raw):return hashlib.sha256(raw).hexdigest()


def camera_pivot(profile):
    pivot=profile.get('cameraPivotPx',[SIZE[0]/2,SIZE[1]/2])
    if not isinstance(pivot,list) or len(pivot)!=2 or any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=SIZE[a] for a,v in enumerate(pivot)):
        raise ValueError('Camera pivot must be two finite scene coordinates')
    return pivot


def encode_level(job):
    level_id,settings=job;start=time.monotonic()
    assert_frozen(settings)
    catalogue=Path(settings['catalogue']);art=Path(settings['art']);out=Path(settings['out']);optimizer=Path(settings['optimizer'])
    profile=settings['profiles']['levels'][str(level_id)]
    pivot_x,pivot_y=camera_pivot(profile)
    if profile.get('levelId')!=level_id or len(profile.get('parts',[]))!=5:raise ValueError('Motion profile must bind exactly five parts to this level')
    payload,root,records,catalogue_sha=source_animation(catalogue,level_id);level=payload['levels'][0]
    still=payload['assets'][level['image']]
    if still!=composition_descriptor(level,payload['assets'],still):raise ValueError('Invalid source composition identity')
    dest=out/f'level-{level_id:03d}.gif';receipt_path=out/f'level-{level_id:03d}.json'
    if dest.exists() or receipt_path.exists():
        if not(dest.exists() and receipt_path.exists()):raise ValueError('Partial previous output; choose a clean authoring directory')
        previous=json.loads(receipt_path.read_text())
        if previous.get('levelId')!=level_id or previous.get('sourceCatalogueSha256')!=catalogue_sha or previous.get('sourceImageSha256')!=still['sha256']:raise ValueError('Existing output uses another source level, catalogue or composition')
        if previous['profileSha256']!=sha(json.dumps(profile,sort_keys=True).encode()):raise ValueError('Existing output uses another motion profile')
        checked=validate_file(dest)
        if checked['descriptor']['sha256']!=previous['conformance']['descriptor']['sha256']:raise ValueError('Existing GIF identity differs')
        return {'levelId':level_id,'reused':True,'bytes':dest.stat().st_size,'seconds':round(time.monotonic()-start,2)}
    if profile.get('reusePrototype'):
        return reuse_prototype(level_id,settings,profile,still,catalogue_sha,start)
    spec_path=art/profile['authoring'];spec_raw=spec_path.read_bytes();spec=json.loads(spec_raw)
    record=next(row for row in settings['profiles']['sourceAuthoring'] if row['path']==profile['authoring'])
    if sha(spec_raw)!=record['sha256']:raise ValueError('Source authoring metadata changed')
    if spec['levelId']!=level_id:raise ValueError('Source authoring belongs to another level')
    animation=level['paintedAnimation'];images=[]
    if len(animation['parts'])!=5 or len(spec['parts'])!=5:raise ValueError('Source animation and authoring must contain exactly five painted parts')
    with Image.open(read_source(root,payload['assets'][animation['background']],records)) as source:
        background=source.convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
    for part,authored,physical in zip(animation['parts'],spec['parts'],profile['parts']):
        if authored['sha256']!=physical['sourceSha256'] or authored['sha256'][:12] not in part['source'] or authored['rect']!=part['rect']:raise ValueError('Wrong scene part binding')
        master=art/'scenes/ah001-v1-verified'/authored['source']
        if sha(master.read_bytes())!=authored['sha256']:raise ValueError('Original painted part changed')
        with Image.open(read_source(root,payload['assets'][part['source']],records)) as source:
            image=source.convert('RGBA').resize((round(part['rect'][2]*SIZE[0]),round(part['rect'][3]*SIZE[1])),Image.Resampling.LANCZOS)
        original_size=Image.open(master).size
        painted,actor,offset,metadata=prepare(image,physical,original_size)
        mask_records=[]
        if 'anatomicalMasks' in metadata:
            mask_dir=out/f'level-{level_id:03d}-masks';mask_dir.mkdir(exist_ok=True)
            for name,mask in metadata['anatomicalMasks'].items():
                mask_path=mask_dir/f'part-{physical["part"]}-{name}.png';mask.save(mask_path)
                mask_records.append({'path':mask_path.relative_to(out).as_posix(),'sha256':sha(mask_path.read_bytes())})
            source_path=mask_dir/f'part-{physical["part"]}-source.png';painted.save(source_path)
            mask_records.append({'path':source_path.relative_to(out).as_posix(),'sha256':sha(source_path.read_bytes())})
        images.append((part,physical,painted,actor,offset,mask_records))
    frames=[];proof=[set() for _ in images];endpoints=[[] for _ in images];clipping=[]
    for index in range(75):
        phase=index/74;zoom=1+.05*smooth(phase);image=background.copy()
        for part_index,(part,physical,cutout,actor,offset,masks) in enumerate(images):
            painted=actor.frame(index*.04) if actor else cutout
            pose_hash=sha(painted.tobytes());proof[part_index].add(pose_hash)
            if index in [0,74]:endpoints[part_index].append(pose_hash)
            x,y=round(part['rect'][0]*SIZE[0])+offset[0],round(part['rect'][1]*SIZE[1])+offset[1]
            box=painted.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox()
            if box:
                left=(x+box[0]-pivot_x)*zoom+pivot_x;right=(x+box[2]-pivot_x)*zoom+pivot_x
                top=(y+box[1]-pivot_y)*zoom+pivot_y;bottom=(y+box[3]-pivot_y)*zoom+pivot_y
                if min(left,top,SIZE[0]-right,SIZE[1]-bottom)<0:clipping.append((index,part_index+1))
            image.alpha_composite(painted,(x,y))
        image=image.transform(SIZE,Image.Transform.AFFINE,(1/zoom,0,pivot_x*(1-1/zoom),0,1/zoom,pivot_y*(1-1/zoom)),Image.Resampling.BICUBIC).convert('RGB')
        image.info.clear();frames.append(image.resize((376,450),Image.Resampling.LANCZOS))
    if clipping:raise ValueError('Visible painted part clips: '+str(clipping[:8]))
    for item,poses in zip(images,proof):
        if item[1]['action']=='fixed_solid' and len(poses)!=1:raise ValueError('A designated fixed solid moved')
    if all(len(poses)==1 for poses in proof):raise ValueError('This scene has no local action; needs explicit art-direction review')
    attempts=[]
    with tempfile.TemporaryDirectory(prefix=f'gif-{level_id:03d}-',dir=out) as temp:
        source=Path(temp)/'palette.gif';candidate=Path(temp)/'optimized.gif'
        accepted=False
        for width in [376,352,320]:
            height=round(width*1350/1128)
            resized=frames if width==376 else [frame.resize((width,height),Image.Resampling.LANCZOS) for frame in frames]
            training=Image.new('RGB',(width*5,height))
            for column,index in enumerate([0,19,37,56,74]):training.paste(resized[index],(column*width,0))
            palette=training.quantize(colors=255,method=Image.Quantize.MEDIANCUT)
            quantized=[frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in resized]
            for frame in quantized:frame.info.clear()
            quantized[0].save(source,save_all=True,append_images=quantized[1:],duration=40,optimize=True,disposal=1,interlace=False,palette=palette.getpalette())
            # Preserve rich colors and all75 frames. User preference is a
            # modest resolution reduction instead of visible lossy sky grain.
            for lossy in [0,10,20]:
                options=['-O3','--no-interlace','--no-loopcount']+([f'--lossy={lossy}'] if lossy else [])
                subprocess.run([str(optimizer),*options,str(source),'-o',str(candidate)],check=True,capture_output=True,timeout=120)
                attempts.append({'width':width,'height':height,'colors':255,'lossy':lossy,'bytes':candidate.stat().st_size})
                if candidate.stat().st_size<=5_000_000:
                    accepted=True;break
            if accepted:break
        if not accepted:raise ValueError('No allowed255-color75-frame encoding fits5MB with restrained loss; scene needs review')
        conformance=validate_file(candidate)
        decoded=[];advisory={}
        with Image.open(candidate) as gif:
            for index in [0,19,32,37,55,74]:
                gif.seek(index);decoded_image=gif.convert('RGB');decoded.append((index,decoded_image.copy()))
                if index in [0,19,37,74]:advisory[str(index)]=quality(frames[index],decoded_image.resize((376,450),Image.Resampling.BILINEAR))
        dest.write_bytes(candidate.read_bytes())
    for index,image in decoded:image.save(out/f'level-{level_id:03d}-frame-{index:02d}.png')
    assert_frozen(settings)
    row=dict(levelId=level_id,sourceCatalogueSha256=catalogue_sha,sourceImageSha256=still['sha256'],
             profileSha256=sha(json.dumps(profile,sort_keys=True).encode()),sourceAuthoringSha256=sha(spec_raw),
             verifiedSources=records,motionProfiles=profile['parts'],uniquePartPoses=[len(s) for s in proof],
             mandatoryAllPartsMotion=False,forcedReturnToFirstPose=False,clippedFrames=0,
             sourceSnapshot=settings['sourceSnapshot'],sourceSnapshotSha256=settings['sourceSnapshotSha256'],
             masks=[mask for item in images for mask in item[5]],
             openVisualDefects=profile.get('openVisualDefects',[]),cameraPivotPx=[pivot_x,pivot_y],encodingAttempts=attempts,
             encoder={'pillow':PILLOW_VERSION,'gifsicle':'1.93','gifsicleSha256':settings['optimizerSha256']},
             advisoryQuality=advisory,conformance=conformance,published=False,seconds=round(time.monotonic()-start,2))
    receipt_path.write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
    return {'levelId':level_id,'bytes':dest.stat().st_size,'width':width,'lossy':lossy,'seconds':row['seconds']}


def freeze_sources(settings,profile_path):
    """A content-addressed capsule prevents later source/profile edits rewriting history."""
    source_paths=[*sorted(HERE.glob('*.py')),TOOLS/'prototypes/completion_gif/encode_sample.py',
                  *[TOOLS/name for name in ['completion_gif.py','measure_completion_gif.py','delivery_variants.py','image_compression.py']]]
    inputs=[profile_path,Path(settings['catalogue']),Path(settings['optimizer'])]
    inputs += [Path(row['path']) for row in settings['profiles'].get('reviewSources',[])]
    records=[{'kind':'source','path':p.relative_to(TOOLS).as_posix(),'name':p.name,'sha256':sha(p.read_bytes())} for p in source_paths]
    records += [{'kind':'input','path':str(p),'name':('profiles.json' if p==profile_path else p.name),'sha256':sha(p.read_bytes())} for p in inputs]
    manifest={'schemaVersion':1,'files':records,'approvedMethodReferenceSha256':'1542f4938ad508fd465a3d4b5c81a38a0db92259a550b909c65de080fb1bf45d'}
    raw=(json.dumps(manifest,indent=2)+'\n').encode();digest=sha(raw)
    folder=Path(settings['out'])/'source-snapshots'/digest;folder.mkdir(parents=True,exist_ok=True)
    for path,record in zip(source_paths+inputs,records):
        # Preserve source and JSON input bytes. The external encoder binary is
        # identified by its exact SHA/version rather than copying an executable.
        if path==Path(settings['optimizer']):continue
        target=folder/record['name']
        if target.exists() and target.read_bytes()!=path.read_bytes():raise ValueError('Snapshot collision')
        if not target.exists():target.write_bytes(path.read_bytes())
    (folder/'manifest.json').write_bytes(raw)
    settings['frozenInputs']={str(p):sha(p.read_bytes()) for p in source_paths+inputs}
    settings['sourceSnapshot']=f'source-snapshots/{digest}/manifest.json';settings['sourceSnapshotSha256']=digest


def assert_frozen(settings):
    for path,digest in settings['frozenInputs'].items():
        if sha(Path(path).read_bytes())!=digest:raise ValueError('Frozen authoring source/input changed: '+path)


def reuse_prototype(level_id,settings,profile,still,catalogue_sha,start):
    prototype=Path(settings['prototypeRoot']);out=Path(settings['out']);stem=f'level-{level_id:03d}'
    source=prototype/(stem+'.gif');original_receipt=prototype/(stem+'.json')
    validated=validate_file(source);receipt=json.loads(original_receipt.read_text())
    if validated['descriptor']['sha256']!=profile['expectedGifSha256']:raise ValueError('Approved prototype bytes changed')
    if receipt['sourceCatalogueSha256']!=catalogue_sha or receipt['sourceImageSha256']!=still['sha256']:raise ValueError('Approved prototype source mismatch')
    if validated!=receipt['conformance']:raise ValueError('Prototype conformance receipt mismatch')
    destination=out/(stem+'.gif');destination.write_bytes(source.read_bytes())
    for frame in [0,19,32,37,55,74]:
        shutil.copyfile(prototype/f'{stem}-frame-{frame:02d}.png',out/f'{stem}-frame-{frame:02d}.png')
    archive=out/'approved-prototypes'/stem;archive.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(original_receipt,archive/'original-receipt.json')
    frozen_manifest=prototype/receipt['sourceSnapshot']
    if sha(frozen_manifest.read_bytes())!=receipt['sourceSnapshotManifestSha256']:raise ValueError('Approved prototype source snapshot changed')
    frozen=json.loads(frozen_manifest.read_text())
    archived_manifest=archive/receipt['sourceSnapshot'];archived_manifest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(frozen_manifest,archived_manifest)
    for item in frozen['files']:
        exact=prototype/item['snapshot']
        if sha(exact.read_bytes())!=item['sha256']:raise ValueError('Approved prototype source file changed')
        target=archive/item['snapshot'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(exact,target)
    plan_path=prototype/receipt['motionPlan']
    if sha(plan_path.read_bytes())!=receipt['motionPlanSha256']:raise ValueError('Approved prototype plan changed')
    target_plan=archive/receipt['motionPlan'];shutil.copyfile(plan_path,target_plan)
    final_masks=[]
    for mask in json.loads(plan_path.read_text()).get('maskFiles',[]):
        source_mask=prototype/mask['path']
        if sha(source_mask.read_bytes())!=mask['sha256']:raise ValueError('Approved prototype mask changed')
        target=archive/mask['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_mask,target)
        final_masks.append({'path':target.relative_to(out).as_posix(),'sha256':mask['sha256']})
    row=receipt|{'profileSha256':sha(json.dumps(profile,sort_keys=True).encode()),'motionProfiles':profile['parts'],
                 'sourceSnapshot':settings['sourceSnapshot'],'sourceSnapshotSha256':settings['sourceSnapshotSha256'],
                 'sourceSnapshotManifestSha256':settings['sourceSnapshotSha256'],
                 'motionPlan':target_plan.relative_to(out).as_posix(),'motionPlanBaseDirectory':archive.relative_to(out).as_posix(),
                 'masks':final_masks,'approvedPrototypeReuse':True,'reusedFromGifSha256':profile['expectedGifSha256'],
                 'approvedPrototypeReceiptPath':(archive/'original-receipt.json').relative_to(out).as_posix(),
                 'approvedPrototypeReceiptSha256':sha(original_receipt.read_bytes()),
                 'approvedPrototypeSourceSnapshot':archived_manifest.relative_to(out).as_posix(),
                 'approvedPrototypeSourceSnapshotManifestSha256':receipt['sourceSnapshotManifestSha256'],
                 'approvedPrototypeAuthoringSourceHashes':receipt['authoringSourceHashes'],
                 'advisoryQuality':{},'mandatoryAllPartsMotion':False,'forcedReturnToFirstPose':False,
                 'openVisualDefects':profile.get('openVisualDefects',[]),'published':False}
    row.pop('authoringSourceHashes',None)
    assert_frozen(settings)
    (out/(stem+'.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
    return {'levelId':level_id,'reusedApprovedPrototype':True,'bytes':destination.stat().st_size,'seconds':round(time.monotonic()-start,2)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reuse-prototypes',type=Path,required=True);p.add_argument('--catalogue',type=Path,required=True);p.add_argument('--art-root',type=Path,required=True);p.add_argument('--profiles',type=Path,required=True);p.add_argument('--gifsicle',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--levels',required=True);p.add_argument('--workers',type=int,choices=[1,2,3],default=3);args=p.parse_args()
    ids=[]
    for token in args.levels.split(','):
        start,end=(map(int,token.split('-')) if '-' in token else (int(token),int(token)));ids.extend(range(start,end+1))
    if len(ids)!=len(set(ids)) or not set(ids)<=set(range(1,121)):p.error('Choose unique authored level IDs1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“120')
    profile=json.loads(args.profiles.read_text());args.output.mkdir(parents=True,exist_ok=True)
    version=subprocess.run([str(args.gifsicle.resolve()),'--version'],check=True,capture_output=True,text=True).stdout
    if 'Gifsicle 1.93' not in version:p.error('Explicit Gifsicle1.93 required')
    settings={'catalogue':str(args.catalogue.resolve()),'art':str(args.art_root.resolve()),'out':str(args.output.resolve()),'optimizer':str(args.gifsicle.resolve()),'optimizerSha256':sha(args.gifsicle.read_bytes()),'profiles':profile}
    settings['prototypeRoot']=str(args.reuse_prototypes.resolve())
    freeze_sources(settings,args.profiles.resolve())
    results=[];errors=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        work={pool.submit(encode_level,(level,settings)):level for level in ids}
        for future in concurrent.futures.as_completed(work):
            try:
                result=future.result();results.append(result);print(json.dumps(result),flush=True)
            except Exception as error:
                row={'levelId':work[future],'error':str(error)};errors.append(row);print(json.dumps(row),flush=True)
            (args.output/('batch-progress-'+args.levels.replace(',','_')+'.json')).write_text(json.dumps({'completed':results,'errors':errors},indent=2)+'\n')
    receipts={}
    for level in range(1,121):
        file=args.output/f'level-{level:03d}.json'
        if file.exists():
            row=json.loads(file.read_text())
            current=settings['profiles']['levels'][str(level)]
            if row['profileSha256']!=sha(json.dumps(current,sort_keys=True).encode()):continue
            receipts[str(level)]={'levelId':level,'path':f'level-{level:03d}.gif','gifSha256':row['conformance']['descriptor']['sha256'],'sourceImageSha256':row['sourceImageSha256']}
    index={'schemaVersion':1,'sourceCatalogueSha256':sha(args.catalogue.read_bytes()),'levels':receipts}
    (args.output/'index.json').write_text(json.dumps(index,indent=2)+'\n')
    totals={};sizes=[]
    for key,value in receipts.items():
        size=(args.output/value['path']).stat().st_size;sizes.append(size);city=str((int(key)-1)//20+1);totals[city]=totals.get(city,0)+size
    (args.output/'download-summary.json').write_text(json.dumps({'count':len(sizes),'totalBytes':sum(sizes),'perCityBytes':totals,'minimumBytes':min(sizes,default=0),'meanBytes':sum(sizes)/len(sizes) if sizes else 0,'maximumBytes':max(sizes,default=0),'hardCapPerGifBytes':5000000},indent=2)+'\n')
    if errors:raise SystemExit(f'{len(errors)} scenes need authoring corrections; see the bounded batch progress receipt')


if __name__=='__main__':main()
