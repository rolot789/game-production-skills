#!/usr/bin/env node
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(here, '..');
const skillsRoot = join(packageRoot, 'skills');

function skills() {
  return readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(skillsRoot, entry.name, 'SKILL.md')))
    .map((entry) => entry.name)
    .sort();
}

function usage() {
  console.log(`game-production-skills\n\nUsage:\n  game-production-skills list\n  game-production-skills install [skill ...] [--cwd DIR] [--output DIR] [--force]\n\nExamples:\n  npx game-production-skills list\n  npx game-production-skills install\n  npx game-production-skills install game-spec-builder art-style-builder\n  npx game-production-skills install --output .agents/skills --force`);
}

function valueAfter(args, flag) {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : undefined;
}

const args = process.argv.slice(2);
const command = args[0] || 'help';

if (command === 'list') {
  for (const name of skills()) console.log(name);
  process.exit(0);
}

if (command === 'install') {
  const cwd = resolve(valueAfter(args, '--cwd') || process.cwd());
  const output = resolve(cwd, valueAfter(args, '--output') || '.agents/skills');
  const force = args.includes('--force');
  const flagsWithValues = new Set(['--cwd', '--output']);
  const requested = [];

  for (let i = 1; i < args.length; i += 1) {
    const arg = args[i];
    if (flagsWithValues.has(arg)) {
      i += 1;
      continue;
    }
    if (arg.startsWith('--')) continue;
    requested.push(arg);
  }

  const available = skills();
  const selected = requested.length ? requested : available;
  const invalid = selected.filter((name) => !available.includes(name));
  if (invalid.length) {
    console.error(`Unknown skill(s): ${invalid.join(', ')}`);
    console.error(`Available: ${available.join(', ')}`);
    process.exit(1);
  }

  mkdirSync(output, { recursive: true });

  for (const name of selected) {
    const source = join(skillsRoot, name);
    const destination = join(output, name);
    if (existsSync(destination)) {
      if (!force) {
        console.error(`Already exists: ${destination} (use --force to replace)`);
        process.exit(1);
      }
      rmSync(destination, { recursive: true, force: true });
    }
    cpSync(source, destination, { recursive: true });
    console.log(`installed ${name} -> ${destination}`);
  }

  console.log(`\nInstalled ${selected.length} skill(s).`);
  process.exit(0);
}

usage();
