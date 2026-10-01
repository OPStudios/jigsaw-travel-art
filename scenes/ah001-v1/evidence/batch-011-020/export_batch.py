"""Technical export only: retain/crop actual generated sprites; no painted pixels synthesized."""
import json, importlib.util
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import numpy as np
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
sources=json.loads((ROOT/'generation-sources.json').read_text())
plan=json.loads((REPO/'reports/ah-001-2026-09-30/scene-art-plan-120.json').read_text())['rows']
specmod=importlib.util.spec_from_file_location('export_scene',ROOT.parent/'export_scene.py'); mod=importlib.util.module_from_spec(specmod); specmod.loader.exec_module(mod)
B={
11:[[0,0,512,540],[512,0,1024,540],[1024,0,1536,540],[0,540,540,1024],[540,540,1120,1024]],
12:[[0,0,512,512],[512,0,1024,512],[1024,0,1536,512],[0,520,520,1024],None],
13:[[0,0,512,528],[512,0,1024,528],[1024,0,1536,528],[0,528,490,1024],[490,550,1150,1000]],
14:[[0,0,512,530],[512,0,1024,530],[1024,0,1536,530],[0,530,500,1024],[500,540,1080,1000]],
15:[[0,0,512,512],[512,0,1024,512],[1024,0,1536,512],[0,520,570,1024],[600,515,1024,1024]],
16:[[0,100,600,500],[600,0,1024,520],[1024,0,1536,530],[0,530,440,1024],[440,560,1160,990]],
17:[[0,0,535,512],None,[1030,0,1536,512],[0,512,512,1024],[512,512,1024,1024]],
18:[[0,0,545,512],[545,0,1040,512],[1040,0,1536,512],[0,512,512,1024],[512,512,1080,1024]],
19:[[0,150,590,510],[590,150,1070,510],[1070,0,1536,545],[0,600,580,1000],[580,600,1250,1000]],
20:[[0,0,512,485],[512,0,1050,485],[1050,0,1536,510],[0,530,560,1000],[600,485,990,1024]]}
# subject, maxSize, anchor mode, anchor point, axis
P={
11:[('tea steam',[115,225],'bottom',[409,596],[0,-1]),('rosemary in mixed herb pot',[110,200],'bottom',[1125,454],[1,0]),('daisy in bud vase',[135,230],'bottom',[155,847],[1,0]),('fallen strawberry leaf',[130,105],'center',[565,1250],[1,0]),('mint garnish on berry tart',[90,66],'center',[843,790],[1,0])],
12:[('awning pennant',[110,130],'top_left',[310,358],[1,0]),('awning tassel',[65,170],'top_left',[790,328],[1,0]),('lavender in cream bud vase',[85,185],'bottom',[1181,1112],[1,0]),('olive sprig in clay pot',[90,205],'bottom',[112,879],[1,0]),('cotton bow on spice packet',[86,60],'center',[477,1118],[0,1])],
13:[('oak twig connected to tree branch',[140,185],'bottom',[248,218],[1,0]),('sage shrub sprig',[145,210],'bottom',[1040,300],[1,0]),('rooted chicory wildflower',[130,185],'bottom',[183,1392],[1,0]),('rooted dry meadow grass',[130,180],'bottom',[1045,1427],[1,0]),('high meadow cloud',[250,85],'center',[722,112],[1,0])],
14:[('residential string pennant',[100,120],'top_left',[580,191],[1,0]),('windowbox pink geranium',[115,175],'bottom',[1080,642],[1,0]),('ivory window curtain',[120,240],'top_left',[150,207],[1,0]),('olive sprig in foreground pot',[130,220],'bottom',[235,1278],[1,0]),('small blue-sky cloud',[210,72],'center',[685,72],[1,0])],
15:[('studio window curtain',[130,300],'top_left',[87,32],[1,0]),('ivy sprig in rear shelf pot',[105,185],'bottom',[1198,239],[1,0]),('pink cosmos in bud vase',[140,225],'bottom',[697,1060],[1,0]),('violet sketchbook bow',[128,85],'center',[1101,1268],[0,1]),('lavender easel tie',[65,170],'top_left',[478,480],[1,0])],
16:[('soft ivory near cloud',[240,95],'center',[715,147],[1,0]),('butter-yellow basket bow',[135,155],'center',[998,720],[1,0]),('rooted sage roadside sprig',[125,185],'bottom',[217,1301],[1,0]),('rooted blue wildflowers',[85,140],'bottom',[1221,1404],[1,0]),('thin ivory far cloud',[220,65],'center',[934,245],[1,0])],
17:[('coral ribbon on sewing table',[150,110],'center',[470,772],[1,0]),('flat loose ivory sewing thread',[180,100],'center',[735,1090],[0,1]),('eucalyptus in glass jar',[130,240],'bottom',[1100,487],[1,0]),('thread tassel on spool stand',[70,180],'top_left',[692,143],[1,0]),('pink carnation in bud vase',[140,245],'bottom',[198,934],[1,0])],
18:[('gingham cloth on picnic basket',[155,125],'top_left',[156,672],[1,0]),('pear-leaf twig attached to branch',[135,175],'bottom',[1150,338],[1,0]),('yellow butterfly near garden flowers',[58,54],'center',[510,630],[1,0]),('rooted garden daisies',[120,170],'bottom',[1072,1347],[1,0]),('foreground meadow grass',[125,120],'bottom',[742,1369],[1,0])],
19:[('near sunset water reflection',[240,110],'center',[344,1139],[1,0]),('far sunset water reflection',[230,95],'center',[742,1369],[1,0]),('shore reeds rooted in rock soil',[110,255],'bottom',[1200,1077],[1,0]),('near sunset cloud',[240,95],'center',[399,160],[1,0]),('far sunset cloud',[230,70],'center',[913,297],[1,0])],
20:[('stage string pennant',[112,150],'top_left',[267,165],[1,0]),('peach lantern on overhead hook',[120,155],'top_left',[909,228],[1,0]),('teal ribbon on guitar stand',[60,165],'top_left',[463,700],[1,0]),('flower garland on stage front',[230,165],'top_left',[135,1120],[1,0]),('cream streamer on right post',[70,225],'top_left',[1180,770],[1,0])]
}
labels={11:'warm terracotta',12:'golden ochre',13:'cocoa brown and dry meadow tan',14:'clear blue',15:'soft violet',16:'warm ivory',17:'turquoise',18:'sage green',19:'berry rose',20:'light coral pink'}
manifests=[]; checks=[]
for ident in range(11,21):
    row=next(r for r in plan if r['level_id']==ident); report=ROOT/f'scene-{ident:03d}'; report.mkdir(parents=True,exist_ok=True)
    archive=report/'technical-crops'; archive.mkdir(exist_ok=True)
    entries=[{'name':k,'path':sources[f'{ident}-{k}']['source'],'prompt':sources[f'{ident}-{k}']['prompt']} for k in ['background','atlas']]
    if ident==12: entries.append({'name':'bow','path':sources['12-bow']['source'],'prompt':sources['12-bow']['prompt']})
    if ident==17: entries.append({'name':'thread','path':sources['17-thread']['source'],'prompt':sources['17-thread']['prompt']})
    atlas=Image.open(sources[f'{ident}-atlas']['source']).convert('RGBA'); parts=[]
    for index,(subject,maximum,mode,point,axis) in enumerate(P[ident]):
        if B[ident][index] is None:
            name='thread' if ident==17 else 'bow'; box=None; crop=Image.open(sources[f'{ident}-{name}']['source']).convert('RGBA')
        else:
            box=B[ident][index];crop=atlas.crop(box);name=f'cutout-{index+1}';cp=archive/(name+'.png');crop.save(cp,optimize=True)
            entries.append({'name':name,'path':str(cp.resolve()),'prompt':'Technical rectangular extraction from the retained atlas, unchanged RGBA pixels. No repainting or generated content.','originalAtlas':sources[f'{ident}-atlas']['source'],'originalPixelRect':box})
        a=np.array(crop)[:,:,3];border=np.concatenate([a[0],a[-1],a[:,0],a[:,-1]])
        checks.append({'level':ident,'part':index+1,'sourceRect':box,'alphaRange':[int(a.min()),int(a.max())],'borderPixelsAbove2':int((border>2).sum()),'borderMax':int(border.max())})
        parts.append({'subject':subject,'source':name,'maxSize':maximum,'anchor':{'mode':mode,'point':point},'axis':axis,'amplitude':4})
    spec={'levelId':ident,'sceneId':row['scene_id'],'theme':row['theme_slug'],'masterPixels':[1280,1600],'visualReviewed':True,'noDestinationLandmark':True,'mainColourLabel':labels[ident],'visualReviewNotes':'Background and all five independently painted cutouts visually inspected. Actual image anchors selected for rooted stems, hanging details, tabletop objects and sky/water layers. Source alpha and contrasting-background review recorded separately. This is implementation review only; root review pending.','sources':entries,'parts':parts}
    palette_regions={14:[350,660,440,840],15:[560,1320,760,1470],16:[715,45,1050,165],18:[480,1200,790,1450],20:[580,330,960,780]}
    if ident in palette_regions:
        region=palette_regions[ident]; bg=Image.open(sources[f'{ident}-background']['source']).convert('RGB').resize((1280,1600),Image.Resampling.LANCZOS); col=np.median(np.array(bg.crop(region)).reshape(-1,3),axis=0).round().astype(int)
        spec['mainColour']='#'+''.join(f'{v:02x}' for v in col); spec['paletteReview']={'representativeSurfaceRect':region,'medianRGB':col.tolist(),'reason':'Visually reviewed large defining surface; broad chromatic buckets also count warm shadows and wood. Both evidence methods retained.'}
        spec['visualReviewNotes']+=' Main colour measured from the visible defining surface at '+str(region)+', rather than inferring a different main colour from the broad hue histogram alone.'
    sp=report/'scene-spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    manifests.append(mod.export_scene(sp,REPO/'assets/art/ah001-scenes',report))
combined={k:v for k,v in manifests[0].items() if k!='scenes'};combined['scenes']=[s for m in manifests for s in m['scenes']]
(ROOT/'complete-scene-manifest.json').write_text(json.dumps(combined,indent=2)+'\n',encoding='utf-8')
(ROOT/'alpha-source-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print('BORDER WARNINGS',json.dumps([r for r in checks if r['borderPixelsAbove2']]))
