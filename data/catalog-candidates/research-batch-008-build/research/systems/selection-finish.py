"""Append the remaining source-inspected meaning rows and bounded alternatives."""
from pathlib import Path
exec((Path(__file__).parent/'selection-assembly.py').read_text().split("C='Computing")[0])
L='Learning & language'; M='Mind & behavior'; S='Society & relationships'

add('local:catalog:voice-onset-time','Voice onset time',['VOT'],L,'Acoustic phonetics','idea',
    'Timing between stop release and vocal-fold vibration distinguishes speech sounds.', ['Q35395','Q8183'],
    'A defined acoustic interval for stop consonants, distinct from phonetics broadly and from categorical perception of that interval.',
    'https://www.haskinslaboratories.org/vot','Legacy: Abramson/Lisker VOT Stimuli, definition and synthesized continuum, lines 21-27',
    'Haskins Laboratories: Legacy—Abramson/Lisker VOT Stimuli',parent='Q35395',
    parent_note='The laboratory explicitly presents VOT as an acoustic phonetic measure introduced to characterize stop-consonant voicing distinctions.',
    limits=['Voicing may begin before release, so VOT can be negative; do not give a universal phoneme-boundary duration.'])
mcgurk='https://www.violetabrown.com/pdfs/Brown%20et%20al.%202018%20-%20What%20accounts%20for%20individual%20differences%20in%20susceptibility%20to%20the%20McGurk%20effect.pdf'
add('local:catalog:mcgurk-effect','McGurk effect',['McGurk illusion'],L,'Audiovisual speech perception','idea',
    'Mismatched heard and seen syllables can produce a perceived syllable present in neither input.', ['Q8183','Q2459671','Q160402'],
    'A specifically studied audiovisual speech illusion, distinct from phoneme categorization generally and from lexical interpretation biases.',
    mcgurk,'Abstract and Introduction, PDF pp. 1-2, lines 8-28 and 63-80',
    'Brown et al. (2018), What accounts for individual differences in susceptibility to the McGurk effect?',
    parent='Q160402',assertion='editorial',parent_note='The paper characterizes a perceptual speech illusion; perception is a general editorial parent.',
    limits=['Susceptibility varies across people and tasks; a fusion example does not predict every listener’s response or everyday speech ability.'],revision='PLOS ONE 13(11): e0207160, 2018-11-12')
word='https://cpb-us-w2.wpmucdn.com/voices.uchicago.edu/dist/7/1535/files/2019/11/WoodwardMarkman1991.pdf'
add('local:catalog:mutual-exclusivity-word-learning','Mutual exclusivity in word learning',['Mutual exclusivity bias','Lexical mutual exclusivity'],L,'Early word learning','idea',
    'An unfamiliar label can be assigned to an unnamed object or property instead of a familiar whole object.', ['Q815859'],
    'The distinct word-learning bias restricts candidate referents; it is not logical mutual exclusion or the whole-object assumption.',
    word,'Mutual Exclusivity, printed pp. 140-141 / PDF pp. 4-5; Constraints as Default Assumptions, pp. 142-145',
    'Woodward and Markman (1991), Constraints on Learning as Default Assumptions',parent='Q815859',
    parent_note='The authors explicitly treat mutual exclusivity as a proposed constraint guiding children’s acquisition of word meanings.',
    limits=['A probabilistic default that can be overridden, not a law that every object has one name; historical evidence and interpretation are debated.'],revision='Developmental Review 11, 1991, pp. 137-163')
add('local:catalog:whole-object-assumption','Whole-object assumption in word learning',['Whole object assumption','Whole-object bias'],L,'Early word learning','idea',
    'A new object label is initially interpreted as naming the whole object rather than its parts or material.', ['Q815859'],
    'The paper separately names this initial referent hypothesis and mutual exclusivity; one chooses whole-object scope, the other rejects an additional label.',
    word,'The Taxonomic and Whole Object Assumptions, printed p. 139 / PDF p. 3, lines 79-85; default-bias qualification, p. 145 / PDF p. 9, lines 274-299',
    'Woodward and Markman (1991), Constraints on Learning as Default Assumptions',parent='Q815859',
    parent_note='The paper explicitly defines it as one of the biases used by children to constrain possible meanings during word learning.',
    limits=['An overridable first hypothesis; object context, grammar, and other biases can change the interpretation.'])
