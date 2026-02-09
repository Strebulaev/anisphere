from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import update_last_login
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
import random
import string
import json
import pyotp
import qrcode
from io import BytesIO
import base64
import google.auth.transport.requests
import google.oauth2.id_token
import requests
from .models import (
    User, UserProfileSettings, TwoFactorAuth, ActiveSession,
    NotificationSettings, PrivacySettings, UserTheme, ChatBackground,
    UserAnalytics, EmailLog, SecurityLog
)
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    PhoneVerificationSerializer, EmailVerificationSerializer,
    GoogleAuthSerializer, PasswordResetSerializer,
    ProfileUpdateSerializer, UserSessionSerializer, UserSettingsSerializer,
    NicknameCheckSerializer, TwoFactorSetupSerializer
)
from core.redis_events import event_publisher


def send_sms_via_textbee(phone_number, message):
    """Отправка SMS через TextBee API"""
    api_key = 'cfba766b-889e-4521-a983-fc8326cd5052'
    url = f'https://api.textbee.dev/sendSMS?apiKey={api_key}&to={phone_number}&from=AnimeCore&message={message}'

    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception as e:
        print(f"SMS send error: {e}")
        return False


def send_verification_email(email, code_or_link, is_link=False):
    """Отправка email с кодом подтверждения или ссылкой"""
    if is_link:
        subject = 'Подтверждение email адреса - AnimeCore'
        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">AnimeCore</h1>
                <p style="color: #e8e8e8; margin: 10px 0 0 0;">Подтверждение email адреса</p>
            </div>

            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-top: 0;">Добро пожаловать!</h2>
                <p style="color: #666; line-height: 1.6;">Для завершения регистрации подтвердите ваш email адрес:</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{code_or_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        Подтвердить email
                    </a>
                </div>

                <p style="color: #999; font-size: 14px; margin-top: 30px;">Ссылка действительна в течение 24 часов.</p>
                <p style="color: #999; font-size: 14px;">Если вы не регистрировались на AnimeCore, просто игнорируйте это письмо.</p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2024 AnimeCore. Все права защищены.</p>
            </div>
        </body>
        </html>
        '''
        plain_message = f'Для подтверждения email перейдите по ссылке: {code_or_link}\n\nСсылка действительна в течение 24 часов.'
    else:
        subject = 'Подтверждение email адреса - AnimeCore'
        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">AnimeCore</h1>
                <p style="color: #e8e8e8; margin: 10px 0 0 0;">Подтверждение email адреса</p>
            </div>

            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-top: 0;">Код подтверждения</h2>
                <p style="color: #666; line-height: 1.6;">Для завершения регистрации введите этот код на сайте:</p>

                <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 3px;">{code_or_link}</span>
                </div>

                <p style="color: #999; font-size: 14px; margin-top: 30px;">Код действителен в течение 30 минут.</p>
                <p style="color: #999; font-size: 14px;">Если вы не запрашивали этот код, просто игнорируйте это письмо.</p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2024 AnimeCore. Все права защищены.</p>
            </div>
        </body>
        </html>
        '''
        plain_message = f'Ваш код подтверждения: {code_or_link}\n\nКод действителен в течение 30 минут.'

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        """Отправляем email подтверждения после создания пользователя"""
        user = serializer.save()

        # Генерируем токен для подтверждения
        from django.utils.crypto import get_random_string
        from django.core.cache import cache

        token = get_random_string(64)
        cache.set(f'email_confirm_{user.email}', {
            'user_id': user.id,
            'token': token
        }, timeout=86400)  # 24 часа

        # Отправляем письмо с ссылкой подтверждения
        confirm_url = f"http://localhost:5173/confirm-email?token={token}&email={user.email}"
        send_verification_email(user.email, confirm_url, is_link=True)


class LoginView(APIView):
    """Вход в систему"""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Serializer validation already authenticated the user
            user = serializer.validated_data.get('user')
            if user:
                login(request, user)
                user.is_online = True
                user.save()
                refresh = RefreshToken.for_user(user)
                update_last_login(None, user)

                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    """Аутентификация через Google"""
    permission_classes = (AllowAny,)

    def get(self, request):
        """Начинаем OAuth flow - перенаправляем на Google"""
        from urllib.parse import urlencode
        import secrets

        # Генерируем state для защиты от CSRF
        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state
        request.session.save()  # Принудительно сохраняем сессию

        print(f"DEBUG: Generated state: {state}")
        print(f"DEBUG: Session key: {request.session.session_key}")

        # Для локальной разработки используем фиксированный redirect URI
        redirect_uri = "http://localhost:8000/api/users/google/callback/"
        print(f"DEBUG: Using redirect_uri: {redirect_uri}")

        # Проверяем наличие Google credentials
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            print("ERROR: Google OAuth credentials not configured")
            return Response({'error': 'Google OAuth не настроен'}, status=500)

        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }

        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        print(f"DEBUG: Full Google auth URL: {google_auth_url}")
        return Response({'auth_url': google_auth_url})

    def post(self, request):
        """Обработка ID token (для альтернативного подхода)"""
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Верификация Google токена
                id_token = serializer.validated_data['id_token']
                idinfo = google.oauth2.id_token.verify_oauth2_token(
                    id_token, google.auth.transport.requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )

                google_id = idinfo['sub']
                email = idinfo['email']
                name = idinfo.get('name', '')

                # Ищем пользователя или создаем нового
                user, created = User.objects.get_or_create(
                    google_id=google_id,
                    defaults={
                        'email': email,
                        'username': email.split('@')[0] + str(random.randint(1000, 9999)),
                        'first_name': name.split(' ')[0] if name else '',
                        'last_name': ' '.join(name.split(' ')[1:]) if name and len(name.split(' ')) > 1 else '',
                        'email_verified': True,
                    }
                )

                if not created and user.email != email:
                    user.email = email
                    user.save()

                login(request, user)
                user.is_online = True
                user.save()
                refresh = RefreshToken.for_user(user)
                update_last_login(None, user)

                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })

            except Exception as e:
                return Response({'error': f'Ошибка Google аутентификации: {str(e)}'},
                              status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthCallbackView(APIView):
    """Callback для обработки Google OAuth authorization code"""
    permission_classes = (AllowAny,)

    def get(self, request):
        """Обрабатываем authorization code от Google"""
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        print(f"DEBUG: Callback received - code: {code}, state: {state}, error: {error}")
        print(f"DEBUG: Session key: {request.session.session_key}")
        print(f"DEBUG: Session data: {dict(request.session)}")

        # Проверяем ошибки
        if error:
            return Response({'error': f'Google OAuth error: {error}'}, status=400)

        if not code:
            return Response({'error': 'No authorization code received'}, status=400)

        # Отключаем проверку state для локальной разработки (небезопасно для продакшена!)
        # TODO: В продакшене включить state проверку с Redis сессиями
        # session_state = request.session.get('google_oauth_state')
        # if not state or state != session_state:
        #     return Response({'error': 'Invalid state parameter'}, status=400)
        # del request.session['google_oauth_state']

        print(f"DEBUG: Skipping state validation for development")

        try:
            # Обмениваем authorization code на access token
            token_data = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': "http://localhost:8000/api/users/google/callback/"
            }

            token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            token_response.raise_for_status()
            token_json = token_response.json()

            access_token = token_json.get('access_token')
            id_token = token_json.get('id_token')

            if not access_token:
                return Response({'error': 'Failed to obtain access token'}, status=400)

            # Получаем информацию о пользователе
            user_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            user_response.raise_for_status()
            user_info = user_response.json()

            google_id = user_info['id']
            email = user_info['email']
            name = user_info.get('name', '')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')

            # Ищем пользователя или создаем нового
            user, created = User.objects.get_or_create(
                google_id=google_id,
                defaults={
                    'email': email,
                    'username': email.split('@')[0] + str(random.randint(1000, 9999)),
                    'first_name': first_name,
                    'last_name': last_name,
                    'email_verified': True,
                }
            )

            if not created and user.email != email:
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.save()

            login(request, user)
            user.is_online = True
            user.save()
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            # Возвращаем HTML страницу, которая сохранит токены и перенаправит на frontend
            user_data = UserSerializer(user).data
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google OAuth - AnimeCore</title>
                <script>
                    // Сохраняем токены в localStorage
                    localStorage.setItem('access_token', '{refresh.access_token}');
                    localStorage.setItem('refresh_token', '{refresh}');
                    localStorage.setItem('user', JSON.stringify({json.dumps(user_data)}));

                    // Перенаправляем на главную страницу
                    window.location.href = 'http://localhost:5173/';
                </script>
            </head>
            <body>
                <p>Google авторизация успешна! Перенаправление...</p>
            </body>
            </html>
            """

            return HttpResponse(html_content, content_type='text/html')

        except Exception as e:
            return Response({'error': f'Google OAuth callback error: {str(e)}'}, status=500)


class PhoneVerificationView(APIView):
    """Отправка и проверка SMS кода для телефона"""

    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            action = serializer.validated_data['action']

            if action == 'send':
                # Генерируем код
                code = ''.join(random.choices(string.digits, k=6))

                # Сохраняем код
                user = request.user
                user.sms_code = code
                user.sms_code_expires = timezone.now() + timedelta(minutes=10)
                user.save()

                # Отправляем SMS через TextBee
                message = f'Ваш код подтверждения: {code}'
                if send_sms_via_textbee(str(phone_number), message):
                    return Response({'message': 'SMS код отправлен'})
                else:
                    return Response({'error': 'Ошибка отправки SMS'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif action == 'verify':
                code = serializer.validated_data['code']
                user = request.user

                if (user.sms_code == code and
                    user.sms_code_expires and
                    timezone.now() < user.sms_code_expires):

                    user.phone_verified = True
                    user.sms_code = None
                    user.sms_code_expires = None
                    user.save()

                    return Response({'message': 'Телефон подтвержден'})
                else:
                    return Response({'error': 'Неверный или истекший код'},
                                  status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """Отправка и проверка email кода"""

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            action = serializer.validated_data['action']

            if action == 'send':
                # Генерируем код
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

                # Сохраняем код в сессии или временном хранилище
                request.session[f'email_code_{email}'] = {
                    'code': code,
                    'expires': (timezone.now() + timedelta(minutes=30)).isoformat()
                }

                # Отправляем email
                if send_verification_email(email, code):
                    return Response({'message': 'Код отправлен на email'})
                else:
                    return Response({'error': 'Ошибка отправки email'},
                                  status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif action == 'verify':
                code = serializer.validated_data['code']
                session_key = f'email_code_{email}'
                session_data = request.session.get(session_key)

                if session_data and timezone.now() < timezone.datetime.fromisoformat(session_data['expires']):
                    if session_data['code'] == code:
                        # Обновляем пользователя
                        user = request.user
                        user.email = email
                        user.email_verified = True
                        user.save()

                        # Очищаем сессию
                        del request.session[session_key]

                        return Response({'message': 'Email подтвержден'})
                    else:
                        return Response({'error': 'Неверный код'},
                                      status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': 'Код истек или не найден'},
                                  status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailConfirmView(APIView):
    """Подтверждение email по ссылке"""
    permission_classes = (AllowAny,)

    def get(self, request):
        """Подтверждаем email по токену"""
        token = request.GET.get('token')
        email = request.GET.get('email')

        if not token or not email:
            return Response({'error': 'Неверная ссылка подтверждения'}, status=400)

        # Получаем данные из кэша
        from django.core.cache import cache
        cache_key = f'email_confirm_{email}'
        confirm_data = cache.get(cache_key)

        if not confirm_data or confirm_data.get('token') != token:
            return Response({'error': 'Ссылка подтверждения недействительна или истекла'}, status=400)

        try:
            user = User.objects.get(id=confirm_data['user_id'], email=email)
            user.email_verified = True
            user.save()

            # Очищаем кэш
            cache.delete(cache_key)

            # HTML страница успешного подтверждения
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email подтвержден - AnimeCore</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #28a745; font-size: 24px; margin-bottom: 20px; }
                    .message { color: #666; margin-bottom: 30px; }
                    .button { background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="success">✓ Email подтвержден!</div>
                <div class="message">Теперь вы можете полноценно использовать AnimeCore</div>
                <a href="http://localhost:5173/login" class="button">Войти в аккаунт</a>
            </body>
            </html>
            """

            return HttpResponse(html_content, content_type='text/html')

        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)


