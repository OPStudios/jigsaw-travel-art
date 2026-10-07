"""Two isolated painted-action prototypes; no content publishing or v1 edits."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, __version__ as PILLOW_VERSION

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'completion_gif'))
from encode_sample import source_animation,read_source,SIZE
from completion_gif import validate_file
from delivery_variants import composition_descriptor
sys.path.insert(0,str(HERE))
from motions import Steam,Insect,RigidPlant,Pond,affine,rotation


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_point(point,image,pad,original_size):
    return [pad+point[a]*image.size[a]/original_size[a] for a in range(2)]


def write_json(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def freeze_sources(args):
    """Preserve exact source bytes once for the entire candidate pair."""
    tools_root=HERE.parents[1]
    paths=[Path(__file__).resolve(),HERE/'motions.py',
           HERE.parent/'completion_gif'/'encode_sample.py',
           *[tools_root/name for name in ['completion_gif.py','measure_completion_gif.py',
                                         'delivery_variants.py','image_compression.py']]]
    folder=args.output/'source-snapshot';folder.mkdir(exist_ok=True)
    records=[]
    for path in paths:
        raw=path.read_bytes();target=folder/path.name
        if target.exists() and target.read_bytes()!=raw:
            raise ValueError('Existing source snapshot differs; preserve this candidate before another version')
        if not target.exists():target.write_bytes(raw)
        records.append({'path':path.relative_to(tools_root).as_posix(),
                        'snapshot':f'source-snapshot/{path.name}','sha256':sha(raw)})
    manifest={'schemaVersion':1,'purpose':'exact offline prototype source, shared by both scenes',
              'sourceCatalogueSha256':sha(args.catalogue.read_bytes()),'files':records}
    manifest_path=folder/'manifest.json'
    raw=(json.dumps(manifest,indent=2)+'\n').encode('utf-8')
    if manifest_path.exists() and manifest_path.read_bytes()!=raw:
        raise ValueError('Existing source manifest differs')
    manifest_path.write_bytes(raw)
    args.frozen_sources={path:sha(path.read_bytes()) for path in paths}
    args.snapshot_sha=sha(raw)


def assert_frozen(args):
    if any(sha(path.read_bytes())!=digest for path,digest in args.frozen_sources.items()):
        raise ValueError('Authoring source changed during this candidate pair; stop instead of mixing versions')


def encode(frames,out,optimizer,receipt):
    if out.exists():
        raise ValueError('Use an isolated new output path; no reviewed GIF is overwritten')
    attempts=[]
    with tempfile.TemporaryDirectory(prefix='v2-',dir=out.parent) as folder:
        palette_file=Path(folder)/'source.gif';candidate=Path(folder)/'candidate.gif'
        accepted=False
        for width in [376,352,320]:
            height=round(width*1350/1128)
            sized=frames if width==376 else [x.resize((width,height),Image.Resampling.LANCZOS) for x in frames]
            training=Image.new('RGB',(width*5,height))
            for column,index in enumerate([0,19,37,56,74]):
                training.paste(sized[index],(column*width,0))
            palette=training.quantize(colors=255,method=Image.Quantize.MEDIANCUT)
            quantized=[x.quantize(palette=palette,dither=Image.Dither.NONE) for x in sized]
            for image in quantized:image.info.clear()
            quantized[0].save(palette_file,save_all=True,append_images=quantized[1:],duration=40,
                              optimize=True,disposal=1,interlace=False,palette=palette.getpalette())
            for lossy in [0,10,20]:
                options=['-O3','--no-loopcount','--no-interlace']+([f'--lossy={lossy}'] if lossy else [])
                subprocess.run([str(optimizer),*options,str(palette_file),'-o',str(candidate)],
                               check=True,capture_output=True,timeout=180)
                attempts.append({'width':width,'height':height,'colors':255,'lossy':lossy,'bytes':candidate.stat().st_size})
                if candidate.stat().st_size<=5_000_000:
                    accepted=True;break
            if accepted:break
        if not accepted:raise ValueError('No restrained255-color candidate meets5MB; stop for review')
        proof=validate_file(candidate)
        out.write_bytes(candidate.read_bytes())
    receipt=receipt|{'encodingAttempts':attempts,'conformance':proof,
                     'encoder':{'pillow':PILLOW_VERSION,'gifsicle':'1.93','gifsicleSha256':sha(optimizer.read_bytes())}}
    write_json(out.with_suffix('.json'),receipt)
    with Image.open(out) as gif:
        for index in [0,19,32,37,55,74]:
            gif.seek(index)
            gif.convert('RGB').save(out.with_name(out.stem+f'-frame-{index:02d}.png'))
    print(json.dumps({'path':str(out),'bytes':out.stat().st_size,'width':width,'height':height,'lossy':lossy}),flush=True)


def render(args,level_id):
    if not args.prepare_only:assert_frozen(args)
    profiles=json.loads((args.art/'animation/ah002-gif-v1/profiles.json').read_text(encoding='utf-8'))
    original_profile=profiles['levels'][str(level_id)]
    spec_path=args.art/original_profile['authoring'];spec_raw=spec_path.read_bytes();spec=json.loads(spec_raw)
    assert spec['levelId']==level_id
    expected=next(x['sha256'] for x in profiles['sourceAuthoring'] if x['path']==original_profile['authoring'])
    if sha(spec_raw)!=expected:raise ValueError('Original source metadata changed')
    payload,cdn,sources,catalogue_sha=source_animation(args.catalogue.resolve(),level_id)
    level=payload['levels'][0];animation=level['paintedAnimation'];still=payload['assets'][level['image']]
    if still!=composition_descriptor(level,payload['assets'],still):raise ValueError('Invalid composition source identity')
    background=Image.open(read_source(cdn,payload['assets'][animation['background']],sources)).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
    actors=[];plans=[];mask_dir=args.output/f'level-{level_id:03d}-masks';mask_dir.mkdir(exist_ok=True)
    for index,(part,authored) in enumerate(zip(animation['parts'],spec['parts'])):
        original=args.art/'scenes/ah001-v1-verified'/authored['source']
        if sha(original.read_bytes())!=authored['sha256'] or authored['sha256'][:12] not in part['source'] or part['rect']!=authored['rect']:
            raise ValueError('Wrong painted part binding')
        original_size=Image.open(original).size
        bare=Image.open(read_source(cdn,payload['assets'][part['source']],sources)).convert('RGBA').resize(
            (round(part['rect'][2]*SIZE[0]),round(part['rect'][3]*SIZE[1])),Image.Resampling.LANCZOS)
        pad=40;image=Image.new('RGBA',(bare.width+pad*2,bare.height+pad*2));image.alpha_composite(bare,(pad,pad))
        anchor=original_profile['parts'][index]['originalPlacementAnchorNormalized']
        anchor=[pad+anchor[a]*bare.size[a] for a in range(2)]
        offset=(-pad,-pad);action='stationary';actor=None;metadata={}
        if level_id==1:
            if index==0:
                actor=Steam(bare);image=bare;offset=(0,0);action='continuous upward steam advection with steady cup emission'
                metadata={'upwardSpeedSourcePxPerSecond':36,'noPlumeReset':True}
            elif index in [1,2]:
                strength,delay=(.8,.35) if index==1 else (1.15,.62)
                actor=RigidPlant(image,anchor,strength,delay)
                action='rigid stem and foliage group responds at its actual root to a delayed directional gust'
                metadata={'anchorPx':anchor,'degrees':strength,'delaySeconds':delay,'rigidComponentScale':1,'leafBladesSplit':False}
            elif index==3:
                joint=source_point((54,59),bare,pad,original_size)
                axis=(18*bare.width/107,-29*bare.height/104)
                antenna_sources=[[(53,51),(64,54),(68,45),(66,15),(55,15),(55,44)],
                                 [(54,47),(60,55),(91,34),(89,26),(78,29)]]
                antenna=[[source_point(p,bare,pad,original_size) for p in poly] for poly in antenna_sources]
                wing_sources=[[(0,0),(55,0),(55,43),(55,56),(47,69),(39,84),(39,95),(0,95)],
                              [(49,50),(76,42),(107,44),(107,104),(32,104),(32,82),(41,65)]]
                wing_polygons=[[source_point(p,bare,pad,original_size) for p in poly] for poly in wing_sources]
                actor=Insect(image,axis,joint,2.8*bare.width/107,'butterfly',antenna,wing_polygons)
                action='two coherent coupled wing-pair planes and short directional hover; rigid body and complete antennae'
                metadata={'thoraxJointPx':joint,'bodyAxis':axis,'bodyExtraPolygons':antenna,'wingPairPolygons':wing_polygons,'bodyScale':1,'sourceLimitation':'No underside, turning pose or full3D flight is available from the single painting.'}
            else:
                action='mint garnish remains completely stationary on the pastry'
        else:
            if index<3:
                if index==0:
                    anchor=source_point((24,166),bare,pad,original_size)
                strength,delay=[(.45,.50),(.65,.85),(1.05,1.00)][index]
                actor=RigidPlant(image,anchor,strength,delay)
                action='rigid foliage rotates subtly at its actual root with delayed directional breeze'
                metadata={'anchorPx':anchor,'degrees':strength,'delaySeconds':delay,'rigidComponentScale':1}
                if index==0:metadata['anchorReview']='Manual source[24,166] is the cut stem. Historical metadata points to a lower-right leaf tip and is not used as the v2 hinge.'
            elif index==3:
                action='lily remains a rigid floating group; slow subpixel drift without changing silhouette'
                metadata={'maximumTranslationSourcePx':1.8,'maximumRotationDegrees':.22,'rigidComponentScale':1}
            else:
                joint=source_point((41,32),bare,pad,original_size)
                axis=(-27*bare.width/80,-47*bare.height/73)
                # Trace the curved abdomen through its actual tail, instead of
                # approximating the animal with a straight central stripe.
                body_source=[(28,15),(39,15),(42,20),(42,24),(45,26),(48,31),
                             (48,36),(51,40),(53,43),(55,47),(59,51),(61,55),
                             (63,60),(64,64),(67,68),(68,73),(64,73),(61,68),
                             (59,64),(57,60),(54,56),(52,53),(50,51),(49,47),
                             (47,44),(46,42),(43,40),(39,37),(37,33),(36,29),
                             (33,28),(29,28),(26,24),(25,19),(29,19),(31,23),(29,20)]
                body=[source_point(p,bare,pad,original_size) for p in body_source]
                wing_sources=[[(-4,20),(34,22),(44,28),(51,42),(54,54),(35,67),(-4,70)],
                              [(34,23),(46,8),(59,-4),(84,-4),(84,47),(63,49),(47,42),(40,35)]]
                wing_polygons=[[source_point(p,bare,pad,original_size) for p in poly] for poly in wing_sources]
                actor=Insect(image,axis,joint,0,'dragonfly',[body],wing_polygons)
                action='rigid head, thorax and complete curved abdomen; two coherent coupled wing-pair planes with exposure integration'
                metadata={'thoraxJointPx':joint,'bodyAxis':axis,'bodyExtraPolygon':body,'wingPolygons':wing_polygons,'bodyScale':1,'bodyMaskMethod':'complete traced silhouette; no straight stripe','wingMaskMethod':'coupled side pairs; ambiguous painted fore/hind overlap is not cut','sourceLimitation':'A single80x73 painted pose cannot provide new views or occluded anatomy.'}
        image.save(mask_dir/f'part-{index+1}-source.png')
        if isinstance(actor,Insect):
            actor.body.save(mask_dir/f'part-{index+1}-rigid-body.png')
            for wing_no,(wing,side,fore,hinge) in enumerate(actor.wings):
                wing.save(mask_dir/f'part-{index+1}-wing-{wing_no+1}.png')
            metadata['wingHinges']=[list(map(float,w[3])) for w in actor.wings]
        if isinstance(actor,RigidPlant) and actor.joint is not None:
            actor.upper.save(mask_dir/f'part-{index+1}-rigid-upper.png');actor.lower.save(mask_dir/f'part-{index+1}-rigid-lower.png')
        actors.append((part,image,actor,offset,index))
        plans.append({'part':index+1,'subject':authored['subject'],'source':authored['source'],'sourceSha256':authored['sha256'],'action':action,**metadata})
    pond=Pond(background) if level_id==3 else None
    scene_plan={'levelId':level_id,'recipe':'isolated-natural-actions-v2','status':'prototype-awaiting-normal-speed-review',
                'sourceCatalogueSha256':catalogue_sha,'sourceImageSha256':still['sha256'],'sourceAuthoringSha256':sha(spec_raw),
                'frameCount':75,'frameDelayMs':40,'durationMs':3000,'finalZoom':1.05,
                'parts':plans,'maskPolicy':'Hand-traced selections of original painted pixels only; no synthetic replacement art.',
                'uploadApproved':False,'v1OutputsChanged':False,'noMandatoryAllPartsMotion':True,'noForcedReturnToFirstPose':True}
    if pond:
        pond.surface.save(mask_dir/'pond-water-mask.png');pond.falls.save(mask_dir/'waterfall-mask.png')
        scene_plan['waterMasks']={'referencePixels':[1280,1600],'surface':Pond.SURFACE,'exclusions':Pond.EXCLUSIONS,'waterfalls':Pond.FALLS,'backgroundFixedOutsideMasks':True}
    scene_plan['maskFiles']=[{'path':f'{mask_dir.name}/{path.name}','sha256':sha(path.read_bytes())} for path in sorted(mask_dir.glob('*.png'))]
    scene_plan['antialiasFringePolicy']='Any unassigned source pixel must have alpha <=20 and is preserved on its nearest substantial painted component; no visible body or wing omission is repaired by this rule.'
    write_json(args.output/f'level-{level_id:03d}-motion-plan.json',scene_plan)
    if args.prepare_only:
        print(json.dumps({'levelId':level_id,'preparedMasks':str(mask_dir)}),flush=True)
        return
    presentation=[];locked=[];traces=[[] for _ in actors]
    for frame in range(75):
        time=frame*.04;phase=frame/74
        scene=pond.frame(time) if pond else background.copy()
        for part,image,actor,offset,index in actors:
            painted=actor.frame(time) if actor else image
            if level_id==3 and index==3:
                # Solid leaf and flower move together. Their painted geometry
                # does not receive the water-reflection deformation.
                translation=(1.6*math.sin(time*.72),.8*math.sin(time*.93))
                painted=affine(image,rotation(.20*math.sin(time*.8)),(image.width*.5,image.height*.5),translation)
            traces[index].append(sha(painted.tobytes()))
            x=round(part['rect'][0]*SIZE[0])+offset[0];y=round(part['rect'][1]*SIZE[1])+offset[1]
            scene.alpha_composite(painted,(x,y))
        locked.append(scene.convert('RGB').resize((376,450),Image.Resampling.LANCZOS))
        zoom=1+.05*(phase*phase*(3-2*phase))
        view=scene.transform(SIZE,Image.Transform.AFFINE,(1/zoom,0,564*(1-1/zoom),0,1/zoom,675*(1-1/zoom)),Image.Resampling.BICUBIC)
        presentation.append(view.convert('RGB').resize((376,450),Image.Resampling.LANCZOS))
    proof={'sourceCatalogueSha256':catalogue_sha,'sourceImageSha256':still['sha256'],'verifiedSources':sources,
           'sourceAuthoringSha256':sha(spec_raw),'motionPlan':f'level-{level_id:03d}-motion-plan.json',
           'motionPlanSha256':sha((args.output/f'level-{level_id:03d}-motion-plan.json').read_bytes()),
           'uniqueActorPoses':[len(set(x)) for x in traces],'levelId':level_id,'visualAcceptance':'not-yet-reviewed',
           'published':False,'prototypeOnly':True,'sourceSnapshot':'source-snapshot/manifest.json','sourceSnapshotManifestSha256':args.snapshot_sha,'authoringSourceHashes':{p.name:sha(p.read_bytes()) for p in [Path(__file__),HERE/'motions.py']}}
    if level_id==1 and proof['uniqueActorPoses'][4]!=1:raise ValueError('Resting mint must stay exactly stationary')
    for index in [0,19,32,37,55,74]:
        locked[index].save(args.output/f'level-{level_id:03d}-locked-reference-{index:02d}.png')
    assert_frozen(args)
    encode(presentation,args.output/f'level-{level_id:03d}.gif',args.gifsicle,proof|{'camera':'100-to105-percent'})
    encode(locked,args.output/f'level-{level_id:03d}-locked.gif',args.gifsicle,proof|{'camera':'locked-diagnostic'})
    assert_frozen(args)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalogue',type=Path,required=True);p.add_argument('--art',type=Path,required=True)
    p.add_argument('--gifsicle',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--levels',type=int,nargs='+',choices=[1,3],required=True)
    p.add_argument('--prepare-only',action='store_true')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    args.gifsicle=args.gifsicle.resolve()
    version=subprocess.run([str(args.gifsicle),'--version'],capture_output=True,text=True,check=True).stdout
    if 'Gifsicle 1.93' not in version:raise ValueError('Explicit Gifsicle1.93 required')
    if not args.prepare_only:freeze_sources(args)
    for level_id in args.levels:render(args,level_id)


if __name__=='__main__':main()
