import { cli, Strategy } from '@jackwener/opencli/registry';

import { fetchChartRows } from './utils.js';

cli({
  site: 'douban',
  name: 'chart',
  access: 'read',
  description: '读取六个固定豆瓣公开榜单（只读）',
  domain: 'douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    {
      name: 'board',
      required: true,
      positional: true,
      choices: [
        'movie_weekly',
        'movie_north_america',
        'movie_new',
        'movie_top250',
        'book_hot',
        'music_hot',
      ],
      help: '固定榜单 key',
    },
    { name: 'limit', type: 'int', default: 10, help: '返回数量（按榜单限制）' },
  ],
  columns: [
    'rank',
    'subjectId',
    'title',
    'url',
    'rating',
    'ratingCount',
    'year',
    'summary',
    'trend',
    'chartNote',
  ],
  func: async (page, args) => fetchChartRows(page, args.board, args.limit),
});