add('local:catalog:generation-effect','Generation effect',['Self-generation effect'],L,'Memory during study','idea',
    'Generating a word can improve later memory compared with reading the same word.', ['Q492','Q7705913'],
    'The generate-versus-read encoding comparison is distinct from recalling already studied material in retrieval practice.',
    'https://garfield.library.upenn.edu/classics1992/A1992HN61400001.pdf','Original abstract summary and author retrospective, single PDF page, lines 3-8 and 26-43',
    'Norman J. Slamecka (1992), Delineation of the Generation Effect—Citation Classic',parent='Q492',
    parent_note='The author describes the original experiments as comparisons of memory for generated and read words.',
    limits=['Author retrospective about the 1978 experiments; generation has documented boundaries and no single mechanism is asserted here.'],revision='Author commentary received 1992-03-24; original study 1978')
add('local:catalog:productive-failure','Productive failure',['Productive failure in learning'],L,'Problem solving before instruction','idea',
    'Unsuccessful problem exploration can support later transfer when subsequent problems supply a useful contrast.', ['Q133500','local:catalog:worked-example'],
    'The study names latent learning benefits from initially unsuccessful exploration; this is distinct from the worked-example effect or generic learning from mistakes.',
    'https://escholarship.org/content/qt5f26n97z/qt5f26n97z_noSplash_3e0168f3bef8cfb49b0193c6593738b6.pdf',
    'Abstract, PDF p. 1, lines 4-22',
    'Manu Kapur, Productive Failure: A Hidden Efficacy of Seemingly Unproductive Production',parent='Q133500',
    parent_note='The experiment explicitly analyzes meaningful learning and transfer after contrasting problem-solving conditions.',
    limits=['Bounded to the inspected study’s collaborative tasks and contrasting-case design; struggling or failing alone is not guaranteed to improve learning.'],revision='Cognitive Science Society proceedings, 2007')
add('local:catalog:desirable-difficulties','Desirable difficulties',['Desirable difficulty'],L,'Retention versus practice performance','idea',
    'Some practice conditions slow immediate performance while improving later retention or transfer.', ['Q1095859','Q7705913','Q133500'],
    'An umbrella learning-performance distinction includes spacing and testing but is broader than either individual effect; not all difficulty is desirable.',
    'https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/07/RBjork_inpress.pdf',
    'Opening definition, PDF p. 1, lines 1-11; Why Desirable Difficulties Are Desirable, PDF pp. 3-4, lines 60-71',
    'Robert A. Bjork, Desirable Difficulties Perspective on Learning',parent='Q133500',
    parent_note='The author explicitly frames desirable difficulties as learning conditions affecting retention and transfer.',
    limits=['A learner must have enough prior knowledge and cues to overcome the difficulty; the hosted manuscript’s exact publication revision is unavailable.'])
add('Q7705913','Testing effect',['Practice testing','Retrieval practice','Testing effect'],L,'Retrieval-based learning','idea',
    'An initial memory test can strengthen retention on a later test beyond additional study.', ['Q7705913'],
    'The imported testing-effect identity and its retrieval-practice aliases are the same subject; primary-author evidence updates the reference bundle.',
    'https://www.psychologicalscience.org/observer/test-enhanced-learning-2','Testing-effect explanation and prose-study example, lines 17-23',
    'Roediger, McDaniel and McDermott (2006), Test Enhanced Learning',parent='Q133500',
    parent_note='The authors expressly describe the memory-test intervention as an aid to learning.',
    limits=['Initial recall and feedback conditions affect benefits; this claim does not concern the merits of high-stakes standardized testing.'],revision='APS Observer, 2006-03-01')

add('local:catalog:change-blindness','Change blindness',['Visual change blindness'],M,'Visual change detection','idea',
    'An interruption can make a substantial scene change go unnoticed across successive views.', ['local:catalog:inattentional-blindness','local:catalog:attentional-blink','Q160402'],
    'Failure to compare successive scene states differs from missing an unexpected object during another task and from rapid-sequence attentional blink.',
    'https://www2.psych.ubc.ca/~rensink/publications/download/Vis_Cog_02_Rensink.pdf',
    'Opening summary and change-blindness discussion, PDF pp. 1-2, lines 8-18 and 39-45',
    'Ronald A. Rensink, The Dynamic Representation of Scenes',parent='Q160402',
    parent_note='The author expressly discusses this visual-perception phenomenon as evidence about scene representation.',
    limits=['Hosted author manuscript is marked in press and requests no direct quotation; use original paraphrase and separate the demonstrated phenomenon from the proposed representation theory.'],revision='Author manuscript marked in press, expected late 1999')
