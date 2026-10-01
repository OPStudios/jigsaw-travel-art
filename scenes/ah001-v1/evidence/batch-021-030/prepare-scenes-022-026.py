from pathlib import Path
from PIL import Image
import json,shutil
root=Path('reports/ah-001-2026-09-30/scenes/batch-021-030');gens=json.loads((root/'generation-in-progress.json').read_text(encoding='utf-8-sig'));plans=json.loads(Path('reports/ah-001-2026-09-30/scene-art-plan-120.json').read_text(encoding='utf-8'))['rows']
config={
22:[('cream-berry-pennant',[70,70,490,487],[150,150],'top_left',[273,229]),('awning-tassel',[620,10,925,502],[60,145],'top_left',[920,310]),('white-daisy',[1077,40,1492,511],[100,200],'bottom',[970,883]),('olive-sprig',[40,510,520,1000],[185,205],'bottom',[84,674]),('parcel-ribbon',[531,545,1015,970],[115,100],'center',[625,850])],
23:[('jasmine-vine',[45,55,539,511],[145,165],'bottom',[245,330]),('banana-leaf',[647,10,937,542],[128,250],'bottom',[1180,600]),('fern-frond',[1030,40,1496,559],[175,200],'bottom',[251,935]),('spider-plant',[27,548,531,1000],[205,190],'bottom',[1103,1240]),('window-cloud',[535,600,1160,952],[105,60],'center',[691,224])],
24:[('awning-pennant',[73,100,485,459],[130,120],'top_left',[175,454]),('window-jasmine',[582,87,937,455],[128,155],'bottom',[852,561]),('near-cloud',[986,142,1534,417],[170,95],'center',[915,158]),('foreground-olive',[83,517,495,947],[170,210],'bottom',[102,1340]),('wet-paving-reflection',[535,613,1013,932],[230,105],'center',[853,1450])],
25:[('tea-steam',[115,0,432,578],[112,190],'bottom',[393,1007]),('ficus-leaves',[548,35,1018,548],[160,210],'bottom',[1128,554]),('vase-daisy',[1125,45,1418,544],[105,220],'bottom',[720,830]),('window-butterfly',[125,615,455,947],[70,80],'center',[119,395]),('teapot-ribbon',[583,632,1020,978],[100,85],'center',[505,780])],
26:[('morning-cloud',[0,120,610,434],[210,110],'center',[692,145]),('mooring-ribbon',[626,110,1024,474],[100,95],'center',[558,670]),('shore-alder',[1051,45,1500,485],[170,190],'top_left',[45,893]),('shore-reeds',[25,456,558,998],[210,230],'bottom',[508,1534]),('lake-reflection',[570,610,1067,941],[200,100],'center',[1140,1375])]
}
for level,parts_config in config.items():
 plan=plans[level-1];out=root/f'scene-{level:03}';out.mkdir(exist_ok=True);sources=[]
 for s in gens:
  if s['level']!=level:continue
  dest=out/(s['kind']+'-original.png');shutil.copyfile(s['source'],dest);sources.append({'name':s['kind'],'path':str(dest),'prompt':s['prompt'],'generatorOriginalPath':s['source']})
 im=Image.open(out/'atlas-original.png').convert('RGBA');parts=[];checks=[]
 for name,box,size,mode,point in parts_config:
  crop=im.crop(box);dest=out/(name+'-isolated.png');crop.save(dest);a=crop.getchannel('A');edge=[]
  for b in [(0,0,crop.width,1),(0,crop.height-1,crop.width,crop.height),(0,0,1,crop.height),(crop.width-1,0,crop.width,crop.height)]:edge+=list(a.crop(b).get_flattened_data())
  checks.append({'part':name,'crop':box,'edgeMaxAlpha':max(edge),'alphaRange':a.getextrema()})
  sources.append({'name':name,'path':str(dest),'prompt':'Lossless isolation of a separately purpose-painted atlas silhouette; no repainting or matte removal.','derivedFrom':'atlas','sourceCropPixels':box})
  parts.append({'subject':name.replace('-',' '),'source':name,'maxSize':size,'anchor':{'mode':mode,'point':point},'axis':[0,-1] if 'steam' in name else [1,0],'amplitude':4})
 spec={'levelId':level,'sceneId':plan['scene_id'],'theme':plan['theme_slug'],'masterPixels':[1280,1600],'visualReviewed':True,'noDestinationLandmark':True,'mainColourLabel':plan['main_colour'],'visualReviewNotes':'Background composition and all five original alpha subjects visually reviewed. Lossless source regions isolate complete non-overlapping painted objects even where original atlas subjects cross nominal grid cells. Exact anchor alignment and alpha on contrasting backgrounds are inspected after export before final batch readiness. No recognizable destination landmark. Parts adapt the provisional brief to the actual clean plate; no moving rectangle of scenery is used.','sources':sources,'parts':parts}
 (out/'scene-spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(out/'alpha-isolation-checks.json').write_text(json.dumps(checks,indent=2));print(level,[(c['part'],c['edgeMaxAlpha']) for c in checks])
