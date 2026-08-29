import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { JSDOM } from 'jsdom';

import {
  extractChart,
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

test('chart extractor normalizes all six fixed public boards', () => {
  const document = fixture('chart', 'https://movie.douban.com/chart');
  const expected = {
    movie_weekly: {
      rank: 1,
      subjectId: '100001',
      title: '虚构/口碑影片',
      url: 'https://movie.douban.com/subject/100001/',
      rating: null,
      ratingCount: null,
      year: null,
      summary: '',
      trend: '',
      chartNote: '连续上榜 2 周',
    },
    movie_north_america: {
      rank: 1,
      subjectId: '100002',
      title: '虚构票房影片',
      url: 'https://movie.douban.com/subject/100002/',
      rating: null,
      ratingCount: null,
      year: null,
      summary: '',
      trend: '',
      chartNote: '1250万美元',
    },
    movie_new: {
      rank: 1,
      subjectId: '100003',
      title: '虚构新片',
      url: 'https://movie.douban.com/subject/100003/',
      rating: 8.5,
      ratingCount: 3210,
      year: 2026,
      summary: '2026 / 示例地区 / 剧情',
      trend: '',
      chartNote: '',
    },
    movie_top250: {
      rank: 1,
      subjectId: '100004',
      title: '虚构经典',
      url: 'https://movie.douban.com/subject/100004/',
      rating: 9.6,
      ratingCount: 456789,
      year: 1994,
      summary: '导演甲 主演甲 / 1994 / 示例地区 / 剧情',
      trend: '',
      chartNote: '虚构经典台词',
    },
    book_hot: {
      rank: 1,
      subjectId: '200001',
      title: '虚构热门图书',
      url: 'https://book.douban.com/subject/200001/',
      rating: 9.1,
      ratingCount: 5678,
      year: null,
      summary: '作者甲 / 虚构出版社 / 2026',
      trend: 'up',
      chartNote: '',
    },
    music_hot: {
      rank: 1,
      subjectId: '300001',
      title: '虚构热门单曲',
      url: 'https://site.douban.com/example-musician/',
      rating: null,
      ratingCount: null,
      year: null,
      summary: '音乐人甲 / 2026',
      trend: 'down',
      chartNote: '上榜 3 天',
    },
  };

  for (const [board, row] of Object.entries(expected)) {
    assert.deepEqual(extractChart(document, board), [row], board);
  }
});
