from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True,args=['--allow-file-access-from-files','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1500,'height':1000},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(os.environ.get('BM1_VIEWER_URL','http://127.0.0.1:8765/viewer/'));page.wait_for_function('window.BM1?.loaded',timeout=60000)
    count=page.evaluate('BM1.objects.length');assert count>100
    page.select_option('#part','PRT-0505');page.click('#isolate');visible=page.evaluate('BM1.objects.filter(o=>o.visible).length');assert visible==2
    page.click('#all');page.uncheck('#covers');covers=page.evaluate('BM1.objects.filter(o=>o.userData.cover&&o.visible).length');assert covers==0
    page.check('#covers');page.locator('#explode').fill('0.5');page.locator('#explode').dispatch_event('input');page.wait_for_timeout(1000)
    assert page.evaluate('BM1.objects.some(o=>o.position.distanceTo(o.userData.home)>0.1)')
    page.locator('#explode').fill('0');page.locator('#explode').dispatch_event('input');page.click('[data-cam="iso"]');page.wait_for_timeout(1200)
    page.screenshot(path=str(R/'output/render/viewer_preview.png'))
    page.select_option('#part','PRT-0701');page.locator('#part').dispatch_event('input');assert page.locator('#info').inner_text().find('PRT-0701')>=0
    browser.close()
(R/'reports/viewer_validation.json').write_text(json.dumps(dict(loaded=True,meshes=count,wheel_isolation=visible,cover_toggle=True,explode_slider=True,part_information=True,js_errors=errors),indent=2));assert not errors,errors
print('VIEWER CHECK PASSED',count)
