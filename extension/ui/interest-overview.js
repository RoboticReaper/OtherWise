const rows = value => Array.isArray(value) ? value.filter(row => row && typeof (row.id || row.topic) === 'string' && (row.id || row.topic).trim()) : [];
const unique = items => [...new Map(items.map(row => [row.id || row.topic, row])).values()];

/** A bounded, local summary. Counts describe saved/search records, not inferred preferences. */
export function summarizeInterests(state) {
  const approved = unique(rows(state?.approved));
  const counts = new Map();
  let unclassifiedCount = 0;
  for (const row of approved) {
    const name = typeof row.domain === 'string' ? row.domain.trim() : '';
    if (!name || name.toLowerCase() === 'custom') { unclassifiedCount++; continue; }
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  const domains = [...counts].map(([name,count]) => ({name,count})).sort((a,b) => b.count-a.count || a.name.localeCompare(b.name));
  const byTime = rows(state?.explored).slice().reverse().sort((a,b) => (Number.isFinite(b.at) ? b.at : -Infinity) - (Number.isFinite(a.at) ? a.at : -Infinity));
  const seen = new Set();
  const explored = byTime.filter(row => { const id=row.id || row.topic; if (seen.has(id)) return false; seen.add(id); return true; });
  return {savedCount:approved.length,domainCount:domains.length,unclassifiedCount,
    domains:domains.slice(0,4),otherClassifiedCount:domains.slice(4).reduce((sum,row) => sum+row.count,0),
    exploredCount:explored.length,recent:explored.slice(0,3)};
}
