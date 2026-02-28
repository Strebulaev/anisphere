"""
Поиск по сообщениям с использованием Elasticsearch
"""
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Message


@registry.register_document
class MessageDocument(Document):
    """Elasticsearch документ для сообщений"""

    sender_id = fields.IntegerField()
    sender_username = fields.TextField()

    chat_id = fields.IntegerField()
    chat_name = fields.TextField()

    private_chat_id = fields.IntegerField()

    # Для групповых чатов - название чата
    class Index:
        name = 'messages'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Message
        fields = [
            'id',
            'text',
            'media_type',
            'created_at',
            'updated_at',
        ]

    def prepare_sender_username(self, instance):
        """Подготовка имени отправителя"""
        return instance.sender.username if instance.sender else ''

    def prepare_chat_name(self, instance):
        """Подготовка названия чата"""
        if instance.chat:
            return instance.chat.name
        return ''

    def prepare_chat_id(self, instance):
        """Подготовка ID чата"""
        return instance.chat_id

    def prepare_private_chat_id(self, instance):
        """Подготовка ID личного чата"""
        return instance.private_chat_id


def search_messages(query, user_id, chat_id=None, media_type=None, date_from=None, date_to=None):
    """
    Поиск сообщений

    Args:
        query: Поисковый запрос
        user_id: ID пользователя (для фильтрации по доступу)
        chat_id: ID чата (опционально)
        media_type: Тип медиа (опционально)
        date_from: Начальная дата (опционально)
        date_to: Конечная дата (опционально)

    Returns:
        Список сообщений
    """
    from elasticsearch_dsl import Q, Search
    from django.db.models import Q as DjangoQ  # Импортируем Q из django.db.models
    from .models import GroupChat, PrivateChat

    s = Search(index='messages')

    # Полнотекстовый поиск
    if query:
        s = s.query('multi_match', query=query, fields=['text'])

    # Фильтр по чату
    if chat_id:
        s = s.filter('term', chat_id=chat_id) | s.filter('term', private_chat_id=chat_id)
    else:
        # Фильтр по доступным чатам пользователя
        # Получаем ID чатов, к которым есть доступ
        group_chat_ids = list(GroupChat.objects.filter(
            members__user_id=user_id
        ).values_list('id', flat=True))

        private_chat_ids = list(PrivateChat.objects.filter(
            DjangoQ(user1_id=user_id) | DjangoQ(user2_id=user_id)  # Используем DjangoQ вместо models.Q
        ).values_list('id', flat=True))

        s = s.filter(
            Q('terms', chat_id=group_chat_ids) | Q('terms', private_chat_id=private_chat_ids)
        )

    # Фильтр по типу медиа
    if media_type:
        s = s.filter('term', media_type=media_type)

    # Фильтр по дате
    if date_from:
        s = s.filter('range', created_at={'gte': date_from})
    if date_to:
        s = s.filter('range', created_at={'lte': date_to})

    # Фильтр только не удалённые сообщения
    s = s.exclude('term', is_deleted=True)

    # Сортировка по дате (новые первые)
    s = s.sort('-created_at')

    # Ограничение результатов
    s = s[:100]

    response = s.execute()

    # Получаем объекты из базы данных
    message_ids = [hit.id for hit in response.hits]
    messages = Message.objects.filter(id__in=message_ids)

    # Сортируем результаты в том же порядке, что и в Elasticsearch
    messages_dict = {msg.id: msg for msg in messages}
    sorted_messages = [messages_dict[int(msg_id)] for msg_id in message_ids if int(msg_id) in messages_dict]

    return sorted_messages


def reindex_messages():
    """
    Переиндексация всех сообщений
    """
    from .models import Message

    # Получаем все сообщения
    messages = Message.objects.filter(is_deleted=False)

    # Индексируем
    for message in messages:
        try:
            doc = MessageDocument()
            doc._id = message.id
            doc.sender_id = message.sender_id
            doc.sender_username = message.sender.username if message.sender else ''
            doc.chat_id = message.chat_id
            doc.chat_name = message.chat.name if message.chat else ''
            doc.private_chat_id = message.private_chat_id
            doc.text = message.text
            doc.media_type = message.media_type
            doc.created_at = message.created_at
            doc.updated_at = message.updated_at
            doc.save()
        except Exception as e:
            print(f"Ошибка индексации сообщения {message.id}: {e}")

    return {'status': 'completed'}