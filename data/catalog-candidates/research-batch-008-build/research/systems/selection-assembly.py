"""Local assembly of inspected selection notes; no network or card generation."""
import json, re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[1] / 'baseline-index.json'
baseline = json.loads(BASE.read_text())
path = ROOT / 'proposals.json'
document = json.loads(path.read_text())
now = datetime.now(timezone.utc).isoformat()
key = lambda text: re.sub(r'[\s_\-\u2010-\u2015]+', ' ', text.strip().casefold()).strip()

def add(identifier, label, aliases, domain, subfield, scope, takeaway, nearby, boundary,
        url, locator, title, parent=None, relation='broader_topic', assertion='source_asserted',
        parent_note=None, limits=(), kind='idea', mode='web.run actual extracted HTML/PDF passage',
        revision=None, role='primary'):
    found = next((p for p in document['proposals'] if p['id'] == identifier), None)
    if found:
        return
    status = 'existing' if identifier in baseline['concepts'] else 'proposed_new'
    assert nearby and all(i in baseline['concepts'] for i in nearby)
    if parent:
        assert parent in baseline['concepts'] or any(p['id'] == parent for p in document['proposals'])
    row = dict(id=identifier, label=label, aliases=aliases, primary_domain=domain,
               primary_subfield=subfield, entity_kind=kind, scope=scope,
               learning_takeaway=takeaway, inventory_status=status,
               nearest_baseline_matches=[dict(id=i, label=baseline['concepts'][i]['label'], reason=boundary) for i in nearby],
               identity_reason=boundary,
               discovery_evidence=[dict(url=url, locator=locator, note=takeaway, inspection_mode=mode)],
               proposed_parent=(dict(target_id=parent, type=relation, assertion=assertion,
                                    url=url, locator=locator, note=parent_note or boundary) if parent else None),
               limits=list(limits), selection_role=role)
    if status == 'existing':
        b = baseline['concepts'][identifier]
        row['control_record_metadata'] = dict(original_description=b.get('original_description'),
            maximum_prior_card_version=b.get('latest_card_version',0),
            prior_bundles=[{k:c.get(k) for k in ['batch_id','batch_revision','source_bundle_path','source_bundle_sha256']} for c in b.get('candidate_records',[])])
    document['proposals'].append(row)
    src=next((s for s in document['sources_inspected'] if s['url']==url),None)
    if src:
        if locator not in src['locator']: src['locator'] += '; ' + locator
    else:
        document['sources_inspected'].append(dict(id=f"systems-source-{len(document['sources_inspected'])+1:03}",title=title,url=url,locator=locator,
            revision=revision,acquired_at=now,acquisition_mode='Local timestamp after reading; exact remote retrieval time unavailable',inspection_mode=mode))

C='Computing & information'; E='Economics & organizations'; T='Engineering & transport'; G='Games & sports'
add('Q21198','Computer science',['Computer science'],C,'Computational problem solving','broad_field',
    'Algorithms and representations turn inputs into problem-solving outputs.', ['Q21198'],
    'Same broad field as the imported study-of-computation identity; a teaching perspective reuses the ID.',
    'https://cs50.harvard.edu/x/notes/0/','Computer Science and Problem Solving; Algorithms; Summing Up, lines 199-209, 327-331, 624-633',
    'CS50x 2026 Lecture 0',revision='2026 course notes')

school='https://www.tayfunsonmez.net/wp-content/uploads/2013/10/AbdulkadirogluSonmez-AER20031.pdf'
add('local:catalog:top-trading-cycles','Top trading cycles',['TTC','Top trading cycles mechanism'],E,'Matching market design','idea',
    'Directed preference-and-priority cycles assign seats simultaneously and remove completed trades.', ['Q620702','Q65123731'],
    'The cycle-trading algorithm is distinct from the deferred-acceptance procedure and from the stable-matching problem; its school-choice variant can trade efficiency against justified envy.',
    school,'II.B, printed pp. 736-737 / PDF pp. 8-9, steps 1-k and propositions 3-4',
    'Abdulkadiroglu and Sonmez (2003), School Choice: A Mechanism Design Approach',parent='local:authored:000608',assertion='editorial',
    parent_note='Editorial parent in game theory: the source analyzes strategic reports and allocations in a mechanism-design model.',
    limits=['Strict reported school rankings and exogenous priorities in the inspected school-choice formulation; do not transfer every property to all TTC variants.'],revision='AER 93(3), June 2003, pp. 729-747')
