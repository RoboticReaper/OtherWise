export const PAGE_SIZE = 10;

export function paginate(items, page, pageSize = PAGE_SIZE) {
  const list = Array.isArray(items) ? items : [];
  const size = Number.isFinite(pageSize) && pageSize >= 1 ? Math.floor(pageSize) : PAGE_SIZE;
  const total = list.length;
  const pageCount = Math.max(1, Math.ceil(total / size));
  const current = Math.min(pageCount, Math.max(1, Number.isFinite(page) ? Math.floor(page) : 1));
  const offset = (current - 1) * size;
  return { items: list.slice(offset, offset + size), page: current, pageCount, total, start: total ? offset + 1 : 0, end: Math.min(total, offset + size) };
}
