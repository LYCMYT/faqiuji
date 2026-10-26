"""Encode and fully decode the R4 assembly/explosion illustration."""
from pathlib import Path
import json
import os
import subprocess
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import active_context,atomic_json,file_hash
from PIL import Image,ImageDraw,ImageFont

def main():
    ctx=active_context(R,'r4_media');O=R/'output/fixture_r4'
    atomic_json(R/'reports/r4_media_validation.json',ctx.report('RUNNING'))
    p=json.loads((R/'data/r4_presentation.json').read_text(encoding='utf-8'))
    expected=[O/'frames'/f'{n:04d}.png' for n in range(1,p['duration_frames']+1,p['render_sample_step'])]
    if any(not path.is_file() for path in expected):raise RuntimeError('Missing expected animation frames')
    w,h=p['resolution'];top,bottom=p['caption_bands_px'];height=h+top+bottom
    font=ImageFont.truetype(os.environ.get('BM1_CHINESE_FONT','C:/Windows/Fonts/msyh.ttc'),20)
    target=O/'BM1_R4_connections_explode.mp4';ffmpeg=os.environ.get('BM1_FFMPEG_EXE','ffmpeg')
    cmd=[ffmpeg,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{height}','-r',str(p['fps']/p['render_sample_step']),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r',str(p['fps']),'-movflags','+faststart',str(target)]
    with (O/'encode.log').open('w',encoding='utf-8') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=log,stderr=log)
        try:
            for path in expected:
                im=Image.new('RGB',(w,height),'#183a4d')
                with Image.open(path) as frame:im.paste(frame.convert('RGB'),(0,top))
                draw=ImageDraw.Draw(im);draw.text((18,12),'BM1 R4 / 原生实体装配与分解',font=font,fill='white')
                draw.text((18,height-bottom+8),'图示分解位移；实际拆装、保持、载荷与低速操作须经实物确认。',font=font,fill='white')
                draw.text((18,height-31),'制造未放行 · 未进行高速轮组或球路验证',font=font,fill='#f3c67d')
                proc.stdin.write(im.tobytes())
                if path==expected[len(expected)//2]:im.save(O/'animation_preview.png')
            proc.stdin.close()
            if proc.wait()!=0:raise RuntimeError('Video encode failed; inspect encode.log')
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
    subprocess.run([ffmpeg,'-v','error','-i',str(target),'-f','null','-'],check=True,capture_output=True)
    atomic_json(R/'reports/r4_media_validation.json',ctx.report('PASS',['video_fully_decoded'],{target.relative_to(R).as_posix():file_hash(target)},frames=len(expected),video_size=[w,height],physical_motion_proof=False))
    print('R4 video encoded and fully decoded:',len(expected),'source frames')
if __name__=='__main__':main()
