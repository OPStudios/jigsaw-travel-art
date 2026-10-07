"""Create explicit per-scene refined decisions from verified artwork and review overrides."""
from __future__ import annotations
import argparse,copy,hashlib,json
from pathlib import Path

def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def decision(part):
    old=part['motion'];subject=part['subject'].lower();index=part['part']
    result=copy.deepcopy(part)
    result['priorMotion']=old
    result['anchorNormalized']=part['anchor']
    result['delaySeconds']=.25+.14*index
    result['maximumDegrees']=.65 if index%2 else .95
    if old=='plant':
        action='rooted_rigid';reason='A small delayed breeze rotates this complete rigid painted plant at its reviewed physical contact.'
    elif old=='steam':
        action='continuous_emission';reason='Painted steam transports continuously upward from a stationary emitter and dissipates without restoring its initial plume.'
    elif old=='water':
        action='reflection_flow';reason='Only reflection/light texture moves; its painted material boundary stays fixed.'
    elif old=='flame':
        action='flame_flow';reason='Continuous upward texture motion stays inside the flame silhouette, preserving the fixed source attachment.'
    elif old=='float':
        action='rigid_float';reason='A floating solid retains its silhouette and proportions during a subpixel drift.'
    elif old=='cloud':
        action='cloud_drift';reason='A coherent cloud drifts slowly without breathing or changing its painted shape.';result['velocity']=[1.4,0]
    elif old in ['butterfly','dragonfly','bee','bird']:
        action='rigid_glide';reason='A short directional glide preserves all original anatomy; no unverified wing deformation or hidden pose is fabricated.'
        result['velocity']=[-4.0,-.25] if old=='bird' else [2.2,-.6]
        result['anatomyLimitation']='Single flattened source pose; no alternate view, underside or articulated flapping is available without inspected component masks.'
    elif old=='pendulum' or (old in ['fabric_top','fabric_left'] and any(word in subject for word in ['tassel','streamer','bookmark','ribbon','tie','tag'])):
        action='hanging_rigid';reason='A restrained breeze rotates the complete hanging object at its reviewed single attachment; material proportions stay fixed.'
        result['maximumDegrees']=.55
    elif old=='kite':
        action='hanging_rigid';reason='A small rigid kite response pivots at the existing tether point instead of distorting the sail.';result['maximumDegrees']=.40
    else:
        action='fixed_solid';reason='Resting objects, tied knots, supported solids and multiple-attachment fabric remain still without an explicit physical cause.'
    result['action']=action;result['motion']=action;result['reason']=reason
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--overrides',type=Path,nargs='*',default=[]);parser.add_argument('--corrections',type=Path,nargs='*',default=[]);args=parser.parse_args()
    raw=args.source.read_bytes();source=json.loads(raw);overrides={};review_sources=[]
    for path in args.overrides:
        incoming=json.loads(path.read_text(encoding='utf-8'));incoming=incoming.get('overrides',incoming)
        for key,value in incoming.items():
            if key in overrides:
                old=overrides[key]
                for field in ['source','sourceSha256','subject','action']:
                    if field in old and field in value and old[field]!=value[field]:raise ValueError('Conflicting review identity/action '+key+'.'+field)
                overrides[key]=old|value
            else:overrides[key]=value
        review_sources.append({'path':str(path),'sha256':digest(path.read_bytes())})
    for path in args.corrections:
        correction=json.loads(path.read_text(encoding='utf-8'))['overrides'];review_sha=digest(path.read_bytes())
        for key,value in correction.items():
            if key not in overrides:raise ValueError('Correction must supersede an existing reviewed part '+key)
            for field in ['source','sourceSha256','subject']:
                if field in value and value[field]!=overrides[key].get(field):raise ValueError('Correction changes source identity '+key)
            previous=overrides[key].get('action')
            overrides[key]=overrides[key]|value|{'supersededAction':previous,'correctionReviewSha256':review_sha}
        review_sources.append({'path':str(path),'sha256':review_sha,'kind':'explicit post-render correction'})
    result={'schemaVersion':2,'method':'approved-refined-level1-material-actions','sourceProfilesSha256':digest(raw),
            'sourceAuthoring':source['sourceAuthoring'],'reviewSources':review_sources,
            'approvedReferenceSha256':'1542f4938ad508fd465a3d4b5c81a38a0db92259a550b909c65de080fb1bf45d',
            'mandatoryAllPartsMotion':False,'forcedReturnToFirstPose':False,'uploadApproved':False,'levels':{}}
    for level in range(1,121):
        old=source['levels'][str(level)];row={k:copy.deepcopy(v) for k,v in old.items() if k!='parts'}
        row['parts']=[]
        for part in old['parts']:
            item=decision(part);key=f'{level}.{part["part"]}'
            if key in overrides:
                item.update(overrides.pop(key));item['motion']=item['action'];item['explicitReviewOverride']=True
            if 'velocityDisplayPtPerSecond' in item:item['velocity']=[float(value)*3 for value in item['velocityDisplayPtPerSecond']]
            if item['action']=='continuous_emission' and 'flame' in item['subject'].lower():item['action']='flame_flow';item['motion']='flame_flow'
            row['parts'].append(item)
        if level in [1,3]:
            row['reusePrototype']=True
            row['expectedGifSha256']={1:'1542f4938ad508fd465a3d4b5c81a38a0db92259a550b909c65de080fb1bf45d',3:'f6deea5fb768bc0c015a5d1f3add72a10862ea087cfc1ec12de327fca639caf7'}[level]
        if level==43:
            row['openVisualDefects']=[{'part':2,'kind':'pre-existing source-art attachment gap','releaseBlocking':True,'description':'The original rosemary stem floats above the bare branch. Preserve for explicit review; no unapproved source-art correction is hidden in animation.'}]
        result['levels'][str(level)]=row
    if overrides:raise ValueError('Unknown reviewed part keys '+str(sorted(overrides)))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    counts={}
    for row in result['levels'].values():
        for part in row['parts']:counts[part['action']]=counts.get(part['action'],0)+1
    print(json.dumps({'levels':120,'parts':600,'actions':counts,'profileSha256':digest(canonical(result))}))

if __name__=='__main__':main()
