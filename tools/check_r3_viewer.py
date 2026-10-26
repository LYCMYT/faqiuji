from pathlib import Path
import json,threading
from functools import partial
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from serve_viewer import Handler
R=Path(__file__).resolve().parents[1]
class Quiet(Handler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(R)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=browser.new_page(viewport={'width':1400,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/output/fixture_r3/viewer.html');page.wait_for_function('window.BM1_R3?.meshes.length>0',timeout=60000)
        count=page.evaluate('BM1_R3.meshes.length');expected=json.loads((R/'output/fixture_r3/mesh.json').read_text(encoding='utf-8'));assert count==len(expected)
        first=page.evaluate('BM1_R3.meshes.find(o=>o.userData.instance_id==="PRT-0602-R3-BASE").name');page.select_option('#part',first);page.click('#isolate');assert page.evaluate('BM1_R3.meshes.filter(o=>o.visible).length')==1
        assert 'ASM-06' in page.locator('#info').inner_text();page.click('#all');assert page.evaluate('BM1_R3.meshes.filter(o=>o.visible).length')==count
        page.wait_for_timeout(1000);page.screenshot(path=str(R/'output/fixture_r3/viewer_preview.png'));assert not errors,errors;browser.close()
    (R/'reports/r3_viewer_validation.json').write_text(json.dumps(dict(loaded=True,meshes=count,part_isolation=True,restore_all=True,asm_prt_metadata=True,js_errors=errors),indent=2),encoding='utf-8');print('R3 VIEWER PASS',count)
finally:server.shutdown();server.server_close();thread.join()
