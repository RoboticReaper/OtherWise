import {paginate} from './pagination.js';

const normalize = value => String(value ?? '').normalize('NFKC').trim().toLowerCase();

export function savedInterestPage(interests, query, page, desktop = false) {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  const filtered = (Array.isArray(interests) ? interests : []).filter(topic => {
    const title = normalize(topic.topic || topic.id);
    return words.every(word => title.includes(word));
  });
  return paginate(filtered, page, desktop ? 8 : 6);
}

export function togglePageSelection(selected, topics) {
  const next = new Set(selected);
  const ids = topics.map(topic => topic.id || topic.topic);
  const clear = ids.every(id => next.has(id));
  ids.forEach(id => clear ? next.delete(id) : next.add(id));
  return next;
}
