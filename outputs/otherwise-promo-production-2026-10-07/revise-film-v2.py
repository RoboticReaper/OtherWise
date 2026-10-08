"""Export the requested vertical association arrow and more audible music."""
from pathlib import Path
import importlib.util,shutil,json

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('film',ROOT/'finish-film.py')
film=importlib.util.module_from_spec(spec);spec.loader.exec_module(film)
previous=ROOT/'finished'
film.OUT=ROOT/'finished-v2'
film.SHOTS=film.OUT/'scenes'
film.QA=film.OUT/'review-frames'
for p in [film.OUT,film.SHOTS,film.QA]:p.mkdir(parents=True,exist_ok=True)
for scene in film.T['scenes']:
    if scene['number']!=3:
        shutil.copy2(previous/'scenes'/(scene['name']+'.mp4'),film.SHOTS/(scene['name']+'.mp4'))
scene=film.T['scenes'][2]
film.manual_scene(scene,film.g.scenes()[scene['name']])
print('Updated Spotify scene: vertical double-headed association arrow.',flush=True)
film.audio();film.final();film.fcpxml()
for src,name in [(ROOT/'OtherWise-subtitles-en.srt','OtherWise-subtitles-en.srt'),
                 (ROOT/'final-timeline.json','OtherWise-scene-timings.json')]:
    shutil.copy2(src,film.OUT/name)
notes=(previous/'README.txt').read_text()
notes=notes.replace('7 October 2026','7 October 2026 — revision 2',1)
notes=notes.replace('Verification\n', 'Revision 2\nThe Spotify association arrow is now vertical to match the stacked findings. Music gain was increased by 6.02 dB before compression, and reduction during narration was made less aggressive. The previous export is preserved in the neighboring finished folder.\n\nVerification of revision 1\n')
(film.OUT/'README.txt').write_text(notes)
print('Saved revision 2; previous finished exports preserved.',flush=True)
