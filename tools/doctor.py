"""Probe installed tools; missing render dependencies are NOT_RUN, never invented."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import tool_versions, atomic_json, file_hash


def probe():
    result={'python':sys.executable,'packages':tool_versions(),'tools':{}}
    for name,env,candidates in [
        ('blender','BM1_BLENDER_EXE',list((R/'tools/blender').glob('*/blender.exe'))),
        ('ffmpeg','BM1_FFMPEG_EXE',[]),('ffprobe','BM1_FFPROBE_EXE',[]),
        ('chrome','BM1_CHROME_EXE',[Path('C:/Program Files/Google/Chrome/Application/chrome.exe')])]:
        path=os.environ.get(env) or shutil.which(name) or next((str(p) for p in candidates if p.is_file()),None)
        entry={'path':path,'status':'NOT_RUN'}
        if path:
            # Chrome GUI --version is unreliable on Windows; PE product version via PowerShell.
            cmd=[path,'--version' if name=='blender' else '-version']
            if name=='chrome':
                cmd=['powershell','-NoProfile','-Command',"(Get-Item -LiteralPath '"+path.replace("'","''")+"').VersionInfo.ProductVersion"]
            try:
                p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
                entry.update(status='AVAILABLE' if p.returncode==0 else 'FAILED',version=(p.stdout or p.stderr).splitlines()[0],sha256=file_hash(path))
            except Exception as exc:entry['error']=str(exc)
        result['tools'][name]=entry
    font=Path(os.environ.get('BM1_CHINESE_FONT','C:/Windows/Fonts/msyh.ttc'))
    result['chinese_font']={'path':str(font),'status':'AVAILABLE' if font.is_file() else 'NOT_RUN',
                            'sha256':file_hash(font) if font.is_file() else None}
    return result

if __name__=='__main__':
    result=probe();atomic_json(R/'reports/doctor.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
