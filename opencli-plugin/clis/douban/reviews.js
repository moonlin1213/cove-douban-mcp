import { cli, Strategy } from '@jackwener/opencli/registry';

import { extractReviews } from './extractors.js';
import {
  EmptyResultError,
  evaluateExtractor,
  navigateVisiblePage,
  normalizeLimit,
  resolveUid,
} from './utils.js';

cli({
  site: 'douban',
  name: 'reviews',
  access: 'read',
  description: '读取个人影评（只读）',
  domain: 'movie.douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回数量（最大 50）' },
    { name: 'uid', default: '', help: '用户 ID；留空读取当前登录账号' },
    { name: 'full', type: 'bool', default: false, help: '读取完整影评正文' },
  ],
  columns: [
    'reviewId', 'movieId', 'movieTitle', 'title', 'myRating', 'votes',
    'content', 'createdAt', 'url',
  ],
  func: async (page, args) => {
    const limit = normalizeLimit(args.limit, 20, 50);
    const uid = await resolveUid(page, args.uid);
    const rows = [];
    let start = 0;
    while (rows.length < limit) {
      const url = `https://movie.douban.com/people/${encodeURIComponent(uid)}/reviews?start=${start}&sort=time`;
      await navigateVisiblePage(page, url, 'body');
      const pageRows = await evaluateExtractor(page, extractReviews);
      if (!pageRows.length) break;
      rows.push(...pageRows);
      if (pageRows.length < 20) break;
      start += 20;
    }
    if (!rows.length) {
      throw new EmptyResultError('douban reviews', 'No visible reviews');
    }
    const result = rows.slice(0, limit);
    if (Boolean(args.full)) {
      for (const row of result) {
        if (!row.url) continue;
        await navigateVisiblePage(page, row.url, 'body');
        row.content = await page.evaluate(
          `String(document.querySelector('.review-content')?.textContent || '').replace(/\\s+/g, ' ').trim()`,
        );
      }
    }
    return result;
  },
});

