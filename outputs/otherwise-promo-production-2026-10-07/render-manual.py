"""Editable native motion graphics for the OtherWise research film.

Run with the bundled Python (Pillow/numpy) and installed ffmpeg.
No generated text, simulated product UI, or invented experimental results.
"""
from pathlib import Path
from functools import lru_cache
import json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
W,H,FPS=1920,1080,30
IVORY='#f0ecdf'; SAGE='#bccfc5'; MUTED='#a0acb8'; BLUE='#97b6da'; LINE='#354858'
for name in ['clips','stills','layers']: (ROOT/name).mkdir(exist_ok=True)

@lru_cache(None)
def font(size=32,kind='sans'):
    name={'sans':'Arial','bold':'Arial Bold','serif':'Georgia','italic':'Georgia Italic'}[kind]
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/'+name+'.ttf',size)

def text(im,s,xy,size=32,color=IVORY,kind='sans',anchor=None,spacing=12):
    ImageDraw.Draw(im).multiline_text(xy,s,font=font(size,kind),fill=color,anchor=anchor,spacing=spacing)

def wrapped(s,width,size=32,kind='sans'):
    result=[]
    for paragraph in s.split('\n'):
        row=''
        for word in paragraph.split():
            proposed=(row+' '+word).strip()
            if font(size,kind).getlength(proposed)>width and row:result.append(row);row=word
            else:row=proposed
        result.append(row)
    return '\n'.join(result)

def label(im,s,xy=(110,94),color=SAGE,size=24):
    d=ImageDraw.Draw(im);x,y=xy
    for char in s.upper():
        d.text((x,y),char,font=font(size),fill=color);x+=font(size).getlength(char)+2.8

def card(im,box,fill='#172534',outline=LINE,radius=22):
    ImageDraw.Draw(im).rounded_rectangle(box,radius,fill=fill,outline=outline,width=2)

def base():
    yy,xx=np.mgrid[0:H,0:W]
    glow=np.exp(-(((xx-W*.76)/(W*.57))**2+((yy-H*.1)/(H*.7))**2)*2)
    out=np.empty((H,W,3),np.uint8)
    for i,(a,b) in enumerate([(12,14),(22,17),(35,19)]):out[:,:,i]=a+glow*b
    im=Image.fromarray(out).convert('RGBA');d=ImageDraw.Draw(im)
    d.line((110,153,1810,153),fill='#2a3949',width=1)
    text(im,'OTHERWISE', (1687,94),20,MUTED)
    return im

BASE=base()
def layer():return Image.new('RGBA',(W,H))
def heading(s):
    im=layer();text(im,s,(110,192),64,kind='serif');return im
def source(s):
    im=layer();ImageDraw.Draw(im).line((110,790,1810,790),fill=LINE,width=1)
    text(im,s,(110,812),24,MUTED);return im

