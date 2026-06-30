/**
 * Скрипт для замены эмодзи на <SakuraIcon /> в .vue файлах
 * Запуск: npx tsx scripts/replace-emojis.ts
 */

import { readFileSync, writeFileSync, readdirSync, statSync } from 'fs'
import { join, extname } from 'path'
import { emojiToIconMap } from '../src/utils/emojiToIcon'

const ROOT_DIR = './src'
const DRY_RUN = process.argv.includes('--dry-run')

function getAllFiles(dir: string, extensions: string[]): string[] {
  const files: string[] = []
  
  try {
    const items = readdirSync(dir)
    
    for (const item of items) {
      const fullPath = join(dir, item)
      const stat = statSync(fullPath)
      
      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        files.push(...getAllFiles(fullPath, extensions))
      } else if (extensions.includes(extname(fullPath))) {
        files.push(fullPath)
      }
    }
  } catch (e) {
    
  }
  
  return files
}

function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function replaceInContent(content: string): { result: string; count: number } {
  let count = 0
  let result = content
  
  
  const emojis = Object.keys(emojiToIconMap).sort((a, b) => b.length - a.length)
  
  for (const emoji of emojis) {
    const iconName = emojiToIconMap[emoji]
    const escaped = escapeRegExp(emoji)
    
    
    const parts: string[] = []
    
    
    const scriptMatch = result.matchAll(/<script[\s\S]*?<\/script>/gi)
    const styleMatch = result.matchAll(/<style[\s\S]*?<\/style>/gi)
    
    
    const skipRanges: {start: number, end: number}[] = []
    for (const match of scriptMatch) {
      skipRanges.push({ start: match.index!, end: match.index! + match[0].length })
    }
    for (const match of styleMatch) {
      skipRanges.push({ start: match.index!, end: match.index! + match[0].length })
    }
    
    
    skipRanges.sort((a, b) => a.start - b.start)
    
    
    let currentIndex = 0
    for (const range of skipRanges) {
      
      const beforePart = result.slice(currentIndex, range.start)
      const processed = processPart(beforePart, emoji, iconName, escaped)
      parts.push(processed.text)
      count += processed.count
      
      
      parts.push(result.slice(range.start, range.end))
      currentIndex = range.end
    }
    
    
    const afterPart = result.slice(currentIndex)
    const processedAfter = processPart(afterPart, emoji, iconName, escaped)
    parts.push(processedAfter.text)
    count += processedAfter.count
    
    result = parts.join('')
    
    
    result = processAttributes(result, emoji, iconName, escaped)
  }
  
  return { result, count }
}

