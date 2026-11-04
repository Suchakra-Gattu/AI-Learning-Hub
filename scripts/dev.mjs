// Tiny dev server: builds, serves dist/, and rebuilds when content or ui change.
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync, watch } from 'node:fs';
import { join, extname, dirname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = join(ROOT, 'dist');
const PORT = Number(process.env.PORT || 4173);
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };

function build() {
  const r = spawnSync(process.execPath, [join(ROOT, 'scripts', 'build.mjs')], { stdio: 'inherit' });
  return r.status === 0;
}

build();

let timer;
for (const dir of ['content', 'ui']) {
  watch(join(ROOT, dir), { recursive: true }, () => {
    clearTimeout(timer);
    timer = setTimeout(build, 150);
  });
}

createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const file = normalize(join(DIST, p));
  if (!file.startsWith(DIST) || !existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    return res.end('Not found');
  }
  res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(readFileSync(file));
}).listen(PORT, () => console.log(`\nLearning site: http://localhost:${PORT}\nEdit anything in content/ or ui/ and refresh.`));
