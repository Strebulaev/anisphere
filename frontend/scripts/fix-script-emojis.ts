import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { emojiToIconMap } from '../src/utils/emojiToIcon'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.join(__dirname, '..')


const iconToEmojiMap: Record<string, string> = {}
for (const [emoji, iconName] of Object.entries(emojiToIconMap)) {
  iconToEmojiMap[iconName] = emoji
}

function escapeRegExp(string: string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function processVueFile(filePath: string): { result: string; count: number } {
  let content = fs.readFileSync(filePath, 'utf-8')
  let count = 0
  
  
  const scriptMatches = content.matchAll(/<script[\s\S]*?<\/script>/gi)
  
  for (const match of scriptMatches) {
    let scriptContent = match[0]
    const scriptStart = match.index!
    
    
    for (const [iconName, emoji] of Object.entries(iconToEmojiMap)) {
      const pattern = new RegExp(`<SakuraIcon name="${escapeRegExp(iconName)}"\\s*/>`, 'g')
      const matches = scriptContent.match(pattern)
      if (matches) {
        count += matches.length
        scriptContent = scriptContent.replace(pattern, emoji)
      }
    }
    
    
    content = content.slice(0, scriptStart) + scriptContent + content.slice(scriptStart + match[0].length)
  }
  
  return { result: content, count }
}

function findVueFiles(dir: string): string[] {
  const files: string[] = []
  
  function walk(directory: string) {
    const entries = fs.readdirSync(directory, { withFileTypes: true })
    
    for (const entry of entries) {
      const fullPath = path.join(directory, entry.name)
      
      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules' && entry.name !== 'dist') {
        walk(fullPath)
      } else if (entry.isFile() && entry.name.endsWith('.vue')) {
        files.push(fullPath)
      }
    }
  }
  
  walk(dir)
  return files
}


console.log('🔍 Поиск .vue файлов...')
const srcDir = path.join(rootDir, 'src')
const vueFiles = findVueFiles(srcDir)
console.log(`Найдено ${vueFiles.length} .vue файлов`)

let totalCount = 0
let modifiedFiles = 0

for (const file of vueFiles) {
  const { result, count } = processVueFile(file)
  
  if (count > 0) {
    fs.writeFileSync(file, result, 'utf-8')
    const relativePath = path.relative(rootDir, file)
    console.log(`📄 ${relativePath} - восстановлено: ${count}`)
    modifiedFiles++
    totalCount += count
  }
}

console.log('='.repeat(50))
console.log(`Итого: ${modifiedFiles} файлов, ${totalCount} восстановлено`)
console.log('✅ Изменения сохранены')