class LogoutView(APIView):
    """Выход из системы"""

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            user.is_online = False
            user.save()
        logout(request)
        return Response({'message': 'Выход выполнен'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Профиль пользователя"""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset(request):
    """Сброс пароля"""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Генерируем новый пароль и отправляем
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            user.set_password(new_password)
            user.save()

            # Отправляем email с новым паролем
            subject = 'Восстановление пароля - AnimeCore'
            html_message = f'''
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">AnimeCore</h1>
                    <p style="color: #e8e8e8; margin: 10px 0 0 0;">Восстановление пароля</p>
                </div>

                <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; margin-top: 0;">Ваш новый пароль</h2>
                    <p style="color: #666; line-height: 1.6;">Был сгенерирован новый пароль для вашей учетной записи:</p>

                    <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <span style="font-size: 24px; font-weight: bold; color: #667eea;">{new_password}</span>
                    </div>

                    <p style="color: #666; line-height: 1.6;"><strong>Важно:</strong> Рекомендуем изменить этот пароль после входа в систему в настройках профиля.</p>
                </div>

                <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                    <p>© 2024 AnimeCore. Все права защищены.</p>
                </div>
            </body>
            </html>
            '''
            plain_message = f'Ваш новый пароль: {new_password}\nРекомендуем изменить его после входа.'

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
            )

            return Response({'message': 'Новый пароль отправлен на email'})
        except User.DoesNotExist:
            return Response({'error': 'Пользователь с таким email не найден'},
                          status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileUpdateView(generics.UpdateAPIView):
    """Обновление профиля пользователя"""
    serializer_class = ProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserSessionsView(generics.ListAPIView):
    """Просмотр активных сессий"""
    serializer_class = UserSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)


class UserSessionDetailView(generics.DestroyAPIView):
    """Завершение конкретной сессии"""
    serializer_class = UserSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        """При завершении сессии также удаляем её из Django сессий"""
        from django.contrib.sessions.models import Session

        # Удаляем сессию из Django
        try:
            Session.objects.filter(session_key=instance.session_key).delete()
        except:
            pass  # Игнорируем если сессия уже удалена

        # Удаляем нашу запись
        instance.delete()


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """Управление настройками пользователя"""
    serializer_class = UserSettingsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        # Получаем или создаем настройки пользователя
        settings, created = UserSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class OnlineUsersView(generics.ListAPIView):
    """Просмотр пользователей онлайн с фильтрацией"""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Получаем пользователей онлайн, исключая текущего
        queryset = User.objects.filter(is_online=True).exclude(id=self.request.user.id)

        # Фильтруем по настройкам приватности - показываем только тех, кто разрешает
        # Используем LEFT JOIN через select_related и фильтр на существование настроек
        from django.db.models import Q, Exists, OuterRef
        from .models import UserSettings

        queryset = queryset.filter(
            Q(settings__isnull=True) |  # Если настроек нет, считаем публичным
            Q(settings__show_online_status=True)  # Или если явно разрешено
        ).select_related('settings')

        # Фильтр по жанрам
        genres = self.request.query_params.getlist('genres')
        if genres:
            # Фильтруем пользователей, у которых есть выбранные жанры в favorite_genres
            genre_filters = []
            for genre in genres:
                genre_filters.append(f'"favorite_genres" ? "{genre}"')
            if genre_filters:
                import functools
                import operator
                from django.db.models import Q
                genre_query = functools.reduce(operator.or_, [Q(**{f'favorite_genres__contains': genre}) for genre in genres])
                queryset = queryset.filter(genre_query)

        # Поиск по username или nickname
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(nickname__icontains=search) |
                Q(display_name__icontains=search)
            )

        # Сортировка
        ordering = self.request.query_params.get('ordering', '-last_login')
        if ordering in ['username', '-username', 'nickname', '-nickname', 'display_name', '-display_name', 'level', '-level', '-last_login']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-last_login')

        return queryset.select_related()


class UserSearchView(generics.ListAPIView):
    """Поиск пользователей для создания чатов"""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # Получаем всех пользователей, исключая текущего
        queryset = User.objects.exclude(id=self.request.user.id).select_related('settings')

        # Поиск по username, nickname или display_name
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(nickname__icontains=search) |
                Q(display_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Сортировка: сначала по релевантности поиска, затем по онлайн статусу
        if search:
            # Более сложная сортировка для поиска
            queryset = queryset.order_by('-is_online', '-last_login')
        else:
            # Для общего списка - сначала онлайн, затем по активности
            queryset = queryset.order_by('-is_online', '-last_login')

        return queryset[:50]  # Ограничиваем результат 50 пользователями


class NicknameCheckView(APIView):
    """Проверка доступности nickname"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = NicknameCheckSerializer(data=request.data)
        if serializer.is_valid():
            return Response({'available': True, 'message': 'Nickname доступен'})
        return Response({
            'available': False,
            'error': serializer.errors['nickname'][0] if 'nickname' in serializer.errors else 'Недопустимый nickname'
        }, status=status.HTTP_400_BAD_REQUEST)


class TwoFactorSetupView(APIView):
    """Настройка двухфакторной аутентификации"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            action = serializer.validated_data['action']

            if action == 'enable':
                # Проверяем, что email и телефон подтверждены
                if not user.email_verified:
                    return Response({
                        'error': 'Необходимо подтвердить email для включения 2FA',
                        'missing': 'email'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if not user.phone_verified:
                    return Response({
                        'error': 'Необходимо подтвердить номер телефона для включения 2FA',
                        'missing': 'phone'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Логика включения 2FA
                secret = pyotp.random_base32()
                user.two_factor_secret = secret
                user.two_factor_enabled = True
                user.save()

                # Генерируем QR код для приложения-аутентификатора
                totp = pyotp.TOTP(secret)
                provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="AnimeCore")

                return Response({
                    'message': '2FA включен',
                    'secret': secret,
                    'provisioning_uri': provisioning_uri
                })

            elif action == 'disable':
                user.two_factor_enabled = False
                user.two_factor_secret = None
                user.save()
                return Response({'message': '2FA отключен'})

            elif action == 'verify':
                code = serializer.validated_data['code']
                totp = pyotp.TOTP(user.two_factor_secret)
                if totp.verify(code):
                    return Response({'message': 'Код подтвержден'})
                else:
                    return Response({'error': 'Неверный код'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RealtimeUpdatesView(APIView):
    """Получение обновлений в реальном времени из Redis"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """Получить недавние обновления"""
        limit = int(request.query_params.get('limit', 50))
        events = event_publisher.get_recent_events(limit)
        return Response({'events': events})


# Сигналы для автоматического создания настроек и отслеживания сессий
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from .models import (
    UserSettings, UserSession, UserProfileSettings, TwoFactorAuth,
    NotificationSettings, PrivacySettings, UserAnalytics
)

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Автоматически создаем настройки для нового пользователя"""
    if created:
        # Создаем все необходимые настройки
        UserSettings.objects.create(user=instance)
        UserProfileSettings.objects.create(user=instance)
        TwoFactorAuth.objects.create(user=instance)
        NotificationSettings.objects.create(user=instance)
        PrivacySettings.objects.create(user=instance)
        UserAnalytics.objects.create(user=instance)

@receiver(post_save, sender=Session)
def create_user_session(sender, instance, created, **kwargs):
    """Отслеживаем активные сессии пользователей"""
    if created:
        try:
            session_data = instance.get_decoded()
            user_id = session_data.get('_auth_user_id')
            if user_id:
                user = User.objects.get(id=user_id)
                # Получаем информацию о устройстве из User-Agent
                from django.http import HttpRequest
                # Создаем фиктивный request для парсинга User-Agent
                user_agent = getattr(instance, 'user_agent', 'Unknown')

                # Определяем тип устройства на основе User-Agent
                device_info = 'Unknown Device'
                if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                    device_info = 'Mobile Device'
                elif 'Windows' in user_agent:
                    device_info = 'Windows PC'
                elif 'Mac' in user_agent:
                    device_info = 'Mac Computer'
                elif 'Linux' in user_agent:
                    device_info = 'Linux Computer'
                else:
                    device_info = 'Web Browser'

                UserSession.objects.get_or_create(
                    user=user,
                    session_key=instance.session_key,
                    defaults={
                        'device_info': device_info,
                        'user_agent': user_agent[:200],  # Ограничиваем длину
                    }
                )
        except Exception as e:
            # Игнорируем ошибки при создании сессий
            pass

@receiver(post_delete, sender=Session)
def cleanup_user_sessions(sender, instance, **kwargs):
    """Удаляем записи о сессиях при их завершении"""
    UserSession.objects.filter(session_key=instance.session_key).delete()


@receiver(user_logged_out)
def set_user_offline(sender, user, request, **kwargs):
    """Устанавливаем статус оффлайн при выходе пользователя"""
    user.is_online = False
    user.save(update_fields=['is_online'])
    # Публикуем событие пользователь оффлайн
    from core.redis_events import publish_user_offline
    publish_user_offline(user.id, user.username)


# Новые ViewSets для расширенных настроек
from rest_framework import viewsets
from .models import (
    UserProfileSettings, TwoFactorAuth, ActiveSession,
    NotificationSettings, PrivacySettings, UserTheme,
    ChatBackground, UserAnalytics
)
from .serializers import (
    UserProfileSettingsSerializer, TwoFactorAuthSerializer,
    ActiveSessionSerializer, NotificationSettingsSerializer,
    PrivacySettingsSerializer, UserThemeSerializer,
    ChatBackgroundSerializer, UserAnalyticsSerializer
)


class UserProfileSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet для основных настроек профиля"""
    serializer_class = UserProfileSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfileSettings.objects.filter(user=self.request.user)

    def get_object(self):
        """Возвращает настройки пользователя или создает их"""
        settings, created = UserProfileSettings.objects.get_or_create(user=self.request.user)
        return settings


class TwoFactorAuthViewSet(viewsets.ViewSet):
    """ViewSet для двухфакторной аутентификации"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Получить статус 2FA"""
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
        serializer = TwoFactorAuthSerializer(two_factor)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def enable(self, request):
        """Включить 2FA"""
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)

        if two_factor.is_enabled:
            return Response({'error': '2FA уже включена'}, status=400)

        # Генерация секрета если его нет
        if not two_factor.secret_key:
            two_factor.generate_secret()
            two_factor.generate_backup_codes()
            two_factor.save()

        # Генерация QR-кода
        totp = pyotp.TOTP(two_factor.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email,
            issuer_name="Messenger"
        )

        # Создание QR-кода в base64
        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'secret': two_factor.secret_key,
            'qr_code': f'data:image/png;base64,{qr_base64}',
            'backup_codes': two_factor.backup_codes[:3]  # Показываем только первые 3
        })

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Верификация и включение 2FA"""
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Код обязателен'}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)

        if two_factor.verify_code(code):
            two_factor.is_enabled = True
            two_factor.save()

            # Запись в логи безопасности
            from .models import SecurityLog
            SecurityLog.objects.create(
                user=request.user,
                action='2fa_enabled',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            return Response({'success': True})

        return Response({'error': 'Неверный код'}, status=400)

    @action(detail=False, methods=['get'])
    def backup_codes(self, request):
        """Получить резервные коды"""
        two_factor = TwoFactorAuth.objects.get(user=request.user)
        if not two_factor.is_enabled:
            return Response({'error': '2FA не включена'}, status=400)

        return Response({'codes': two_factor.backup_codes})

    @action(detail=False, methods=['post'])
    def regenerate_backup_codes(self, request):
        """Сгенерировать новые резервные коды"""
        two_factor = TwoFactorAuth.objects.get(user=request.user)
        two_factor.generate_backup_codes()
        two_factor.save()

        return Response({'codes': two_factor.backup_codes})

    @action(detail=False, methods=['post'])
    def disable(self, request):
        """Отключить 2FA"""
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Пароль обязателен'}, status=400)

        # Проверка пароля
        if not request.user.check_password(password):
            return Response({'error': 'Неверный пароль'}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)
        two_factor.is_enabled = False
        two_factor.save()

        return Response({'success': True})

    def get_client_ip(self, request):
        """Получить IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionViewSet(viewsets.ViewSet):
    """ViewSet для управления активными сессиями"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить все активные сессии пользователя"""
        # Получаем все сессии Django для пользователя
        sessions = ActiveSession.objects.filter(user=request.user)
        serializer = ActiveSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def terminate(self, request):
        """Завершить конкретную сессию"""
        session_key = request.data.get('session_key')

        if not session_key:
            return Response({'error': 'session_key обязателен'}, status=400)

        # Нельзя завершить текущую сессию через этот метод
        if session_key == request.session.session_key:
            return Response({'error': 'Нельзя завершить текущую сессию'}, status=400)

        try:
            session = Session.objects.get(session_key=session_key)

            # Проверяем, что сессия принадлежит пользователю
            session_data = session.get_decoded()
            if '_auth_user_id' not in session_data or str(request.user.id) != session_data['_auth_user_id']:
                return Response({'error': 'Доступ запрещен'}, status=403)

            # Удаляем сессию
            session.delete()

            # Удаляем запись ActiveSession
            ActiveSession.objects.filter(session_key=session_key).delete()

            return Response({'success': True})

        except Session.DoesNotExist:
            return Response({'error': 'Сессия не найдена'}, status=404)

    @action(detail=False, methods=['post'])
    def terminate_all_others(self, request):
        """Завершить все другие сессии"""
        current_session_key = request.session.session_key

        # Находим все сессии пользователя кроме текущей
        user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        sessions_to_delete = []

        for session in user_sessions:
            session_data = session.get_decoded()
            if ('_auth_user_id' in session_data and
                str(request.user.id) == session_data['_auth_user_id'] and
                session.session_key != current_session_key):

                sessions_to_delete.append(session.session_key)

        # Удаляем сессии
        Session.objects.filter(session_key__in=sessions_to_delete).delete()
        ActiveSession.objects.filter(session_key__in=sessions_to_delete).delete()

        return Response({
            'success': True,
            'terminated_count': len(sessions_to_delete)
        })


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet для настроек уведомлений"""
    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationSettings.objects.filter(user=self.request.user)

    def get_object(self):
        """Возвращает настройки уведомлений пользователя или создает их"""
        settings, created = NotificationSettings.objects.get_or_create(user=self.request.user)
        return settings


class PrivacySettingsViewSet(viewsets.ModelViewSet):
    """ViewSet для настроек приватности"""
    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrivacySettings.objects.filter(user=self.request.user)

    def get_object(self):
        """Возвращает настройки приватности пользователя или создает их"""
        settings, created = PrivacySettings.objects.get_or_create(user=self.request.user)
        return settings

    @action(detail=False, methods=['get'])
    def check_visibility(self, request):
        """Проверить, что может видеть другой пользователь"""
        target_user_id = request.query_params.get('user_id')

        if not target_user_id:
            return Response({'error': 'user_id обязателен'}, status=400)

        try:
            target_user = User.objects.get(id=target_user_id)

            # Проверяем, являются ли пользователи контактами
            from social.models import PrivateChat
            from django.db.models import Q
            is_contact = PrivateChat.objects.filter(
                (Q(user1=request.user) & Q(user2=target_user)) |
                (Q(user1=target_user) & Q(user2=request.user))
            ).exists()

            try:
                privacy_settings = target_user.privacy_settings
                visibility = {
                    'phone': self.check_field_visibility('who_can_see_phone', privacy_settings, is_contact),
                    'email': self.check_field_visibility('who_can_see_email', privacy_settings, is_contact),
                    'last_seen': self.check_field_visibility('who_can_see_last_seen', privacy_settings, is_contact),
                    'profile_photo': self.check_field_visibility('who_can_see_profile_photo', privacy_settings, is_contact),
                    'can_call': self.check_field_visibility('who_can_call', privacy_settings, is_contact),
                    'is_blocked': privacy_settings.blocked_users.filter(id=request.user.id).exists()
                }
            except Exception:
                # Если настройки приватности не существуют, возвращаем значения по умолчанию
                visibility = {
                    'phone': True,  # contacts
                    'email': True,  # contacts
                    'last_seen': True,  # everyone
                    'profile_photo': True,  # everyone
                    'can_call': True,  # everyone
                    'is_blocked': False
                }

            return Response(visibility)

        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

    def check_field_visibility(self, field_name, privacy_settings, is_contact):
        """Проверка видимости поля"""
        value = getattr(privacy_settings, field_name)

        if value == 'everyone':
            return True
        elif value == 'contacts':
            return is_contact
        else:  # nobody
            return False

    @action(detail=False, methods=['get'])
    def blocked_users(self, request):
        """Получить список заблокированных пользователей"""
        try:
            privacy_settings = request.user.privacy_settings
            blocked_users = privacy_settings.blocked_users.all()
        except Exception:
            # Если настройки не существуют, возвращаем пустой список
            blocked_users = []

        from .serializers import UserSimpleSerializer  # Создадим простой сериализатор для пользователей
        serializer = UserSimpleSerializer(blocked_users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def block_user(self, request):
        """Заблокировать пользователя"""
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=400)

        try:
            user_to_block = User.objects.get(id=user_id)

            try:
                privacy_settings = request.user.privacy_settings

                if privacy_settings.blocked_users.filter(id=user_id).exists():
                    return Response({'error': 'Пользователь уже заблокирован'}, status=400)

                privacy_settings.blocked_users.add(user_to_block)
            except Exception:
                # Если настройки не существуют, создаем их
                from .models import PrivacySettings
                privacy_settings, created = PrivacySettings.objects.get_or_create(user=request.user)
                privacy_settings.blocked_users.add(user_to_block)

            # Удаляем из контактов (контакты определяются наличием личного чата, который уже удален выше)
            pass

            # Удаляем из общих чатов (личных)
            from social.models import PrivateChat
            PrivateChat.objects.filter(
                (Q(user1=request.user) & Q(user2=user_to_block)) |
                (Q(user1=user_to_block) & Q(user2=request.user))
            ).delete()

            return Response({'success': True})

        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

    @action(detail=False, methods=['post'])
    def unblock_user(self, request):
        """Разблокировать пользователя"""
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=400)

        try:
            user_to_unblock = User.objects.get(id=user_id)

            try:
                privacy_settings = request.user.privacy_settings

                if not privacy_settings.blocked_users.filter(id=user_id).exists():
                    return Response({'error': 'Пользователь не заблокирован'}, status=400)

                privacy_settings.blocked_users.remove(user_to_unblock)
            except Exception:
                # Если настройки не существуют, пользователь не может быть заблокирован
                return Response({'error': 'Пользователь не заблокирован'}, status=400)

            return Response({'success': True})

        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)


class UserThemeViewSet(viewsets.ModelViewSet):
    """ViewSet для пользовательских тем"""
    serializer_class = UserThemeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTheme.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatBackgroundViewSet(viewsets.ModelViewSet):
    """ViewSet для фонов чатов"""
    serializer_class = ChatBackgroundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatBackground.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для аналитики пользователя"""
    serializer_class = UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAnalytics.objects.filter(user=self.request.user)

    def get_object(self):
        """Возвращает аналитику пользователя или создает её"""
        analytics, created = UserAnalytics.objects.get_or_create(user=self.request.user)
        return analytics

