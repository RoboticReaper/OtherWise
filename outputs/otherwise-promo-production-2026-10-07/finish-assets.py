"""Frame the real product recording and build an ordered review reel."""
from pathlib import Path
import json,subprocess,importlib.util
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('graphics',ROOT/'render-manual.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
FFMPEG='/opt/homebrew/bin/ffmpeg'
def run(args):subprocess.run([FFMPEG,'-v','error','-y',*args],check=True)

def product():
    data=json.loads((ROOT/'product/capture.json').read_text());offset=data['videoOffsetSeconds']
    definition=[
      ('07-choose-interest','choose',9,'Start with what you choose.',(180,60,1100,620)),
      ('08-exploration-range','range',7,'Choose how far to explore.',(210,175,1050,545)),
      ('09-follow-a-topic','follow',12,'Discover. Save. Explore further.',(205,180,1075,540)),
      ('10-interest-galaxy','map',10,'See where curiosity takes you.',None)]
    for name,key,duration,title,crop in definition:
        bg=g.BASE.copy();d=ImageDraw.Draw(bg)
        # The captured interface sits entirely above the subtitle-safe region.
        # Labels at the top identify the feature without introducing mock UI.
        g.label(bg,title,(110,58),size=22)
        bgpath=ROOT/'product'/f'{name}-background.png';bg.convert('RGB').save(bgpath)
        ranges=data['clips'][key]['ranges']
        if key=='map':ranges=[[ranges[0][0],ranges[0][1]-2.4]]
        rawDuration=sum(b-a for a,b in ranges)
        temp=ROOT/'product'/f'{name}-trim.mp4'
        graph=[]
        for i,(a,b) in enumerate(ranges):graph.append(f'[0:v]trim=start={a+offset}:end={b+offset},setpts=PTS-STARTPTS[v{i}]')
        graph.append(''.join(f'[v{i}]' for i in range(len(ranges)))+f'concat=n={len(ranges)}:v=1:a=0[cut]')
        run(['-i',data['rawVideo'],'-filter_complex',';'.join(graph),'-map','[cut]','-an','-c:v','libx264','-preset','veryfast','-crf','16',str(temp)])
        if crop:
            x,y,w,h=crop;maxw,maxh=1670,700;s=min(maxw/w,maxh/h)
            sw,sh=round(w*s)//2*2,round(h*s)//2*2
            filt=f'crop={w}:{h}:{x}:{y},scale={sw}:{sh}:flags=lanczos'
        else:
            sw,sh=1350,760;filt=f'scale={sw}:{sh}:flags=lanczos'
        x=(1920-sw)//2;y=125+(715-sh)//2
        if y<100:y=100
        # Slow only short screen actions; hold the final real frame for reading.
        stretch=min(1.45,max(1,duration/rawDuration))
        graph=f'[1:v]{filt},setpts={stretch}*(PTS-STARTPTS),fps=30,tpad=stop_mode=clone:stop=-1[ui];[0:v][ui]overlay={x}:{y}:eof_action=repeat,fps=30,format=yuv420p[out]'
        target=ROOT/'clips'/f'{name}.mp4'
        run(['-loop','1','-framerate','30','-i',str(bgpath),'-i',str(temp),'-filter_complex',graph,'-map','[out]','-t',str(duration),'-an','-c:v','libx264','-preset','veryfast','-crf','18','-movflags','+faststart',str(target)])
        run(['-ss',str(duration*.64),'-i',str(target),'-frames:v','1',str(ROOT/'stills'/f'{name}.png')])
        print(f'Finished real product scene: {name} ({duration}s)',flush=True)

def preview():
    files=sorted((ROOT/'clips').glob('*.mp4'))
    concat=ROOT/'manual-reel.ffconcat';concat.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\n" for p in files))
    bgm=Path('/Users/arthurfu/Downloads/Quiet_Horizons_2026-10-07T072723.mp3')
    total=sum(float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(p)])) for p in files)
    run(['-f','concat','-safe','0','-i',str(concat),'-i',str(bgm),'-map','0:v','-map','1:a','-c:v','copy','-af',f'volume=0.28,afade=t=in:d=1.2,afade=t=out:st={total-2}:d=2','-t',str(total),'-c:a','aac','-b:a','192k','-movflags','+faststart',str(ROOT/'OtherWise-manual-scenes-preview.mp4')])
    # A shorter overview retains the principal finding/state of each clip.
    review=[]
    for p in files:
        duration=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(p)]))
        start=max(0,duration-5)
        short=ROOT/'product'/f'preview-{p.name}'
        run(['-ss',str(start),'-i',str(p),'-t','4','-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',str(short)])
        review.append(short)
    shortlist=ROOT/'overview.ffconcat';shortlist.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\n" for p in review))
    shortTotal=4*len(review)
    run(['-f','concat','-safe','0','-i',str(shortlist),'-i',str(bgm),'-map','0:v','-map','1:a','-c:v','copy','-af',f'volume=0.28,afade=t=in:d=1,afade=t=out:st={shortTotal-2}:d=2','-t',str(shortTotal),'-c:a','aac','-b:a','192k','-movflags','+faststart',str(ROOT/'OtherWise-manual-overview-52s.mp4')])
    print(f'Preview: {total:.1f}s; overview: {shortTotal}s',flush=True)

if __name__=='__main__':product();preview()