add('local:catalog:boston-immediate-acceptance-mechanism','Boston immediate acceptance mechanism',['Boston mechanism','Boston student assignment mechanism','Immediate acceptance mechanism'],E,'School choice mechanisms','facet_or_application',
    'Finalizing first-choice admissions before later rounds makes preference reporting strategically consequential.', ['Q65123731','Q620702'],
    'Immediate final assignments differ from deferred acceptance, which holds proposals tentatively; this is a separately described school-choice mechanism.',
    school,'I.A Boston Student Assignment Mechanism, printed pp. 732-733 / PDF pp. 4-5, rounds 1-k and strategy-proofness discussion',
    'Abdulkadiroglu and Sonmez (2003), School Choice: A Mechanism Design Approach',parent='local:authored:000608',assertion='editorial',
    parent_note='The source analyzes the strategy incentives of this allocation mechanism; game theory is an editorial navigation parent.',
    limits=['The Boston implementation is historical, as described in 2003; the card must not claim it is Boston’s current policy.'])
add('local:catalog:clarke-pivot-rule','Clarke pivot rule',['Clarke tax','Pivotal mechanism'],E,'Mechanism payments','idea',
    'A VCG payment measures the welfare effect a participant imposes on the other participants.', ['local:catalog:second-price-sealed-bid-auction','Q7731670'],
    'The externality payment rule applies to multi-outcome allocation problems; a single-item second-price auction is one special case, not the same general subject.',
    'https://people.csail.mit.edu/costis/6896sp10/Lecture21.pdf','VCG (with Clarke Pivot Rule), PDF page 7; path-auction example, pages 8-9',
    'MIT 6.896 Spring 2010 Lecture 21: Frugal Mechanism Design',parent='Q7731670',assertion='editorial',
    parent_note='Editorial parent: the lecture places the rule in the VCG incentive-compatible mechanism framework.',
    limits=['Quasilinear private-value mechanism setting; distinguish welfare effects and transfer sign conventions.'],revision='Spring 2010')
team='https://people.duke.edu/~qc2/BA532/1982%20Rand%20Holmstrom%20team.pdf'
add('local:catalog:moral-hazard-in-teams','Moral hazard in teams',['Team moral hazard'],E,'Team incentive contracts','facet_or_application',
    'Shared observable output with hidden individual actions creates a team-specific free-riding problem.', ['local:catalog:moral-hazard','Q1053211'],
    'A separately modeled multi-agent application with shared-output and budget-balance constraints, rather than another example of generic hidden action.',
    team,'Abstract and Introduction, printed p. 324 / PDF p. 1',
    'Holmstrom (1982), Moral Hazard in Teams',parent='local:catalog:moral-hazard',relation='facet_of',
    parent_note='The introduction explicitly defines the paper’s setting as a multiagent extension of the moral-hazard problem.',
    limits=['Model conclusion about non-budget-balanced incentives is conditional; no claim that all real teams require an outside principal.'],
    mode='Local rendered scanned PDF visually inspected (teams-page1.png)',revision='Bell Journal of Economics 13(2), 1982, pp. 324-340')