add('local:catalog:choice-blindness','Choice blindness',['Choice-outcome blindness'],M,'Choice and introspection','idea',
    'People can miss a covertly swapped choice outcome and give reasons for the outcome they did not select.', ['Q210501','local:catalog:inattentional-blindness'],
    'The named intention-versus-presented-outcome mismatch differs from visual change detection or simply overlooking an unexpected object.',
    'https://www.lucs.lu.se/fileadmin/user_upload/lucs/2011/01/Johansson-et-al.-2006-How-Something-Can-Be-Said-About-Telling-More-Than-We-Can-Know.pdf',
    'Abstract, PDF pp. 1-2; section 2, PDF p. 4, lines 104-120',
    'Johansson et al. (2006), How something can be said about telling more than we can know',parent='Q210501',
    parent_note='The paper explicitly studies introspectively derived reports of reasons within the choice-blindness paradigm.',
    limits=['The inspected manipulation is a face-choice task; do not generalize its detection rate to every choice or infer fixed private preferences.'],revision='Consciousness and Cognition 15, 2006, pp. 673-692')
add('local:catalog:illusion-of-explanatory-depth','Illusion of explanatory depth',['IOED'],M,'Metacognitive calibration','idea',
    'Trying to explain a mechanism can reveal gaps hidden by an initial feeling of understanding.', ['Q1126970','Q210501'],
    'The paper explicitly distinguishes overestimating explanatory understanding from general confidence about facts, procedures, or narratives.',
    'https://cogdevlab.yale.edu/sites/default/files/files/rozenblit%20%26%20keil%20%202002.pdf',
    'Abstract and Introduction, PDF pp. 1-2, lines 8-17 and 54-65; discussion of recalibration after explanation, PDF p. 15, lines 482-487',
    'Rozenblit and Keil (2002), The misunderstood limits of folk science: an illusion of explanatory depth',parent='Q1126970',
    parent_note='The authors identify the explanatory-knowledge illusion as a metacognitive problem and test changes in self-ratings of understanding.',
    limits=['Effects vary by knowledge type; this is not a blanket claim that everyone misunderstands every mechanism.'],revision='Cognitive Science 26, 2002, pp. 521-562')
add('local:catalog:stop-signal-reaction-time','Stop-signal reaction time',['SSRT'],M,'Response inhibition measurement','idea',
    'A race model estimates the hidden latency of stopping from go responses and stop-signal delays.', ['Q783092','Q500096'],
    'The estimated covert stopping latency is distinct from overt go reaction time, signal delay, and executive functioning generally.',
    'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0210065',
    'Introduction, lines 174-181; discussion of independence and slowing, lines 477-484',
    'A reaction-time adjusted PSI method for estimating performance in the stop-signal task',parent='Q783092',relation='facet_of',
    parent_note='The introduction explicitly places stopping and response-inhibition measurement among executive functions.',
    limits=['It is an estimate conditional on task/model assumptions; strategic go-response slowing can affect estimates. Avoid diagnostic conclusions.'],revision='PLOS ONE 14, 2019, e0210065')
add('local:catalog:simon-effect','Simon effect',['Spatial Simon effect'],M,'Spatial response compatibility','idea',
    'An irrelevant stimulus location can interfere with a response selected by color or shape.', ['Q384176','Q6501338'],
    'Spatial stimulus-response correspondence defines the Simon task; the Stroop effect instead uses an irrelevant word dimension and is not the same subject.',
    'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0090954',
    'Instruction, lines 139-146',
    'Tang, Zhao and Chen (2014), The Task-Relevant Attribute Representation Can Mediate the Simon Effect',
    parent='local:authored:000048',assertion='editorial',parent_note='The paper’s experimental response-selection results provide an editorial navigation parent in cognitive psychology.',
    limits=['The compatible-response benefit depends on task conditions; the paper compares theories rather than establishing one universal mechanism.'],revision='PLOS ONE 9(3): e90954, 2014-03-11')
