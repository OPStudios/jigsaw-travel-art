"""Build city-by-city multi-pose evidence and on-demand GIF review pages."""
import argparse, html, json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);args=p.parse_args();root=args.root
 contacts=root/'contacts';contacts.mkdir(exist_ok=True);font=ImageFont.load_default(size=14)
 rows={}
 for path in root.glob('level-*.json'):
  row=json.loads(path.read_text());rows[row['levelId']]=row
 frame_ids=[0,19,32,55,74]
 for start in range(1,121,5):
  available=[level for level in range(start,start+5) if level in rows]
  if not available:continue
  sheet=Image.new('RGB',(1010,len(available)*265+20),'#f5efe1');draw=ImageDraw.Draw(sheet)
  for r,level in enumerate(available):
   row=rows[level];loss=row['encodingAttempts'][-1]['lossy'];size=row['conformance']['descriptor']['bytes']
   for c,frame in enumerate(frame_ids):
    x=10+c*200;y=10+r*265
    draw.text((x,y),f'Level {level:03d} | {frame*40}ms',fill='#222',font=font)
    with Image.open(root/f'level-{level:03d}-frame-{frame:02d}.png') as image:sheet.paste(image.resize((188,225),Image.Resampling.LANCZOS),(x,y+20))
    if c==0:draw.text((x,y+246),f'{size/1000000:.3f}MB / lossy {loss}',fill='#333',font=font)
  sheet.save(contacts/f'city-{(start-1)//20+1:02d}-levels-{start:03d}-{start+4:03d}.png')
 for city in range(1,7):
  start=(city-1)*20+1;cards=[]
  for level in range(start,start+20):
   if level not in rows:continue
   row=rows[level];actions=', '.join(p['subject']+': '+p['motion'] for p in row['motionProfiles']);encoded=row['conformance']['descriptor']['bytes'];lossy=row['encodingAttempts'][-1]['lossy']
   cards.append(f'''<article><h2>Level {level}</h2><img id="p{level}" src="level-{level:03d}-frame-00.png" width="376" height="450"><p>{encoded:,} bytes · 255 colors · 25fps · 3 seconds · encoder lossy {lossy}</p><button onclick="document.getElementById('p{level}').src='level-{level:03d}.gif?replay='+Date.now()">Play once</button><p>{html.escape(actions)}</p></article>''')
  page='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>GIF city review</title><style>body{font:15px system-ui;background:#f7f0e3;color:#2d251d;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:20px}article{padding:16px;border:1px solid #c6b48c;background:white;border-radius:12px}img{display:block;max-width:100%;height:auto}button{padding:10px 20px;cursor:pointer}</style>'''+f'<h1>City {city}: levels {start}–{start+19}</h1><p>Each real GIF plays once. Inspect the painted actions, attachment points and palette at actual376×450 board size.</p><main>'+''.join(cards)+'</main>'
  (root/f'city-{city:02d}.html').write_text(page,encoding='utf-8')
 summary={'completed':len(rows),'maximumBytes':max((r['conformance']['descriptor']['bytes'] for r in rows.values()),default=0),'highCompressionReview':[{'levelId':n,'lossy':r['encodingAttempts'][-1]['lossy'],'middle':r['advisoryQuality'].get('37')} for n,r in sorted(rows.items()) if r['encodingAttempts'][-1]['lossy']>=60]}
 (root/'visual-review-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