function processPart(text: string, emoji: string, iconName: string, escaped: string): { text: string, count: number } {
  let count = 0
  let result = text
  
  
  
  const pattern1 = new RegExp(`>\\s*${escaped}\\s*<`, 'g')
  if (pattern1.test(result)) {
    const matches = result.match(new RegExp(`>\\s*${escaped}\\s*<`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern1, `> <SakuraIcon name="${iconName}" /> <`)
  }
  
  
  const pattern2 = new RegExp(`(^|>)\\s*${escaped}`, 'gm')
  if (pattern2.test(result)) {
    const matches = result.match(new RegExp(`(^|>)\\s*${escaped}`, 'gm'))
    count += matches ? matches.length : 0
    result = result.replace(pattern2, `$1 <SakuraIcon name="${iconName}" />`)
  }
  
  
  const pattern3 = new RegExp(`\\s${escaped}\\s`, 'g')
  if (pattern3.test(result)) {
    const matches = result.match(new RegExp(`\\s${escaped}\\s`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern3, ` <SakuraIcon name="${iconName}" /> `)
  }
  
  
  const pattern4 = new RegExp(`\\s${escaped}(\\s*$|\\n)`, 'gm')
  if (pattern4.test(result)) {
    const matches = result.match(new RegExp(`\\s${escaped}(\\s*$|\\n)`, 'gm'))
    count += matches ? matches.length : 0
    result = result.replace(pattern4, ` <SakuraIcon name="${iconName}" />$1`)
  }
  
  
  const pattern5 = new RegExp(`([а-яА-ЯёЁa-zA-Z0-9])${escaped}([а-яА-ЯёЁa-zA-Z0-9])`, 'g')
  if (pattern5.test(result)) {
    const matches = result.match(new RegExp(`([а-яА-ЯёЁa-zA-Z0-9])${escaped}([а-яА-ЯёЁa-zA-Z0-9])`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern5, `$1 <SakuraIcon name="${iconName}" /> $2`)
  }
  
  
  const pattern6 = new RegExp(`([а-яА-ЯёЁa-zA-Z0-9])${escaped}`, 'g')
  if (pattern6.test(result)) {
    const matches = result.match(new RegExp(`([а-яА-ЯёЁa-zA-Z0-9])${escaped}`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern6, `$1 <SakuraIcon name="${iconName}" />`)
  }
  
  
  const pattern7 = new RegExp(`${escaped}([а-яА-ЯёЁa-zA-Z0-9])`, 'g')
  if (pattern7.test(result)) {
    const matches = result.match(new RegExp(`${escaped}([а-яА-ЯёЁa-zA-Z0-9])`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern7, `<SakuraIcon name="${iconName}" /> $1`)
  }
  
  
  const pattern8 = new RegExp(`${escaped}([^\s<])`, 'g')
  if (pattern8.test(result)) {
    const matches = result.match(new RegExp(`${escaped}([^\s<])`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern8, `<SakuraIcon name="${iconName}" /> $1`)
  }
  
  
  const pattern9 = new RegExp(`([^>])${escaped}`, 'g')
  if (pattern9.test(result)) {
    const matches = result.match(new RegExp(`([^>])${escaped}`, 'g'))
    count += matches ? matches.length : 0
    result = result.replace(pattern9, `$1 <SakuraIcon name="${iconName}" />`)
  }
  
  return { text: result, count }
}

function processAttributes(text: string, emoji: string, iconName: string, escaped: string): string {
  let result = text
  
  
  
  
  
  const pattern1 = new RegExp(`:title="\\\`([^${escaped}]*)${escaped}([^\\\`]*)\\\`"`, 'g')
  result = result.replace(pattern1, `:title="\`$1<SakuraIcon name=\\"${iconName}\\" />$2\`"`)
  
  
  const pattern2 = new RegExp(`:title="'([^${escaped}]*)${escaped}([^']*)'"`, 'g')
  result = result.replace(pattern2, `:title="'$1<SakuraIcon name=\\"${iconName}\\" />$2'"`)
  
  
  const pattern3 = new RegExp(`title="([^${escaped}]*)${escaped}([^"]*)"`, 'g')
  result = result.replace(pattern3, `title="$1<SakuraIcon name=\\"${iconName}\\" />$2"`)
  
  
  const pattern4 = new RegExp(`placeholder="([^${escaped}]*)${escaped}([^"]*)"`, 'g')
  result = result.replace(pattern4, `placeholder="$1<SakuraIcon name=\\"${iconName}\\" />$2"`)
  
  return result
}

function processFiles() {
  console.log('🔍 Поиск .vue файлов...\n')
  
  const files = getAllFiles(ROOT_DIR, ['.vue'])
  console.log(`Найдено ${files.length} .vue файлов\n`)
  
  let totalReplaced = 0
  let filesWithChanges = 0
  
  for (const file of files) {
    const content = readFileSync(file, 'utf-8')
    const { result, count } = replaceInContent(content)
    
    if (count > 0) {
      filesWithChanges++
      totalReplaced += count
      console.log(`📄 ${file} - заменено: ${count}`)
      
      if (!DRY_RUN) {
        writeFileSync(file, result, 'utf-8')
      }
    }
  }
  
  console.log('\n' + '='.repeat(50))
  console.log(`Итого: ${filesWithChanges} файлов, ${totalReplaced} замен`)
  console.log(DRY_RUN ? '\n⚠️ DRY RUN - изменения не сохранены' : '\n✅ Изменения сохранены')
}

processFiles()