add('local:catalog:relative-performance-evaluation','Relative performance evaluation',['RPE'],E,'Informative incentive signals','idea',
    'Peers’ outcomes can help distinguish an individual’s contribution from shared uncertainty.', ['Q1414816','Q1053211'],
    'Using peer outcomes as an informative contractual signal is distinct from generic incentives, productivity, or team free-riding.',
    team,'Abstract, printed p. 324 / PDF p. 1',
    'Holmstrom (1982), Moral Hazard in Teams',parent='Q1414816',assertion='source_asserted',
    parent_note='The abstract explicitly investigates relative performance evaluation as a scheme to improve incentives using information about peer agents.',
    limits=['Selection is supported by the primary abstract; detailed assumptions about signal correlation should be inspected before drafting a mechanism claim.'],
    mode='Local rendered scanned PDF visually inspected (teams-page1.png)')
add('local:catalog:multitask-incentive-problem','Multitask incentive problem',['Multitask principal-agent problem','Multitask incentives'],E,'Incentives and job design','idea',
    'Rewarding measurable output can shift effort away from other valuable duties competing for attention.', ['Q1053211','Q1414816','Q2169419'],
    'The paper identifies a distinct multidimensional principal-agent model: allocation of attention across tasks, not merely hidden action or any unintended incentive.',
    'https://web.stanford.edu/~milgrom/publishedarticles/Multitask%20Principal%20Agent.pdf',
    'Introduction, printed pp. 24-26 / PDF pages 1-2, distinguishing mark and competing-attention paragraphs',
    'Holmstrom and Milgrom (1991), Multitask Principal-Agent Analyses: Incentive Contracts, Asset Ownership, and Job Design',
    parent='Q1053211',relation='facet_of',parent_note='The introduction explicitly contrasts multidimensional principal-agent models with one-dimensional models.',
    limits=['Effort substitution and measurement assumptions matter; this is not a general claim that incentive pay always lowers quality.'],
    mode='Local scanned PDF rendered with pypdfium2 and visually inspected (multitask-page1.png and multitask-page2.png)',revision='JLEO 7, Special Issue 1991, pp. 24-52')
add('local:catalog:market-unraveling','Market unraveling',['Unraveling in matching markets','Early contracting in matching markets'],E,'Matching market timing','idea',
    'Competition to secure matches can push offers earlier, before useful information becomes available.', ['Q620702','Q65123731'],
    'Timing instability in a decentralized matching market differs from a blocking pair or the matching algorithm itself.',
    'https://users.ssc.wisc.edu/~dquint/econ690/lecture%2014.pdf','Introduction, PDF page 1, lines 6-17, internship hiring moving earlier',
    'Dan Quint, Econ 690 Lecture 14: Matching',parent='Q620702',assertion='editorial',
    parent_note='The introductory matching-market history supplies the factual connection; the broader stable-matching problem is an editorial learning parent.',
    limits=['The passage is a historical internship-market example; do not universalize it to every matching market.'])

faa='https://www.faa.gov/sites/faa.gov/files/07_phak_ch5_0.pdf'
add('local:catalog:dutch-roll','Dutch roll',['Dutch-roll oscillation'],T,'Aircraft lateral and directional dynamics','idea',
    'Coupled roll and yaw oscillations can have weak damping and may require yaw dampers.', ['Q8424','Q765633'],
    'A defined lateral-directional oscillation mode rather than aerodynamics generally or a generic aircraft turn.',
    faa,'Chapter 5, Free Directional Oscillations (Dutch Roll), printed p. 5-20 / PDF p. 20',
    'FAA Pilot’s Handbook of Aeronautical Knowledge, Chapter 5: Aerodynamics of Flight',parent='Q8424',
    parent_note='This mode is explicitly taught within the handbook’s Aerodynamics of Flight chapter.',
    limits=['Damping varies by aircraft; the inspected text does not imply all aircraft have sustained oscillations.'],mode='Local official PDF passage extracted with pypdf and read')
