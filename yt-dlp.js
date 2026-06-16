#!/usr/bin/env node
const { readFileSync, createWriteStream, mkdirSync, existsSync } = require('fs');
const { request } = require('https');
const { request: httpRequest } = require('http');
const { URL } = require('url');
const { basename, extname, join, dirname } = require('path');

const INVIDIOUS_INSTANCES = [
  'https://invidious.io',
  'https://yewtu.be',
  'https://yewtu.eu',
  'https://yewtu.cafe',
  'https://yewtu.eu',
  'https://yewtu.dccn.nl'
];

function printUsage() {
  console.log('Usage: node yt-dlp.js <URL> [--output-dir dir] [--list-invidious]');
  console.log('Downloads a YouTube/Invidious video using public Invidious instances.');
}

function normalizeUrl(url) {
  if (url.includes('watch?v=')) return url;
  if (url.includes('youtu.be/')) {
    const id = url.split('youtu.be/')[1].split(/[?&]/)[0];
    return `https://www.youtube.com/watch?v=${id}`;
  }
  return url;
}

function extractVideoId(urlString) {
  try {
    const url = new URL(urlString);
    if (url.hostname.endsWith('youtu.be')) {
      return url.pathname.slice(1);
    }
    if (url.searchParams.has('v')) {
      return url.searchParams.get('v');
    }
    const parts = url.pathname.split('/').filter(Boolean);
    return parts.length ? parts[parts.length - 1] : null;
  } catch (err) {
    return null;
  }
}

function safeFilename(name) {
  return name.replace(/[<>:"/\\|?*]+/g, '_').slice(0, 200);
}

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https://') ? request : httpRequest;
    const req = client(url, { headers: { 'User-Agent': 'yt-dlp-js/1.0' } }, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`Status ${res.statusCode}`));
        res.resume();
        return;
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (err) {
          reject(err);
        }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

function downloadUrl(url, destPath) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https://') ? request : httpRequest;
    const req = client(url, { headers: { 'User-Agent': 'yt-dlp-js/1.0' } }, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`Status ${res.statusCode}`));
        res.resume();
        return;
      }
      mkdirSync(dirname(destPath), { recursive: true });
      const file = createWriteStream(destPath);
      res.pipe(file);
      file.on('finish', () => file.close(resolve));
      file.on('error', (err) => reject(err));
    });
    req.on('error', reject);
    req.end();
  });
}

function chooseFormat(formats) {
  let best = null;
  for (const format of formats) {
    const url = format.url || format.audio_url;
    if (!url) continue;
    const progressive = !format.dash && !format.is_dash;
    const height = format.height || 0;
    const score = (progressive ? 2 : 1) * 10000 + height;
    if (!best || score > best.score) {
      best = { score, format };
    }
  }
  return best ? best.format : null;
}

async function listInvidious() {
  console.log('Available Invidious instances:');
  for (const instance of INVIDIOUS_INSTANCES) {
    console.log('  ' + instance);
  }
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    printUsage();
    process.exit(0);
  }

  if (args.includes('--list-invidious')) {
    await listInvidious();
    process.exit(0);
  }

  const urlArg = args[0];
  const outputDirIndex = args.indexOf('--output-dir');
  const outputDir = outputDirIndex !== -1 && args[outputDirIndex + 1] ? args[outputDirIndex + 1] : 'downloads';
  const url = normalizeUrl(urlArg);
  const videoId = extractVideoId(url);
  if (!videoId) {
    console.error('Unable to extract a video id from the URL.');
    process.exit(1);
  }

  for (const instance of INVIDIOUS_INSTANCES) {
    try {
      const info = await fetchJson(`${instance.replace(/\/+$/, '')}/api/v1/videos/${videoId}`);
      const formats = info.formats || info.adaptive_formats || [];
      const best = chooseFormat(formats);
      if (!best) continue;
      const mediaUrl = best.url || best.audio_url;
      if (!mediaUrl) continue;
      const title = safeFilename(info.title || videoId);
      const ext = best.ext || 'mp4';
      const filename = `${title}.${ext}`;
      const outputPath = join(outputDir, filename);
      console.log(`Downloading ${title} from ${instance} to ${outputPath}`);
      await downloadUrl(mediaUrl, outputPath);
      console.log('Download complete.');
      process.exit(0);
    } catch (err) {
      console.error(`Failed to download from ${instance}: ${err.message}`);
    }
  }

  console.error('All Invidious instances failed.');
  process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
