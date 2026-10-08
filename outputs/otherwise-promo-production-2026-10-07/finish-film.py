"""Finish the complete OtherWise film from local, inspected media.

Produces captioned/clean masters, aligned chapters, separate audio stems and
an FCPXML timeline. No external publishing or account changes are involved.
"""
from pathlib import Path
import importlib.util,json,subprocess,math,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from xml.etree.ElementTree import Element,SubElement,ElementTree,indent

ROOT=Path(__file__).resolve().parent
FF='/opt/homebrew/bin/ffmpeg'; PROBE='/opt/homebrew/bin/ffprobe';FPS=30
spec=importlib.util.spec_from_file_location('g',ROOT/'render-manual.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
T=json.loads((ROOT/'final-timeline.json').read_text())
OUT=ROOT/'finished';OUT.mkdir(exist_ok=True)
SHOTS=OUT/'scenes';SHOTS.mkdir(exist_ok=True)
QA=OUT/'review-frames';QA.mkdir(exist_ok=True)
def run(args):subprocess.run([FF,'-v','error','-y',*args],check=True)
def duration(path):return float(subprocess.check_output([PROBE,'-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)]))
def count(s):return round(s['end']*FPS)-round(s['start']*FPS)
def encode_frames(path,n,make):
    process=subprocess.Popen([FF,'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
    for i in range(n):process.stdin.write(make(i/FPS).convert('RGB').tobytes())
    process.stdin.close()
    if process.wait():raise RuntimeError(f'Encoding failed: {path.name}')

def tech_tile(seed):
    rng=np.random.default_rng(seed);w,h=560,315
    yy,xx=np.mgrid[:h,:w];light=np.exp(-(((xx-w*.5)/(w*.6))**2+((yy-h*.45)/(h*.8))**2)*2)
    a=np.empty((h,w,3),dtype=np.uint8)
    for i,(v,k) in enumerate([(14,22),(28,37),(41,44)]):a[:,:,i]=v+light*k
    im=Image.fromarray(a).convert('RGBA');d=ImageDraw.Draw(im)
    blue=['#8ca7be','#a5bfb5','#6e8ca9'][seed%3]
    if seed%3!=2:
        # A stylized semiconductor photographed from above, with no text.
        for k in range(25):
            x=int(rng.integers(20,w-20));y=int(rng.integers(20,h-20))
            pts=[(x,y),(x+int(rng.integers(-70,70)),y),(x+int(rng.integers(-70,70)),int(rng.integers(0,h)))]
            d.line(pts,fill='#365365',width=2)
        cx,cy=280,153;cw,ch=180+(seed%2)*40,148
        for j in range(18):
            px=cx-cw//2+8+j*(cw-16)//17
            d.line((px,cy-ch//2-30,px,cy-ch//2+3),fill=blue,width=3)
            d.line((px,cy+ch//2-3,px,cy+ch//2+30),fill=blue,width=3)
        for j in range(13):
            py=cy-ch//2+8+j*(ch-16)//12
            d.line((cx-cw//2-30,py,cx-cw//2+3,py),fill=blue,width=3)
            d.line((cx+cw//2-3,py,cx+cw//2+30,py),fill=blue,width=3)
        d.rounded_rectangle((cx-cw//2-8,cy-ch//2-8,cx+cw//2+8,cy+ch//2+14),12,fill='#09111c')
        d.rounded_rectangle((cx-cw//2,cy-ch//2,cx+cw//2,cy+ch//2),7,fill='#506b7c',outline='#a2b6b8',width=2)
        d.rectangle((cx-cw//2+18,cy-ch//2+18,cx+cw//2-18,cy+ch//2-18),fill='#233c50',outline='#718e9c',width=2)
        for row in range(4):
            for col in range(6):
                x=cx-cw//2+25+col*24;y=cy-ch//2+25+row*22
                d.rectangle((x,y,x+17,y+15),fill=['#425f71','#74918f','#365369'][(row+col+seed)%3])
        d.line((cx-cw//2+3,cy-ch//2+2,cx+cw//2-3,cy-ch//2+2),fill='#c2cfcc',width=2)
    else:
        # Repeated server modules offer a different view of the same tech theme.
        for j in range(5):
            x=64+j*90
            d.rounded_rectangle((x,35,x+69,284),8,fill='#142837',outline='#537386',width=2)
            for row in range(8):
                y=51+row*27;d.rounded_rectangle((x+10,y,x+59,y+16),3,fill='#253f50',outline='#405f70')
                d.ellipse((x+48,y+5,x+53,y+10),fill='#adcdc3')
                d.line((x+16,y+8,x+39,y+8),fill='#7896a4',width=2)
    vignette=Image.new('RGBA',(w,h));vd=ImageDraw.Draw(vignette)
    for y in range(h):
        alpha=round(55*(abs(y-h/2)/(h/2))**2);vd.line((0,y,w,y),fill=(5,13,23,alpha))
    im=Image.alpha_composite(im,vignette)
    mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),17,fill=255)
    im.putalpha(mask);ImageDraw.Draw(im).rounded_rectangle((1,1,w-2,h-2),17,outline='#4b6070',width=2)
    return im

def opener(s):
    base=g.BASE.copy();d=ImageDraw.Draw(base);d.rectangle((0,0,1920,180),fill='#101a29')
    tiles=[tech_tile(i) for i in range(9)]
    title=g.layer();g.label(title,'A familiar feed',(150,269),size=24)
    g.text(title,'Something\nnew?',(145,352),108,g.IVORY,'serif',spacing=16)
    g.text(title,'A little room for discovery.',(151,634),30,g.MUTED)
    fade=Image.new('RGBA',(1920,1080));fd=ImageDraw.Draw(fade)
    for y in range(1080):
        alpha=round(255*max(0,(y-790)/200)) if y>790 else round(170*max(0,(110-y)/110))
        fd.line((0,y,1920,y),fill=(16,26,41,min(255,alpha)))
    def frame(t):
        im=base.copy()
        for i,tile in enumerate(tiles):
            y=round(-480+i*346-t*91)
            if -315<y<1080:im.alpha_composite(tile,(1130,y))
        im.alpha_composite(fade)
        e=g.ease(t/.65)
        if e<.999:
            ti=title.copy();ti.putalpha(title.getchannel('A').point(lambda a:round(a*e)));im.alpha_composite(ti,(round(20*(1-e)),0))
        else:im.alpha_composite(title)
        return im
    encode_frames(SHOTS/f"{s['name']}.mp4",count(s),frame)

def word_time(scene,needle,default):
    for w in T['words']:
        if w['scene']==scene and w['normal']==needle:return max(0,w['start']-T['scenes'][scene-1]['start']-.16)
    return default

def manual_scene(s,data):
    old,bg,layers=data
    if s['number']==3:
        layers[1]=(layers[1][0],word_time(3,'spotify',2.4))
    elif s['number']==4:
        layers[2]=(layers[2][0],word_time(4,'similar',4.5)-.45)
    elif s['number']==6:
        for i,key in [(1,'other'),(2,'wise'),(3,'invitation')]:layers[i]=(layers[i][0],word_time(6,key,layers[i][1]))
    elif s['number']==11:
        layers[1]=(layers[1][0],word_time(11,'small',2.2));layers[3]=(layers[3][0],word_time(11,'its',8.7))
    elif s['number']==13:
        for i,key in [(1,'interests'),(2,'gradual'),(3,'visual')]:layers[i]=(layers[i][0],word_time(13,key,layers[i][1]))
    def frame(t):
        im=g.composite(bg,layers,t,s['duration']).convert('RGBA')
        if s['number']==4 and t>1.3:
            # A quiet pulse traces the real feedback-loop diagram.
            path=[(1550,585),(1550,634),(370,634),(370,585)]
            lengths=[math.dist(path[i],path[i+1]) for i in range(3)];dist=((t-1.3)/4%1)*sum(lengths)
            for i,length in enumerate(lengths):
                if dist<=length:
                    x=path[i][0]+(path[i+1][0]-path[i][0])*dist/length;y=path[i][1]+(path[i+1][1]-path[i][1])*dist/length;break
                dist-=length
            d=ImageDraw.Draw(im);d.ellipse((x-5,y-5,x+5,y+5),fill=g.SAGE)
        return im
    encode_frames(SHOTS/f"{s['name']}.mp4",count(s),frame)

def media_scene(s,path,overlay=None):
    target=SHOTS/f"{s['name']}.mp4";srcdur=duration(path);n=count(s);dst=n/FPS
    inputs=['-i',str(path)]
    filt=f'[0:v]setpts={dst/srcdur:.10f}*(PTS-STARTPTS),scale=1920:1080:flags=lanczos,fps=30,tpad=stop_mode=clone:stop=-1[v]'
    if overlay:
        inputs+=['-loop','1','-i',str(overlay)]
        filt+=';[1:v]format=rgba,fade=t=in:d=0.6:alpha=1[title];[v][title]overlay=0:0:shortest=1[out]'
    else:filt+=';[v]null[out]'
    run([*inputs,'-filter_complex',filt,'-map','[out]','-frames:v',str(n),'-an','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(target)])

def pictures():
    native=g.scenes();download=Path('/Users/arthurfu/Downloads')
    for s in T['scenes']:
        n=s['number']
        if n==1:opener(s)
        elif n==2:media_scene(s,download/'ElevenLabs_video_gemini-omni-flash-1-1_Create an 8-sec_2026-10-07T06_32_14.mp4',ROOT/'layers/02-ai-caption-transparent.png')
        elif n==5:media_scene(s,download/'gemini_generated_video_4f14c082.mp4',ROOT/'layers/05-ai-caption-transparent.png')
        elif n in [7,8,9,10]:media_scene(s,ROOT/'clips'/f"{s['name']}.mp4")
        else:manual_scene(s,native[s['name']])
        path=SHOTS/f"{s['name']}.mp4"
        run(['-ss',str(max(.3,count(s)/FPS-.5)),'-i',str(path),'-frames:v','1',str(QA/f"{s['name']}.jpg")])
        print(f"Finished aligned scene {n:02}: {count(s)/FPS:.2f}s",flush=True)

def audio():
    D=round(T['duration']*30)/30
    bgm=Path('/Users/arthurfu/Downloads/Quiet_Horizons_2026-10-07T072723.mp3');md=duration(bgm)
    graph=f'''[0:a]loudnorm=I=-17:TP=-2:LRA=11,aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{D},asplit=3[voice][side][voiceout];
    [1:a]asplit=2[m1][m2];
    [m1]atrim=0:{D-10},asetpts=PTS-STARTPTS[a];
    [m2]atrim=start={md-12}:end={md},asetpts=PTS-STARTPTS[b];
    [a][b]acrossfade=d=2:c1=tri:c2=tri,aformat=sample_rates=48000:channel_layouts=stereo,volume=0.36,afade=t=in:d=1.0,afade=t=out:st={D-2.0}:d=2.0[music];
    [music][side]sidechaincompress=threshold=0.05:ratio=3:attack=25:release=450:makeup=1,asplit=2[duck][musicout];
    [voice][duck]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.891:level=disabled,atrim=0:{D}[mix]'''.replace('\n','')
    run(['-i',T['voice'],'-i',str(bgm),'-filter_complex',graph,'-map','[mix]','-c:a','pcm_s16le',str(OUT/'OtherWise-mixed-audio.wav'),'-map','[voiceout]','-c:a','pcm_s16le',str(OUT/'OtherWise-narration.wav'),'-map','[musicout]','-c:a','pcm_s16le',str(OUT/'OtherWise-music.wav')])
    print('Mixed narration and ducked BGM, with a musical closing section.',flush=True)

def final():
    concat=OUT/'final-picture.ffconcat'
    concat.write_text('ffconcat version 1.0\n'+''.join(f"file '{(SHOTS/(s['name']+'.mp4')).as_posix()}'\n" for s in T['scenes']))
    clean=OUT/'OtherWise-final-clean-1080p.mp4';caption=OUT/'OtherWise-final-subtitled-1080p.mp4'
    chapters=OUT/'chapters.ffmetadata';lines=[';FFMETADATA1']
    for s in T['scenes']:
        lines+=['[CHAPTER]','TIMEBASE=1/1000',f"START={round(round(s['start']*30)/30*1000)}",f"END={round(round(s['end']*30)/30*1000)}",f"title={s['name'][3:].replace('-',' ').title()}"]
    chapters.write_text('\n'.join(lines)+'\n')
    run(['-f','concat','-safe','0','-i',str(concat),'-i',str(OUT/'OtherWise-mixed-audio.wav'),'-i',str(chapters),'-map','0:v','-map','1:a','-map_metadata','2','-map_chapters','2','-c:v','copy','-c:a','aac','-b:a','256k','-metadata','title=OtherWise — Your world, a little wider','-movflags','+faststart',str(clean)])
    run(['-i',str(clean),'-vf',f"ass={ROOT/'OtherWise-subtitles-en.ass'}",'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-map_chapters','0','-movflags','+faststart',str(caption)])
    print('Exported complete clean and captioned 1080p films.',flush=True)

def fcpxml():
    x=Element('fcpxml',version='1.10');resources=SubElement(x,'resources')
    SubElement(resources,'format',id='r1',name='FFVideoFormat1080p30',frameDuration='1/30s',width='1920',height='1080',colorSpace='1-1-1 (Rec. 709)')
    for i,s in enumerate(T['scenes'],2):
        a=SubElement(resources,'asset',id=f'r{i}',name=s['name'],start='0s',duration=f'{count(s)}/30s',hasVideo='1',hasAudio='0',format='r1')
        SubElement(a,'media-rep',kind='original-media',src=(SHOTS/(s['name']+'.mp4')).as_uri())
    total=round(T['duration']*30)
    for i,name in [(18,'OtherWise-narration.wav'),(19,'OtherWise-music.wav')]:
        a=SubElement(resources,'asset',id=f'r{i}',name=name,start='0s',duration=f'{total}/30s',hasVideo='0',hasAudio='1',audioSources='1',audioChannels='2',audioRate='48000')
        SubElement(a,'media-rep',kind='original-media',src=(OUT/name).as_uri())
    library=SubElement(x,'library');event=SubElement(library,'event',name='OtherWise — October 2026')
    project=SubElement(event,'project',name='OtherWise complete film')
    seq=SubElement(project,'sequence',format='r1',duration=f'{total}/30s',tcStart='0s',tcFormat='NDF',audioLayout='stereo',audioRate='48k')
    spine=SubElement(seq,'spine');offset=0
    for i,s in enumerate(T['scenes'],2):
        clip=SubElement(spine,'asset-clip',name=s['name'],ref=f'r{i}',offset=f'{offset}/30s',start='0s',duration=f'{count(s)}/30s')
        if i==2:
            for ref,lane,role in [('r18','-1','dialogue'),('r19','-2','music')]:SubElement(clip,'asset-clip',ref=ref,lane=lane,offset='0s',start='0s',duration=f'{total}/30s',audioRole=role)
        offset+=count(s)
    indent(x)
    ElementTree(x).write(OUT/'OtherWise-editable-timeline.fcpxml',encoding='utf-8',xml_declaration=True)
    print('Saved editable FCPXML timeline with 16 scenes and separate audio stems.',flush=True)

if __name__=='__main__':
    if '--mix-only' not in sys.argv:pictures()
    audio();final();fcpxml()
