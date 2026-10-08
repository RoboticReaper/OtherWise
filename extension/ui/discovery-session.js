// A retained batch belongs to the page that was already displaying its token.
export function discoverySession(previous, state, active = true) {
  const batch = state?.recommendationBatch;
  if (!active || !batch) return null;
  return state.lastUpdated != null || previous?.token === batch.token ? batch : null;
}