add('local:catalog:p-factor','P-factor',['Asymmetric propeller loading','P-Factor'],T,'Propeller aerodynamics','idea',
    'High angle of attack gives propeller blades unequal loading and shifts thrust away from the shaft center.', ['Q205451','Q8424'],
    'A named asymmetry in propeller loading, distinct from torque reaction, gyroscopic precession, or adverse yaw.',
    faa,'Chapter 5, Asymmetric Loading (P-Factor), printed p. 5-32 / PDF p. 32',
    'FAA Pilot’s Handbook of Aeronautical Knowledge, Chapter 5: Aerodynamics of Flight',parent='Q205451',relation='facet_of',
    parent_note='The passage explains the mechanism through the rotating propeller blades and displacement of the thrust center.',
    limits=['Yaw direction depends on propeller rotation and viewpoint; preserve the high-angle-of-attack condition.'],mode='Local official PDF passage extracted with pypdf and read')
add('local:catalog:adverse-yaw','Adverse yaw',['Aileron adverse yaw'],T,'Aircraft control coupling','idea',
    'Unequal drag during an aileron roll can yaw an aircraft opposite to the intended bank.', ['Q1705284','Q8424'],
    'The differential-drag yaw accompanying aileron use is distinct from propeller P-factor and roll-yaw oscillation.',
    'https://www.faa.gov/sites/faa.gov/files/08_phak_ch6.pdf','Chapter 6, Adverse Yaw, printed p. 6-3 / PDF p. 3',
    'FAA Pilot’s Handbook of Aeronautical Knowledge, Chapter 6: Flight Controls',parent='Q1705284',relation='facet_of',
    parent_note='The aileron section explicitly explains the yaw produced by deflecting these flight-control surfaces.',
    limits=['This is the aileron-induced effect; avoid presenting it as every opposite-direction aircraft yaw.'],mode='Local official PDF passage extracted with pypdf and read')
add('local:catalog:etcs-braking-curve','ETCS braking curve',['ETCS braking curves','European Train Control System braking curve'],T,'Train speed supervision','facet_or_application',
    'A train-and-track model predicts speed against distance so ETCS can supervise braking toward a limit.', ['Q862562','Q4260703'],
    'A specific ETCS supervision calculation differs from the brake hardware, general railway signaling, and braking itself.',
    'https://www.era.europa.eu/domains/european-rail-traffic-management-system/braking-curves','Introduction and braking-curve prediction description, lines 15-21',
    'European Union Agency for Railways: Braking curves',parent='Q862562',relation='facet_of',
    parent_note='The source explicitly describes braking-curve computation as part of ETCS speed-and-position supervision.',limits=['A prediction uses train braking and track data; it is not a claim of exact realized stopping distance.'])
add('local:catalog:airport-surface-hotspot','Airport surface hotspot',['Runway safety hotspot','Airport hot spot'],T,'Airport surface safety','idea',
    'Published hotspot locations identify collision or incursion risk that deserves heightened attention.', ['Q184590','Q765633'],
    'A risk-designated location differs from a runway incursion incident; either history or potential risk can qualify.',
    'https://www.faa.gov/airports/runway_safety/hotspots','Hot spot definition, lines 114-117',
    'FAA: Hot Spots',parent='Q765633',parent_note='FAA defines this location on an aerodrome movement area as an aviation surface-safety subject.',
    limits=['U.S. FAA source terminology; chart locations can change. The card should explain the designation rather than identify a current location.'])
add('local:catalog:start-up-lost-time','Start-up lost time at a traffic signal',['Start-up lost time','Startup lost time'],T,'Traffic signal capacity','idea',
    'The first queued vehicles need extra reaction and acceleration time before steady discharge begins.', ['Q8004'],
    'The named initial lost-time quantity is different from saturation flow’s hypothetical hourly discharge and from intersection delay generally.',
    'https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter3.htm','3.1 Queuing and Discharge Characteristics, start-up lost time paragraph, lines 68-77',
    'FHWA Traffic Signal Timing Manual, Chapter 3: Traffic Signal Operation and Control',parent='Q8004',relation='facet_of',
    parent_note='The source defines start-up lost time for a queue starting to discharge after the traffic signal turns green.',
    limits=['The archived manual’s numerical defaults are not current universal values.'])
