import assert from 'node:assert/strict';
import test from 'node:test';

import { fetchChartRows, fetchMarkRows, resolveUid } from '../clis/douban/utils.js';

function pageWithDelayedProfileRedirect() {
  const hrefs = [
    'https://www.douban.com/mine/',
    'https://www.douban.com/mine/',
    'https://www.douban.com/people/example-user/',
  ];
  const waits = [];
  return {
    waits,
    async goto() {},
    async wait(options) {
      waits.push(options);
    },
    async evaluate(script) {
      if (script === 'location.href') return hrefs.shift() ?? hrefs.at(-1);
      return false;
    },
  };
}

test('resolveUid waits for the client-side /mine/ profile redirect', async () => {
  const page = pageWithDelayedProfileRedirect();

  const uid = await resolveUid(page);

  assert.equal(uid, 'example-user');
  assert.deepEqual(
    page.waits.filter((options) => Object.hasOwn(options, 'time')),
    [{ time: 0.5 }, { time: 0.5 }],
  );
});

test('fetchMarkRows waits for mark content instead of the always-present body', async () => {
  const selectors = [];
  const row = {
    movieId: '100001',
    title: '虚构影片',
    myStatus: 'collect',
    url: 'https://movie.example.invalid/subject/100001/',
  };
  const page = {
    async goto() {},
    async wait(options) {
      if (options.selector) selectors.push(options.selector);
    },
    async evaluate(script) {
      if (script.includes('function pageRequiresLogin')) return false;
      if (script.includes('function extractMarks')) return [row];
      throw new Error(`unexpected evaluation: ${script}`);
    },
  };

  const rows = await fetchMarkRows(page, 'example-user', 'collect', 1);

  assert.deepEqual(rows, [row]);
  assert.deepEqual(selectors, ['.grid-view, .item']);
});

test('fetchMarkRows starts a bounded sync chunk at the requested offset', async () => {
  const visited = [];
  const page = {
    async goto(url) {
      visited.push(url);
    },
    async wait() {},
    async evaluate(script) {
      if (script.includes('function pageRequiresLogin')) return false;
      if (script.includes('function extractMarks')) {
        return [{
          movieId: '100151',
          title: '第151部虚构影片',
          myStatus: 'collect',
          url: 'https://movie.example.invalid/subject/100151/',
        }];
      }
      throw new Error(`unexpected evaluation: ${script}`);
    },
  };

  await fetchMarkRows(page, 'example-user', 'collect', 1, 150);

  assert.equal(new URL(visited[0]).searchParams.get('start'), '150');
});

test('fetchMarkRows returns an empty continuation chunk at the end', async () => {
  const page = {
    async goto() {},
    async wait() {},
    async evaluate(script) {
      if (script.includes('function pageRequiresLogin')) return false;
      if (script.includes('function extractMarks')) return [];
      throw new Error(`unexpected evaluation: ${script}`);
    },
  };

  const rows = await fetchMarkRows(page, 'example-user', 'collect', 150, 150);

  assert.deepEqual(rows, []);
});

test('fetchChartRows maps a board key to its fixed public URL', async () => {
  const visited = [];
  const page = {
    async goto(url) { visited.push(url); },
    async wait() {},
    async evaluate(script) {
      if (script === 'location.href') return visited.at(-1);
      if (script.includes('function pageRequiresLogin')) return false;
      if (script.includes('function extractChart')) return [{ rank: 1, title: '虚构影片' }];
      throw new Error(`unexpected evaluation: ${script}`);
    },
  };

  const rows = await fetchChartRows(page, 'movie_weekly', 10);

  assert.deepEqual(rows, [{ rank: 1, title: '虚构影片' }]);
  assert.deepEqual(visited, ['https://movie.douban.com/chart']);
});

test('fetchChartRows bounds Top250 navigation to official page offsets', async () => {
  const visited = [];
  let nextRank = 1;
  const page = {
    async goto(url) { visited.push(url); },
    async wait() {},
    async evaluate(script) {
      if (script === 'location.href') return visited.at(-1);
      if (script.includes('function pageRequiresLogin')) return false;
      if (script.includes('function extractChart')) {
        return Array.from({ length: 25 }, () => ({ rank: nextRank++, title: '虚构影片' }));
      }
      throw new Error(`unexpected evaluation: ${script}`);
    },
  };

  const rows = await fetchChartRows(page, 'movie_top250', 30);

  assert.equal(rows.length, 30);
  assert.deepEqual(visited, [
    'https://movie.douban.com/top250?start=0',
    'https://movie.douban.com/top250?start=25',
  ]);
});

test('fetchChartRows rejects a redirect away from the fixed public URL', async () => {
  const page = {
    async goto() {},
    async wait() {},
    async evaluate(script) {
      if (script === 'location.href') return 'https://example.invalid/redirected';
      if (script.includes('function pageRequiresLogin')) return false;
      throw new Error(`unexpected evaluation: ${script}`);
    },
  };

  await assert.rejects(
    fetchChartRows(page, 'movie_weekly', 10),
    /unexpected page location/i,
  );
});
