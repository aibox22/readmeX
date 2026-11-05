import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const usage = 'Usage: node bin/render-diagram.mjs <diagram.json> --repo-root <target> [--layout-json]'
const renderers = {
  architecture: 'renderers/architecture/render-architecture.mjs',
  workflow: 'renderers/workflow/render-workflow.mjs',
}

function fail(message) {
  process.stderr.write(`${message.trim()}\n`)
  process.exit(1)
}

function parseArgs(argv) {
  let input = null
  let repoRoot = null
  let layoutJson = false
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--repo-root') {
      repoRoot = argv[index + 1]
      index += 1
      continue
    }
    if (arg === '--layout-json') {
      layoutJson = true
      continue
    }
    if (!input && !arg.startsWith('--')) {
      input = arg
      continue
    }
    fail(usage)
  }
  if (!input || !repoRoot) fail(usage)
  return { input: path.resolve(input), repoRoot: path.resolve(repoRoot), layoutJson }
}

const { input, repoRoot, layoutJson } = parseArgs(process.argv)
if (!fs.statSync(repoRoot, { throwIfNoEntry: false })?.isDirectory()) fail(`--repo-root is not a directory: ${repoRoot}`)

let diagramType
try {
  diagramType = JSON.parse(fs.readFileSync(input, 'utf8')).diagram_type
} catch (error) {
  fail(`Cannot read ${input}: ${error.message}`)
}
if (!Object.hasOwn(renderers, diagramType)) {
  fail(`diagram_type must be "architecture" or "workflow", got ${JSON.stringify(diagramType)}`)
}

// meta.output resolves from the working directory, so the renderer runs inside
// the target repository and writes there, not into the skill directory.
const result = spawnSync(
  process.execPath,
  [path.join(skillRoot, renderers[diagramType]), input, ...(layoutJson ? ['--layout-json'] : [])],
  { cwd: repoRoot, env: { ...process.env, ARCHIFY_REPO_ROOT: repoRoot }, stdio: 'inherit' },
)
if (result.error) fail(result.error.message)
process.exit(result.status ?? 1)
