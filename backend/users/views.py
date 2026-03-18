from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import update_last_login
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from rest_framework import status, generics, viewsets
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
    UserSerializer, UserSimpleSerializer, RegisterSerializer, LoginSerializer,
    PhoneVerificationSerializer, EmailVerificationSerializer,
    GoogleAuthSerializer, PasswordResetSerializer,
    ProfileUpdateSerializer, UserSessionSerializer, UserSettingsSerializer,
    NicknameCheckSerializer, TwoFactorSetupSerializer, ChangePasswordSerializer,
    UserLibrarySerializer
)
from .models import UserLibrary
from core.redis_events import event_publisher


class CurrentUserView(APIView):
    """Получение текущего авторизованного пользователя"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/users/me/ - получить данные текущего пользователя"""
        user = request.user
        serializer = UserSerializer(user)
        data = serializer.data

        # Добавляем avatar_url
        data['avatar_url'] = user.avatar.url if user.avatar else None
        
        return Response(data)


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
                <p>© 2026 AnimeCore. Все права защищены.</p>
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

                <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center;">
                    <span style="font-size: 32px; font-weight: bold; color: #667eea;">{code_or_link}</span>
                </div>

                <p style="color: #999; font-size: 14px; margin-top: 30px;">Код действителен в течение 30 минут.</p>
                <p style="color: #999; font-size: 14px;">Если вы не запрашивали этот код, просто игнорируйте это письмо.</p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2026 AnimeCore. Все права защищены.</p>
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
        confirm_url = f"http://anisphere.ru/confirm-email?token={token}&email={user.email}"
        send_verification_email(user.email, confirm_url, is_link=True)


