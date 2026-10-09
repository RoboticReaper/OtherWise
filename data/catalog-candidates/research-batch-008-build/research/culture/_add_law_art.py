"""Manually researched law and visual art cards; local assembly only."""
from datetime import datetime, timezone
from _draft_tools import HERE, read, write, assemble

sources = read(HERE / 'draft-sources-inspected.json')
now = datetime.now(timezone.utc).isoformat()
titles = {
 'echr-pilot-judgments':'Factsheet – Pilot judgments',
 'echr-article-8-guide':'Guide on Article 8 of the European Convention on Human Rights: Right to respect for private and family life, home and correspondence',
 'met-estampe-originale':"L'Estampe Originale: A Rare Print Portfolio Now Online",
}
reinspected = {'un-vienna-treaties','un-rome-complementarity','echr-pilot-judgments','echr-article-8-guide',
    'unhcr-refoulement-note','met-estampe-originale','wsn-shibori','met-kanoko-1975-37',
    'met-itoh-furisode-1997-228','met-kintsugi','smithsonian-gyotaku'}
for s in sources:
    if s['id'] in titles: s['title'] = titles[s['id']]
    if s['id'] in reinspected:
        s.setdefault('selection_inspected_at',s['inspected_at'])
        s['inspected_at'] = now
        s['acquisition']['local_inspection_completed_at'] = now
write(HERE / 'draft-sources-inspected.json',sources)

