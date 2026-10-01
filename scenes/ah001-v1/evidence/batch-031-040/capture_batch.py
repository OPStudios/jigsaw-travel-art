import subprocess,json,time,hashlib
from pathlib import Path
root=Path('C:/GIT/jigsaw-travel-client');reports=root/'reports/ah-001-2026-09-30/scenes/batch-031-040'
candidate=root/'builds/ah001-art-candidate-031-040/scene-candidates/dbb07fb75477d65222f4459a3be0c15b4588d22abff6fa351c350ef136f4294d.json'
results=[]
for ident in range(31,41):
 out=reports/f'scene-{ident:03d}'/'gpu-final';out.mkdir(parents=True,exist_ok=True)
 cmd=['C:/Godot/Godot_v4.7.2-stable_win64_console.exe','--path',str(root),'--rendering-method','gl_compatibility','--audio-driver','Dummy','--position','-10000,-10000','--script','tests/capture_ah_001_painted_scene.gd','--',str(candidate),str(ident),str(out)]
 started=time.time()
 p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
 (out/'renderer.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
 proof=json.loads((out/'motion-proof.json').read_text()) if (out/'motion-proof.json').exists() else {}
 row={'levelId':ident,'exitCode':p.returncode,'seconds':round(time.time()-started,2),'passed':p.returncode==0 and proof.get('passed') is True,'changedPixelsPerPart':proof.get('changedPixelsPerPart'),'changedPixelsOutsideParts':proof.get('changedPixelsOutsideParts'),'frames':len(proof.get('frames',[])),'proof':str(out/'motion-proof.json')}
 results.append(row);print(json.dumps(row),flush=True)
 (reports/'runtime-validation.json').write_text(json.dumps({'candidateSha256':candidate.stem,'results':results,'complete':len(results)==10,'passed':len(results)==10 and all(x['passed'] for x in results)},indent=2)+'\n',encoding='utf-8')
 if not row['passed']:raise SystemExit(1)