class LoginView(APIView):
    """Вход в систему"""
    permission_classes = (AllowAny,)

    def post(self, request):
        print(f"🔐 LoginView - Login attempt for user: {request.data.get('username')}")
        print(f"🔐 LoginView - Request headers: {dict(request.headers)}")

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Serializer validation already authenticated the user
            user = serializer.validated_data.get('user')
            if user:
                print(f"✅ LoginView - User authenticated: {user.username} (ID: {user.id})")

                login(request, user)
                user.is_online = True
                user.save()

                refresh = RefreshToken.for_user(user)
                update_last_login(None, user)

                print(f"✅ LoginView - Tokens generated")
                print(f"🔑 LoginView - Access token: {str(refresh.access_token)[:50]}...")
                print(f"🔑 LoginView - Refresh token: {str(refresh)[:50]}...")

                # Проверяем payload токена
                access_token = refresh.access_token
                print(f"🔍 LoginView - Access token payload: user_id={access_token.get('user_id')}, exp={access_token.get('exp')}")

                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
        else:
            print(f"❌ LoginView - Validation failed: {serializer.errors}")

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
        redirect_uri = f"{settings.SITE_URL.rstrip('/')}/api/users/google/callback/"
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
        session_state = request.session.get('google_oauth_state')
        if not state or state != session_state:
            return Response({'error': 'Invalid state parameter'}, status=400)
        del request.session['google_oauth_state']

        print(f"DEBUG: Skipping state validation for development")

        # Проверка state отключена, т.к. сессия не сохраняется между доменами
        # В продакшене нужно использовать Redis для хранения state или передавать его через frontend
        # session_state = request.session.get('google_oauth_state')
        # if not state or state != session_state:
        #     return Response({'error': 'Invalid state parameter'}, status=400)
        # if request.session.get('google_oauth_state'):
        #     del request.session['google_oauth_state']

        print(f"DEBUG: State validation skipped - proceeding with token exchange")

        try:
            # Обмениваем authorization code на access token
            redirect_uri = f"{settings.SITE_URL.rstrip('/')}/api/users/google/callback/"
            token_data = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }

            print(f"DEBUG: Token exchange request")
            print(f"  client_id: {settings.GOOGLE_CLIENT_ID[:20]}...")
            print(f"  redirect_uri: {redirect_uri}")
            print(f"  code: {code[:20]}...")

            token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            print(f"DEBUG: Token response status: {token_response.status_code}")
            if token_response.status_code != 200:
                print(f"DEBUG: Token error response: {token_response.text}")
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

            # Определяем URL для редиректа (используем referer или SITE_URL)
            referer = request.META.get('HTTP_REFERER', '')
            if 'www.anisphere.ru' in referer:
                redirect_url = 'https://www.anisphere.ru/'
            elif 'anisphere.ru' in referer:
                redirect_url = 'https://anisphere.ru/'
            else:
                redirect_url = settings.SITE_URL

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
                    window.location.href = '{redirect_url}';
                </script>
            </head>
            <body>
                <p>Google авторизация успешна! Перенаправление...</p>
            </body>
            </html>
            """

            return HttpResponse(html_content, content_type='text/html')

        except Exception as e:
            print(f"ERROR: Google OAuth callback exception: {str(e)}")
            import traceback
            print(traceback.format_exc())
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
                <a href="http://anisphere.ru/login" class="button">Войти в аккаунт</a>
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


class UserPublicProfileView(generics.RetrieveAPIView):
    """Публичный профиль пользователя (доступен по ID или username)"""
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'pk'

    def get_queryset(self):
        return User.objects.all()

    def get_object(self):
        """Получает пользователя по ID из URL"""
        pk = self.kwargs.get('pk')
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise generics.NotFound('Пользователь не найден')


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

                    <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center;">
                        <span style="font-size: 24px; font-weight: bold; color: #667eea;">{new_password}</span>
                    </div>

                    <p style="color: #666; line-height: 1.6;"><strong>Важно:</strong> Рекомендуем изменить этот пароль после входа в систему в настройках профиля.</p>
                </div>

                <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                    <p>© 2026 AnimeCore. Все права защищены.</p>
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
    if user:
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
        """Начать процесс включения 2FA"""
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)

        if two_factor.is_enabled:
            return Response({'error': '2FA уже включена'}, status=400)

        # Проверяем подтверждение email
        if not request.user.email_verified:
            return Response({
                'error': 'Необходимо подтвердить email для включения 2FA',
                'missing': 'email'
            }, status=400)

        # Генерация секрета если его нет
        if not two_factor.secret_key:
            two_factor.generate_secret()
            two_factor.generate_backup_codes()
            two_factor.save()

        # Генерация QR-кода
        totp = pyotp.TOTP(two_factor.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email,
            issuer_name="AnimeCore"
        )

        # Создание QR-кода в base64
        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Запись в логи безопасности
        SecurityLog.objects.create(
            user=request.user,
            action='2fa_setup_started',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'secret': two_factor.secret_key,
            'qr_code': f'data:image/png;base64,{qr_base64}',
            'backup_codes_count': len(two_factor.backup_codes),
            'message': 'Отсканируйте QR-код в приложении аутентификатора и введите код для подтверждения'
        })

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Верификация и включение 2FA"""
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Код обязателен'}, status=400)

        # Проверяем формат кода
        if not code.isdigit() or len(code) != 6:
            return Response({'error': 'Код должен состоять из 6 цифр'}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)

        if two_factor.verify_code(code):
            two_factor.is_enabled = True
            two_factor.save()

            # Запись в логи безопасности
            SecurityLog.objects.create(
                user=request.user,
                action='2fa_enabled',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                additional_data={
                    'method': 'totp',
                    'require_on_new_device': two_factor.require_on_new_device
                }
            )

            # Публикуем событие в Redis
            from core.redis_events import publish_settings_update
            publish_settings_update(request.user.id, ['two_factor_enabled'])

            return Response({
                'success': True,
                'message': 'Двухфакторная аутентификация успешно включена'
            })

        return Response({'error': 'Неверный код. Попробуйте еще раз.'}, status=400)

    @action(detail=False, methods=['post'])
    def verify_backup_code(self, request):
        """Верификация резервного кода"""
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Код обязателен'}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)

        if not two_factor.is_enabled:
            return Response({'error': '2FA не включена'}, status=400)

        # Проверяем резервный код
        if code in two_factor.backup_codes:
            two_factor.backup_codes.remove(code)
            two_factor.save()

            # Запись в логи безопасности
            SecurityLog.objects.create(
                user=request.user,
                action='2fa_backup_code_used',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                additional_data={
                    'codes_remaining': len(two_factor.backup_codes)
                }
            )

            return Response({
                'success': True,
                'message': 'Код подтвержден. Рекомендуем сгенерировать новые резервные коды.',
                'codes_remaining': len(two_factor.backup_codes)
            })

        return Response({'error': 'Неверный резервный код'}, status=400)

    @action(detail=False, methods=['get'])
    def backup_codes(self, request):
        """Получить резервные коды"""
        two_factor = TwoFactorAuth.objects.get(user=request.user)
        if not two_factor.is_enabled:
            return Response({'error': '2FA не включена'}, status=400)

        return Response({
            'codes': two_factor.backup_codes,
            'count': len(two_factor.backup_codes)
        })

    @action(detail=False, methods=['post'])
    def regenerate_backup_codes(self, request):
        """Сгенерировать новые резервные коды"""
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Пароль обязателен для генерации новых кодов'}, status=400)

        # Проверка пароля
        if not request.user.check_password(password):
            return Response({'error': 'Неверный пароль'}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)
        two_factor.generate_backup_codes()
        two_factor.save()

        # Запись в логи безопасности
        SecurityLog.objects.create(
            user=request.user,
            action='2fa_backup_codes_regenerated',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data={
                'codes_count': len(two_factor.backup_codes)
            }
        )

        return Response({
            'success': True,
            'codes': two_factor.backup_codes,
            'message': 'Новые резервные коды сгенерированы. Сохраните их в безопасном месте.'
        })

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

        # Не удаляем секретный ключ и резервные коды - они могут понадобиться при повторном включении

        two_factor.save()

        # Запись в логи безопасности
        SecurityLog.objects.create(
            user=request.user,
            action='2fa_disabled',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['two_factor_disabled'])

        return Response({
            'success': True,
            'message': 'Двухфакторная аутентификация отключена'
        })

    @action(detail=False, methods=['post'])
    def update_settings(self, request):
        """Обновить настройки 2FA"""
        data = request.data
        two_factor = TwoFactorAuth.objects.get(user=request.user)

        # Обновляем настройки
        if 'require_on_new_device' in data:
            two_factor.require_on_new_device = data['require_on_new_device']

        if 'remember_device_days' in data:
            days = data['remember_device_days']
            if not isinstance(days, int) or days < 1 or days > 365:
                return Response({'error': 'Количество дней должно быть от 1 до 365'}, status=400)
            two_factor.remember_device_days = days

        if 'email_enabled' in data:
            two_factor.email_enabled = data['email_enabled']

        if 'phone_number' in data:
            phone = data['phone_number']
            if phone and not request.user.phone_verified:
                return Response({
                    'error': 'Необходимо подтвердить номер телефона для использования SMS 2FA'
                }, status=400)
            two_factor.phone_number = phone

        two_factor.save()

        # Запись в логи безопасности
        SecurityLog.objects.create(
            user=request.user,
            action='2fa_settings_updated',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data={
                'require_on_new_device': two_factor.require_on_new_device,
                'remember_device_days': two_factor.remember_device_days,
                'email_enabled': two_factor.email_enabled,
                'phone_enabled': bool(two_factor.phone_number)
            }
        )

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['two_factor_settings'])

        return Response({
            'success': True,
            'message': 'Настройки 2FA обновлены'
        })

    @action(detail=False, methods=['get'])
    def security_log(self, request):
        """Получить лог безопасности 2FA"""
        logs = SecurityLog.objects.filter(
            user=request.user,
            action__startswith='2fa'
        ).order_by('-created_at')[:20]

        log_data = []
        for log in logs:
            log_data.append({
                'action': log.action,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent[:100] if log.user_agent else '',
                'created_at': log.created_at.isoformat(),
                'additional_data': log.additional_data
            })

        return Response({'logs': log_data})

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


