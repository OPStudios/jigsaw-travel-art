"""Prepare explicit per-part motion profiles and review boards from art provenance."""
import argparse, hashlib, json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def motion_type(subject):
    s = subject.lower()
    if 'steam' in s: return 'steam'
    if 'flame' in s: return 'flame'
    if 'mobile string' in s or re.search(r'\btag\b',s) or any(v in s for v in ['lantern','cabinet key','wooden fish','violin charm','wooden spoon','zipper pull','folded parasol']): return 'pendulum'
    if any(v in s for v in ['garland','floral string','marigold string']): return 'garland'
    if any(v in s for v in ['butterfly','moth']): return 'butterfly'
    if 'dragonfly' in s: return 'dragonfly'
    if any(v in s for v in ['bumblebee','honeybee']): return 'bee'
    if 'feather' not in s and any(v in s for v in ['swallow','sparrow','seabird','gull']): return 'bird'
    if 'ladybird' in s or 'crab' in s: return 'crawl'
    if 'cloud' in s or 'wisp' in s: return 'cloud'
    if any(v in s for v in ['reflection','caustic','ripple','glint','highlight']): return 'water'
    if any(v in s for v in ['water lily','lily pad','lily leaf','marsh lily','floating','kelp','seaweed']): return 'float'
    if any(v in s for v in ['bow','ribbon','knot','tie']): return 'fabric_join'
    if any(v in s for v in ['curtain','tassel','streamer','bookmark','pennant','bunting','cloth','linen','cord']): return 'fabric_top'
    if 'kite' in s: return 'kite'
    if any(v in s for v in ['resting','fallen','loose','offcut','shaving','thread coil','sewing thread','acorn','wrapped parcel','paintbrush','painter brush','willow curl','feather','orange peel']): return 'resting'
    if any(v in s for v in ['garnish','mint','parsley','scallion']) and not any(v in s for v in ['pot','shoot','stem','tip']): return 'leaf_join'
    if any(v in s for v in ['twig','branch','sprig','fern','vine','ivy','leaf','leaves','flower','daisy','daisies','cosmos','rose','grass','reed','stem','blossom','jasmine','lavender','geranium','rosemary','sage','basil','pelargonium','seed','sprout','shoot','thyme','pothos','succulent','clover','chamomile','oat','hydrangea','calendula','scabious','aster','coreopsis','hay spray','orchid','alder','eucalyptus','carnation','plant','olive','mint','hibiscus','cattail','violets','linden','birch','willow','beech','bluebell']): return 'plant'
    return 'UNREVIEWED'


