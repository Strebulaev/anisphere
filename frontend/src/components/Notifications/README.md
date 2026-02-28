# Модуль уведомлений

Этот модуль предоставляет систему уведомлений в виде всплывающих тостов.

## Экспортируемые компоненты и функции

### useToast
Composable функция для управления уведомлениями.

**Возвращаемые значения:**
- `toasts` (Ref<Toast[]>) - массив активных тостов
- `showToast` (function) - показать уведомление
- `removeToast` (function) - удалить уведомление

**Методы `showToast`:**
- `showToast(message, options)` - показать уведомление с опциями
- `showToast.success(message, options)` - показать успешное уведомление
- `showToast.error(message, options)` - показать ошибку
- `showToast.warning(message, options)` - показать предупреждение
- `showToast.info(message, options)` - показать информационное уведомление

**Параметры `options`:**
- `duration` (number, опционально) - время отображения в мс (по умолчанию 3000)
- `onClick` (function, опционально) - обработчик клика
- `persistent` (boolean, опционально) - не закрывать автоматически

**Пример использования:**
```vue
<script setup>
import { useToast } from '@/components/Notifications'

const { showToast } = useToast()

const handleSuccess = () => {
  showToast.success('Успешно сохранено!', {
    duration: 5000
  })
}

const handleError = () => {
  showToast.error('Произошла ошибка', {
    persistent: true,
    onClick: () => console.log('Clicked')
  })
}

const handleWarning = () => {
  showToast.warning('Предупреждение')
}

const handleInfo = () => {
  showToast.info('Информационное сообщение')
}
</script>
```

### Toast
Компонент отдельного тоста (обычно используется через ToastContainer).

**Props:**
- `toasts` (Toast[]) - массив тостов для отображения
- `remove` (function) - функция удаления тоста
- `click` (function) - функция обработки клика

### ToastContainer
Контейнер для отображения всех тостов в приложении.

**Установка:**
Добавьте компонент в корневой компонент приложения (App.vue):

```vue
<script setup>
import { ToastContainer } from '@/components/Notifications'
</script>

<template>
  <div id="app">
    <router-view />
    <ToastContainer />
  </div>
</template>
```

## Полный пример использования

```vue
<script setup>
import { useToast } from '@/components/Notifications'

const { showToast } = useToast()

const actions = {
  success: () => {
    showToast.success('Аниме добавлено в избранное!')
  },

  error: () => {
    showToast.error('Не удалось добавить в избранное')
  },

  warning: () => {
    showToast.warning('Это аниме уже есть в избранном')
  },

  info: () => {
    showToast.info('Информация о аниме обновлена')
  },

  custom: () => {
    showToast('Кастомное сообщение', {
      duration: 5000,
      onClick: () => console.log('Клик по уведомлению'),
      persistent: false
    })
  }
}
</script>

<template>
  <div class="toast-demo">
    <button @click="actions.success">Успех</button>
    <button @click="actions.error">Ошибка</button>
    <button @click="actions.warning">Предупреждение</button>
    <button @click="actions.info">Информация</button>
    <button @click="actions.custom">Кастомное</button>
  </div>
</template>
```

## Типы уведомлений

- `success` - успешное действие (зеленый цвет)
- `error` - ошибка (красный цвет)
- `warning` - предупреждение (желтый цвет)
- `info` - информация (синий цвет)

## Особенности

- Автоматическое исчезновение через 3-5 секунд (настраивается)
- Анимации появления и исчезновения
- Поддержка клика по уведомлению
- Возможность сделать уведомление постоянным
- Адаптивный дизайн для мобильных устройств
- Поддержка темной/светлой темы через CSS-переменные