class ThemeSettingsView(APIView):
    """ViewSet для настроек темы"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить настройки темы"""
        profile = request.user.profile_settings

        return Response({
            'theme': profile.theme,
            'accent_color': profile.accent_color,
            'use_shared_background': profile.use_shared_background,
            'custom_background': profile.custom_background,
            'smooth_animations': profile.smooth_animations,
            'scroll_effects': profile.scroll_effects,
            'parallax_effect': profile.parallax_effect,
            'truncate_names': profile.truncate_names,
            'compact_lists': profile.compact_lists,
            'hide_avatars': profile.hide_avatars,
            'show_time_everywhere': profile.show_time_everywhere,
            'small_emojis': profile.small_emojis,
            'high_contrast': profile.high_contrast,
        })

    def put(self, request):
        """Обновить настройки темы"""
        profile = request.user.profile_settings
        data = request.data

        # Обновляем настройки темы
        if 'theme' in data:
            profile.theme = data['theme']
        if 'accent_color' in data:
            profile.accent_color = data['accent_color']
        if 'use_shared_background' in data:
            profile.use_shared_background = data['use_shared_background']
        if 'custom_background' in data:
            profile.custom_background = data['custom_background']
        if 'smooth_animations' in data:
            profile.smooth_animations = data['smooth_animations']
        if 'scroll_effects' in data:
            profile.scroll_effects = data['scroll_effects']
        if 'parallax_effect' in data:
            profile.parallax_effect = data['parallax_effect']
        if 'truncate_names' in data:
            profile.truncate_names = data['truncate_names']
        if 'compact_lists' in data:
            profile.compact_lists = data['compact_lists']
        if 'hide_avatars' in data:
            profile.hide_avatars = data['hide_avatars']
        if 'show_time_everywhere' in data:
            profile.show_time_everywhere = data['show_time_everywhere']
        if 'small_emojis' in data:
            profile.small_emojis = data['small_emojis']
        if 'high_contrast' in data:
            profile.high_contrast = data['high_contrast']

        profile.save()

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['theme_settings'])

        return Response({'success': True, 'message': 'Настройки темы обновлены'})


class ChatBackgroundSettingsView(APIView):
    """ViewSet для настроек фона чатов"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить настройки фона чатов"""
        profile = request.user.profile_settings

        # Получаем пользовательские фоны
        from .models import ChatBackground
        backgrounds = ChatBackground.objects.filter(user=request.user)

        background_data = []
        for bg in backgrounds:
            background_data.append({
                'id': bg.id,
                'name': bg.name,
                'image': bg.image.url if bg.image else None,
                'thumbnail': bg.thumbnail.url if bg.thumbnail else None,
                'is_default': bg.is_default,
                'opacity': bg.opacity,
                'created_at': bg.created_at.isoformat(),
            })

        return Response({
            'background_type': profile.background_type or 'default',
            'solid_color': profile.solid_color,
            'gradient_colors': profile.gradient_colors or {},
            'custom_image': profile.custom_image,
            'effects': profile.background_effects or {},
            'custom_backgrounds': background_data,
            'is_premium': profile.is_premium,
        })

    def put(self, request):
        """Обновить настройки фона чатов"""
        profile = request.user.profile_settings
        data = request.data

        # Обновляем настройки фона
        if 'background_type' in data:
            profile.background_type = data['background_type']
        if 'solid_color' in data:
            profile.solid_color = data['solid_color']
        if 'gradient_colors' in data:
            profile.gradient_colors = data['gradient_colors']
        if 'custom_image' in data:
            profile.custom_image = data['custom_image']
        if 'effects' in data:
            profile.background_effects = data['effects']

        profile.save()

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['chat_background_settings'])

        return Response({'success': True, 'message': 'Настройки фона обновлены'})

    def post(self, request):
        """Загрузить изображение фона"""
        from .models import ChatBackground
        from django.core.files.images import get_image_dimensions

        file = request.FILES.get('background_image')
        if not file:
            return Response({'error': 'Изображение не загружено'}, status=400)

        # Проверяем размер файла
        if file.size > 10 * 1024 * 1024:  # 10MB
            return Response({'error': 'Размер файла не должен превышать 10MB'}, status=400)

        # Создаем фон
        background = ChatBackground.objects.create(
            user=request.user,
            name=request.data.get('name', 'Custom Background'),
            image=file,
            opacity=float(request.data.get('opacity', 0.1)),
        )

        # Создаем превью
        from PIL import Image
        import io

        img = Image.open(file)
        img.thumbnail((200, 200))
        thumb_io = io.BytesIO()
        img.save(thumb_io, format='JPEG', quality=85)
        thumb_io.seek(0)

        from django.core.files.uploadedfile import InMemoryUploadedFile
        thumb_file = InMemoryUploadedFile(
            thumb_io,
            None,
            f'thumb_{file.name}',
            'image/jpeg',
            thumb_io.tell(),
            None
        )

        background.thumbnail.save(thumb_file.name, thumb_file, save=False)
        background.save()

        return Response({
            'success': True,
            'id': background.id,
            'url': background.image.url,
            'thumbnail': background.thumbnail.url if background.thumbnail else None,
        })

    def delete(self, request):
        """Удалить фоновое изображение"""
        profile = request.user.profile_settings
        profile.custom_image = ''
        profile.save()

        return Response({'success': True, 'message': 'Фоновое изображение удалено'})