def anchor(image, kind):
    alpha=image.getchannel('A');box=alpha.point(lambda v:255 if v>32 else 0).getbbox()
    if kind=='center': return [.5,.5]
    x0,y0,x1,y1=box;w,h=image.size
    ys=range(y0,min(y1,y0+max(3,(y1-y0)//12))) if kind=='top' else range(max(y0,y1-max(3,(y1-y0)//12)),y1)
    candidates=[]
    for y in ys:
        xs=[x for x in range(x0,x1) if alpha.getpixel((x,y))>32]
        if len(xs)>=2:candidates.append((len(xs),sum(xs)/len(xs),y))
    if not candidates:return [.5,0 if kind=='top' else 1]
    _,x,y=min(candidates)
    return [round(x/w,6),round(y/h,6)]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--art-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--review',type=Path,required=True);args=p.parse_args()
    scenes=args.art_root/'scenes/ah001-v1-verified';profiles={};source_records=[];all_parts=[]
    override_path=args.output.parent/'overrides.json'
    override_data=json.loads(override_path.read_text()) if override_path.exists() else {}
    overrides=override_data.get('overrides',{})
    scene_overrides=override_data.get('sceneOverrides',{})
    for spec_path in sorted(scenes.glob('*/authoring.portable.json')):
        raw=spec_path.read_bytes();spec=json.loads(raw);level=spec['levelId'];parts=[]
        source_records.append({'path':spec_path.relative_to(args.art_root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()})
        for i,part in enumerate(spec['parts']):
            raw_art=(scenes/part['source']).read_bytes()
            if hashlib.sha256(raw_art).hexdigest()!=part['sha256']:raise ValueError('Art identity mismatch')
            im=Image.open(scenes/part['source']).convert('RGBA');kind=motion_type(part['subject'])
            location='top' if kind in ['fabric_top','pendulum','kite'] or(kind=='plant' and any(t in part['subject'].lower() for t in ['hanging','trailing','overhanging'])) else 'bottom' if kind=='plant' else 'center'
            original_anchor=part.get('anchor',{});mode=original_anchor.get('kind',original_anchor.get('mode'))
            if mode not in ['bottom','center','top_left'] or len(original_anchor.get('point',[]))!=2:raise ValueError('Missing explicit source anchor')
            rect=part['sourcePixelRect'];pivot=[(original_anchor['point'][0]-rect[0])/rect[2],(original_anchor['point'][1]-rect[1])/rect[3]]
            if any(not -.02<=v<=1.02 for v in pivot):raise ValueError('Source placement anchor outside expected rounding margin')
            original_pivot=[round(v,6) for v in pivot];location='top' if mode=='top_left' else mode
            # top_left positions the sprite rectangle; it is not necessarily
            # the physical hinge (e.g. a lantern loop lies at top-center).
            pivot=anchor(im,'top') if mode=='top_left' else original_pivot
            profile={'part':i+1,'source':part['source'],'sourceSha256':part['sha256'],'subject':part['subject'],'motion':kind,'anchorKind':location,'anchor':pivot,'originalPlacementAnchor':original_anchor,'originalPlacementAnchorNormalized':original_pivot,'amplitudePt':min(4,part['amplitude']),'phaseOffset':round(i*.23,2)}
            if kind in ['butterfly','dragonfly','bee','bird']:profile.update(bodyAxis=[0,-1],bodyJoint=[.5,.55])
            if level==1:
                profile['motion']=['steam','plant','plant','butterfly','leaf_join'][i]
                profile['previewRecipePart']=i
            profile.update(overrides.get(f'{level}.{i+1}',{}))
            parts.append(profile);all_parts.append((level,profile,im.copy()))
        profiles[str(level)]={'levelId':level,'sceneId':spec['sceneId'],'authoring':spec_path.relative_to(args.art_root).as_posix(),'parts':parts}
        profiles[str(level)].update(scene_overrides.get(str(level),{}))
    if set(profiles)!={str(i) for i in range(1,121)}:raise ValueError('Expected exactly120 scenes')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.review.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'schemaVersion':1,'recipe':'ah002-natural-gif-v1','status':'anchor-review-in-progress','frameCount':75,'frameDelayMs':40,'durationMs':3000,'dimensions':[376,450],'colors':255,'maximumGifBytes':5000000,'sourceAuthoring':source_records,'levels':profiles},indent=2)+'\n')
    font=ImageFont.load_default(size=15);small=ImageFont.load_default(size=12)
    def board(rows,path):
        sheet=Image.new('RGB',(1250,235*len(rows)+10),'#eee9dc');d=ImageDraw.Draw(sheet)
        for r,row in enumerate(rows):
            for c,(level,part,im) in enumerate(row):
                x=c*250;y=r*235
                preview=im.copy();preview.thumbnail((225,157),Image.Resampling.LANCZOS)
                sheet.paste(preview,(x+(250-preview.width)//2,y+58),preview)
                d.text((x+7,y+5),f"{level:03d}.{part['part']} {part['motion']} / {part['anchorKind']}",font=font,fill='#222')
                words=part['subject'].split();line='';lines=[]
                for word in words:
                    if len(line+' '+word)>32:lines.append(line);line=word
                    else:line=(line+' '+word).strip()
                lines.append(line)
                for n,line in enumerate(lines[:2]):d.text((x+7,y+24+n*14),line,font=small,fill='#444')
        sheet.save(path)
    for start in range(1,121,5):
        board([[v for v in all_parts if v[0]==level] for level in range(start,start+5)],args.review/f'parts-{start:03d}-{start+4:03d}.png')
    risky=[v for v in all_parts if v[1]['motion'] in ['butterfly','dragonfly','bee','bird','crawl','resting','UNREVIEWED']]
    for start in range(0,len(risky),25):
        board([risky[n:n+5] for n in range(start,min(start+25,len(risky)),5)],args.review/f'anatomy-{start:03d}.png')
    counts={kind:sum(v[1]['motion']==kind for v in all_parts) for kind in sorted({v[1]['motion'] for v in all_parts})}
    print(json.dumps({'profiles':str(args.output),'counts':counts,'unsupported':[(v[0],v[1]['part'],v[1]['subject']) for v in all_parts if v[1]['motion']=='UNREVIEWED']},indent=2))


if __name__=='__main__':main()