add('local:catalog:duration-neglect','Duration neglect',['Duration neglect in remembered experience'],M,'Retrospective experience evaluation','idea',
    'Remembered evaluations of brief experiences can give duration little weight even when duration is known.', ['Q492','Q1126970'],
    'Underweighting episode length is a specifically tested evaluation phenomenon, distinct from forgetting duration or memory broadly.',
    'https://bear.warrington.ufl.edu/brenner/mar7588/Papers/fredr-kahneman-jpsp1993.pdf',
    'General Discussion, PDF p. 10, lines 1029-1033, 1057-1070',
    'Fredrickson and Kahneman (1993), Duration Neglect in Retrospective Evaluations of Affective Episodes',parent='Q492',assertion='editorial',
    parent_note='The study’s remembered-experience evaluations establish the factual memory connection; memory is an editorial parent.',
    limits=['The authors caution about extrapolating seconds/minutes-long episodes to days or months; duration neglect is not failure to know duration.'],revision='Journal of Personality and Social Psychology 65(1), 1993, pp. 45-55')
add('local:catalog:inattentional-blindness','Inattentional blindness',['Inattentional blindness'],M,'Attention and conscious perception','idea',
    'Attention to a monitoring task can leave a visible unexpected event unnoticed.', ['local:catalog:inattentional-blindness'],
    'The same existing phenomenon and counting-task demonstration are retained; a new original-paper bundle does not create a new identity.',
    'https://www.chabris.com/Simons1999.pdf','Abstract and Introduction, PDF pp. 1-2, lines 32-56; Procedures and Results, PDF pp. 8-11',
    'Simons and Chabris (1999), Gorillas in our midst: sustained inattentional blindness for dynamic events',parent='Q160402',
    parent_note='The original authors explicitly study inattentional blindness as a form of visual perception without focused attention.',
    limits=['Unexpected-event detection differs by display, attended object, and task; no universal missed-event rate.'],revision='Perception 28, 1999, pp. 1059-1074')

ch4='https://www.cs.cornell.edu/home/kleinber/networks-book/networks-book-ch04.pdf'
add('local:catalog:homophily','Homophily',['Social homophily'],S,'Similarity in social ties','idea',
    'Social links tend to connect people who share characteristics, producing nonrandom friendship patterns.', ['Q17029202','Q2715623','local:catalog:triadic-closure'],
    'Similarity among connected people is distinct from heterophily, its opposite tendency, and from closing a triangle between friends of friends.',
    ch4,'4.1 Homophily, PDF pp. 2-3, lines 23-45 and 64-78',
    'Easley and Kleinberg (2010), Networks, Crowds, and Markets, Chapter 4',parent='Q2715623',
    parent_note='The chapter explicitly defines homophily as a principle affecting the structure and formation of social-network links.',
    limits=['An aggregate tendency, not a rule for every friendship; multiple selection and influence mechanisms can produce similarity.'],revision='Author preprint draft 2010-06-10')
add('local:catalog:focal-closure','Focal closure',['Shared-focus closure'],S,'Activity-mediated tie formation','idea',
    'Two people can form a social tie because they participate in the same activity or organization.', ['local:catalog:triadic-closure','Q2715623'],
    'The shared neighbor is an activity focus and the new edge is person-to-person; baseline triadic closure uses a shared person.',
    ch4,'4.3, Co-Evolution of Social and Affiliation Networks, PDF p. 12, lines 370-374',
    'Easley and Kleinberg (2010), Networks, Crowds, and Markets, Chapter 4',parent='Q2715623',
    parent_note='The source identifies focal closure as one mechanism of social-link formation within social-affiliation networks.',
    limits=['A proposed tendency, not proof that a particular friendship arose from shared membership.'])
add('local:catalog:membership-closure','Membership closure',['Friend-mediated affiliation'],S,'Social recruitment into activities','idea',
    'A person may join an activity that a friend already participates in.', ['local:catalog:triadic-closure','Q2715623'],
    'The new edge links a person to a focus, distinct from focal closure’s new friendship and triadic closure’s person-person link.',
    ch4,'4.3, Co-Evolution of Social and Affiliation Networks, PDF pp. 12-13, lines 375-402',
    'Easley and Kleinberg (2010), Networks, Crowds, and Markets, Chapter 4',parent='Q2715623',
    parent_note='The source explicitly presents membership closure as a social-influence mechanism in social-affiliation networks.',
    limits=['A modeled mechanism; actual affiliation may have several causes.'])