class FontSettingsView(APIView):
    """ViewSet для настроек шрифтов"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить настройки шрифтов"""
        from .models import FontSettings

        font_settings, created = FontSettings.objects.get_or_create(user=request.user)

        return Response({
            'font_family': font_settings.font_family,
            'font_size': font_settings.font_size,
            'interface_scale': font_settings.interface_scale,
            'line_height': font_settings.line_height,
            'density': font_settings.density,
            'bold_headings': font_settings.bold_headings,
            'increase_line_height': font_settings.increase_line_height,
            'monospace_code': font_settings.monospace_code,
            'reduce_motion': font_settings.reduce_motion,
            'high_contrast_mode': font_settings.high_contrast_mode,
        })

    def put(self, request):
        """Обновить настройки шрифтов"""
        from .models import FontSettings

        font_settings, created = FontSettings.objects.get_or_create(user=request.user)
        data = request.data

        # Обновляем настройки шрифтов
        if 'font_family' in data:
            font_settings.font_family = data['font_family']
        if 'font_size' in data:
            font_settings.font_size = data['font_size']
        if 'interface_scale' in data:
            font_settings.interface_scale = data['interface_scale']
        if 'line_height' in data:
            font_settings.line_height = data['line_height']
        if 'density' in data:
            font_settings.density = data['density']
        if 'bold_headings' in data:
            font_settings.bold_headings = data['bold_headings']
        if 'increase_line_height' in data:
            font_settings.increase_line_height = data['increase_line_height']
        if 'monospace_code' in data:
            font_settings.monospace_code = data['monospace_code']
        if 'reduce_motion' in data:
            font_settings.reduce_motion = data['reduce_motion']
        if 'high_contrast_mode' in data:
            font_settings.high_contrast_mode = data['high_contrast_mode']

        font_settings.save()

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['font_settings'])

        return Response({'success': True, 'message': 'Настройки шрифтов обновлены'})


