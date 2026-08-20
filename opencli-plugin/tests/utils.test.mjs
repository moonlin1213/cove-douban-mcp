import assert from 'node:assert/strict';
import test from 'node:test';

import { fetchMarkRows, resolveUid } from '../clis/douban/utils.js';

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
