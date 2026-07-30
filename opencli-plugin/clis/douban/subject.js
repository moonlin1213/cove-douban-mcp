import { cli, Strategy } from '@jackwener/opencli/registry';

import { loadSubjectRow, normalizeChoice, normalizeNumericId } from './utils.js';

cli({
  site: 'douban',
  name: 'subject',
  access: 'read',
  description: '读取一个豆瓣电影或图书条目（只读）',
  domain: 'movie.douban.com',
  strategy: Strategy.COOKIE,
  browser: true,
  navigateBefore: false,
  args: [
    { name: 'id', required: true, positional: true, help: '条目 ID 或条目 URL' },
    {
      name: 'type',
      default: 'movie',
      choices: ['movie', 'book'],
      help: '条目类型：movie / book',
    },
  ],
  columns: [
    'id', 'type', 'title', 'subtitle', 'originalTitle', 'authors',
    'translators', 'publisher', 'publishDate', 'publishYear', 'pageCount',
    'binding', 'price', 'series', 'isbn10', 'isbn13', 'year', 'rating',
    'ratingCount', 'genres', 'directors', 'casts', 'country', 'duration',
    'summary', 'url',
  ],
  func: async (page, args) => {
    const id = normalizeNumericId(args.id, 'subject id');
    const type = normalizeChoice(args.type ?? 'movie', ['movie', 'book'], 'type');
    return [await loadSubjectRow(page, id, type)];
  },
});