class SessionViewSet(viewsets.ViewSet):
    """ViewSet для управления сессиями пользователя"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Получить список активных сессий"""
        from django.contrib.sessions.models import Session

        # Получаем все сессии
        sessions = Session.objects.all()

        # Фильтруем сессии текущего пользователя
        user_sessions = []
        for session in sessions:
            try:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(request.user.id):
                    user_sessions.append({
                        'id': session.pk,
                        'session_key': session.pk,
                        'user_agent': session_data.get('user_agent', ''),
                        'ip_address': session_data.get('ip_address', ''),
                        'device_name': session_data.get('device_name', 'Unknown'),
                        'location': session_data.get('location', 'Unknown'),
                        'last_activity': session_data.get('last_activity'),
                        'created_at': session_data.get('created_at'),
                    })
            except:
                continue

        # Сортируем по времени последней активности
        user_sessions.sort(key=lambda x: x.get('last_activity', ''), reverse=True)

        return Response(user_sessions)

    @action(detail=False, methods=['post'])
    def terminate(self, request):
        """Завершить конкретную сессию"""
        from django.contrib.sessions.models import Session

        session_key = request.data.get('session_key')
        if not session_key:
            return Response({'error': 'session_key обязателен'}, status=400)

        try:
            session = Session.objects.get(pk=session_key)
            session.delete()
            return Response({'success': True, 'message': 'Сессия завершена'})
        except Session.DoesNotExist:
            return Response({'error': 'Сессия не найдена'}, status=404)

    @action(detail=False, methods=['post'])
    def terminate_all_others(self, request):
        """Завершить все сессии кроме текущей"""
        from django.contrib.sessions.models import Session
        from django.contrib.auth import logout

        # Получаем текущую сессию
        current_session_key = request.session.session_key

        # Удаляем все сессии кроме текущей
        Session.objects.exclude(session_key=current_session_key).delete()

        # Записываем в лог безопасности
        SecurityLog.objects.create(
            user=request.user,
            action='all_other_sessions_terminated',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({'success': True, 'message': 'Все другие сессии завершены'})

    def get_client_ip(self, request):
        """Получить IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class StorageUsageView(APIView):
    """ViewSet для использования памяти"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить статистику использования памяти"""
        from social.models import Message, Comment, PrivateChat
        from anime.models import Anime, Playlist

        user = request.user

        # Подсчёт использования памяти (упрощённо)
        messages_count = Message.objects.filter(sender=user).count()
        comments_count = Comment.objects.filter(author=user).count()
        playlists_count = Playlist.objects.filter(user=user).count()
        library_count = user.library.count() if hasattr(user, 'library') else 0

        # Расчёт примерного размера (в байтах)
        messages_size = messages_count * 500  # среднее 500 байт на сообщение
        comments_size = comments_count * 300  # среднее 300 байт на комментарий
        media_size = 0  # TODO: посчитать реальные медиа файлы
        documents_size = 0  # TODO: посчитать документы
        audio_size = 0  # TODO: посчитать аудио

        # Кэш (упрощённо)
        cache_size = 10 * 1024 * 1024  # 10 MB

        total_size = messages_size + comments_size + media_size + documents_size + audio_size + cache_size
        total_limit = 2 * 1024 * 1024 * 1024  # 2 GB

        return Response({
            'messages': messages_size,
            'media': media_size,
            'documents': documents_size,
            'audio': audio_size,
            'cache': cache_size,
            'total': total_size,
            'limit': total_limit,
            'usage_percent': round((total_size / total_limit) * 100, 1),
            'breakdown': {
                'messages_count': messages_count,
                'comments_count': comments_count,
                'playlists_count': playlists_count,
                'library_count': library_count,
            }
        })


class SyncSettingsView(APIView):
    """ViewSet для настроек синхронизации"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить настройки синхронизации"""
        from .models import SyncSettings

        sync_settings, created = SyncSettings.objects.get_or_create(user=request.user)

        # Получаем список устройств
        devices = self.get_user_devices(request.user)

        return Response({
            'sync_options': {
                'playlists': sync_settings.sync_playlists,
                'settings': sync_settings.sync_settings,
                'favorites': sync_settings.sync_favorites,
                'history': sync_settings.sync_history,
                'drafts': sync_settings.sync_drafts,
                'watchlist': sync_settings.sync_watchlist,
            },
            'sync_condition': sync_settings.sync_condition,
            'sync_schedule': sync_settings.sync_schedule,
            'wifi_only': sync_settings.wifi_only,
            'charging_only': sync_settings.charging_only,
            'last_sync_time': sync_settings.last_sync_time.isoformat() if sync_settings.last_sync_time else None,
            'next_sync_time': sync_settings.next_sync_time.isoformat() if sync_settings.next_sync_time else None,
            'sync_status': sync_settings.sync_status,
            'synced_devices': len(devices),
            'sync_data_size': self.calculate_sync_size(request.user),
            'devices': devices,
        })

    def put(self, request):
        """Обновить настройки синхронизации"""
        from .models import SyncSettings

        sync_settings, created = SyncSettings.objects.get_or_create(user=request.user)
        data = request.data

        # Обновляем настройки синхронизации
        sync_options = data.get('sync_options', {})
        if 'playlists' in sync_options:
            sync_settings.sync_playlists = sync_options['playlists']
        if 'settings' in sync_options:
            sync_settings.sync_settings = sync_options['settings']
        if 'favorites' in sync_options:
            sync_settings.sync_favorites = sync_options['favorites']
        if 'history' in sync_options:
            sync_settings.sync_history = sync_options['history']
        if 'drafts' in sync_options:
            sync_settings.sync_drafts = sync_options['drafts']
        if 'watchlist' in sync_options:
            sync_settings.sync_watchlist = sync_options['watchlist']

        if 'sync_condition' in data:
            sync_settings.sync_condition = data['sync_condition']
        if 'sync_schedule' in data:
            sync_settings.sync_schedule = data['sync_schedule']
        if 'wifi_only' in data:
            sync_settings.wifi_only = data['wifi_only']
        if 'charging_only' in data:
            sync_settings.charging_only = data['charging_only']

        sync_settings.save()

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['sync_settings'])

        return Response({'success': True, 'message': 'Настройки синхронизации обновлены'})

    def post(self, request):
        """Запустить синхронизацию"""
        from .models import SyncSettings

        sync_settings, created = SyncSettings.objects.get_or_create(user=request.user)
        sync_settings.sync_status = 'syncing'
        sync_settings.save()

        # Здесь должна быть логика синхронизации
        # Для примера просто меняем статус

        sync_settings.sync_status = 'synced'
        sync_settings.last_sync_time = timezone.now()
        sync_settings.save()

        # Публикуем событие в Redis
        from core.redis_events import publish_settings_update
        publish_settings_update(request.user.id, ['sync_completed'])

        return Response({'success': True, 'message': 'Синхронизация завершена'})

    def get_user_devices(self, user):
        """Получить список устройств пользователя"""
        # Упрощённая реализация
        return [
            {
                'id': 1,
                'name': 'Текущее устройство',
                'type': 'desktop',
                'platform': 'Web',
                'last_sync': timezone.now().isoformat(),
                'current': True,
                'synced': True,
            }
        ]

    def calculate_sync_size(self, user):
        """Рассчитать размер синхронизируемых данных"""
        # Упрощённая реализация
        return '2.4 MB'


