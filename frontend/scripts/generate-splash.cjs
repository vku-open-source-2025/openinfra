#!/usr/bin/env node
/**
 * Generate iOS splash screen images for PWA
 * Run: node scripts/generate-splash.js
 * Requires: npm install sharp
 */

const fs = require('fs');
const path = require('path');

// Try to use sharp, fallback to creating placeholder SVGs
let sharp;
try {
  sharp = require('sharp');
} catch (e) {
  console.log('Sharp not installed. Run: npm install sharp -D');
  console.log('Creating SVG placeholders instead...');
  sharp = null;
}

const SPLASH_SIZES = [
  { name: 'splash-640x1136', width: 640, height: 1136 },   // iPhone SE
  { name: 'splash-750x1334', width: 750, height: 1334 },   // iPhone 6/7/8
  { name: 'splash-1242x2208', width: 1242, height: 2208 }, // iPhone 6+/7+/8+
  { name: 'splash-1125x2436', width: 1125, height: 2436 }, // iPhone X/XS/11 Pro
  { name: 'splash-1170x2532', width: 1170, height: 2532 }, // iPhone 12/13/14
  { name: 'splash-1179x2556', width: 1179, height: 2556 }, // iPhone 14 Pro
  { name: 'splash-1284x2778', width: 1284, height: 2778 }, // iPhone 12/13/14 Pro Max
  { name: 'splash-1290x2796', width: 1290, height: 2796 }, // iPhone 14 Pro Max
];

const ICON_SIZES = [
  { name: 'apple-touch-icon-180x180', size: 180 },
];

const OUTPUT_DIR = path.join(__dirname, '../public/icons');

// SVG template for splash screen
function createSplashSVG(width, height) {
  const logoSize = Math.min(width, height) * 0.2;
  const centerX = width / 2;
  const centerY = height / 2 - 50;
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4FACFE"/>
      <stop offset="100%" style="stop-color:#00F2FE"/>
    </linearGradient>
  </defs>
  <rect width="${width}" height="${height}" fill="url(#bg)"/>
  <g transform="translate(${centerX - logoSize/2}, ${centerY - logoSize/2})">
    <rect width="${logoSize}" height="${logoSize}" rx="${logoSize * 0.2}" fill="white"/>
    <g transform="translate(${logoSize * 0.25}, ${logoSize * 0.25})">
      <svg width="${logoSize * 0.5}" height="${logoSize * 0.5}" viewBox="0 0 24 24">
        <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#4FACFE"/>
        <path d="M2 17L12 22L22 17" stroke="#4FACFE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M2 12L12 17L22 12" stroke="#00F2FE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      </svg>
    </g>
  </g>
  <text x="${centerX}" y="${centerY + logoSize/2 + 60}" font-family="system-ui, -apple-system, sans-serif" font-size="${logoSize * 0.25}" font-weight="700" fill="white" text-anchor="middle">OpenInfra</text>
  <text x="${centerX}" y="${centerY + logoSize/2 + 100}" font-family="system-ui, -apple-system, sans-serif" font-size="${logoSize * 0.12}" fill="rgba(255,255,255,0.9)" text-anchor="middle">Smart Infrastructure Management</text>
</svg>`;
}

// SVG template for icon
function createIconSVG(size) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4FACFE"/>
      <stop offset="100%" style="stop-color:#00F2FE"/>
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" fill="url(#bg)"/>
  <g transform="translate(${size * 0.2}, ${size * 0.2})">
    <svg width="${size * 0.6}" height="${size * 0.6}" viewBox="0 0 24 24">
      <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white"/>
      <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <path d="M2 12L12 17L22 12" stroke="rgba(255,255,255,0.8)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>
  </g>
</svg>`;
}

async function generateImages() {
  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  console.log('Generating PWA splash screens and icons...\n');

  // Generate splash screens
  for (const { name, width, height } of SPLASH_SIZES) {
    const svgContent = createSplashSVG(width, height);
    const outputPath = path.join(OUTPUT_DIR, `${name}.png`);
    
    if (sharp) {
      await sharp(Buffer.from(svgContent))
        .png()
        .toFile(outputPath);
      console.log(`✓ Generated ${name}.png (${width}x${height})`);
    } else {
      // Save as SVG if sharp not available
      fs.writeFileSync(path.join(OUTPUT_DIR, `${name}.svg`), svgContent);
      console.log(`✓ Generated ${name}.svg (${width}x${height}) - Convert to PNG manually`);
    }
  }

  // Generate icons
  for (const { name, size } of ICON_SIZES) {
    const svgContent = createIconSVG(size);
    const outputPath = path.join(OUTPUT_DIR, `${name}.png`);
    
    if (sharp) {
      await sharp(Buffer.from(svgContent))
        .png()
        .toFile(outputPath);
      console.log(`✓ Generated ${name}.png (${size}x${size})`);
    } else {
      fs.writeFileSync(path.join(OUTPUT_DIR, `${name}.svg`), svgContent);
      console.log(`✓ Generated ${name}.svg (${size}x${size}) - Convert to PNG manually`);
    }
  }

  console.log('\n✅ Done! Splash screens generated in public/icons/');
  
  if (!sharp) {
    console.log('\n⚠️  Note: SVG files were created. For best results:');
    console.log('   1. Install sharp: npm install sharp -D');
    console.log('   2. Run this script again to generate PNG files');
    console.log('   Or use an online converter to convert SVGs to PNGs');
  }
}

generateImages().catch(console.error);
