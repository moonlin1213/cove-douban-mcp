/**
 * Pure visible-DOM extractors. Each function is self-contained so OpenCLI can
 * serialize it into the browser context and tests can replay synthetic HTML.
 */

export function pageRequiresLogin(document) {
  const title = String(document?.title || '').trim();
  const body = String(document?.body?.textContent || '');
  return /登录豆瓣|登录跳转|异常请求|请登录后继续/i.test(`${title}\n${body}`);
}

export function extractSearchResults(document, limit) {
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
  const rows = [];
  const nodes = document.querySelectorAll(
    '.result-item, .item-root, .result-list .result-item',
  );
  for (const node of nodes) {
    const link = node.querySelector('h3 a[href*="/subject/"]')
      || node.querySelector('.title a[href*="/subject/"]')
      || node.querySelector('a.title-text[href*="/subject/"]')
      || node.querySelector('a[href*="/subject/"]');
    if (!link) continue;
    const url = link.href || link.getAttribute('href') || '';
    const id = url.match(/\/subject\/(\d+)/)?.[1] || '';
    const title = normalize(link.textContent);
    if (!id || !title) continue;
    const ratingText = normalize(
      node.querySelector('.rating_nums, .rating-num, [class*="rating"]')?.textContent,
    );
    const rating = Number.parseFloat(ratingText);
    rows.push({
      rank: rows.length + 1,
      subjectId: id,
      title,
      rating: Number.isFinite(rating) ? rating : null,
      abstract: normalize(
        node.querySelector('.abstract, .meta, .subject-cast')?.textContent,
      ),
      url,
    });
    if (rows.length >= limit) break;
  }
  return rows;
}

export function extractSubject(document, subjectId, subjectType) {
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
  const fullTitle = normalize(
    document.querySelector('h1 [property="v:itemreviewed"], h1 span, h1')?.textContent,
  );
  const titleMatch = fullTitle.match(/^(.+?)\s+[A-Za-z][\s\S]*$/);
  const title = normalize(titleMatch?.[1] || fullTitle);
  const originalTitle = titleMatch ? normalize(fullTitle.slice(title.length)) : '';
  const yearText = normalize(document.querySelector('.year')?.textContent);
  const yearMatch = yearText.match(/\b(18|19|20|21)\d{2}\b/);
  const ratingValue = Number.parseFloat(
    normalize(
      document.querySelector('strong[property="v:average"], strong.rating_num')
        ?.textContent,
    ),
  );
  const countValue = Number.parseInt(
    normalize(
      document.querySelector('span[property="v:votes"], a.rating_people span')
        ?.textContent,
    ).replace(/[^\d]/g, ''),
    10,
  );
  const infoText = String(document.querySelector('#info')?.textContent || '');
  const countryText = infoText.match(/制片国家\s*\/\s*地区\s*:\s*([^\n]+)/)?.[1] || '';
  const runtimeText = normalize(
    document.querySelector('span[property="v:runtime"]')?.textContent,
  );
  const durationValue = Number.parseInt(runtimeText.match(/\d+/)?.[0] || '', 10);
  const genres = Array.from(document.querySelectorAll('[property="v:genre"]'))
    .map((node) => normalize(node.textContent))
    .filter(Boolean);
  const directors = Array.from(document.querySelectorAll('[rel="v:directedBy"]'))
    .map((node) => normalize(node.textContent))
    .filter(Boolean);
  const casts = Array.from(document.querySelectorAll('[rel="v:starring"]'))
    .map((node) => normalize(node.textContent))
    .filter(Boolean);
  const infoLines = infoText
    .split(/\n/)
    .map((line) => normalize(line))
    .filter(Boolean);
  const info = Object.fromEntries(
    infoLines
      .map((line) => line.match(/^([^:：]+)[:：]\s*(.*)$/))
      .filter(Boolean)
      .map((match) => [normalize(match[1]), normalize(match[2])]),
  );
  const splitPeople = (value) => normalize(value).split(/\s*\/\s*/).filter(Boolean);
  const isbn = normalize(info.ISBN).replace(/[^\dxX]/g, '');
  return {
    id: String(subjectId),
    type: String(subjectType),
    title,
    subtitle: normalize(info['副标题']),
    originalTitle: normalize(info['原作名'] || originalTitle),
    authors: splitPeople(info['作者']),
    translators: splitPeople(info['译者']),
    publisher: normalize(info['出版社'] || info['出品方']),
    publishDate: normalize(info['出版年']),
    publishYear: normalize(info['出版年']).match(/\b(18|19|20|21)\d{2}\b/)?.[0] || '',
    pageCount: Number.parseInt(normalize(info['页数']).match(/\d+/)?.[0] || '', 10) || null,
    binding: normalize(info['装帧']),
    price: normalize(info['定价']),
    series: normalize(info['丛书']),
    isbn10: isbn.length === 10 ? isbn : '',
    isbn13: isbn.length === 13 ? isbn : '',
    year: yearMatch ? Number.parseInt(yearMatch[0], 10) : null,
    rating: Number.isFinite(ratingValue) ? ratingValue : null,
    ratingCount: Number.isFinite(countValue) ? countValue : null,
    genres,
    directors,
    casts,
    country: countryText.split(/\s*\/\s*/).map(normalize).filter(Boolean),
    duration: Number.isFinite(durationValue) ? durationValue : null,
    summary: normalize(
      document.querySelector(
        '[property="v:summary"], #link-report .intro, .related_info .intro',
      )?.textContent,
    ),
    url: document.location?.href || '',
  };
}

