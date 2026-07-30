import {
  ArgumentError,
  AuthRequiredError,
  CommandExecutionError,
  EmptyResultError,
} from '@jackwener/opencli/errors';

import {
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
  const href = await page.evaluate('location.href');
  const uid = String(href || '').match(/\/people\/([^/]+)/)?.[1] || '';
  if (!uid) {
    throw new AuthRequiredError(
      'www.douban.com',
      'The current signed-in Douban user could not be identified.',
    );
  }
  return uid;
}

export async function fetchMarkRows(page, uid, status, requestedLimit) {
  const rows = [];
  let offset = 0;
  const maximum = requestedLimit === 0 ? 2000 : requestedLimit;
  while (rows.length < maximum) {
    const url = new URL(`https://movie.douban.com/people/${encodeURIComponent(uid)}/${status}`);
    url.searchParams.set('start', String(offset));
    url.searchParams.set('sort', 'time');
    url.searchParams.set('rating', 'all');
    url.searchParams.set('filter', 'all');
    url.searchParams.set('mode', 'grid');
    await navigateVisiblePage(page, url.toString(), 'body');
    const pageRows = await evaluateExtractor(page, extractMarks, status);
    if (!Array.isArray(pageRows)) {
      throw new CommandExecutionError('Douban marks returned an unexpected page shape');
    }
    if (pageRows.length === 0) break;
    rows.push(...pageRows);
    if (pageRows.length < 15) break;
    offset += 15;
  }
  if (rows.length === 0) {
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

