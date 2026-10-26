import os
from pathlib import Path
import json,threading
from functools import partial
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from serve_viewer import Handler
R=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(R))
from tools.build_context import active_context,atomic_json,file_hash
ctx=active_context(R,'r4_viewer')
atomic_json(R/'reports/r4_viewer_validation.json',ctx.report('RUNNING'))
class Quiet(Handler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(R)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(**({'executable_path':os.environ['BM1_CHROME_EXE']} if os.environ.get('BM1_CHROME_EXE') else {'channel':'chrome'}),headless=True,args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1400,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/output/fixture_r4/viewer.html');page.wait_for_function('window.BM1_R4?.meshes.length>0',timeout=60000)
        count=page.evaluate('BM1_R4.meshes.length');expected=json.loads((R/'output/fixture_r4/mesh.json').read_text(encoding='utf-8'));assert count==len(expected)
        first=page.evaluate('BM1_R4.meshes.find(o=>o.userData.instance_id==="PRT-0602-R3-BASE").name');page.select_option('#part',first);page.click('#isolate');assert page.evaluate('BM1_R4.meshes.filter(o=>o.visible).length')==1
        assert 'ASM-06' in page.locator('#info').inner_text();page.click('#all');assert page.evaluate('BM1_R4.meshes.filter(o=>o.visible).length')==count
        page.wait_for_timeout(1000);page.screenshot(path=str(R/'output/fixture_r4/viewer_preview.png'));assert not errors,errors;browser.close()
    atomic_json(R/'reports/r4_viewer_validation.json',ctx.report('PASS',['loaded','isolation','restored'],{'output/fixture_r4/viewer.html':file_hash(R/'output/fixture_r4/viewer.html'),'output/fixture_r4/viewer_preview.png':file_hash(R/'output/fixture_r4/viewer_preview.png')},loaded=True,meshes=count,part_isolation=True,restore_all=True,asm_prt_metadata=True,js_errors=errors))
    print('R4 VIEWER PASS',count)
finally:server.shutdown();server.server_close();thread.join()
