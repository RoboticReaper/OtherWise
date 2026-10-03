import {buildFocusRequest, focusIdentity, validateFocusResponse} from './core/focus-contract.js';

class FocusError extends Error {}
const validRequestId = value => typeof value === 'string' && value.length > 0 && value.length <= 120;

/** Owner objects come from trusted runtime Ports; no saved interests are read here. */
export function createFocusTransport({catalog, loadIdentity, getConnection, hasEndpointPermission, fetchImpl = fetch}) {
  const catalogById = new Map(catalog.map(row => [row.topic, row]));
  const active = new Map(), listeners = new Set();
  let revision = 0;
  function cancel(owner, requestId) {
    const request = active.get(owner);
    if (request && (requestId === undefined || requestId === request.requestId)) {
      request.controller.abort(new FocusError('Focus request cancelled.'));
      active.delete(owner);
    }
  }
  function invalidate() {
    revision++;
    for (const owner of active.keys()) cancel(owner);
    for (const listener of listeners) { try { listener(); } catch { /* One window cannot block others. */ } }
  }
  function subscribeInvalidation(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }
  async function request(owner, {requestId, topicId, options = {}} = {}) {
    if (!owner || typeof owner !== 'object' || !validRequestId(requestId)) throw new FocusError('Invalid Focus request.');
    cancel(owner);
    const controller = new AbortController(), startedRevision = revision;
    const slot = {requestId, controller};
    active.set(owner, slot);
    let rejectAbort;
    const aborted = new Promise((_, reject) => { rejectAbort = () => reject(controller.signal.reason); });
    controller.signal.addEventListener('abort', rejectAbort, {once: true});
    const timer = setTimeout(() => controller.abort(new FocusError('The Focus request took too long. Try again.')), 30000);
    try {
      const connection = getConnection();
      if (!connection || typeof connection.endpoint !== 'string' || !connection.endpoint ||
          typeof connection.accessToken !== 'string' || !connection.accessToken ||
          !Number.isSafeInteger(connection.epoch) || connection.epoch < 0) {
        throw new FocusError('Add your connection and team access code in Settings.');
      }
      function assertCurrent() {
        const current = getConnection();
        if (controller.signal.aborted || active.get(owner) !== slot || revision !== startedRevision ||
            current.epoch !== connection.epoch || current.endpoint !== connection.endpoint || current.accessToken !== connection.accessToken) {
          throw new FocusError('Focus request cancelled because the connection changed.');
        }
      }
      async function checkPermission() {
        const allowed = await hasEndpointPermission(connection.endpoint);
        assertCurrent();
        if (!allowed) {
          invalidate();
          throw new FocusError('Save the connection in Settings to allow this service.');
        }
      }
      const computation = (async () => {
        const identity = focusIdentity(await loadIdentity());
        assertCurrent();
        const body = buildFocusRequest(topicId, identity, options, catalogById);
        await checkPermission();
        // The final epoch check and upload are synchronous: a reset cannot fit between them.
        assertCurrent();
        const response = await fetchImpl(`${connection.endpoint}/api/focus`, {
          method: 'POST', headers: {'Content-Type': 'application/json', Authorization: `Bearer ${connection.accessToken}`},
          body: JSON.stringify(body), credentials: 'omit', redirect: 'error', signal: controller.signal,
        });
        assertCurrent();
        if (!response.ok) {
          const messages = {401: 'The team access code was not accepted. Check Settings.',
            403: 'This connection is not permitted.', 409: 'The service and Galaxy data do not match. Update the data before trying again.',
            422: 'The Focus topic or settings were not accepted.', 429: 'The service is busy. Try again shortly.',
            503: 'The recommendation model is warming up. Try again shortly.'};
          throw new FocusError(messages[response.status] || 'The service could not complete the Focus request.');
        }
        const raw = await response.text();
        assertCurrent();
        if (raw.length > 150000) throw new FocusError('The Focus service response was too large.');
        const result = validateFocusResponse(JSON.parse(raw), body, catalogById);
        await checkPermission();
        assertCurrent();
        return result;
      })();
      return await Promise.race([computation, aborted]);
    } catch (error) {
      if (controller.signal.aborted) throw controller.signal.reason;
      throw error instanceof FocusError ? error : new FocusError('The Focus data is unavailable or invalid. Check the connection and try again.');
    } finally {
      clearTimeout(timer);
      controller.signal.removeEventListener('abort', rejectAbort);
      if (active.get(owner) === slot) active.delete(owner);
    }
  }
  // Every explicit request fetches fresh data. The per-window session owns the LRU.
  return {request, cancel, invalidate, subscribeInvalidation};
}