add('local:catalog:bus-queue-jump','Bus queue jump',['Queue jump lane','Queue jumper'],T,'Transit intersection priority','facet_or_application',
    'A short bus lane and early green let a transit vehicle bypass waiting traffic at an intersection.', ['Q1740966','Q8004'],
    'The combined lane-and-signal treatment differs from generic bus service or signal priority alone.',
    'https://www.transit.dot.gov/research-innovation/signal-priority','Queue Jumpers, lines 52-54',
    'Federal Transit Administration: Signal Priority',parent='Q1740966',relation='facet_of',
    parent_note='The official passage explicitly defines a short bus lane with signal priority to let buses pass a queue.',
    limits=['Official educational page last updated 2015-12-06; this passage supports the design concept, not a current engineering recommendation or universal delay benefit.'],revision='Last updated 2015-12-06')
add('Q11023','Engineering',['Engineering'],T,'Iterative design and testing','broad_field',
    'Prototyping, testing, and revision connect a problem definition with a workable solution.', ['Q11023'],
    'The same broad engineering identity already has card version 1; this new source perspective requires ID reuse.',
    'https://www.jpl.nasa.gov/edu/resources/lesson-plan/robotics-making-a-self-driving-rover/','Introduce the Challenge, lines 139-142; Criteria for Success and Engineering Constraints, lines 150-165',
    'NASA JPL: Robotics—Making a Self-Driving Rover')

fivb='https://www.fivb.com/wp-content/uploads/2025/01/FIVB-Volleyball_Rules2025_2028-EN.pdf'
add('local:catalog:volleyball-rotational-fault','Volleyball rotational fault',['Rotational fault in volleyball','Serving out of rotation'],G,'Volleyball service order','idea',
    'Serving out of rotation is a service-order fault with a correction and specified scoring consequences.', ['local:authored:000287'],
    'Rule 7.7 names wrong service order, distinct from a positional fault involving players’ locations.',
    fivb,'7.7 Rotational Fault, printed p. 23 / PDF p. 25, lines 824-840',
    'FIVB Official Volleyball Rules 2025-2028',parent='local:authored:000287',relation='facet_of',
    parent_note='The named fault is one of the official game rules for volleyball service order.',
    limits=['Apply the FIVB 2025-2028 rule set; distinguish rotational fault from positional fault.'],revision='2025-2028 edition, effective 2025-01-01')
tennis='https://www.itftennis.com/media/7221/2026-rules-of-tennis-english.pdf'
add('local:catalog:tennis-service-let','Tennis service let',['Service let','Let on service'],G,'Tennis service rules','idea',
    'A qualifying service let repeats that serve while preserving an earlier service fault.', ['Q847'],
    'A specifically defined nullified serve differs from a fault and from a general rally let.',
    tennis,'Rule 22 The Let During a Service, printed p. 9 / PDF p. 11, lines 342-350',
    'ITF Rules of Tennis 2026',parent='Q847',relation='facet_of',parent_note='Rule 22 defines the service let as part of the tennis rules.',
    limits=['The standard ITF rule is inspected; Appendix VI permits alternative no-let procedures.'],revision='2026 edition')
add('local:catalog:wheelchair-tennis-two-bounce-rule','Wheelchair tennis two-bounce rule',['Two-bounce rule in wheelchair tennis'],G,'Wheelchair tennis adaptations','facet_or_application',
    'A wheelchair player may return after two bounces, and the second bounce may fall outside the court.', ['Q847','Q191931'],
    'This named wheelchair-tennis rule is a separately specified adaptation rather than generic tennis or wheelchair use.',
    tennis,'Rules of Wheelchair Tennis, a. The Two Bounce Rule, printed p. 16 / PDF p. 18, lines 568-571',
    'ITF Rules of Tennis 2026',parent='Q847',relation='facet_of',parent_note='The Rules of Wheelchair Tennis explicitly introduce exceptions to the ITF Rules of Tennis.',
    limits=['The first bounce still follows the ordinary court-boundary rule.'])
