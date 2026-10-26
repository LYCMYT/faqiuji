from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];f=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);sm=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
states=json.loads((R/'data/demo_states.json').read_text(encoding='utf-8'))
for name,out in [('feed','BM1_feed_sequence.mp4'),('explode','BM1_explode_restore.mp4'),('service','BM1_R1_cassette_service.mp4')]:
    files=sorted((R/'output/animation'/name).glob('*.png'));assert files
    if name=='feed':files=files[:98]+[files[97]]*18
    proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','960x720','-r','6','-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(R/'output/animation'/out)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for n,path in enumerate(files):
        im=Image.open(path).convert('RGB');dr=ImageDraw.Draw(im);dr.rectangle((0,0,960,70),fill='#183A4D');dr.rectangle((0,630,960,720),fill='#183A4D')
        if name=='feed':
            frame=min(390,1+n*4);label=max((s for s in states if s['frame']<=frame),key=lambda s:s['frame'])['label'];title='BM1 / '+label
            notice='演示在释放边界暂停：离轮动态未知；ST10复位须以实际出球确认为条件。' if frame>=390 else '先收导套 → 前移脱筒 → 转头 → 真实开夹 → 捕获后解除托架绑定'
        elif name=='service':title='BM1 R1 / 双销退出 → 供球组件整体后抽';notice='空筒、最低轴高、隔离能源、断开线束并由托车承重；承载和实际操作待试验。'
        else:title='BM1 / 总装模块爆炸与复原';notice='爆炸位移仅用于展示；不等于已验证的拆装顺序或工具可达性。'
        dr.text((22,18),title,font=f,fill='white');dr.text((22,644),notice,font=sm,fill='#E4EFF4');dr.text((22,678),'顺序示意，时间与发球轨迹未验证。实际转速、容量、落点与安全等级未定。',font=sm,fill='#F3C67D')
        proc.stdin.write(im.tobytes())
        if n in [0,len(files)//2,len(files)-1]:im.save(R/'output/render'/f'{name}_preview_{n}.png')
    proc.stdin.close();log=proc.stderr.read().decode('utf-8',errors='replace');rc=proc.wait();(R/'reports'/f'encode_{name}.log').write_text(log,encoding='utf-8');assert rc==0
    print(out,len(files),'frames',flush=True)
