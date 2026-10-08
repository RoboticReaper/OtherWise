from pathlib import Path
import re,json,difflib,math
ROOT=Path(__file__).resolve().parent
paragraphs=(ROOT.parent/'otherwise-promo-2026-10-07/subtitles-en.txt').read_text().strip().split('\n\n')
raw=json.loads((ROOT/'voice-alignment-raw.json').read_text())
norm=lambda s:re.sub('[^a-z0-9]','',s.lower()).replace('oralist','auralist')
words=[]
for scene,p in enumerate(paragraphs,1):
    for word in p.split():words.append({'text':word,'normal':norm(word),'scene':scene})
asr=[c for c in raw['chunks'] if norm(c['text'])]
sm=difflib.SequenceMatcher(None,[w['normal'] for w in words],[norm(c['text']) for c in asr],autojunk=False)
matched=0
for tag,a,b,c,d in sm.get_opcodes():
    if tag=='equal':
        matched+=b-a
        for w,t in zip(words[a:b],asr[c:d]):w['start'],w['end']=t['timestamp']
    elif b>a:
        start=asr[c]['timestamp'][0] if c<d else asr[max(0,c-1)]['timestamp'][1]
        end=asr[d-1]['timestamp'][1] if c<d else (asr[d]['timestamp'][0] if d<len(asr) else start+.3)
        for i,w in enumerate(words[a:b]):w['start']=start+(end-start)*i/(b-a);w['end']=start+(end-start)*(i+1)/(b-a)
for i,w in enumerate(words):
    assert w.get('start') is not None and w.get('end') is not None
    if i and w['start']<words[i-1]['start']:raise RuntimeError('Non-monotonic voice timestamps')
names=['01-tech-feed','02-unexplored-interests','03-spotify','04-feedback-loop','05-new-interests','06-brand-meaning','07-choose-interest','08-exploration-range','09-follow-a-topic','10-interest-galaxy','11-auralist','12-purs','13-contribution','14-research-question','15-professor-invitation','16-end-card']
timeline=[]
for i,name in enumerate(names,1):
    sw=[w for w in words if w['scene']==i]
    start=0 if i==1 else max(0,sw[0]['start']-.09)
    timeline.append({'number':i,'name':name,'start':start,'speech_end':sw[-1]['end'],'text':paragraphs[i-1]})
for i,s in enumerate(timeline):
    s['end']=timeline[i+1]['start'] if i<15 else math.ceil((words[-1]['end']+3.2)*30)/30
    s['duration']=s['end']-s['start']

# Editorial phrase boundaries preserve complete ideas rather than dividing
# subtitles at arbitrary character counts. The spoken copy stays unchanged.
cue_text=[
    ['You open your feed for something new.',
     'Somehow, you keep returning\nto the same topics.'],
    ['The videos change.',
     'The interests we explore\ncan stay surprisingly familiar.',
     'We began to worry that our interests\nwere narrowing without us noticing.'],
    ['Research gave us a reason\nto take that question seriously.',
     'A Spotify study linked algorithmic listening\nwith lower consumption diversity.'],
    ['Other researchers showed, in simulations,',
     "how recommendation feedback loops\ncan make users' choices more similar",
     'and reduce the value they get.'],
    ['That raised a question for us:',
     'How can we make unfamiliar interests\neasier to discover?'],
    ['This is OtherWise.', 'Other, for another perspective.',
     'Wise, for more thoughtful judgment.',
     'And an invitation to think otherwise.'],
    ['Start with an interest you choose.',
     'OtherWise suggests unfamiliar\nbut related topics across fields.'],
    ['You control how far to explore,',
     'from nearby ideas to broader connections.'],
    ['Follow a topic that catches your attention.',
     'Save it when you want to pursue it,',
     'and explore from that new starting point.'],
    ['A galaxy map makes your exploration visible,',
     'so you can revisit discoveries\nand choose where to go next.'],
    ['Existing research gives this direction\nan initial basis.',
     'In a small user study,',
     'Auralist produced more useful,\npreviously unknown recommendations.',
     'Its authors also proposed letting users\nadjust the level of novelty.'],
    ['PURS showed how unexpected recommendations\ncould remain relevant.'],
    ['Our proposed contribution is to bring these ideas\ninto a general topic explorer:',
     'interests you confirm,', 'gradual exploration across fields,',
     'and a visual record of your journey.'],
    ["We're developing it as both a product\nand a research project.",
     'Next, we want to test',
     'whether a new discovery today\ncan grow into a lasting interest.'],
    ['If your research connects with recommendation,',
     'learning, or human-computer interaction,',
     "we'd love your guidance."],
    ['OtherWise. Your world, a little wider.'],
]
cues=[]
for scene,phrases in enumerate(cue_text,1):
    sw=[w for w in words if w['scene']==scene];offset=0
    assert ' '.join(' '.join(p.split()) for p in phrases)==' '.join(paragraphs[scene-1].split()), (scene,phrases,paragraphs[scene-1])
    for phrase in phrases:
        n=len(phrase.split());cue=sw[offset:offset+n];offset+=n
        cues.append((cue,phrase))
    assert offset==len(sw)
def time(t,ass=False):
    ms=round(t*(100 if ass else 1000));unit=100 if ass else 1000
    hh=ms//(3600*unit);mm=ms//(60*unit)%60;ss=ms//unit%60;fraction=ms%unit
    return f'{hh}:{mm:02}:{ss:02}.{fraction:02}' if ass else f'{hh:02}:{mm:02}:{ss:02},{fraction:03}'
subtitle=[];srt=[]
for i,(cue,body) in enumerate(cues):
    start=max(0,cue[0]['start']-.04);nextStart=max(0,cues[i+1][0][0]['start']-.04) if i+1<len(cues) else words[-1]['end']+.6
    end=min(nextStart-.025,max(cue[-1]['end']+.13,start+.75))
    assert end>start and (not subtitle or start>=subtitle[-1]['end'])
    subtitle.append({'start':start,'end':end,'text':body,'scene':cue[0]['scene']})
    srt.append(f'{i+1}\n{time(start)} --> {time(end)}\n{body}\n')
(ROOT/'OtherWise-subtitles-en.srt').write_text('\n'.join(srt))
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Arial,44,&H00DFECF0,&H00DFECF0,&H0020100A,&H80000000,0,0,0,0,100,100,0,0,1,2,0.5,2,180,180,70,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
events=[]
for c in subtitle:
    body=c['text'].replace('\n',r'\N')
    events.append(f"Dialogue: 0,{time(c['start'],True)},{time(c['end'],True)},Default,,0,0,0,,{body}")
(ROOT/'OtherWise-subtitles-en.ass').write_text(header+'\n'.join(events)+'\n')
(ROOT/'final-timeline.json').write_text(json.dumps({'voice':raw['audio'],'duration':timeline[-1]['end'],'word_match_fraction':matched/len(words),'scenes':timeline,'words':words,'subtitles':subtitle},indent=2))
for s in timeline:print(f"{s['number']:02} {s['start']:6.2f}–{s['end']:6.2f} ({s['duration']:5.2f}s) {s['name']}")
print(f'{matched}/{len(words)} words matched exactly; {len(cues)} subtitle cues.')
