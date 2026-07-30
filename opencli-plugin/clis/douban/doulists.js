import { cli, Strategy } from '@jackwener/opencli/registry';

import { extractDoulists } from './extractors.js';
import {
  EmptyResultError,
  evaluateExtractor,
  navigateVisiblePage,
  normalizeChoice,
  normalizeLimit,
  resolveUid,
} from './utils.js';

cli({
  site: 'douban',
  name: 'doulists',
  access: 'read',
  description: '读取当前账号或指定用户创建的豆列（只读）',
  domain: 'www.douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    {
      name: 'kind',
      default: 'all',
      choices: ['all', 'movie', 'book'],
      help: '列表类型：all / movie / book',
    },
    { name: 'limit', type: 'int', default: 30, help: '返回数量（最大 80）' },
    { name: 'uid', default: '', help: '用户 ID；留空读取当前登录账号' },
  ],
  columns: ['id', 'title', 'kind', 'count', 'description', 'updatedAt', 'url'],
  func: async (page, args) => {
    const kind = normalizeChoice(args.kind ?? 'all', ['all', 'movie', 'book'], 'kind');
    const limit = normalizeLimit(args.limit, 30, 80);
    const uid = await resolveUid(page, args.uid);
    const host = kind === 'movie'
      ? 'movie.douban.com'
      : kind === 'book'
        ? 'book.douban.com'
        : 'www.douban.com';
    const url = `https://${host}/people/${encodeURIComponent(uid)}/doulists/${kind}`;
    await navigateVisiblePage(page, url, 'body');
    const rows = await evaluateExtractor(page, extractDoulists);
    if (!rows.length) {
      throw new EmptyResultError('douban doulists', `No visible ${kind} lists`);
    }
    return rows.slice(0, limit);
  },
});

