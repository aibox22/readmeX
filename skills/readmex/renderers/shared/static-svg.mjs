import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { esc } from './utils.mjs';

// The image carries its own palette. No viewer, browser CSS, or network font is
// needed by GitHub's image proxy or by librsvg when producing previews/GIFs.
function staticStyle(preset) {
  const source = fs.readFileSync(fileURLToPath(new URL('./svg-theme.css', import.meta.url)), 'utf8');
  const variables = {};
  let rules = source.replace(/([^{}]+)\{([^{}]*)\}/g, (block, selector, body) => {
    if (!body.includes('--bg:')) return block;
    if (!selector.includes('data-preset') || selector.includes(`data-preset="${preset}"`)) {
      for (const match of body.matchAll(/(--[\w-]+):\s*([^;]+);/g)) variables[match[1]] = match[2].trim();
    }
    return '';
  });
  rules = rules.replace(/var\((--[\w-]+)\)/g, (_, name) => variables[name] || '#64748b');
  rules = rules.replace(/color-mix\([^;]+\)/g, 'rgba(251, 191, 36, 0.05)');
  return { css: rules, variables, background: variables['--bg'] || '#f4f5f7' };
}

export function makeStaticSvg(svg, meta, evidence) {
  const root = svg.match(/<svg\b([^>]*)>([\s\S]*)<\/svg>\s*$/);
  const box = root?.[1].match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
  if (!box) throw new Error('Static SVG requires a finite zero-origin viewBox.');
  const width = Number(box[1]);
  const height = Number(box[2]);
  if (!(width > 0 && height > 0)) throw new Error('Static SVG viewBox must be positive.');
  const scale = 1200 / width;
  const finalHeight = Number((height * scale).toFixed(3));
  const attrs = root[1].replace(/\s*viewBox="[^"]*"/, '').replace(/\s*data-animation="[^"]*"/g, '');
  let body = root[2]
    .replace(/\s*(?:tabindex|aria-pressed)="[^"]*"/g, '')
    .replace(/\s*role="button"/g, '')
    .replace(/\s*data-animate="[^"]*"/g, '')
    .replace(/\s*style="--step:[^"]*"/g, '');
  if (/<(?:script|foreignObject)\b/i.test(body)) throw new Error('Unsupported executable SVG content.');
  for (const text of body.matchAll(/<text\b([^>]*)>/g)) {
    const font = Number(text[1].match(/font-size="([\d.]+)"/)?.[1]);
    const primary = /data-node-label/.test(text[1]);
    const minimum = primary ? 20 : 18;
    if (!font || font * scale < minimum - 0.001) {
      throw new Error(`README text is too small after 1200-unit normalization (${(font * scale).toFixed(1)} < ${minimum}). Simplify/split the diagram and enlarge its labels; move detail into Markdown.`);
    }
  }
  const theme = staticStyle(meta.visual_preset || 'classic');
  body = body.replace(/var\((--[\w-]+)\)/g, (_, name) => theme.variables[name] || '#64748b');
  const provenance = evidence ? `\n<metadata id="readmex-source-evidence">${esc(JSON.stringify(evidence))}</metadata>` : '';
  return `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="${finalHeight}" viewBox="0 0 1200 ${finalHeight}" data-theme="light"${attrs}>\n<style>${theme.css}</style>${provenance}\n<rect width="1200" height="${finalHeight}" fill="${theme.background}"/>\n<g id="diagram-content" transform="scale(${scale})">${body}\n</g>\n</svg>\n`;
}
