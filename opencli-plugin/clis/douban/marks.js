import { cli, Strategy } from '@jackwener/opencli/registry';

import {
  fetchMarkRows,
  normalizeChoice,
  normalizeLimit,
  resolveUid,
} from './utils.js';

cli({
  site: 'douban',
  name: 'marks',
  access: 'read',
  description: '读取个人观影标记（只读）',
  domain: 'movie.douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    {
      name: 'status',
      default: 'collect',
      choices: ['collect', 'wish', 'do', 'all'],
      help: '标记类型：collect / wish / do / all',
    },
    { name: 'limit', type: 'int', default: 50, help: '返回数量，0 表示全部' },
    { name: 'uid', default: '', help: '用户 ID；留空读取当前登录账号' },
  ],
  columns: [
    'movieId', 'title', 'year', 'myRating', 'myStatus', 'myDate',
    'myComment', 'url',
  ],
  func: async (page, args) => {
    const status = normalizeChoice(
      args.status ?? 'collect',
      ['collect', 'wish', 'do', 'all'],
      'status',
    );
    const limit = normalizeLimit(args.limit, 50, 2000, { allowZero: true });
    const uid = await resolveUid(page, args.uid);
    const statuses = status === 'all' ? ['collect', 'wish', 'do'] : [status];
    const rows = [];
    for (const selected of statuses) {
      const remaining = limit === 0 ? 0 : limit - rows.length;
      if (limit > 0 && remaining <= 0) break;
      rows.push(...await fetchMarkRows(page, uid, selected, remaining));
    }
    return limit === 0 ? rows : rows.slice(0, limit);
  },
});