class ExportDataView(APIView):
    """ViewSet для экспорта данных"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить список предыдущих экспортов"""
        from .models import DataExport

        exports = DataExport.objects.filter(user=request.user).order_by('-created_at')[:10]

        export_list = []
        for exp in exports:
            export_list.append({
                'id': exp.id,
                'created_at': exp.created_at.isoformat(),
                'format': exp.format,
                'size': exp.size,
                'status': exp.status,
                'expires_at': exp.expires_at.isoformat() if exp.expires_at else None,
                'download_url': exp.download_url if exp.status == 'ready' else None,
            })

        return Response({'exports': export_list})

    def post(self, request):
        """Запросить экспорт данных"""
        from .models import DataExport
        from datetime import timedelta

        data = request.data
        items = data.get('items', [])
        format_type = data.get('format', 'json')

        if not items:
            return Response({'error': 'Не выбраны данные для экспорта'}, status=400)

        # Создаём запрос на экспорт
        export = DataExport.objects.create(
            user=request.user,
            items=items,
            format=format_type,
            status='processing',
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Здесь должна быть логика экспорта
        # Для примера сразу помечаем как готовый
        export.status = 'ready'
        export.size = '42.5 MB'
        export.save()

        # Отправляем email уведомление
        self.send_export_notification(request.user, export)

        return Response({
            'success': True,
            'message': 'Запрос на экспорт создан. Ссылка будет отправлена на email.',
            'export_id': export.id
        })

    def send_export_notification(self, user, export):
        """Отправить уведомление о готовности экспорта"""
        from django.conf import settings
        from django.core.mail import send_mail

        subject = 'Данные готовы к скачиванию - AnimeCore'
        message = f'''
Здравствуйте, {user.display_name or user.username}!

Ваши данные успешно экспортированы и готовы к скачиванию.

Формат: {export.format.upper()}
Размер: {export.size}
Ссылка действительна до: {export.expires_at.strftime('%d.%m.%Y')}

Вы можете скачать данные в настройках профиля.
        '''

        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">AnimeCore</h1>
                <p style="color: #e8e8e8; margin: 10px 0 0 0;">Экспорт данных</p>
            </div>

            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="color: #333; line-height: 1.6;">Здравствуйте, <strong>{user.display_name or user.username}</strong>!</p>

                <p style="color: #666; line-height: 1.6;">Ваши данные успешно экспортированы и готовы к скачиванию.</p>

                <div style="background: #e3f2fd; padding: 20px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 5px 0; color: #1565c0;"><strong>Формат:</strong> {export.format.upper()}</p>
                    <p style="margin: 5px 0; color: #1565c0;"><strong>Размер:</strong> {export.size}</p>
                    <p style="margin: 5px 0; color: #1565c0;"><strong>Действует до:</strong> {export.expires_at.strftime('%d.%m.%Y')}</p>
                </div>

                <p style="color: #666; line-height: 1.6;">Вы можете скачать данные в настройках профиля.</p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2026 AnimeCore. Все права защищены.</p>
            </div>
        </body>
        </html>
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Ошибка отправки email об экспорте: {e}")


class ClearCacheView(APIView):
    """ViewSet для очистки кэша"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Очистить кэш"""
        from django.core.cache import cache

        data = request.data
        items = data.get('items', [])

        if not items:
            return Response({'error': 'Не выбраны элементы для очистки'}, status=400)

        cleared_items = []

        # Очищаем различные типы кэша
        if 'images' in items:
            # Очищаем кэш изображений
            cache.delete_pattern(f'user_{request.user.id}:image:*')
            cleared_items.append('images')

        if 'videos' in items:
            # Очищаем кэш видео
            cache.delete_pattern(f'user_{request.user.id}:video:*')
            cleared_items.append('videos')

        if 'search' in items:
            # Очищаем кэш поиска
            cache.delete_pattern(f'user_{request.user.id}:search:*')
            cleared_items.append('search')

        if 'history' in items:
            # Очищаем историю просмотров (только кэш, не саму историю)
            cache.delete_pattern(f'user_{request.user.id}:history:*')
            cleared_items.append('history')

        if 'cookies' in items:
            # Примечание: очистка cookies происходит на клиенте
            cleared_items.append('cookies')

        if 'posters' in items:
            cache.delete_pattern(f'user_{request.user.id}:poster:*')
            cleared_items.append('posters')

        if 'thumbnails' in items:
            cache.delete_pattern(f'user_{request.user.id}:thumbnail:*')
            cleared_items.append('thumbnails')

        if 'temp' in items:
            cache.delete_pattern(f'user_{request.user.id}:temp:*')
            cleared_items.append('temp')

        # Очищаем общий кэш пользователя
        cache.delete(f'user_settings:{request.user.id}')

        # Записываем в лог безопасности
        SecurityLog.objects.create(
            user=request.user,
            action='cache_cleared',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data={'items': cleared_items}
        )

        return Response({
            'success': True,
            'message': f'Очищено: {", ".join(cleared_items)}',
            'cleared_items': cleared_items
        })

    def get_client_ip(self, request):
        """Получить IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AccountDeletionView(APIView):
    """ViewSet для удаления аккаунта"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить статистику аккаунта перед удалением"""
        from social.models import Message, Comment, PrivateChat
        from anime.models import Anime

        user = request.user

        # Подсчет статистики
        stats = {
            'playlists_count': user.playlists_count,
            'comments_count': user.comments_count,
            'posts_count': user.posts_count,
            'likes_received': user.likes_received,
            'messages_count': Message.objects.filter(sender=user).count(),
            'chats_count': PrivateChat.objects.filter(user1=user).count() + PrivateChat.objects.filter(user2=user).count(),
            'library_count': user.library.count() if hasattr(user, 'library') else 0,
            'has_2fa': user.two_factor_enabled if hasattr(user, 'two_factor_enabled') else False,
            'masked_email': user.email[:3] + '***' + user.email.split('@')[1] if user.email else '',
            'deletion_scheduled': False,
            'deletion_date': None
        }

        # Проверяем, запланировано ли удаление
        from django.core.cache import cache
        deletion_key = f'account_deletion:{user.id}'
        deletion_data = cache.get(deletion_key)

        if deletion_data:
            stats['deletion_scheduled'] = True
            stats['deletion_date'] = deletion_data.get('scheduled_date')

        return Response(stats)

    def post(self, request):
        """Получить статистику аккаунта перед удалением"""
        from social.models import Message, Comment, PrivateChat
        from anime.models import Anime

        user = request.user

        # Подсчет статистики
        stats = {
            'playlists_count': user.playlists_count,
            'comments_count': user.comments_count,
            'posts_count': user.posts_count,
            'likes_received': user.likes_received,
            'messages_count': Message.objects.filter(sender=user).count(),
            'chats_count': PrivateChat.objects.filter(user1=user).count() + PrivateChat.objects.filter(user2=user).count(),
            'library_count': user.library.count() if hasattr(user, 'library') else 0,
            'has_2fa': user.two_factor_enabled if hasattr(user, 'two_factor_enabled') else False,
            'masked_email': user.email[:3] + '***' + user.email.split('@')[1] if user.email else '',
            'deletion_scheduled': False,
            'deletion_date': None
        }

        # Проверяем, запланировано ли удаление
        from django.core.cache import cache
        deletion_key = f'account_deletion:{user.id}'
        deletion_data = cache.get(deletion_key)

        if deletion_data:
            stats['deletion_scheduled'] = True
            stats['deletion_date'] = deletion_data.get('scheduled_date')

        return Response(stats)


class UsersListView(generics.ListAPIView):
    """Список пользователей с фильтрацией по статусу онлайн"""
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        from django.db.models import Q
        
        queryset = User.objects.all()

        # Фильтр по статусу онлайн
        status = self.request.query_params.get('status')
        if status == 'online':
            queryset = queryset.filter(is_online=True)
        elif status == 'offline':
            queryset = queryset.filter(is_online=False)

        # Поиск по username, nickname или display_name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(nickname__icontains=search) |
                Q(display_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Сортировка: сначала онлайн, затем по активности
        ordering = self.request.query_params.get('ordering', '-is_online')
        if ordering == 'online':
            queryset = queryset.order_by('-is_online', '-last_login')
        elif ordering == '-online':
            queryset = queryset.order_by('is_online', '-last_login')
        elif ordering in ['username', '-username', 'nickname', '-nickname', 'display_name', '-display_name', 'level', '-level', '-last_login', '-created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-is_online', '-last_login')

        return queryset


class ChangePasswordView(APIView):
    """Смена пароля"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'error': 'old_password и new_password обязательны'}, status=400)

        if not request.user.check_password(old_password):
            return Response({'error': 'Текущий пароль неверен'}, status=400)

        if len(new_password) < 8:
            return Response({'error': 'Пароль должен содержать минимум 8 символов'}, status=400)

        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': 'Пароль успешно изменён'})


class HeadersDebugView(APIView):
    """Отладка заголовков запроса"""
    permission_classes = [AllowAny]

    def get(self, request):
        headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
        return Response({
            'headers': headers,
            'user': str(request.user),
            'auth': str(request.auth),
        })


class AuthDebugView(APIView):
    """Отладка аутентификации"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'user': str(request.user),
            'is_authenticated': request.user.is_authenticated,
            'auth': str(request.auth),
            'method': request.method,
        })


