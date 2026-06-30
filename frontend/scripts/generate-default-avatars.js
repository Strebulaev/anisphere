/**
 * Скрипт для генерации всех дефолтных аватарок
 * Запустите: node scripts/generate-default-avatars.js
 */

import { writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Палитра цветов
const COLORS = [
  '#6366f1', // Indigo
  '#ec4899', // Pink
  '#8b5cf6', // Violet
  '#3b82f6', // Blue
  '#14b8a6', // Teal
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#10b981', // Emerald
  '#f97316', // Orange
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#d946ef', // Fuchsia
  '#a855f7', // Purple
  '#22c55e', // Green
  '#eab308', // Yellow
  '#0ea5e9', // Sky
  '#e11d48', // Rose
  '#84cc16', // Lawn Green
  '#fb7185', // Soft Red
  '#2dd4bf', // Turquoise
]

function generateAvatar(index, color) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="100" fill="${color}"/>
  <circle cx="100" cy="80" r="30" fill="#ffffff" opacity="0.9"/>
  <circle cx="100" cy="140" r="50" fill="#ffffff" opacity="0.9"/>
</svg>`
}

const outputDir = join(__dirname, '..', 'src', 'assets', 'def_ava')

try {
  mkdirSync(outputDir, { recursive: true })
  
  for (let i = 0; i < COLORS.length; i++) {
    const filename = `def_${i + 1}.svg`
    const filepath = join(outputDir, filename)
    const content = generateAvatar(i + 1, COLORS[i])
    
    writeFileSync(filepath, content)
    console.log(`✓ Создан ${filename}`)
  }
  
  console.log(`\n✓ Готово! Создано ${COLORS.length} аватарок в ${outputDir}`)
} catch (error) {
  console.error('Ошибка при создании аватарок:', error)
  process.exit(1)
}
