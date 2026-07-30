import { cli, Strategy } from '@jackwener/opencli/registry';

import { extractSearchResults } from './extractors.js';
import {
  EmptyResultError,
  evaluateExtractor,
  navigateVisiblePage,
  normalizeChoice,
  normalizeLimit,
} from './utils.js';

cli({
  site: 'douban',
  name: 'search',
  access: 'read',
  description: '搜索豆瓣电影、图书或音乐（只读）',
  domain: 'search.douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    { name: 'keyword', required: true, positional: true, help: '搜索关键词' },
    {
      name: 'type',
      default: 'movie',
      choices: ['movie', 'book', 'music'],
      help: '搜索类型：movie / book / music',
    },
    { name: 'limit', type: 'int', default: 20, help: '返回数量（最大 50）' },
  ],
  columns: ['rank', 'subjectId', 'title', 'rating', 'abstract', 'url'],
  func: async (page, args) => {
    const query = String(args.keyword || '').trim();
    if (!query) throw new EmptyResultError('douban search', 'Search query is empty');
    const type = normalizeChoice(args.type ?? 'movie', ['movie', 'book', 'music'], 'type');
    const limit = normalizeLimit(args.limit, 20, 50);
    const url = new URL(`https://search.douban.com/${type}/subject_search`);
    url.searchParams.set('search_text', query);
    if (type === 'book') url.searchParams.set('cat', '1001');
    await navigateVisiblePage(page, url.toString(), 'body');
    const rows = await evaluateExtractor(page, extractSearchResults, limit);
    if (!rows.length) {
      throw new EmptyResultError('douban search', `No visible results for "${query}"`);
    }
    return rows;
  },
});