class UserFeedView(generics.ListAPIView):
    """Лента пользователя"""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return User.objects.filter(id=user_id)

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

        try:
            from social.models import Post
            from social.serializers import PostSerializer
            posts = Post.objects.filter(author=user).order_by('-created_at')[:20]
            serializer = PostSerializer(posts, many=True, context={'request': request})
            return Response({'results': serializer.data})
        except Exception:
            return Response({'results': []})


class UserStatsView(APIView):
    """Статистика пользователя"""
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        try:
            if isinstance(pk, int) or (isinstance(pk, str) and pk.isdigit()):
                user = User.objects.get(id=int(pk))
            else:
                user = User.objects.get(username=pk)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

        return Response({
            'id': user.id,
            'username': user.username,
            'level': user.level,
            'experience': user.experience,
            'posts_count': user.posts_count,
            'comments_count': user.comments_count,
            'likes_received': user.likes_received,
            'playlists_count': user.playlists_count,
            'library_count': user.library.count() if hasattr(user, 'library') else 0,
            'is_online': user.is_online,
            'created_at': user.created_at,
        })


class AllSettingsView(APIView):
    """Объединённые настройки пользователя"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {}

        try:
            from .models import UserSettings
            settings = UserSettings.objects.get(user=user)
            from .serializers import UserSettingsSerializer
            data['settings'] = UserSettingsSerializer(settings).data
        except Exception:
            data['settings'] = {}

        try:
            profile = user.profile_settings
            from .serializers import UserProfileSettingsSerializer
            data['profile'] = UserProfileSettingsSerializer(profile).data
        except Exception:
            data['profile'] = {}

        try:
            notif = user.notification_settings
            from .serializers import NotificationSettingsSerializer
            data['notifications'] = NotificationSettingsSerializer(notif).data
        except Exception:
            data['notifications'] = {}

        try:
            privacy = user.privacy_settings
            from .serializers import PrivacySettingsSerializer
            data['privacy'] = PrivacySettingsSerializer(privacy).data
        except Exception:
            data['privacy'] = {}

        return Response(data)

    def put(self, request):
        """Массовое обновление настроек"""
        user = request.user
        data = request.data
        updated = []

        if 'settings' in data:
            try:
                from .models import UserSettings
                from .serializers import UserSettingsSerializer
                obj, _ = UserSettings.objects.get_or_create(user=user)
                s = UserSettingsSerializer(obj, data=data['settings'], partial=True)
                if s.is_valid():
                    s.save()
                    updated.append('settings')
            except Exception:
                pass

        return Response({'updated': updated})


class AvatarUploadView(APIView):
    """Загрузка аватара пользователя"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        avatar = request.FILES.get('avatar')

        if not avatar:
            return Response({'error': 'Файл аватара не загружен'}, status=400)

        # Проверяем тип файла
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar.content_type not in allowed_types:
            return Response({'error': 'Недопустимый тип файла. Разрешены: JPEG, PNG, GIF, WebP'}, status=400)

        # Проверяем размер файла (макс 5MB)
        if avatar.size > 5 * 1024 * 1024:
            return Response({'error': 'Размер файла не должен превышать 5MB'}, status=400)

        # Удаляем старый аватар если есть
        if user.avatar:
            try:
                import os
                if os.path.isfile(user.avatar.path):
                    os.remove(user.avatar.path)
            except Exception:
                pass

        user.avatar = avatar
        user.save(update_fields=['avatar'])

        return Response({
            'message': 'Аватар успешно загружен',
            'avatar_url': user.avatar.url
        })

    def delete(self, request):
        user = request.user
        if user.avatar:
            try:
                import os
                if os.path.isfile(user.avatar.path):
                    os.remove(user.avatar.path)
            except Exception:
                pass
            user.avatar = None
            user.save(update_fields=['avatar'])

        return Response({'message': 'Аватар удалён'})