export function extractMarks(document, status) {
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
  const rows = [];
  for (const item of document.querySelectorAll('.item')) {
    const link = item.querySelector('.info a[href*="/subject/"]')
      || item.querySelector('a[href*="/subject/"]');
    const url = link?.href || link?.getAttribute('href') || '';
    const movieId = url.match(/\/subject\/(\d+)/)?.[1] || '';
    const titleText = normalize(link?.querySelector('em')?.textContent || link?.textContent);
    const title = normalize(titleText.split('/')[0]);
    if (!movieId || !title) continue;
    const ratingClass = item.querySelector('[class*="rating"]')?.className || '';
    const ratingMatch = String(ratingClass).match(/rating(\d)-t/);
    const intro = normalize(item.querySelector('.intro')?.textContent);
    const yearMatch = intro.match(/\b(18|19|20|21)\d{2}\b/);
    rows.push({
      movieId,
      title,
      year: yearMatch ? Number.parseInt(yearMatch[0], 10) : null,
      myRating: ratingMatch ? Number.parseInt(ratingMatch[1], 10) * 2 : null,
      myStatus: String(status),
      myDate: normalize(item.querySelector('.date')?.textContent),
      myComment: normalize(item.querySelector('.comment')?.textContent),
      url,
    });
  }
  return rows;
}

export function extractMovieMetadata(document, movieId) {
  const subject = extractSubject(document, movieId, 'movie');
  return {
    movieId: String(movieId),
    title: subject.title,
    year: subject.year,
    genres: subject.genres,
    countries: subject.country,
    directors: subject.directors,
    casts: subject.casts,
  };
}

export function extractReviews(document) {
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
  const rows = [];
  for (const item of document.querySelectorAll('.tlst, .review-item')) {
    const movieLink = item.querySelector('.ilst a[href*="/subject/"]')
      || item.querySelector('a[href*="/subject/"]');
    const reviewLink = item.querySelector('.nlst a[title][href*="/review/"]')
      || item.querySelector('a[href*="/review/"]');
    const movieUrl = movieLink?.href || movieLink?.getAttribute('href') || '';
    const reviewUrl = reviewLink?.href || reviewLink?.getAttribute('href') || '';
    const movieId = movieUrl.match(/\/subject\/(\d+)/)?.[1] || '';
    const reviewId = reviewUrl.match(/\/review(?:s)?\/(\d+)/)?.[1] || '';
    const ratingClass = item.querySelector('[class*="allstar"]')?.className || '';
    const ratingMatch = String(ratingClass).match(/allstar(\d)0/);
    const votesText = normalize(
      item.querySelector('.review-short .pl span, .votes')?.textContent,
    );
    const votes = Number.parseInt(votesText.match(/\d+/)?.[0] || '0', 10);
    if (!reviewId) continue;
    rows.push({
      reviewId,
      movieId,
      movieTitle: normalize(
        movieLink?.getAttribute('title') || movieLink?.textContent,
      ),
      title: normalize(reviewLink?.textContent),
      myRating: ratingMatch ? Number.parseInt(ratingMatch[1], 10) * 2 : null,
      votes,
      content: normalize(
        item.querySelector('.review-short > span, .review-short, .review-content')
          ?.textContent,
      ),
      createdAt: normalize(item.querySelector('time, .date')?.textContent),
      url: reviewUrl,
    });
  }
  return rows;
}

export function extractDoulists(document) {
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
  const rows = [];
  for (const item of document.querySelectorAll(
    '.doulist-item, .doulist-list li, .list-item',
  )) {
    const link = item.querySelector('h3 a[href*="/doulist/"]')
      || item.querySelector('.title a[href*="/doulist/"]')
      || item.querySelector('a[href*="/doulist/"]');
    const url = link?.href || link?.getAttribute('href') || '';
    const id = url.match(/\/doulist\/(\d+)/)?.[1] || '';
    const title = normalize(link?.textContent);
    if (!id || !title) continue;
    const countText = normalize(item.querySelector('.count, .num')?.textContent);
    rows.push({
      id,
      title,
      kind: normalize(item.querySelector('.kind')?.textContent) || 'all',
      count: Number.parseInt(countText.match(/\d+/)?.[0] || '0', 10),
      description: normalize(item.querySelector('.description, .intro')?.textContent),
      updatedAt: normalize(item.querySelector('time, .updated-at')?.textContent),
      url,
    });
  }
  return rows;
}

export function extractDoulistItems(document) {
  const normalize = (value) => String(value || '').replace(/\s+/g, ' ').trim();
  const rows = [];
  for (const item of document.querySelectorAll(
    '.doulist-item, .doulist-list .item, .article .item',
  )) {
    const link = item.querySelector('h3 a[href*="/subject/"]')
      || item.querySelector('.title a[href*="/subject/"]')
      || item.querySelector('a[href*="/subject/"]');
    const url = link?.href || link?.getAttribute('href') || '';
    const subjectId = url.match(/\/subject\/(\d+)/)?.[1] || '';
    const title = normalize(link?.textContent);
    if (!subjectId || !title) continue;
    const ratingValue = Number.parseFloat(
      normalize(item.querySelector('.rating_nums, .rating-num')?.textContent),
    );
    const abstract = normalize(item.querySelector('.abstract, .intro')?.textContent);
    const yearMatch = abstract.match(/\b(18|19|20|21)\d{2}\b/);
    rows.push({
      rank: rows.length + 1,
      itemId: `${subjectId}-${rows.length + 1}`,
      subjectId,
      title,
      type: normalize(item.querySelector('.type')?.textContent) || 'unknown',
      year: yearMatch ? Number.parseInt(yearMatch[0], 10) : null,
      rating: Number.isFinite(ratingValue) ? ratingValue : null,
      abstract,
      url,
    });
  }
  return rows;
}
