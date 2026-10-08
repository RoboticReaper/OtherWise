import {paginate} from './pagination.js';

export function candidateReviewPage(items, page, desktop = false) {
  return paginate(items, page, desktop ? 8 : 5);
}

export function reviewPanelHeight(viewportHeight, panelTop) {
  return Math.max(260, Math.min(680, viewportHeight - panelTop - 28));
}