class UserLibraryViewSet(viewsets.ModelViewSet):
    """CRUD для библиотеки аниме пользователя"""
    serializer_class = UserLibrarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = UserLibrary.objects.filter(
            user=self.request.user
        ).select_related('anime').order_by('-updated_at')
        
        # Фильтр по избранному
        is_favorite = self.request.query_params.get('is_favorite')
        if is_favorite and is_favorite.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(is_favorite=True)
        
        # Фильтр по статусу
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Поиск по названию
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(anime__title_ru__icontains=search) |
                Q(anime__title_en__icontains=search)
            )
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика библиотеки пользователя"""
        qs = UserLibrary.objects.filter(user=request.user)
        from django.db.models import Count, Sum
        
        counts = {s: 0 for s, _ in UserLibrary.STATUS_CHOICES}
        for row in qs.values('status').annotate(n=Count('id')):
            counts[row['status']] = row['n']
        
        # Считаем избранное
        favorites = qs.filter(is_favorite=True).count()
        
        # Считаем просмотренные эпизоды
        episodes_watched = qs.aggregate(total=Sum('episodes_watched'))['total'] or 0
        
        return Response({
            'total': qs.count(),
            'started': counts.get('started', 0),
            'completed': counts.get('completed', 0),
            'on_hold': counts.get('on_hold', 0),
            'dropped': counts.get('dropped', 0),
            'planned': counts.get('planned', 0),
            'favorites': favorites,
            'episodes_watched': episodes_watched,
        })

    @action(detail=False, methods=['get'])
    def check_anime(self, request):
        """Проверить наличие аниме в библиотеке"""
        anime_id = request.query_params.get('anime_id')
        if not anime_id:
            return Response({'error': 'anime_id is required'}, status=400)
        
        try:
            entry = UserLibrary.objects.get(user=request.user, anime_id=anime_id)
            return Response({
                'in_library': True,
                'status': entry.status,
                'current_episode': entry.current_episode,
                'rating': entry.rating,
                'is_favorite': entry.is_favorite,
            })
        except UserLibrary.DoesNotExist:
            return Response({'in_library': False})

    @action(detail=True, methods=['post'])
    def mark_favorite(self, request, pk=None):
        """Переключить флаг is_favorite"""
        entry = self.get_object()
        entry.is_favorite = not entry.is_favorite
        entry.save(update_fields=['is_favorite', 'updated_at'])
        return Response({'is_favorite': entry.is_favorite})

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Обновить текущий эпизод"""
        entry = self.get_object()
        episode = request.data.get('episode')
        if episode is None:
            return Response({'error': 'episode is required'}, status=400)
        entry.update_progress(int(episode))
        return Response(self.get_serializer(entry).data)

class UsersListView(generics.ListAPIView):
    """
    Список пользователей с фильтрацией:
    - ?status=online - только онлайн
    - ?status=offline - только оффлайн
    - ?status=all - все (по умолчанию)
    - ?search=query - поиск по имени
    """
    serializer_class = UserSimpleSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'all')
        search = self.request.query_params.get('search', '').strip()

        queryset = User.objects.all()

        # Фильтр по статусу
        if status_filter == 'online':
            queryset = queryset.filter(is_online=True)
        elif status_filter == 'offline':
            queryset = queryset.filter(is_online=False)
        # all - без фильтра

        # Поиск
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(nickname__icontains=search) |
                Q(display_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Сортировка: сначала онлайн, потом по последней активности
        queryset = queryset.order_by('-is_online', '-last_login')

        # Ограничиваем 50 пользователями
        return queryset.select_related('settings')[:50]

       