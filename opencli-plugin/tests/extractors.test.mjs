import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { JSDOM } from 'jsdom';

import {
  extractDoulistItems,
  extractDoulists,
  extractMarks,
  extractMovieMetadata,
  extractReviews,
  extractSearchResults,
  extractSubject,
  pageRequiresLogin,
} from '../clis/douban/extractors.js';

const here = dirname(fileURLToPath(import.meta.url));
const fixture = (name, url = 'https://movie.example.invalid/') => {
  const html = readFileSync(join(here, 'fixtures', `${name}.html`), 'utf8');
  return new JSDOM(html, { url }).window.document;
};

test('search extractor returns stable rows', () => {
  const rows = extractSearchResults(fixture('search'), 10);
  assert.deepEqual(rows, [{
    rank: 1,
    subjectId: '100001',
    title: '虚构影片',
    rating: 8.6,
    abstract: '2024 / 示例甲地 / 喜剧',
    url: 'https://movie.example.invalid/subject/100001/',
  }]);
});

test('subject extractor returns normalized visible metadata', () => {
  const row = extractSubject(fixture('subject'), '100001', 'movie');
  assert.equal(row.id, '100001');
  assert.equal(row.title, '虚构影片');
  assert.deepEqual(row.genres, ['剧情', '喜剧']);
  assert.deepEqual(row.country, ['示例甲地', '示例乙地']);
  assert.equal(row.duration, 120);
});

test('marks extractor preserves identity and user-visible mark fields', () => {
  const rows = extractMarks(fixture('marks'), 'wish');
  assert.equal(rows[0].movieId, '100001');
  assert.equal(rows[0].myRating, 8);
  assert.equal(rows[0].myStatus, 'wish');
  assert.equal(rows[0].myComment, '虚构短评');
});

test('marks-full metadata extractor enriches the same identity', () => {
  const metadata = extractMovieMetadata(fixture('subject'), '100001');
  assert.equal(metadata.movieId, '100001');
  assert.deepEqual(metadata.directors, ['导演甲']);
  assert.deepEqual(metadata.casts, ['演员甲']);
});

test('reviews extractor returns review and movie identities', () => {
  const rows = extractReviews(fixture('reviews'));
  assert.equal(rows[0].reviewId, '300001');
  assert.equal(rows[0].movieId, '100001');
  assert.equal(rows[0].movieTitle, '虚构影片');
  assert.equal(rows[0].title, '虚构影评');
  assert.equal(rows[0].myRating, 8);
  assert.equal(rows[0].votes, 12);
});

test('doulists extractor returns stable list metadata', () => {
  const rows = extractDoulists(fixture('doulists'));
  assert.deepEqual(rows[0], {
    id: '400001',
    title: '虚构豆列',
    kind: 'movie',
    count: 2,
    description: '虚构列表简介',
    updatedAt: '2026-07-01',
    url: 'https://www.example.invalid/doulist/400001/',
  });
});

test('doulist item extractor returns subject identity', () => {
  const rows = extractDoulistItems(fixture('doulist'));
  assert.equal(rows[0].subjectId, '100001');
  assert.equal(rows[0].type, 'movie');
  assert.equal(rows[0].rating, 8.6);
});

test('login page is detected without exposing browser state', () => {
  assert.equal(pageRequiresLogin(fixture('login')), true);
  assert.equal(pageRequiresLogin(fixture('search')), false);
});
