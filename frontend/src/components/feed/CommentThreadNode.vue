<script lang="ts">
import { defineComponent, ref, computed, h } from 'vue'
import { commentsApi } from '@/api/feed'
import { normalizeComment } from '@/utils/normalizers'

export const CommentThreadNode: any = defineComponent({
  name: 'CommentThreadNode',
  props: {
    comment:     { type: Object, required: true },
    allComments: { type: Array, required: true },
    postId:      { type: Number, required: true },
    isReply:     { type: Boolean, default: false }, // Это ответ (не корневой комментарий)
    replyToUser: { type: String, default: '' },     // Username того, кому отвечаем
    depth:       { type: Number, default: 0 },      // Глубина вложенности
  },
  emits: ['reply-added'],
  setup(p, { emit: emitNode }) {
    const replying = ref(false)
    const replyText = ref('')
    const sendingReply = ref(false)
    const showReplies = ref(false)
    const defaultAv = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32'%3E%3Ccircle cx='16' cy='16' r='16' fill='%23333'/%3E%3C/svg%3E`

    // Дети - только если это корневой комментарий
    const children = computed(() => {
      if (p.isReply) return [] // У ответов нет детей
      return (p.allComments as any[])
        .filter(c => c.parent === p.comment.id)
        .sort((a: any, b: any) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    })

    // Вычисляем текст кнопки
    const toggleButtonText = computed(() => {
      if (showReplies.value) {
        return `▲ Свернуть ответы`
      }
      return `▼ Ответы (${children.value.length})`
    })

    const submitReply = async () => {
      if (!replyText.value.trim() || sendingReply.value) return
      sendingReply.value = true
      try {
        const { data } = await commentsApi.createComment(p.postId, replyText.value, p.comment.id)
        const norm = normalizeComment(data)
        emitNode('reply-added', norm)
        replyText.value = ''
        replying.value = false
        showReplies.value = true
      } catch {}
      finally { sendingReply.value = false }
    }

    const formatTime = (s: string) => {
      const d = new Date(s), now = Date.now(), diff = now - d.getTime()
      const m = Math.floor(diff/60000), hh = Math.floor(diff/3600000)
      if (m < 1) return 'только что'
      if (m < 60) return m + ' мин.'
      if (hh < 24) return hh + ' ч.'
      return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
    }

    return () => {
      const c = p.comment as any

      return h('div', { class: ['comment-node', p.isReply ? 'is-reply' : ''] }, [
        h('div', { class: 'comment-row' }, [
          h('img', { src: c.author_avatar || defaultAv, class: 'c-avatar' }),
          h('div', { class: 'c-body' }, [
            h('div', { class: 'c-header' }, [
              // Если это ответ на ответ - показываем упоминание
              p.isReply && p.replyToUser ? [
                h('span', { class: 'c-author' }, c.author_username || c.author_display_name || ''),
                h('span', { class: 'c-reply-arrow' }, '→'),
                h('span', { class: 'c-reply-to' }, '@' + p.replyToUser),
              ] : [
                h('span', { class: 'c-author' }, c.author_username || c.author_display_name || ''),
              ],
              h('span', { class: 'c-time' }, formatTime(c.created_at)),
            ]),
            h('p', { class: 'c-text', innerHTML: (c.content || '').replace(/\n/g, '<br>') }),
            h('div', { class: 'c-actions' }, [
              h('button', {
                class: ['c-btn', c.is_liked ? 'active' : ''],
                onClick: async (e: Event) => {
                  e.stopPropagation()
                  try {
                    const { data } = await commentsApi.likeComment(c.id)
                    c.is_liked = data.liked
                    c.likes_count = data.likes_count
                  } catch {}
                }
              }, [c.is_liked ? '❵' : '❵', ' ', String(c.likes_count || 0)]),
              // Кнопка "Ответить" только у корневых комментариев
              !p.isReply ? h('button', {
                class: 'c-btn',
                onClick: (e: Event) => { e.stopPropagation(); replying.value = !replying.value }
              }, '💬 Ответить') : null,
              // Кнопка "Ответы/Свернуть" только у корневых комментариев
              !p.isReply && children.value.length > 0 ? h('button', {
                class: 'c-btn c-toggle',
                onClick: (e: Event) => { e.stopPropagation(); showReplies.value = !showReplies.value }
              }, toggleButtonText.value) : null,
            ]),
            // Форма ответа только у корневых комментариев
            !p.isReply && replying.value ? h('div', { class: 'reply-form' }, [
              h('textarea', {
                class: 'reply-textarea',
                placeholder: `Ответ @${c.author_username}...`,
                value: replyText.value,
                onInput: (e: Event) => { replyText.value = (e.target as HTMLTextAreaElement).value },
                onKeydown: (e: KeyboardEvent) => { if (e.ctrlKey && e.key === 'Enter') submitReply() },
                rows: 2,
              }),
              h('div', { class: 'reply-actions' }, [
                h('button', { class: 'reply-cancel', onClick: () => { replying.value = false; replyText.value = '' } }, 'Отмена'),
                h('button', {
                  class: 'reply-send',
                  disabled: !replyText.value.trim() || sendingReply.value,
                  onClick: submitReply
                }, sendingReply.value ? '...' : 'Ответить'),
              ]),
            ]) : null,
            // Ответы внутри комментария (после формы ответа)
            !p.isReply && showReplies.value && children.value.length > 0
              ? h('div', { class: 'comment-replies' },
                  children.value.map((child: any) =>
                    h(CommentThreadNode, {
                      key: child.id,
                      comment: child,
                      allComments: p.allComments,
                      postId: p.postId,
                      isReply: true,
                      replyToUser: c.author_username || c.author_display_name || '',
                      depth: p.depth + 1,
                      onReplyAdded: (reply: any) => emitNode('reply-added', reply),
                    })
                  )
                )
              : null,
          ]),
        ]),
      ])
    }
  }
})

export default CommentThreadNode
</script>