add('local:catalog:rugby-union-advantage','Advantage in rugby union',['Rugby advantage','Advantage law in rugby'],G,'Rugby refereeing','facet_or_application',
    'Play can continue after infringement when the opponents gain clear tactical or territorial advantage.', ['Q5849'],
    'The separately named rugby Law 7 differs from advantage in other sports and from sports rules generally.',
    'https://passport.world.rugby/laws-of-the-game/laws-by-number/7-advantage/','Principle and 7.1-7.3, lines 38-59',
    'World Rugby Laws: 7 Advantage',parent='Q5849',relation='facet_of',parent_note='World Rugby expressly makes advantage a law governing rugby play.',
    limits=['Advantage must be clear and real, with stated Law 7 exceptions; continuation is not automatic for every infringement.'])
add('local:catalog:duckworth-lewis-stern-method','Duckworth–Lewis–Stern method',['DLS method','Duckworth Lewis Stern'],G,'Interrupted cricket matches','idea',
    'DLS recalculates targets when limited-overs cricket loses playing time; overs and wickets define scoring resources.', ['local:authored:000291','Q7435308'],
    'A distinct target-adjustment methodology rather than cricket itself or simple proportional overs-based scoring.',
    'https://www.icc-cricket.com/about/cricket/rules-and-regulations/duckworth-lewis-stern?appview=true','Duckworth Lewis Stern introduction, lines 9-14',
    'ICC: Duckworth Lewis Stern',parent='local:authored:000291',relation='facet_of',
    parent_note='ICC explicitly describes its adopted DLS method for interrupted cricket matches.',
    limits=['The linked methodology describes D-L Standard Edition mechanics as fallback; do not claim its table or numerical formula is the current professional DLS calculator.'])
last=next(p for p in document['proposals'] if p['id']=='local:catalog:duckworth-lewis-stern-method')
if not any(e['url']=='https://images.icc-cricket.com/image/upload/prd/orlbya4cqyhqaceje3b2.pdf' for e in last['discovery_evidence']):
    last['discovery_evidence'].append(dict(url='https://images.icc-cricket.com/image/upload/prd/orlbya4cqyhqaceje3b2.pdf',locator='Opening status statement and section 1, PDF p. 1, lines 1-20',note='Stern Edition requires the ICC calculator; Standard Edition fallback uses overs and wickets jointly as resources.',inspection_mode='web.run actual official PDF passage'))
add('Q11413','Go (board game)',['Go','Go (game)','Go (board game)'],G,'Territory and capture games','topic',
    'Stones share orthogonal liberties, tying local capture to the larger contest for territory.', ['Q11413','Q37227'],
    'The existing board-game identity is reused; Q37227 is the unrelated Go programming-language sense of the same name.',
    'https://britgo.org/intro/intro2.html','The rules; Capturing stones and counting liberties; Strings, lines 11-25 and 38-40',
    'British Go Association: How to Play',kind='named_subject',limits=['This guide uses territory plus prisoners scoring; do not imply all Go rule sets use identical scoring.'])

for p in document['proposals']:
    p['alias_checks'] = [dict(query=q, normalized_key=key(q), matched_ids=baseline['aliases'].get(key(q),[])) for q in [p['label'],*p['aliases']]]
    if p['inventory_status']=='proposed_new':
        collisions=[a for a in p['alias_checks'] if a['matched_ids']]
        assert not collisions, (p['id'],collisions)
document['status']='in_progress'
document['checkpoint_counts']=dict(total=len(document['proposals']),primary_domains=dict(Counter(p['primary_domain'] for p in document['proposals'] if p['selection_role']=='primary')))
path.write_text(json.dumps(document,indent=2,ensure_ascii=False)+'\n')
(ROOT/'source-records.json').write_text(json.dumps(document['sources_inspected'],indent=2,ensure_ascii=False)+'\n')
print(document['checkpoint_counts'])
