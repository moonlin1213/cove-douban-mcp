import { cli, Strategy } from '@jackwener/opencli/registry';

import { extractDoulistItems } from './extractors.js';
import {
  EmptyResultError,
  evaluateExtractor,
  navigateVisiblePage,
  normalizeLimit,
  normalizeNumericId,
} from './utils.js';

cli({
  site: 'douban',
  name: 'doulist',
  access: 'read',
  description: '读取一个豆列、片单或书单中的条目（只读）',
  domain: 'www.douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    { name: 'id', required: true, positional: true, help: '豆列 ID 或豆列 URL' },
    { name: 'limit', type: 'int', default: 40, help: '返回数量（最大 120）' },
  ],
  columns: [
    'rank', 'itemId', 'subjectId', 'title', 'type', 'year', 'rating',
    'abstract', 'url',
  ],
  func: async (page, args) => {
    const id = normalizeNumericId(args.id, 'doulist id');
    const limit = normalizeLimit(args.limit, 40, 120);
    const rows = [];
    let start = 0;
    while (rows.length < limit) {
      const url = `https://www.douban.com/doulist/${id}/?start=${start}`;
      await navigateVisiblePage(page, url, 'body');
      const pageRows = await evaluateExtractor(page, extractDoulistItems);
      if (!pageRows.length) break;
      rows.push(...pageRows);
      if (pageRows.length < 25) break;
      start += 25;
    }
    if (!rows.length) {
      throw new EmptyResultError('douban doulist', `No visible items in list ${id}`);
    }
    return rows.slice(0, limit).map((row, index) => ({
      ...row,
      rank: index + 1,
    }));
  },
});
