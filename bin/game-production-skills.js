#!/usr/bin/env node
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(here, '..');
const skillsRoot = join(packageRoot, 'skills');
const templateRoot = join(packageRoot, 'templates', 'project');

function skills() {
  return readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(skillsRoot, entry.name, 'SKILL.md')))
    .map((entry) => entry.name)
    .sort();
}

function usage() {
  console.log(`game-production-skills

Usage:
  game-production-skills list
  game-production-skills install [skill ...] [--cwd DIR] [--output DIR] [--force]
  game-production-skills init --name NAME [--cwd DIR] [--profile lite|full] [--force]
  game-production-skills validate [--cwd DIR] [--profile lite|full]

Examples:
  npx game-production-skills list
  npx game-production-skills install
  npx game-production-skills install game-spec-builder art-style-builder
  npx game-production-skills install --output .claude/skills --force
  npx game-production-skills init --name "Minimal Puzzle" --profile lite
  npx game-production-skills validate

Typical first run:
  npx game-production-skills install
  npx game-production-skills init --name "My Game"

\`init\` writes project.yaml and .pipeline/, which every skill resolves artifact
paths through. Installing skills without it leaves them with no path registry.`);
}

function valueAfter(args, flag) {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : undefined;
}

function slugify(text) {
  return text.trim().replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase() || 'game-project';
}

const FLAGS_WITH_VALUES = new Set(['--cwd', '--output', '--name', '--profile']);

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
  const requested = [];

  for (let i = 1; i < args.length; i += 1) {
    const arg = args[i];
    if (FLAGS_WITH_VALUES.has(arg)) {
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
    // Each skill directory carries its own mirrored contracts under
    // references/, so an installed skill resolves every path it documents
    // without needing the repository.
    cpSync(source, destination, { recursive: true });
    console.log(`installed ${name} -> ${destination}`);
  }

  console.log(`\nInstalled ${selected.length} skill(s).`);
  if (!existsSync(join(cwd, 'project.yaml'))) {
    console.log('\nNext: create the path registry these skills resolve through.');
    console.log('  npx game-production-skills init --name "<project name>"');
  }
  process.exit(0);
}

if (command === 'init') {
  const cwd = resolve(valueAfter(args, '--cwd') || process.cwd());
  const name = valueAfter(args, '--name');
  const profile = valueAfter(args, '--profile') || 'full';
  const force = args.includes('--force');

  if (!name) {
    console.error('init requires --name, e.g. --name "My Game"');
    process.exit(1);
  }
  if (!['lite', 'full'].includes(profile)) {
    console.error(`Unknown profile: ${profile} (expected lite or full)`);
    process.exit(1);
  }

  const written = [];
  const skipped = [];

  const copyTemplate = (relative) => {
    const source = join(templateRoot, relative);
    const destination = join(cwd, relative);
    if (existsSync(destination) && !force) {
      skipped.push(relative);
      return null;
    }
    mkdirSync(dirname(destination), { recursive: true });
    cpSync(source, destination);
    written.push(relative);
    return destination;
  };

  const stampIdentity = (file) => {
    if (!file) return;
    const text = readFileSync(file, 'utf8')
      .replace(/^(project:\n(?:.*\n)*?)  id: null/m, `$1  id: ${slugify(name)}`)
      .replace(/^(project:\n(?:.*\n)*?)  name: null/m, `$1  name: ${JSON.stringify(name)}`)
      .replace(/^profile: full$/m, `profile: ${profile}`);
    writeFileSync(file, text);
  };

  stampIdentity(copyTemplate('project.yaml'));
  stampIdentity(copyTemplate(join('.pipeline', 'game-art-production-state.yaml')));

  for (const dir of ['spec', 'art', 'assets/specs', 'generation', 'normalized', 'qc',
    'engine-integration', 'runtime-validation', '.pipeline/handoffs']) {
    mkdirSync(join(cwd, dir), { recursive: true });
  }

  for (const file of written) console.log(`created ${file}`);
  for (const file of skipped) console.log(`kept    ${file} (already exists, use --force to replace)`);
  console.log(`\nInitialized "${name}" with the ${profile} profile in ${cwd}`);
  console.log('Every skill resolves artifact paths through project.yaml.');
  console.log('\nValidate at any time:');
  console.log('  npx game-production-skills validate');
  process.exit(0);
}

if (command === 'validate') {
  const cwd = resolve(valueAfter(args, '--cwd') || process.cwd());
  const profile = valueAfter(args, '--profile');
  const script = join(packageRoot, 'scripts', 'validate_project.py');

  if (!existsSync(script)) {
    console.error(`Validator not found at ${script}`);
    process.exit(1);
  }

  const scriptArgs = [script, cwd];
  if (profile) scriptArgs.push('--profile', profile);

  for (const interpreter of ['python3', 'python']) {
    const run = spawnSync(interpreter, scriptArgs, { stdio: 'inherit' });
    if (run.error && run.error.code === 'ENOENT') continue;
    process.exit(run.status ?? 1);
  }

  console.error('validate needs Python 3 with pyyaml installed:');
  console.error('  python3 -m pip install pyyaml');
  process.exit(1);
}

usage();
