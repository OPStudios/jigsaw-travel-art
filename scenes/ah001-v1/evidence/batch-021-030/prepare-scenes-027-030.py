from pathlib import Path
from PIL import Image
import json,shutil
root=Path('reports/ah-001-2026-09-30/scenes/batch-021-030');gens=json.loads((root/'generation-in-progress.json').read_text(encoding='utf-8-sig'));plans=json.loads(Path('reports/ah-001-2026-09-30/scene-art-plan-120.json').read_text(encoding='utf-8'))['rows']
config={
27:[('table-ribbon',[0,0,512,512],[145,110],'center',[350,340]),('yellow-butterfly',[512,0,1024,512],[75,80],'center',[580,185]),('ivy-twig',[1024,0,1536,512],[100,135],'top_left',[680,1140]),('notebook-tassel',[0,512,512,1024],[65,120],'top_left',[1163,411]),('loose-daisy',[512,512,1024,1024],[85,70],'center',[154,1390])],
28:[('peach-pond-reflection',[15,170,551,420],[205,90],'center',[375,433]),('violet-pond-reflection',[558,160,1064,422],[205,100],'center',[959,1200]),('pond-reeds',[1080,20,1520,500],[160,210],'bottom',[135,1460]),('lily-leaf',[50,605,546,911],[165,100],'center',[1040,1463]),('dragonfly',[615,552,985,938],[90,95],'center',[316,850])],
29:[('near-reflection',[0,0,512,512],[180,80],'center',[380,580]),('far-wave-glints',[512,0,1024,512],[150,70],'center',[690,430]),('dune-grass',[1024,0,1536,512],[180,195],'bottom',[1060,1150]),('near-cloud',[0,512,512,1024],[180,100],'center',[728,101]),('far-cloud-wisp',[512,512,1024,1024],[150,65],'center',[1090,210])],
30:[('flower-pennant',[0,0,512,512],[100,145],'top_left',[377,284]),('peach-lantern',[512,0,1024,512],[115,150],'top_left',[765,275]),('coral-bow',[1024,0,1536,512],[145,130],'center',[1041,621]),('flower-garland',[0,512,512,1024],[135,160],'bottom',[359,1000]),('ivory-streamer',[512,512,1024,1024],[100,175],'top_left',[245,538])]
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
  assert max(edge)<=2, (level,name,max(edge))
  checks.append({'part':name,'crop':box,'edgeMaxAlpha':max(edge),'alphaRange':a.getextrema()})
  sources.append({'name':name,'path':str(dest),'prompt':'Lossless isolation of a separately purpose-painted atlas silhouette; no repainting or matte removal.','derivedFrom':'atlas','sourceCropPixels':box})
  parts.append({'subject':name.replace('-',' '),'source':name,'maxSize':size,'anchor':{'mode':mode,'point':point},'axis':[0,-1] if 'steam' in name else [1,0],'amplitude':4})
 spec={'levelId':level,'sceneId':plan['scene_id'],'theme':plan['theme_slug'],'masterPixels':[1280,1600],'visualReviewed':True,'noDestinationLandmark':True,'mainColourLabel':plan['main_colour'],'visualReviewNotes':'Background composition and all five original alpha subjects visually reviewed. Lossless source regions isolate complete non-overlapping painted objects even where original atlas subjects cross nominal grid cells. Exact anchor alignment and alpha on contrasting backgrounds are inspected after export before final batch readiness. No recognizable destination landmark. Parts adapt the provisional brief to the actual clean plate; no moving rectangle of scenery is used.','sources':sources,'parts':parts}
 (out/'scene-spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8');(out/'alpha-isolation-checks.json').write_text(json.dumps(checks,indent=2));print(level,[(c['part'],c['edgeMaxAlpha']) for c in checks])
