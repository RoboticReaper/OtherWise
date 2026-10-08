export const LOCAL_ENDPOINT = 'http://127.0.0.1:8000';

export function normalizeEndpoint(value) {
  let u;
  try { u = new URL(String(value).trim()); } catch { throw new Error('Enter a valid service address.'); }
  if (u.username || u.password || u.search || u.hash || (u.pathname && u.pathname !== '/')) throw new Error('Use only the service address, without a path or credentials.');
  if (u.protocol !== 'https:' && !(u.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(u.hostname))) throw new Error('Use HTTPS, or a local development address.');
  return u.origin;
}

export function isLocalEndpoint(endpoint) {
  try { return new URL(normalizeEndpoint(endpoint)).protocol === 'http:'; } catch { return false; }
}

export function hasServiceConnection(connection) {
  return Boolean(connection?.endpoint && (connection.accessToken || isLocalEndpoint(connection.endpoint)));
}

export function connectionHeaders(connection) {
  return {'Content-Type': 'application/json', ...(connection.accessToken ? {Authorization: `Bearer ${connection.accessToken}`} : {})};
}
