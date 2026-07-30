import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const adapterRoot = join(root, 'clis', 'douban');
const expected = [
  'doulist.js',
  'doulists.js',
  'marks-full.js',
  'marks.js',
  'reviews.js',
  'search.js',
  'subject.js',
];

test('plugin declares the supported OpenCLI range and public identity', () => {
  const manifest = JSON.parse(readFileSync(join(root, 'opencli-plugin.json'), 'utf8'));
  assert.equal(manifest.name, 'cove-douban-mcp');
  assert.equal(manifest.version, '0.1.0');
  assert.equal(manifest.opencli, '>=1.8.0 <2');
});

test('exactly seven command adapters are shipped', () => {
  const files = readdirSync(adapterRoot)
    .filter((name) => name.endsWith('.js') && !['extractors.js', 'utils.js'].includes(name))
    .sort();
  assert.deepEqual(files, expected);
});

test('every adapter is explicitly read-only and uses allowed imports', () => {
  for (const name of expected) {
    const source = readFileSync(join(adapterRoot, name), 'utf8');
    assert.match(source, /access:\s*'read'/, name);
    assert.doesNotMatch(source, /\bCliError\b/, name);
    assert.doesNotMatch(source, /\breturn\s+\[\s*\]\s*;/, name);
    assert.doesNotMatch(source, /Math\.(?:min|max)\s*\(/, name);
    const imports = [...source.matchAll(/from\s+['"]([^'"]+)['"]/g)].map(
      (match) => match[1],
    );
    assert.ok(
      imports.every(
        (value) => value.startsWith('./') || value.startsWith('@jackwener/opencli/'),
      ),
      `${name} has an unsupported import`,
    );
  }
});

test('no write or arbitrary-download command is bundled', () => {
  const source = expected
    .map((name) => readFileSync(join(adapterRoot, name), 'utf8'))
    .join('\n');
  assert.doesNotMatch(source, /name:\s*['"](?:download|photos|rate|publish|delete)['"]/);
  assert.doesNotMatch(source, /child_process|exec\(|spawn\(|writeFile/);
});
