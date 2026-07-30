import { cli, Strategy } from '@jackwener/opencli/registry';

import {
  fetchMarkRows,
  loadSubjectRow,
  normalizeChoice,
  normalizeLimit,
  resolveUid,
} from './utils.js';

cli({
  site: 'douban',
  name: 'marks-full',
  access: 'read',
  description: '读取观影标记并补全影片元数据（只读）',
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
    { name: 'limit', type: 'int', default: 0, help: '返回数量，0 表示全部' },
    { name: 'uid', default: '', help: '用户 ID；留空读取当前登录账号' },
  ],
  columns: [
    'movieId', 'title', 'year', 'genres', 'countries', 'directors', 'casts',
    'myRating', 'myStatus', 'myDate', 'myComment', 'url',
  ],
  func: async (page, args) => {
    const status = normalizeChoice(
      args.status ?? 'collect',
      ['collect', 'wish', 'do', 'all'],
      'status',
    );
    const limit = normalizeLimit(args.limit, 0, 2000, { allowZero: true });
    const uid = await resolveUid(page, args.uid);
    const statuses = status === 'all' ? ['collect', 'wish', 'do'] : [status];
    const marks = [];
    for (const selected of statuses) {
      const remaining = limit === 0 ? 0 : limit - marks.length;
      if (limit > 0 && remaining <= 0) break;
      marks.push(...await fetchMarkRows(page, uid, selected, remaining));
    }
    const rows = [];
    for (const mark of (limit === 0 ? marks : marks.slice(0, limit))) {
      const detail = await loadSubjectRow(page, mark.movieId, 'movie');
      rows.push({
        movieId: mark.movieId,
        title: detail.title || mark.title,
        year: detail.year ?? mark.year,
        genres: detail.genres,
        countries: detail.country,
        directors: detail.directors,
        casts: detail.casts,
        myRating: mark.myRating,
        myStatus: mark.myStatus,
        myDate: mark.myDate,
        myComment: mark.myComment,
        url: mark.url,
      });
    }
    return rows;
  },
});