def logo(im,box):
    path=PROJECT/'assets/branding/otherwise-cosmic-wordmark-v2-transparent.png'
    mark=Image.open(path).convert('RGBA');mark.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
    im.alpha_composite(mark,(box[0]+(box[2]-mark.width)//2,box[1]+(box[3]-mark.height)//2))

def screenshot(im,name,box,zoom=None):
    shot=Image.open(ROOT/'product'/f'{name}.png').convert('RGB')
    if zoom:shot=shot.crop(zoom)
    bw,bh=box[2]-box[0],box[3]-box[1]
    scale=max(bw/shot.width,bh/shot.height)
    shot=shot.resize((round(shot.width*scale),round(shot.height*scale)),Image.Resampling.LANCZOS)
    x=(shot.width-bw)//2;y=(shot.height-bh)//2;shot=shot.crop((x,y,x+bw,y+bh))
    mask=Image.new('L',(bw,bh));ImageDraw.Draw(mask).rounded_rectangle((0,0,bw,bh),18,fill=255)
    im.paste(shot,(box[0],box[1]),mask);ImageDraw.Draw(im).rounded_rectangle(box,18,outline=LINE,width=2)

def scenes():
    out={}
    # Each scene contains a background plus staged vector/text layers.
    bg=BASE.copy();label(bg,'A reason to investigate')
    paper=layer();card(paper,(110,210,690,744))
    label(paper,'The Web Conference 2020',(148,252),size=20)
    text(paper,wrapped('Algorithmic Effects on the Diversity of Consumption on Spotify',490,43,'serif'),(148,320),43,kind='serif')
    text(paper,'Anderson et al.',(148,649),28,SAGE)
    finding=layer();text(finding,'Algorithmic listening',(790,292),46,kind='serif')
    d=ImageDraw.Draw(finding)
    # The associated findings are stacked, so connect them vertically.
    d.line((1104,385,1104,455),fill=SAGE,width=3)
    d.line([(1094,399),(1104,385),(1114,399)],fill=SAGE,width=3)
    d.line([(1094,441),(1104,455),(1114,441)],fill=SAGE,width=3)
    text(finding,'Lower consumption\ndiversity',(790,487),56,kind='serif')
    card(finding,(790,665,1416,725),fill='#1c3037',outline='#405956',radius=30)
    text(finding,'Observed association · Music listening',(815,680),28,SAGE)
    out['03-spotify']=(11,bg,[(paper,.15),(finding,1.0),(source('Anderson et al. · WWW 2020 · doi.org/10.1145/3366423.3380281'),.6)])

    bg=BASE.copy();label(bg,'Recommendation feedback loops')
    title=heading('What we choose shapes what comes next.')
    flow=layer();d=ImageDraw.Draw(flow)
    for i,(number,name,desc) in enumerate([('01','Recommended\ncontent','What the system shows'),('02','User choices','What people select'),('03','Training data','What the system learns')]):
        x=110+i*590;card(flow,(x,335,x+520,570));label(flow,number,(x+28,361),size=20)
        text(flow,name,(x+28,407),42,kind='serif');text(flow,desc,(x+28,521),24,MUTED)
        if i<2:
            d.line((x+535,452,x+574,452),fill=SAGE,width=3);d.polygon([(x+574,452),(x+563,445),(x+563,459)],fill=SAGE)
    d.line([(1550,586),(1550,634),(370,634),(370,586)],fill='#607788',width=3)
    d.polygon([(370,586),(363,598),(377,598)],fill=SAGE)
    result=layer();text(result,'More similar choices  ·  Lower utility',(110,701),36,SAGE)
    out['04-feedback-loop']=(12,bg,[(title,.12),(flow,.7),(result,3.0),(source('Simulation study · Chaney et al., 2018 · doi.org/10.1145/3240323.3240370'),.6)])

    bg=BASE.copy();label(bg,'An invitation to explore')
    brand=layer();logo(brand,(330,155,1260,370))
    other=layer();text(other,'Other',(240,567),46,BLUE,'serif');text(other,'Another perspective',(240,636),32,MUTED)
    wise=layer();text(wise,'Wise',(1050,567),46,SAGE,'serif');text(wise,'More thoughtful judgment',(1050,636),32,MUTED)
    d=ImageDraw.Draw(bg);d.line((960,560,960,710),fill=LINE,width=2)
    invitation=layer();text(invitation,'Think otherwise.',(960,768),48,IVORY,'italic','mm')
    out['06-brand-meaning']=(12,bg,[(brand,.15),(other,1.9),(wise,4.5),(invitation,7.5)])

    bg=BASE.copy();label(bg,'An initial basis for discovery')
    title=heading('Auralist: useful discoveries, beyond the familiar.')
    detail=layer();text(detail,'Liked, previously unknown artists per 20-item list',(110,303),32,MUTED)
    for x,value,name,width in [(110,'2.90','Basic Auralist',362),(980,'5.86','Full Auralist',732)]:
        text(detail,value,(x,377),114,IVORY,'serif');text(detail,name,(x,519),32,SAGE)
        ImageDraw.Draw(detail).rounded_rectangle((x,580,x+width,596),8,fill=SAGE if x==980 else '#607788')
    note=layer();text(note,'n = 21 · Music recommendation study',(110,641),28,MUTED)
    proposal=layer();text(proposal,'Also proposed: user-adjustable novelty',(110,709),35,SAGE)
    out['11-auralist']=(16,bg,[(title,.1),(detail,.8),(note,1.4),(proposal,9.0),(source('Zhang et al. · WSDM 2012 · doi.org/10.1145/2124295.2124300'),.5)])

    bg=BASE.copy();label(bg,'Relevant surprise')
    title=heading('Unexpected can still be relevant.')
    band=layer();d=ImageDraw.Draw(band)
    for x,s,sub in [(110,'Familiar','Already close to what we know'),(700,'Unfamiliar + connected','A meaningful next direction'),(1290,'Unrelated','Harder to connect')]:
        active=x==700;card(band,(x,365,x+520,650),fill='#22373e' if active else '#14212f',outline='#9bb5ab' if active else LINE)
        for j in range(7):
            px=x+60+j*63;py=415+22*math.sin(j*.9);d.ellipse((px-5,py-5,px+5,py+5),fill=SAGE if active else '#657b8a')
        text(band,s,(x+28,482),34,IVORY,'serif');text(band,wrapped(sub,455,25),(x+28,553),25,MUTED)
    conclusion=layer();text(conclusion,'Unexpected + relevant',(960,718),43,SAGE,'serif','mm')
    out['12-purs']=(6,bg,[(title,.1),(band,.6),(conclusion,1.3),(source('PURS · Li et al., RecSys 2020 · doi.org/10.1145/3383313.3412238'),.5)])

    bg=BASE.copy();label(bg,'Our proposed contribution')
    title=heading('One exploration experience. Three ideas together.')
    stages=[]
    for i,(name,s,sub,crop) in enumerate([
        ('confirmed-interest','Confirmed interests','You choose the starting point',(420,840,1490,1395)),
        ('exploration-range','Gradual exploration','You adjust the outward range',(420,535,1520,1105)),
        ('galaxy-selected','Visible exploration paths','You revisit what caught your attention',None)]):
        im=layer();x=110+i*590;screenshot(im,name,(x,340,x+520,610),crop)
        label(im,f'0{i+1}',(x,650),size=20);text(im,s,(x,691),34,IVORY,'serif');text(im,wrapped(sub,515,23),(x,742),23,MUTED)
        stages.append((im,.7+i*.9))
    out['13-contribution']=(13,bg,[(title,.12),*stages])

    bg=BASE.copy();label(bg,'Product + Research')
    question=layer();text(question,'Can a new discovery become\na lasting interest?',(110,220),76,IVORY,'serif',spacing=18)
    steps=layer();d=ImageDraw.Draw(steps)
    for i,(name,sub) in enumerate([('Discover','A new topic today'),('Return','A reason to come back'),('Develop ?','An interest that grows')]):
        x=110+i*590;d.ellipse((x,535,x+68,603),fill='#21343e',outline=SAGE,width=2)
        text(steps,'?' if i==2 else str(i+1),(x+34,568),34,SAGE,anchor='mm')
        if i<2:d.line((x+88,569,x+535,569),fill=LINE,width=2)
        text(steps,name,(x,642),40,IVORY,'serif');text(steps,sub,(x,704),28,MUTED)
    note=layer();text(note,'Our next research question',(110,814),26,SAGE)
    out['14-research-question']=(15,bg,[(question,.2),(steps,2.0),(note,3.0)])

    bg=BASE.copy();label(bg,'Let’s explore this question together')
    message=layer();text(message,"We’d love your\nguidance.",(110,253),104,IVORY,'serif',spacing=14)
    domains=layer();text(domains,'Recommendation\nLearning\nHuman–computer interaction',(1210,335),35,SAGE,spacing=30)
    ImageDraw.Draw(bg).line((1120,288,1120,630),fill=LINE,width=2)
    out['15-professor-invitation']=(10,bg,[(message,.15),(domains,1.4)])

    bg=BASE.copy();label(bg,'Think otherwise.')
    brand=layer();logo(brand,(175,213,1300,410))
    tagline=layer();text(tagline,'Your world, a little wider.',(825,681),53,IVORY,'serif','mm')
    link=layer();text(link,'RoboticReaper.github.io/OtherWise',(825,769),29,SAGE,anchor='mm')
    qr=ROOT/'project-qr.png'
    if qr.exists():
        qi=Image.open(qr).convert('RGBA');qi=qi.resize((252,252),Image.Resampling.NEAREST)
        card(link,(1518,355,1806,643),fill=IVORY,outline=IVORY);link.alpha_composite(qi,(1536,373))
        text(link,'Explore the project',(1662,686),25,SAGE,anchor='mm')
    out['16-end-card']=(6,bg,[(brand,.1),(tagline,.6),(link,1.2)])
    return out

def ease(p):return 1-(1-max(0,min(1,p)))**3
def composite(bg,layers,t,duration):
    im=bg.copy()
    for item,start in layers:
        e=ease((t-start)/.7)
        if e<=0:continue
        if e>.999:im.alpha_composite(item)
        else:
            fade=item.copy();fade.putalpha(item.getchannel('A').point(lambda a:round(a*e)))
            im.alpha_composite(fade,(0,round(22*(1-e))))
    return im.convert('RGB')

def render(name,duration,bg,layers):
    path=ROOT/'clips'/f'{name}.mp4'
    still=composite(bg,layers,duration-1,duration);still.save(ROOT/'stills'/f'{name}.png')
    (ROOT/'layers'/name).mkdir(exist_ok=True)
    bg.convert('RGB').save(ROOT/'layers'/name/'background.png')
    for i,(im,t) in enumerate(layers):im.save(ROOT/'layers'/name/f'layer-{i+1}.png')
    if '--stills' in sys.argv:return
    cmd=['/opt/homebrew/bin/ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    steady=max(t for _,t in layers)+.7
    stable=still.tobytes()
    for n in range(round(duration*FPS)):
        t=n/FPS
        frame=stable if t>=steady else composite(bg,layers,t,duration).tobytes()
        process.stdin.write(frame)
    process.stdin.close()
    if process.wait():raise RuntimeError(f'Failed to encode {name}')
    print(f'Rendered {name}: {duration}s, 1920×1080, 30 fps',flush=True)

if __name__=='__main__':
    index=[]
    for name,(duration,bg,layers) in scenes().items():
        if '--only' not in sys.argv or name==sys.argv[sys.argv.index('--only')+1]:render(name,duration,bg,layers)
        index.append({'file':f'clips/{name}.mp4','duration':duration,'layers':f'layers/{name}'})
    (ROOT/'manual-scenes.json').write_text(json.dumps(index,indent=2))