drafts = read(HERE / 'draft-cards.json')
cards = {
 'Q603959': dict(
    body='Proportionality is a legal test relating a restriction to its justification. Under European Convention Article 8 review, officials must show a pressing social need and measures proportionate to a legitimate aim. Calling an interference useful does not by itself establish necessity.',
    takeaway='Distinguish a legitimate aim from a proportionate restriction.',
    gap='The inspected European rights example does not establish a universal parent for the general legal principle.'),
 'local:catalog:echr-margin-of-appreciation': dict(
    body='The margin of appreciation is discretion allowed to national authorities in European human rights review. They initially assess a restriction’s necessity, but the Court can review their decision. Its breadth varies with the issues and interests involved, so discretion does not settle legality.',
    takeaway='Connect national discretion with continuing judicial review.',
    parent_note='Article 8 review permits qualified national discretion.'),
 'local:catalog:echr-pilot-judgment-procedure': dict(
    body='The pilot judgment procedure lets the European Court of Human Rights address structural problems behind repetitive applications. It selects representative cases and indicates remedial measures to governments. Related cases may be paused while national action proceeds, with examination resumable when justice requires.',
    takeaway='Link individual cases with remedies for a systemic problem.',
    parent_note='Pilot judgments address systemic violations of Convention rights.'),
 'local:catalog:icc-complementarity': dict(
    body='Complementarity gives the International Criminal Court a role alongside national criminal justice. Under the inspected Rome Statute, genuine domestic investigation or prosecution can make a case inadmissible. Proceedings that shield a suspect illustrate unwillingness; other jurisdiction and admissibility conditions also apply.',
    takeaway='Evaluate genuine domestic proceedings before ICC admissibility.',
    parent_note='Articles 1 and 17 establish the ICC’s complementary role.'),
 'local:catalog:treaty-reservations': dict(
    body='A treaty reservation is a state’s unilateral statement seeking to exclude or change provisions’ legal effect for itself. The Vienna Convention limits reservations, including those incompatible with a treaty’s object and purpose.',
    takeaway='Recognize reservations and limits.',
    evidence_note='Articles inspected.',parent_note='Reservations qualify treaty provisions.'),
 'local:catalog:pacta-sunt-servanda': dict(
    body='Pacta sunt servanda requires parties to perform treaties in force in good faith. Article 26 of the Vienna Convention joins two obligations: a treaty binds its parties, and those parties must carry it out.',
    takeaway='Connect binding force with performance.',
    evidence_note='Article inspected.',parent_note='The rule governs treaty performance.'),
 'local:catalog:subsequent-practice-treaty-interpretation': dict(
    body='Subsequent practice can inform treaty interpretation when later application establishes the parties’ agreement about meaning. Article 31 of the Vienna Convention requires that agreement, so an isolated later act cannot automatically settle a disputed interpretation.',
    takeaway='Identify agreement through later application.',
    evidence_note='Article inspected.',parent_note='Treaty practice informs interpretation.'),
 'local:catalog:jus-cogens': dict(
    body='Jus cogens denotes peremptory norms accepted by the international community of states as a whole, permitting no derogation. Under Vienna Convention Article 53, a treaty conflicting with such a norm when concluded is void; ordinary agreement cannot override it.',
    takeaway='Recognize limits on treaty agreement.',
    evidence_note='Article inspected.',parent_note='Peremptory norms constrain international law.'),
 'local:catalog:non-refoulement': dict(
    body='Non-refoulement protects people against return to prohibited danger. UNHCR’s account explains that refugee protection can apply before formal status recognition: returning an applicant prematurely could defeat it. Applicable dangers and exceptions depend on the governing refugee or human rights instrument.',
    takeaway='Connect protection before recognition with instrument-specific rules.',
    parent_note='The note locates non-refoulement in international refugee law.'),
 'local:catalog:chine-colle': dict(
    body='Chine collé prints an image on thin paper adhered to a thicker backing during printing. Starch adhesive and pressure join the sheets, while the thin paper’s tone and surface affect the image. Redon’s gray paper supplies a background hue in The Buddha.',
    takeaway='See paper tone as part of the printed image.',
    parent_note='Chine collé is explicitly defined as a printing process.'),
 'local:catalog:lestampe-originale': dict(
    body='L’Estampe Originale was a print portfolio issued in nine installments from 1893 to 1895. Its range of media depended on collaboration between artists and professional printers. These partnerships enabled technical experiments, making the printer’s expertise part of artistic production.',
    takeaway='Connect artistic experimentation with professional printers’ expertise.',
    parent_note='The portfolio collected collaborative experimental printmaking.'),
 'local:catalog:redon-buddha-1895': dict(
    body='Odilon Redon’s 1895 lithograph The Buddha appeared in the ninth L’Estampe Originale album. Printed using chine collé, it combines black ink with light gray paper. The Met’s account shows how the paper itself contributes the image’s cool background tone.',
    takeaway='Identify paper color’s contribution to this lithograph.',
    parent_note='The Buddha is identified in the portfolio’s ninth album.'),
 'local:catalog:shibori': dict(
    body='Shibori is shaped resist dyeing: fabric is folded, gathered, bound or clamped into three dimensional forms before coloring. When the cloth is flattened, its pattern records both the shape and the pressure that restricted dye access. Structure becomes visible as surface design.',
    takeaway='Relate three dimensional shaping to the resulting dye pattern.',
    parent_note='The practitioner network defines shibori as shaped resist dyeing.',
    locator='Definition, lines 128–131'),
 'local:catalog:kanoko-shibori': dict(
    body='Kanoko shibori is a resist dyeing method that binds small pinches of cloth before dyeing. Releasing the ties produces tiny undyed details, often squares with central dots. A Met robe illustrates how many individually tied units create an extensive patterned surface.',
    takeaway='Connect individual bindings with a repeated dot pattern.',
    parent_note='The Met describes kanoko as a shibori variant.'),
 'local:catalog:itoh-furisode-met-1997-228': dict(
    body='Takuo Itoh’s 1995 furisode kimono demonstrates shibori at the scale of an entire garment. A continuous dyed pattern crosses the back seam and extends from body to sleeves. Planning on fabric of fixed width aligns areas that garment construction later joins.',
    takeaway='Trace a planned dye pattern across garment seams.',
    parent_note='The museum explicitly identifies this garment’s shibori technique.'),
 'local:catalog:kintsugi': dict(
    body='Kintsugi is the Japanese art of repairing broken ceramics with gold lacquer. The repair restores function while giving damage a visible artistic role. The Met interprets this treatment as enhancing a prized object’s value, a curatorial judgment rather than a universal price rule.',
    takeaway='Understand visible repair as an artistic treatment of damage.',
    parent_note='The exhibition identifies kintsugi within Japanese ceramic art.'),
 'local:catalog:gyotaku': dict(
    body='Gyotaku transfers a fish’s surface to paper by rubbing it over an inked specimen. The print records details of shape and texture. In a Smithsonian educational version, rubber replicas replace real fish; excessive paint blurs the transfer, making material quantity part of the result.',
    takeaway='Connect transferred detail with paint quantity and surface contact.',
    parent_note='Documented ink and paper transfer supports this printmaking placement.')
}
for cid,c in cards.items():
    assert 30 <= len(c['body'].split()) <= 50, (cid,len(c['body'].split()))
drafts.update(cards)
write(HERE / 'draft-cards.json',drafts)
assemble()