add('local:catalog:complex-contagion','Complex contagion',['Complex social contagion'],S,'Social reinforcement and diffusion','idea',
    'Some behaviors require reinforcement from multiple contacts, changing how network bridges support their spread.', ['Q106283193','local:catalog:weak-ties','local:catalog:local-bridge-in-a-network'],
    'The named multi-contact adoption process is distinct from generic social contagion or diffusion of information through one contact.',
    'https://ndg.asc.upenn.edu/wp-content/uploads/2016/04/Centola-Macy-2007-AJS.pdf','Abstract and Introduction, printed pp. 702-703 / PDF pp. 1-2, lines 9-19 and 45-59',
    'Centola and Macy (2007), Complex Contagions and the Weakness of Long Ties',parent='Q106283193',
    parent_note='The authors explicitly distinguish simple and complex social contagions, with complex contagion requiring social affirmation from multiple carriers.',
    limits=['The source studies formal diffusion models; weak ties do not universally impede reinforced behavior.'],revision='American Journal of Sociology 113(3), November 2007, pp. 702-734')
add('local:catalog:friendship-paradox','Friendship paradox',['Friends-have-more-friends paradox'],S,'Sampling bias in social networks','idea',
    'Sampling people through friendship links overrepresents people who have many friends.', ['Q2715623','Q7551269'],
    'A degree-weighted sampling phenomenon differs from homophily, friendship quality, or social-network analysis generally.',
    'https://www.journals.uchicago.edu/doi/abs/10.1086/229693?mobileUi=0','Abstract, lines 46-48',
    'Scott L. Feld (1991), Why Your Friends Have More Friends Than You Do',parent='Q2715623',
    parent_note='The original abstract explicitly explains comparisons of friend counts in a social network through disproportionate exposure to highly connected friends.',
    limits=['A statement about averages and sampling, not that every individual has fewer friends than every friend; strict inequality has regular-network exceptions.'],revision='AJS 96(6), 1991-05-01, pp. 1464-1477')
add('local:catalog:preferential-attachment','Preferential attachment',['Degree-preferential attachment'],S,'Network growth mechanisms','idea',
    'A node’s existing links can increase its chance of receiving new links, amplifying early differences.', ['local:authored:000046','Q909609'],
    'A specific degree-dependent link-formation rule differs from generic popularity and from the unrelated psychological attachment theory.',
    'https://www.cs.cornell.edu/home/kleinber/networks-book/networks-book-ch18.pdf',
    '18.3 Rich-Get-Richer Models, PDF pp. 5-6, lines 122-156 and 168-171',
    'Easley and Kleinberg (2010), Networks, Crowds, and Markets, Chapter 18',parent='local:authored:000046',assertion='editorial',
    parent_note='The source provides a network-growth model of link creation; network science is an editorial parent.',
    limits=['The textbook’s simplified copying/link model is illustrative, not a complete empirical account of popularity in every network.'],revision='Author preprint draft 2010-06-10')
add('local:catalog:schelling-segregation-model','Schelling segregation model',['Schelling model of segregation','Spatial segregation model'],S,'Local preferences and spatial patterns','idea',
    'Local neighbor preferences in a simplified movement model can create large segregated regions.', ['Q59816','Q17029202'],
    'The specifically named agent-on-grid mechanism differs from segregation as a social outcome and from homophily as an aggregate tie tendency.',
    ch4,'4.5 A Spatial Model of Segregation, PDF pp. 24-25, lines 727-779; model qualification and outcome, PDF p. 31, lines 934-969',
    'Easley and Kleinberg (2010), Networks, Crowds, and Markets, Chapter 4',parent='Q59816',relation='facet_of',
    parent_note='The source explicitly uses Schelling’s model to explain how spatial segregation can arise from local similarity preferences, including race.',
    limits=['A stylized two-type grid model; it does not claim real segregation has one cause or that modeled preferences are direct measurements of people.'])

for p in document['proposals']:
    p['alias_checks']=[dict(query=q, normalized_key=key(q), matched_ids=baseline['aliases'].get(key(q),[])) for q in [p['label'],*p['aliases']]]
    if p['inventory_status']=='proposed_new': assert not any(a['matched_ids'] for a in p['alias_checks']), p['id']
document['status']='in_progress'
document['checkpoint_counts']=dict(total=len(document['proposals']),primary_domains=dict(Counter(p['primary_domain'] for p in document['proposals'] if p['selection_role']=='primary')))
path.write_text(json.dumps(document,indent=2,ensure_ascii=False)+'\n')
(ROOT/'source-records.json').write_text(json.dumps(document['sources_inspected'],indent=2,ensure_ascii=False)+'\n')
print(document['checkpoint_counts'])
