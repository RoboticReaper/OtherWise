const priority = {selected: 0, hovered: 1, saved: 2, domain: 3};
const intersects = (a, b) => a.x < b.x + b.width + 4 && a.x + a.width + 4 > b.x && a.y < b.y + b.height + 3 && a.y + a.height + 3 > b.y;

/** Selected and hovered annotations are independent of both persisted label switches. */
export function galaxyLabelCandidates(data, view, state, saved, recommended, hovered) {
  const labels = [], used = new Set();
  const add = (id, kind) => { const topic = data.byId.get(id); if (!topic || used.has(id) || view.domain && topic.domain !== view.domain) return; used.add(id); labels.push({...topic, text: topic.topic, kind}); };
  add(view.selected, 'selected'); add(hovered, 'hovered');
  if (state.settings?.galaxyShowInterestLabels !== false) {
    add(state.focus, 'saved'); for (const id of saved) add(id, 'saved');
  }
  if (state.settings?.galaxyShowDomainLabels !== false) {
    for (const domain of data.domains) if (!view.domain || domain.id === view.domain) labels.push({...domain, text: domain.id, kind: 'domain'});
  }
  return labels;
}

/** Short captions without opaque boxes; greedy priority placement leaves controls unobscured. */
export function placeGalaxyLabels(candidates, viewport, measure, exclusions = [], zoom = 1) {
  const {width, height} = viewport, boxes = [...exclusions], placed = [];
  const domainLimit = Math.min(23, Math.round((width < 450 ? 4 : 8) * Math.sqrt(Math.max(1, zoom))));
  const interestLimit = Math.min(70, Math.round((width < 450 ? 6 : 14) * Math.sqrt(Math.max(1, zoom))));
  let domains = 0, interests = 0;
  for (const candidate of [...candidates].sort((a, b) => priority[a.kind] - priority[b.kind])) {
    if (candidate.kind === 'domain' && domains >= domainLimit || candidate.kind === 'saved' && interests >= interestLimit) continue;
    if (candidate.x < 0 || candidate.x > width || candidate.y < 0 || candidate.y > height) continue;
    const maxWidth = Math.min(width - 28, candidate.kind === 'domain' ? 140 : 175);
    let text = candidate.text;
    while (measure(text, candidate.kind) > maxWidth && text.length > 3) text = text.slice(0, -2);
    if (text !== candidate.text) text = text.slice(0, -1) + '…';
    const textWidth = measure(text, candidate.kind);
    for (const [dx, dy] of [[9,-12],[9,22],[-textWidth-9,-12],[-textWidth-9,22],[9,-33],[9,43]]) {
      const x = Math.max(9, Math.min(width - textWidth - 9, candidate.x + dx)), y = candidate.y + dy;
      const box = {x:x-3, y:y-12, width:textWidth+6, height:17};
      if (box.y < 8 || box.y+box.height > height-8 || boxes.some(b => intersects(box,b))) continue;
      boxes.push(box); placed.push({...candidate,text,labelX:x,labelY:y,box});
      if (candidate.kind === 'domain') domains++; else if (candidate.kind === 'saved') interests++;
      break;
    }
  }
  return placed;
}
