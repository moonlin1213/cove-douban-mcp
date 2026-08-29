import {
  ArgumentError,
  AuthRequiredError,
  CommandExecutionError,
  EmptyResultError,
} from '@jackwener/opencli/errors';

import {
  extractChart,
  extractMarks,
  extractSubject,
  pageRequiresLogin,
} from './extractors.js';

export {
  ArgumentError,
  AuthRequiredError,
  CommandExecutionError,
  EmptyResultError,
};

export function normalizeLimit(value, defaultValue, maximum, { allowZero = false } = {}) {
  const raw = value ?? defaultValue;
  const limit = Number(raw);
  if (!Number.isInteger(limit) || limit < 0 || (!allowZero && limit === 0)) {
    throw new ArgumentError(
      allowZero
        ? 'limit must be a non-negative integer'
        : 'limit must be a positive integer',
    );
  }
  if (limit > maximum) {
    throw new ArgumentError(`limit must be <= ${maximum}`);
  }
  return limit;
}

export function normalizeChoice(value, choices, label) {
  const normalized = String(value || '').trim();
  if (!choices.includes(normalized)) {
    throw new ArgumentError(`${label} must be one of: ${choices.join(', ')}`);
  }
  return normalized;
}

export function normalizeNumericId(value, label) {
  const normalized = String(value || '').trim();
  const match = normalized.match(/(?:^|\/)(\d+)(?:\/|$)/);
  if (!match) throw new ArgumentError(`${label} must contain a numeric ID`);
  return match[1];
}

export async function evaluateExtractor(page, extractor, ...arguments_) {
  const serialized = arguments_.map((value) => JSON.stringify(value)).join(',');
  return page.evaluate(
    `(${extractor.toString()})(document${serialized ? `,${serialized}` : ''})`,
  );
}

export async function navigateVisiblePage(page, url, readySelector = 'body') {
  try {
    await page.goto(url);
    await page.wait({ selector: readySelector, timeout: 10 }).catch(() => {});
  } catch (error) {
    throw new CommandExecutionError(
      `Douban page load failed: ${error?.message || String(error)}`,
    );
  }
  if (await evaluateExtractor(page, pageRequiresLogin)) {
    throw new AuthRequiredError(
      new URL(url).hostname,
      'Sign in to Douban in the Chrome session used by OpenCLI.',
    );
  }
}

export async function resolveUid(page, providedUid = '') {
  const normalized = String(providedUid || '').trim();
  if (normalized) {
    if (!/^[A-Za-z0-9._-]+$/.test(normalized)) {
      throw new ArgumentError('uid contains unsupported characters');
    }
    return normalized;
  }
  await navigateVisiblePage(page, 'https://www.douban.com/mine/', 'body');
  let uid = '';
  for (let attempt = 0; attempt < 10 && !uid; attempt += 1) {
    const href = await page.evaluate('location.href');
    uid = String(href || '').match(/\/people\/([^/]+)/)?.[1] || '';
    if (!uid && attempt < 9) await page.wait({ time: 0.5 });
  }
  if (!uid) {
    throw new AuthRequiredError(
      'www.douban.com',
      'The current signed-in Douban user could not be identified.',
    );
  }
  return uid;
}

export async function fetchMarkRows(
  page,
  uid,
  status,
  requestedLimit,
  requestedOffset = 0,
) {
  const rows = [];
  let offset = requestedOffset;
  const maximum = requestedLimit === 0 ? 2000 : requestedLimit;
  while (rows.length < maximum) {
    const url = new URL(`https://movie.douban.com/people/${encodeURIComponent(uid)}/${status}`);
    url.searchParams.set('start', String(offset));
    url.searchParams.set('sort', 'time');
    url.searchParams.set('rating', 'all');
    url.searchParams.set('filter', 'all');
    url.searchParams.set('mode', 'grid');
    await navigateVisiblePage(page, url.toString(), '.grid-view, .item');
    const pageRows = await evaluateExtractor(page, extractMarks, status);
    if (!Array.isArray(pageRows)) {
      throw new CommandExecutionError('Douban marks returned an unexpected page shape');
    }
    if (pageRows.length === 0) break;
    rows.push(...pageRows);
    if (pageRows.length < 15) break;
    offset += 15;
  }
  if (rows.length === 0 && requestedOffset === 0) {
    throw new EmptyResultError('douban marks', `No ${status} marks were visible`);
  }
  return requestedLimit === 0 ? rows : rows.slice(0, requestedLimit);
}

export async function loadSubjectRow(page, subjectId, subjectType = 'movie') {
  const hostname = subjectType === 'book' ? 'book.douban.com' : 'movie.douban.com';
  await navigateVisiblePage(
    page,
    `https://${hostname}/subject/${encodeURIComponent(subjectId)}/`,
    'h1',
  );
  const row = await evaluateExtractor(page, extractSubject, subjectId, subjectType);
  if (!row?.title) {
    throw new EmptyResultError(
      'douban subject',
      `Subject ${subjectId} was not visible`,
    );
  }
  return row;
}

const CHART_SPECS = Object.freeze({
  movie_weekly: {
    url: 'https://movie.douban.com/chart',
    selector: '#listCont2',
    maximum: 10,
  },
  movie_north_america: {
    url: 'https://movie.douban.com/chart',
    selector: '#listCont1',
    maximum: 10,
  },
  movie_new: {
    url: 'https://movie.douban.com/chart',
    selector: '.article',
    maximum: 40,
  },
  movie_top250: {
    url: 'https://movie.douban.com/top250',
    selector: 'ol.grid_view',
    maximum: 250,
    pageSize: 25,
  },
  book_hot: {
    url: 'https://book.douban.com/chart',
    selector: '#content .article',
    maximum: 50,
  },
  music_hot: {
    url: 'https://music.douban.com/chart',
    selector: '#content .article',
    maximum: 50,
  },
});

export async function fetchChartRows(page, board, requestedLimit = 10) {
  const normalizedBoard = normalizeChoice(board, Object.keys(CHART_SPECS), 'board');
  const spec = CHART_SPECS[normalizedBoard];
  const limit = normalizeLimit(requestedLimit, 10, spec.maximum);
  const pageSize = spec.pageSize || limit;
  const pageCount = Math.ceil(limit / pageSize);
  const rows = [];

  for (let pageIndex = 0; pageIndex < pageCount; pageIndex += 1) {
    const url = new URL(spec.url);
    if (spec.pageSize) url.searchParams.set('start', String(pageIndex * spec.pageSize));
    const expectedUrl = url.toString();
    await navigateVisiblePage(page, expectedUrl, spec.selector);
    const actualUrl = String(await page.evaluate('location.href') || '');
    if (actualUrl !== expectedUrl) {
      throw new CommandExecutionError('Douban chart returned an unexpected page location');
    }
    const pageRows = await evaluateExtractor(page, extractChart, normalizedBoard);
    if (!Array.isArray(pageRows)) {
      throw new CommandExecutionError('Douban chart returned an unexpected page shape');
    }
    rows.push(...pageRows);
    if (pageRows.length < pageSize) break;
    if (pageIndex + 1 < pageCount) await page.wait({ time: 1.2 });
  }

  if (!rows.length) {
    throw new EmptyResultError('douban chart', `No visible rows for ${normalizedBoard}`);
  }
  return rows.slice(0, limit);
}
