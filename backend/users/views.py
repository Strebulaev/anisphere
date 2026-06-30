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
from rest_framework.parsers import MultiPartParser, FormParser
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
    User,
    UserProfileSettings,
    TwoFactorAuth,
    ActiveSession,
    NotificationSettings,
    PrivacySettings,
    UserTheme,
    ChatBackground,
    UserAnalytics,
    EmailLog,
    SecurityLog,
    SupportTicket,
    SupportMessage,
)
from .serializers import (
    UserSerializer,
    UserSimpleSerializer,
    RegisterSerializer,
    LoginSerializer,
    PhoneVerificationSerializer,
    EmailVerificationSerializer,
    GoogleAuthSerializer,
    PasswordResetSerializer,
    ProfileUpdateSerializer,
    UserSessionSerializer,
    UserSettingsSerializer,
    NicknameCheckSerializer,
    TwoFactorSetupSerializer,
    ChangePasswordSerializer,
    ActiveSessionSerializer,
    SupportTicketSerializer,
    SupportTicketListSerializer,
    SupportTicketCreateSerializer,
    SupportMessageSerializer,
)
from core.redis_events import event_publisher


class CurrentUserView(APIView):
    """GET/PUT/PATCH /api/users/me/ � ������� ������������"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/users/me/"""
        user = request.user
        from .serializers import UserSerializer

        data = UserSerializer(user).data

        # Проверяем премиум статус
        is_premium = False
        try:
            sub = user.subscription
            is_premium = sub.is_premium
        except Exception:
            pass

        try:
            profile = user.profile_settings
            data["birth_date"] = (
                str(profile.birth_date)
                if getattr(profile, "birth_date", None)
                else None
            )
            data["status"] = getattr(profile, "status", "online") or "online"
            # Social links доступны всем (функционал бесплатный)
            data["social_links"] = getattr(profile, "social_links", []) or []
        except Exception:
            data["birth_date"] = None
            data["status"] = "online"
            data["social_links"] = []

        # Cover image доступен всем (функционал бесплатный)
        data["cover_image"] = user.cover_image.url if user.cover_image else None
        data["cover_image_url"] = user.cover_image.url if user.cover_image else None

        data["is_premium"] = is_premium

        # Добавляем информацию о подписке
        try:
            from .models import Subscription

            sub = user.subscription
            data["subscription"] = {
                "is_active": sub.is_premium,
                "started_at": sub.started_at.isoformat() if sub.started_at else None,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
                "auto_renew": sub.auto_renew,
            }
        except Exception:
            data["subscription"] = None

        return Response(data)

    def put(self, request):
        return self._update_profile(request)

    def patch(self, request):
        return self._update_profile(request)

    def delete(self, request):
        """DELETE /api/users/me/ - удаление аккаунта"""
        user = request.user

        # Проверяем, не удалён ли уже аккаунт
        if getattr(user, "is_deleted", False):
            return Response({"error": "Аккаунт уже удалён"}, status=400)

        # Проверяем, есть ли поле для soft delete
        if hasattr(user, "deleted_at"):
            from django.utils import timezone

            user.is_deleted = True
            user.deleted_at = timezone.now()
            user.email = (
                f"deleted_{user.id}_{timezone.now().timestamp()}@deleted.anisphere"
            )
            user.save()

            # Отзываем все токены
            from rest_framework_simplejwt.tokens import RefreshToken

            try:
                RefreshToken.for_user(user)
            except:
                pass

            return Response(
                {
                    "message": "Аккаунт удалён. Вы можете восстановить его в течение 7 дней, войдя в аккаунт."
                }
            )
        else:
            # Если нет soft delete - удаляем полностью
            user.delete()
            return Response({"message": "Аккаунт удалён"})

    def _update_profile(self, request):
        user = request.user
        allowed = [
            "display_name",
            "nickname",
            "bio",
            "website",
            "vk_profile",
            "telegram",
            "github",
            "discord",
            "twitter",
            "favorite_genres",
        ]
        errors = {}

        if "nickname" in request.data:
            new_nick = request.data["nickname"]
            if (
                new_nick
                and User.objects.filter(nickname=new_nick).exclude(pk=user.pk).exists()
            ):
                errors["nickname"] = "���� nickname ��� �����"
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        for field in allowed:
            if field in request.data:
                setattr(user, field, request.data[field])

        profile_fields = {}
        if "birth_date" in request.data:
            profile_fields["birth_date"] = request.data["birth_date"] or None
        if "status" in request.data:
            profile_fields["status"] = request.data["status"]

        # Social links - доступно всем пользователям (функционал бесплатный)
        if "social_links" in request.data:
            profile_fields["social_links"] = request.data["social_links"]

        if profile_fields:
            profile, _ = UserProfileSettings.objects.get_or_create(user=user)
            for k, v in profile_fields.items():
                if hasattr(profile, k):
                    setattr(profile, k, v)
            profile.save(update_fields=list(profile_fields.keys()))

        user.save()
        from .serializers import UserSerializer

        data = UserSerializer(user).data
        try:
            p = user.profile_settings
            data["birth_date"] = (
                str(p.birth_date) if getattr(p, "birth_date", None) else None
            )
            data["social_links"] = getattr(p, "social_links", []) or []
            data["status"] = getattr(p, "status", "online") or "online"
        except Exception:
            pass
        return Response(data)


def send_sms_via_textbee(phone_number, message):
    """�������� SMS ����� TextBee API"""
    api_key = "cfba766b-889e-4521-a983-fc8326cd5052"
    url = f"https://api.textbee.dev/sendSMS?apiKey={api_key}&to={phone_number}&from=AniSphere&message={message}"

    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception as e:
        print(f"SMS send error: {e}")
        return False


def send_verification_email(email, code_or_link, is_link=False):
    """�������� email � ����� ������������� ��� �������"""
    if is_link:
        subject = "������������� email ������ - AniSphere"
        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">AniSphere</h1>
                <p style="color: #e8e8e8; margin: 10px 0 0 0;">������������� email ������</p>
            </div>

            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-top: 0;">����� ����������!</h2>
                <p style="color: #666; line-height: 1.6;">��� ���������� ����������� ����������� ��� email �����:</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{code_or_link}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        ����������� email
                    </a>
                </div>

                <p style="color: #999; font-size: 14px; margin-top: 30px;">������ ������������� � ������� 24 �����.</p>
                <p style="color: #999; font-size: 14px;">���� �� �� ���������������� �� AniSphere, ������ ����������� ��� ������.</p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>� 2026 AniSphere. ��� ����� ��������.</p>
            </div>
        </body>
        </html>
        '''
        plain_message = f"��� ������������� email ��������� �� ������: {code_or_link}\n\n������ ������������� � ������� 24 �����."
    else:
        subject = "������������� email ������ - AniSphere"
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">AniSphere</h1>
                <p style="color: #e8e8e8; margin: 10px 0 0 0;">������������� email ������</p>
            </div>

            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-top: 0;">��� �������������</h2>
                <p style="color: #666; line-height: 1.6;">��� ���������� ����������� ������� ���� ��� �� �����:</p>

                <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center;">
                    <span style="font-size: 32px; font-weight: bold; color: #667eea;">{code_or_link}</span>
                </div>

                <p style="color: #999; font-size: 14px; margin-top: 30px;">��� ������������ � ������� 30 �����.</p>
                <p style="color: #999; font-size: 14px;">���� �� �� ����������� ���� ���, ������ ����������� ��� ������.</p>
            </div>

            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>� 2026 AniSphere. ��� ����� ��������.</p>
            </div>
        </body>
        </html>
        """
        plain_message = f"��� ��� �������������: {code_or_link}\n\n��� ������������ � ������� 30 �����."

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
    """����������� ������ ������������"""

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        """���������� email ������������� ����� �������� ������������"""
        user = serializer.save()

        # ���������� ����� ��� �������������
        from django.utils.crypto import get_random_string
        from django.core.cache import cache

        token = get_random_string(64)
        cache.set(
            f"email_confirm_{user.email}",
            {"user_id": user.id, "token": token},
            timeout=86400,
        )  # 24 ����

        # ���������� ������ � ������� �������������
        confirm_url = (
            f"http://anisphere.org/confirm-email?token={token}&email={user.email}"
        )
        send_verification_email(user.email, confirm_url, is_link=True)


class LoginView(APIView):
    """���� � �������"""

    permission_classes = (AllowAny,)

    def post(self, request):
        print(f"?? LoginView - Login attempt for user: {request.data.get('username')}")
        print(f"?? LoginView - Request headers: {dict(request.headers)}")

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Serializer validation already authenticated the user
            user = serializer.validated_data.get("user")
            if user:
                print(
                    f"? LoginView - User authenticated: {user.username} (ID: {user.id})"
                )

                login(request, user)
                user.is_online = True
                user.save()

                refresh = RefreshToken.for_user(user)
                update_last_login(None, user)

                print(f"? LoginView - Tokens generated")
                print(
                    f"?? LoginView - Access token: {str(refresh.access_token)[:50]}..."
                )
                print(f"?? LoginView - Refresh token: {str(refresh)[:50]}...")

                # ��������� payload ������
                access_token = refresh.access_token
                print(
                    f"?? LoginView - Access token payload: user_id={access_token.get('user_id')}, exp={access_token.get('exp')}"
                )

                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    }
                )
        else:
            print(f"? LoginView - Validation failed: {serializer.errors}")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    """�������������� ����� Google"""

    permission_classes = (AllowAny,)

    def get(self, request):
        """�������� OAuth flow - �������������� �� Google"""
        from urllib.parse import urlencode
        import secrets

        state = secrets.token_urlsafe(32)
        request.session["google_oauth_state"] = state
        request.session.save()

        print(f"DEBUG: Generated state: {state}")
        print(f"DEBUG: Session key: {request.session.session_key}")

        redirect_uri = f"{settings.SITE_URL.rstrip('/')}/api/users/google/callback/"
        print(f"DEBUG: Using redirect_uri: {redirect_uri}")

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            print("ERROR: Google OAuth credentials not configured")
            return Response({"error": "Google OAuth �� ��������"}, status=500)

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        )
        print(f"DEBUG: Full Google auth URL: {google_auth_url}")
        return Response({"auth_url": google_auth_url})

    def post(self, request):
        """��������� ID token (��� ��������������� �������)"""
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # ����������� Google ������
                id_token = serializer.validated_data["id_token"]
                idinfo = google.oauth2.id_token.verify_oauth2_token(
                    id_token,
                    google.auth.transport.requests.Request(),
                    settings.GOOGLE_CLIENT_ID,
                )

                google_id = idinfo["sub"]
                email = idinfo["email"]
                name = idinfo.get("name", "")

                # ���� ������������ ��� ������� ������
                user, created = User.objects.get_or_create(
                    google_id=google_id,
                    defaults={
                        "email": email,
                        "username": email.split("@")[0]
                        + str(random.randint(1000, 9999)),
                        "first_name": name.split(" ")[0] if name else "",
                        "last_name": " ".join(name.split(" ")[1:])
                        if name and len(name.split(" ")) > 1
                        else "",
                        "email_verified": True,
                    },
                )

                if not created and user.email != email:
                    user.email = email
                    user.save()

                login(request, user)
                user.is_online = True
                user.save()
                refresh = RefreshToken.for_user(user)
                update_last_login(None, user)

                return Response(
                    {
                        "user": UserSerializer(user).data,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    }
                )

            except Exception as e:
                return Response(
                    {"error": f"������ Google ��������������: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthCallbackView(APIView):
    """Callback ��� ��������� Google OAuth authorization code"""

    permission_classes = (AllowAny,)

    def get(self, request):
        """������������ authorization code �� Google"""
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")

        print(
            f"DEBUG: Callback received - code: {code}, state: {state}, error: {error}"
        )
        print(f"DEBUG: Session key: {request.session.session_key}")
        print(f"DEBUG: Session data: {dict(request.session)}")

        # ��������� ������
        if error:
            return Response({"error": f"Google OAuth error: {error}"}, status=400)

        if not code:
            return Response({"error": "No authorization code received"}, status=400)

        # ��������� �������� state ��� ��������� ���������� (����������� ��� ����������!)
        # TODO: � ���������� �������� state �������� � Redis ��������
        # session_state = request.session.get("google_oauth_state")
        
        # if not session_state:
        #     print(f"ERROR: No session_state found. Session keys: {list(request.session.keys())}")
        #     return Response(
        #         {"error": "Сессия истекла. Пожалуйста, попробуйте войти снова."}, 
        #         status=400
        #     )

        # if not state:
        #     return Response({"error": "Missing state parameter"}, status=400)

        # if state != session_state:
        #     print(f"ERROR: State mismatch. Expected: {session_state[:20]}..., Got: {state[:20]}...")
        #     return Response({"error": "Invalid state parameter"}, status=400)
        
        # del request.session["google_oauth_state"]
        print(f"DEBUG: State validation successful")

        try:
            # ���������� authorization code �� access token
            redirect_uri = f"{settings.SITE_URL.rstrip('/')}/api/users/google/callback/"
            token_data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            print(f"DEBUG: Token exchange request")
            print(f"  client_id: {settings.GOOGLE_CLIENT_ID[:20]}...")
            print(f"  redirect_uri: {redirect_uri}")
            print(f"  code: {code[:20]}...")

            token_response = requests.post(
                "https://oauth2.googleapis.com/token", data=token_data
            )
            print(f"DEBUG: Token response status: {token_response.status_code}")
            if token_response.status_code != 200:
                print(f"DEBUG: Token error response: {token_response.text}")
            token_response.raise_for_status()
            token_json = token_response.json()

            access_token = token_json.get("access_token")
            id_token = token_json.get("id_token")

            if not access_token:
                return Response({"error": "Failed to obtain access token"}, status=400)

            user_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_response.raise_for_status()
            user_info = user_response.json()

            google_id = user_info["id"]
            email = user_info["email"]
            name = user_info.get("name", "")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")

            # Найти или создать пользователя (Google Callback)
            _base_username = email.split("@")[0] + str(random.randint(1000, 9999))
            user, created = User.objects.get_or_create(
                google_id=google_id,
                defaults={
                    "email": email,
                    "username": _base_username,
                    "nickname": _base_username,
                    "display_name": name or _base_username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email_verified": True,
                },
            )
            # Если пользователь уже есть, но нет никнейма - исправляем
            if not created:
                needs_save = False
                if user.email != email:
                    user.email = email
                    needs_save = True
                if not user.nickname:
                    user.nickname = user.username
                    needs_save = True
                if not user.display_name:
                    user.display_name = user.username
                    needs_save = True
                user.first_name = first_name
                user.last_name = last_name
                if needs_save:
                    user.save()

            login(request, user)
            user.is_online = True
            user.save()
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            # ���������� URL ��� ��������� (���������� referer ��� SITE_URL)
            referer = request.META.get("HTTP_REFERER", "")
            if "www.anisphere.org" in referer:
                redirect_url = "https://www.anisphere.org/"
            elif "anisphere.org" in referer:
                redirect_url = "https://anisphere.org/"
            else:
                redirect_url = settings.SITE_URL

            # ���������� HTML ��������, ������� �������� ������ � ������������ �� frontend
            user_data = UserSerializer(user).data
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google OAuth - AniSphere</title>
                <script>
                    // ��������� ������ � localStorage
                    localStorage.setItem('access_token', '{refresh.access_token}');
                    localStorage.setItem('refresh_token', '{refresh}');
                    localStorage.setItem('user', JSON.stringify({json.dumps(user_data)}));

                    // �������������� �� ������� ��������
                    window.location.href = '{redirect_url}';
                </script>
            </head>
            <body>
                <p>Google ����������� �������! ���������������...</p>
            </body>
            </html>
            """

            return HttpResponse(html_content, content_type="text/html")

        except Exception as e:
            print(f"ERROR: Google OAuth callback exception: {str(e)}")
            import traceback

            print(traceback.format_exc())
            return Response(
                {"error": f"Google OAuth callback error: {str(e)}"}, status=500
            )


class PhoneVerificationView(APIView):
    """�������� � �������� SMS ���� ��� ��������"""

    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            action = serializer.validated_data["action"]

            if action == "send":
                # ���������� ���
                code = "".join(random.choices(string.digits, k=6))

                # ��������� ���
                user = request.user
                user.sms_code = code
                user.sms_code_expires = timezone.now() + timedelta(minutes=10)
                user.save()

                # ���������� SMS ����� TextBee
                message = f"��� ��� �������������: {code}"
                if send_sms_via_textbee(str(phone_number), message):
                    return Response({"message": "SMS ��� ���������"})
                else:
                    return Response(
                        {"error": "������ �������� SMS"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            elif action == "verify":
                code = serializer.validated_data["code"]
                user = request.user

                if (
                    user.sms_code == code
                    and user.sms_code_expires
                    and timezone.now() < user.sms_code_expires
                ):
                    user.phone_verified = True
                    user.sms_code = None
                    user.sms_code_expires = None
                    user.save()

                    return Response({"message": "������� �����������"})
                else:
                    return Response(
                        {"error": "�������� ��� �������� ���"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """�������� � �������� email ����"""

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            action = serializer.validated_data["action"]

            if action == "send":
                # ���������� ���
                code = "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=8)
                )

                # ��������� ��� � ������ ��� ��������� ���������
                request.session[f"email_code_{email}"] = {
                    "code": code,
                    "expires": (timezone.now() + timedelta(minutes=30)).isoformat(),
                }

                # ���������� email
                if send_verification_email(email, code):
                    return Response({"message": "��� ��������� �� email"})
                else:
                    return Response(
                        {"error": "������ �������� email"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            elif action == "verify":
                code = serializer.validated_data["code"]
                session_key = f"email_code_{email}"
                session_data = request.session.get(session_key)

                if session_data and timezone.now() < timezone.datetime.fromisoformat(
                    session_data["expires"]
                ):
                    if session_data["code"] == code:
                        # ��������� ������������
                        user = request.user
                        user.email = email
                        user.email_verified = True
                        user.save()

                        # ������� ������
                        del request.session[session_key]

                        return Response({"message": "Email �����������"})
                    else:
                        return Response(
                            {"error": "�������� ���"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        {"error": "��� ����� ��� �� ������"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailConfirmView(APIView):
    """������������� email �� ������"""

    permission_classes = (AllowAny,)

    def get(self, request):
        """������������ email �� ������"""
        token = request.GET.get("token")
        email = request.GET.get("email")

        if not token or not email:
            return Response({"error": "�������� ������ �������������"}, status=400)

        # �������� ������ �� ����
        from django.core.cache import cache

        cache_key = f"email_confirm_{email}"
        confirm_data = cache.get(cache_key)

        if not confirm_data or confirm_data.get("token") != token:
            return Response(
                {"error": "������ ������������� ��������������� ��� �������"},
                status=400,
            )

        try:
            user = User.objects.get(id=confirm_data["user_id"], email=email)
            user.email_verified = True
            user.save()

            # ������� ���
            cache.delete(cache_key)

            # HTML �������� ��������� �������������
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email ����������� - AniSphere</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #28a745; font-size: 24px; margin-bottom: 20px; }
                    .message { color: #666; margin-bottom: 30px; }
                    .button { background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="success">? Email �����������!</div>
                <div class="message">������ �� ������ ���������� ������������ AniSphere</div>
                <a href="http://anisphere.org/login" class="button">����� � �������</a>
            </body>
            </html>
            """

            return HttpResponse(html_content, content_type="text/html")

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)


class LogoutView(APIView):
    """����� �� �������"""

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            user.is_online = False
            user.save()
        logout(request)
        return Response({"message": "����� ��������"})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """������� ������������"""

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.select_related("subscription").all()

    def get_object(self):
        return self.request.user


class UserPublicProfileView(generics.RetrieveAPIView):
    """Public profile view (by ID)"""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    lookup_field = "pk"

    def get_queryset(self):
        return User.objects.select_related("subscription").all()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise generics.NotFound("Пользователь не найден")


class UserProfileByNicknameView(generics.RetrieveAPIView):
    """Профиль пользователя по никнейму - GET /api/users/by-nickname/@kaiden812/"""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return User.objects.select_related("subscription").all()

    def get_object(self):
        nickname = self.kwargs.get("nickname", "").lstrip("@")
        try:
            return User.objects.get(nickname=nickname)
        except User.DoesNotExist:
            # Также пробуем по username
            try:
                return User.objects.get(username=nickname)
            except User.DoesNotExist:
                raise generics.NotFound(f"Пользователь @{nickname} не найден")


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset(request):
    """����� ������"""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            # ���������� ����� ������ � ����������
            new_password = "".join(
                random.choices(string.ascii_letters + string.digits, k=12)
            )
            user.set_password(new_password)
            user.save()

            # ���������� email � ����� �������
            subject = "�������������� ������ - AniSphere"
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">AniSphere</h1>
                    <p style="color: #e8e8e8; margin: 10px 0 0 0;">�������������� ������</p>
                </div>

                <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; margin-top: 0;">��� ����� ������</h2>
                    <p style="color: #666; line-height: 1.6;">��� ������������ ����� ������ ��� ����� ������� ������:</p>

                    <div style="background: #f8f9fa; border: 2px dashed #667eea; border-radius: 8px; padding: 20px; text-align: center;">
                        <span style="font-size: 24px; font-weight: bold; color: #667eea;">{new_password}</span>
                    </div>

                    <p style="color: #666; line-height: 1.6;"><strong>�����:</strong> ����������� �������� ���� ������ ����� ����� � ������� � ���������� �������.</p>
                </div>

                <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                    <p>� 2026 AniSphere. ��� ����� ��������.</p>
                </div>
            </body>
            </html>
            """
            plain_message = f"��� ����� ������: {new_password}\n����������� �������� ��� ����� �����."

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
            )

            return Response({"message": "����� ������ ��������� �� email"})
        except User.DoesNotExist:
            return Response(
                {"error": "������������ � ����� email �� ������"},
                status=status.HTTP_404_NOT_FOUND,
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileUpdateView(generics.UpdateAPIView):
    """���������� ������� ������������"""

    serializer_class = ProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserSessionsView(generics.ListAPIView):
    """�������� �������� ������"""

    serializer_class = UserSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)


class UserSessionDetailView(generics.DestroyAPIView):
    """���������� ���������� ������"""

    serializer_class = UserSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        """��� ���������� ������ ����� ������� � �� Django ������"""
        from django.contrib.sessions.models import Session

        # ������� ������ �� Django
        try:
            Session.objects.filter(session_key=instance.session_key).delete()
        except:
            pass  # ���������� ���� ������ ��� �������

        # ������� ���� ������
        instance.delete()


class UserSettingsView(generics.RetrieveUpdateAPIView):
    """Настройки пользователя"""

    serializer_class = UserSettingsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class OnlineStatusView(APIView):
    """Быстрая проверка статуса онлайн для конкретных пользователей (polling)"""

    permission_classes = [AllowAny]

    def get(self, request):
        user_ids = request.query_params.get("user_ids", "")
        if not user_ids:
            return Response(
                {"error": "user_ids required (comma-separated)"}, status=400
            )

        from core.online_status import online_status

        # Парсим список ID
        ids_list = [int(x.strip()) for x in user_ids.split(",") if x.strip().isdigit()]
        
        # Получаем всех онлайн пользователей из Redis
        online_data = online_status.get_online_users()
        online_ids = set(u.get("user_id") for u in online_data if u.get("user_id"))

        # Возвращаем словарь {user_id: is_online}
        result = {}
        for uid in ids_list:
            result[uid] = uid in online_ids

        return Response(result)


class OnlineUsersView(generics.ListAPIView):
    """Список пользователей онлайн с фильтрацией.

    is_online определяется строго по Redis (TTL 30 мин),
    а НЕ по полю is_online в БД (которое не сбрасывается корректно).
    """

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        from core.online_status import online_status

        # Получаем IDs онлайн-пользователей из Redis
        online_data = online_status.get_online_users()
        online_ids = set(u.get("user_id") for u in online_data if u.get("user_id"))
        online_ids.discard(request.user.id)  # исключаем себя

        if not online_ids:
            return Response({"results": [], "count": 0})

        queryset = User.objects.filter(id__in=online_ids).select_related("settings")

        # Приватность
        queryset = queryset.filter(
            Q(settings__isnull=True) | Q(settings__show_online_status=True)
        )

        # Поиск
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(nickname__icontains=search)
                | Q(display_name__icontains=search)
            )

        # Сортировка
        ordering = request.query_params.get("ordering", "-last_login")
        valid = [
            "username",
            "-username",
            "nickname",
            "-nickname",
            "display_name",
            "-display_name",
            "level",
            "-level",
            "-last_login",
        ]
        queryset = queryset.order_by(ordering if ordering in valid else "-last_login")

        serializer = UserSerializer(queryset, many=True)
        data = serializer.data
        # Проставляем is_online=True явно - они точно онлайн (взяли из Redis)
        for item in data:
            item["is_online"] = True

        return Response({"results": data, "count": len(data)})


class UserSearchView(generics.ListAPIView):
    """����� ������������� ��� �������� �����"""

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # �������� ���� �������������, �������� ��������
        queryset = User.objects.exclude(id=self.request.user.id).select_related(
            "settings"
        )

        # ����� �� username, nickname ��� display_name
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(nickname__icontains=search)
                | Q(display_name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        # ����������: ������� �� ������������� ������, ����� �� ������ �������
        if search:
            # ����� ������� ���������� ��� ������
            queryset = queryset.order_by("-is_online", "-last_login")
        else:
            queryset = queryset.order_by("-is_online", "-last_login")

        return queryset[:50]  # ������������ ��������� 50 ��������������


class NicknameCheckView(APIView):
    """�������� ����������� nickname"""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """GET /users/nickname/check/?nickname=xxx"""
        nickname = request.query_params.get("nickname", "")
        if not nickname:
            return Response(
                {"available": False, "error": "������� �� ������"}, status=400
            )
        from .models import User

        occupied = (
            User.objects.filter(nickname=nickname).exclude(pk=request.user.pk).exists()
        )
        return Response({"available": not occupied, "nickname": nickname})

    def post(self, request):
        serializer = NicknameCheckSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"available": True, "message": "Nickname ��������"})
        return Response(
            {
                "available": False,
                "error": serializer.errors["nickname"][0]
                if "nickname" in serializer.errors
                else "������������ nickname",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class TwoFactorSetupView(APIView):
    """��������� ������������� ��������������"""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            action = serializer.validated_data["action"]

            if action == "enable":
                # ���������, ��� email � ������� ������������
                if not user.email_verified:
                    return Response(
                        {
                            "error": "���������� ����������� email ��� ��������� 2FA",
                            "missing": "email",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not user.phone_verified:
                    return Response(
                        {
                            "error": "���������� ����������� ����� �������� ��� ��������� 2FA",
                            "missing": "phone",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # ������ ��������� 2FA
                secret = pyotp.random_base32()
                user.two_factor_secret = secret
                user.two_factor_enabled = True
                user.save()

                # ���������� QR ��� ��� ����������-���������������
                totp = pyotp.TOTP(secret)
                provisioning_uri = totp.provisioning_uri(
                    name=user.email, issuer_name="AniSphere"
                )

                return Response(
                    {
                        "message": "2FA �������",
                        "secret": secret,
                        "provisioning_uri": provisioning_uri,
                    }
                )

            elif action == "disable":
                user.two_factor_enabled = False
                user.two_factor_secret = None
                user.save()
                return Response({"message": "2FA ��������"})

            elif action == "verify":
                code = serializer.validated_data["code"]
                totp = pyotp.TOTP(user.two_factor_secret)
                if totp.verify(code):
                    return Response({"message": "��� �����������"})
                else:
                    return Response(
                        {"error": "�������� ���"}, status=status.HTTP_400_BAD_REQUEST
                    )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RealtimeUpdatesView(APIView):
    """��������� ���������� � �������� ������� �� Redis"""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """�������� �������� ����������"""
        limit = int(request.query_params.get("limit", 50))
        events = event_publisher.get_recent_events(limit)
        return Response({"events": events})


# ������� ��� ��������������� �������� �������� � ������������ ������
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from .models import (
    UserSettings,
    UserSession,
    UserProfileSettings,
    TwoFactorAuth,
    NotificationSettings,
    PrivacySettings,
    UserAnalytics,
)


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """������������� ������� ��������� ��� ������ ������������"""
    if created:
        # ������� ��� ����������� ���������
        UserSettings.objects.create(user=instance)
        UserProfileSettings.objects.create(user=instance)
        TwoFactorAuth.objects.create(user=instance)
        NotificationSettings.objects.create(user=instance)
        PrivacySettings.objects.create(user=instance)
        UserAnalytics.objects.create(user=instance)


@receiver(post_save, sender=Session)
def create_user_session(sender, instance, created, **kwargs):
    """����������� �������� ������ �������������"""
    if created:
        try:
            session_data = instance.get_decoded()
            user_id = session_data.get("_auth_user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                # �������� ���������� � ���������� �� User-Agent
                from django.http import HttpRequest

                # ������� ��������� request ��� �������� User-Agent
                user_agent = getattr(instance, "user_agent", "Unknown")

                # ���������� ��� ���������� �� ������ User-Agent
                device_info = "Unknown Device"
                if (
                    "Mobile" in user_agent
                    or "Android" in user_agent
                    or "iPhone" in user_agent
                ):
                    device_info = "Mobile Device"
                elif "Windows" in user_agent:
                    device_info = "Windows PC"
                elif "Mac" in user_agent:
                    device_info = "Mac Computer"
                elif "Linux" in user_agent:
                    device_info = "Linux Computer"
                else:
                    device_info = "Web Browser"

                UserSession.objects.get_or_create(
                    user=user,
                    session_key=instance.session_key,
                    defaults={
                        "device_info": device_info,
                        "user_agent": user_agent[:200],  # ������������ �����
                    },
                )
        except Exception as e:
            # ���������� ������ ��� �������� ������
            pass


@receiver(post_delete, sender=Session)
def cleanup_user_sessions(sender, instance, **kwargs):
    """������� ������ � ������� ��� �� ����������"""
    UserSession.objects.filter(session_key=instance.session_key).delete()


@receiver(user_logged_out)
def set_user_offline(sender, user, request, **kwargs):
    if user:
        """������������� ������ ������� ��� ������ ������������"""
        user.is_online = False
        user.save(update_fields=["is_online"])
        # ��������� ������� ������������ �������
        from core.redis_events import publish_user_offline

        publish_user_offline(user.id, user.username)


# ����� ViewSets ��� ����������� ��������
from rest_framework import viewsets
from .models import (
    UserProfileSettings,
    TwoFactorAuth,
    ActiveSession,
    NotificationSettings,
    PrivacySettings,
    UserTheme,
    ChatBackground,
    UserAnalytics,
)
from .serializers import (
    UserProfileSettingsSerializer,
    TwoFactorAuthSerializer,
    ActiveSessionSerializer,
    NotificationSettingsSerializer,
    PrivacySettingsSerializer,
    UserThemeSerializer,
    ChatBackgroundSerializer,
    UserAnalyticsSerializer,
)


class UserProfileSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet для настроек профиля пользователя"""

    serializer_class = UserProfileSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfileSettings.objects.filter(user=self.request.user)

    def get_object(self):
        """Возвращаем единственные настройки пользователя или создаём их"""
        settings, created = UserProfileSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

    def update(self, request, *args, **kwargs):
        """Кастомный update с проверкой премиума для цветных никнеймов"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Проверяем премиум для полей цвета никнейма
        premium_fields = ['nickname_color', 'nickname_gradient_start', 'nickname_gradient_end', 'nickname_glow_enabled', 'nickname_glow_color', 'nickname_glow_intensity']
        changed_premium_fields = [f for f in premium_fields if f in request.data]
        
        if changed_premium_fields:
            if not instance.is_premium:
                return Response(
                    {"error": "Изменение цвета никнейма доступно только для премиум пользователей"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class TwoFactorAuthViewSet(viewsets.ViewSet):
    """ViewSet ��� ������������� ��������������"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def status(self, request):
        """�������� ������ 2FA"""
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
        serializer = TwoFactorAuthSerializer(two_factor)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def enable(self, request):
        """������ ������� ��������� 2FA"""
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)

        if two_factor.is_enabled:
            return Response({"error": "2FA ��� ��������"}, status=400)

        # ��������� ������������� email
        if not request.user.email_verified:
            return Response(
                {
                    "error": "���������� ����������� email ��� ��������� 2FA",
                    "missing": "email",
                },
                status=400,
            )

        # ��������� ������� ���� ��� ���
        if not two_factor.secret_key:
            two_factor.generate_secret()
            two_factor.generate_backup_codes()
            two_factor.save()

        # ��������� QR-����
        totp = pyotp.TOTP(two_factor.secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email, issuer_name="AniSphere"
        )

        # �������� QR-���� � base64
        qr = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # ������ � ���� ������������
        SecurityLog.objects.create(
            user=request.user,
            action="2fa_setup_started",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {
                "secret": two_factor.secret_key,
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "backup_codes_count": len(two_factor.backup_codes),
                "message": "������������ QR-��� � ���������� ��������������� � ������� ��� ��� �������������",
            }
        )

    @action(detail=False, methods=["post"])
    def verify(self, request):
        """����������� � ��������� 2FA"""
        code = request.data.get("code")
        if not code:
            return Response({"error": "��� ����������"}, status=400)

        # ��������� ������ ����
        if not code.isdigit() or len(code) != 6:
            return Response({"error": "��� ������ �������� �� 6 ����"}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)

        if two_factor.verify_code(code):
            two_factor.is_enabled = True
            two_factor.save()

            # ������ � ���� ������������
            SecurityLog.objects.create(
                user=request.user,
                action="2fa_enabled",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                additional_data={
                    "method": "totp",
                    "require_on_new_device": two_factor.require_on_new_device,
                },
            )

            # ��������� ������� � Redis
            from core.redis_events import publish_settings_update

            publish_settings_update(request.user.id, ["two_factor_enabled"])

            return Response(
                {
                    "success": True,
                    "message": "������������� �������������� ������� ��������",
                }
            )

        return Response({"error": "�������� ���. ���������� ��� ���."}, status=400)

    @action(detail=False, methods=["post"])
    def verify_backup_code(self, request):
        """����������� ���������� ����"""
        code = request.data.get("code")
        if not code:
            return Response({"error": "��� ����������"}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)

        if not two_factor.is_enabled:
            return Response({"error": "2FA �� ��������"}, status=400)

        # ��������� ��������� ���
        if code in two_factor.backup_codes:
            two_factor.backup_codes.remove(code)
            two_factor.save()

            # ������ � ���� ������������
            SecurityLog.objects.create(
                user=request.user,
                action="2fa_backup_code_used",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                additional_data={"codes_remaining": len(two_factor.backup_codes)},
            )

            return Response(
                {
                    "success": True,
                    "message": "��� �����������. ����������� ������������� ����� ��������� ����.",
                    "codes_remaining": len(two_factor.backup_codes),
                }
            )

        return Response({"error": "�������� ��������� ���"}, status=400)

    @action(detail=False, methods=["get"])
    def backup_codes(self, request):
        """�������� ��������� ����"""
        two_factor = TwoFactorAuth.objects.get(user=request.user)
        if not two_factor.is_enabled:
            return Response({"error": "2FA �� ��������"}, status=400)

        return Response(
            {"codes": two_factor.backup_codes, "count": len(two_factor.backup_codes)}
        )

    @action(detail=False, methods=["post"])
    def regenerate_backup_codes(self, request):
        """������������� ����� ��������� ����"""
        password = request.data.get("password")
        if not password:
            return Response(
                {"error": "������ ���������� ��� ��������� ����� �����"}, status=400
            )

        # �������� ������
        if not request.user.check_password(password):
            return Response({"error": "�������� ������"}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)
        two_factor.generate_backup_codes()
        two_factor.save()

        # ������ � ���� ������������
        SecurityLog.objects.create(
            user=request.user,
            action="2fa_backup_codes_regenerated",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            additional_data={"codes_count": len(two_factor.backup_codes)},
        )

        return Response(
            {
                "success": True,
                "codes": two_factor.backup_codes,
                "message": "����� ��������� ���� �������������. ��������� �� � ���������� �����.",
            }
        )

    @action(detail=False, methods=["post"])
    def disable(self, request):
        """��������� 2FA"""
        password = request.data.get("password")
        if not password:
            return Response({"error": "������ ����������"}, status=400)

        # �������� ������
        if not request.user.check_password(password):
            return Response({"error": "�������� ������"}, status=400)

        two_factor = TwoFactorAuth.objects.get(user=request.user)
        two_factor.is_enabled = False

        # �� ������� ��������� ���� � ��������� ���� - ��� ����� ������������ ��� ��������� ���������

        two_factor.save()

        # ������ � ���� ������������
        SecurityLog.objects.create(
            user=request.user,
            action="2fa_disabled",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        # ��������� ������� � Redis
        from core.redis_events import publish_settings_update

        publish_settings_update(request.user.id, ["two_factor_disabled"])

        return Response(
            {"success": True, "message": "������������� �������������� ���������"}
        )

    @action(detail=False, methods=["post"])
    def update_settings(self, request):
        """�������� ��������� 2FA"""
        data = request.data
        two_factor = TwoFactorAuth.objects.get(user=request.user)

        # ��������� ���������
        if "require_on_new_device" in data:
            two_factor.require_on_new_device = data["require_on_new_device"]

        if "remember_device_days" in data:
            days = data["remember_device_days"]
            if not isinstance(days, int) or days < 1 or days > 365:
                return Response(
                    {"error": "���������� ���� ������ ���� �� 1 �� 365"}, status=400
                )
            two_factor.remember_device_days = days

        if "email_enabled" in data:
            two_factor.email_enabled = data["email_enabled"]

        if "phone_number" in data:
            phone = data["phone_number"]
            if phone and not request.user.phone_verified:
                return Response(
                    {
                        "error": "���������� ����������� ����� �������� ��� ������������� SMS 2FA"
                    },
                    status=400,
                )
            two_factor.phone_number = phone

        two_factor.save()

        # ������ � ���� ������������
        SecurityLog.objects.create(
            user=request.user,
            action="2fa_settings_updated",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            additional_data={
                "require_on_new_device": two_factor.require_on_new_device,
                "remember_device_days": two_factor.remember_device_days,
                "email_enabled": two_factor.email_enabled,
                "phone_enabled": bool(two_factor.phone_number),
            },
        )

        # ��������� ������� � Redis
        from core.redis_events import publish_settings_update

        publish_settings_update(request.user.id, ["two_factor_settings"])

        return Response({"success": True, "message": "��������� 2FA ���������"})

    @action(detail=False, methods=["get"])
    def security_log(self, request):
        """�������� ��� ������������ 2FA"""
        logs = SecurityLog.objects.filter(
            user=request.user, action__startswith="2fa"
        ).order_by("-created_at")[:20]

        log_data = []
        for log in logs:
            log_data.append(
                {
                    "action": log.action,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent[:100] if log.user_agent else "",
                    "created_at": log.created_at.isoformat(),
                    "additional_data": log.additional_data,
                }
            )

        return Response({"logs": log_data})

    def get_client_ip(self, request):
        """�������� IP ����� �������"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class SessionViewSet(viewsets.ViewSet):
    """ViewSet ��� ���������� ��������� ��������"""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """�������� ��� �������� ������ ������������"""
        # �������� ��� ������ Django ��� ������������
        sessions = ActiveSession.objects.filter(user=request.user)
        serializer = ActiveSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def terminate(self, request):
        """��������� ���������� ������"""
        session_key = request.data.get("session_key")

        if not session_key:
            return Response({"error": "session_key ����������"}, status=400)

        # ������ ��������� ������� ������ ����� ���� �����
        if session_key == request.session.session_key:
            return Response({"error": "������ ��������� ������� ������"}, status=400)

        try:
            session = Session.objects.get(session_key=session_key)

            # ���������, ��� ������ ����������� ������������
            session_data = session.get_decoded()
            if (
                "_auth_user_id" not in session_data
                or str(request.user.id) != session_data["_auth_user_id"]
            ):
                return Response({"error": "������ ��������"}, status=403)

            # ������� ������
            session.delete()

            # ������� ������ ActiveSession
            ActiveSession.objects.filter(session_key=session_key).delete()

            return Response({"success": True})

        except Session.DoesNotExist:
            return Response({"error": "������ �� �������"}, status=404)

    @action(detail=False, methods=["post"])
    def terminate_all_others(self, request):
        """��������� ��� ������ ������"""
        current_session_key = request.session.session_key

        # ������� ��� ������ ������������ ����� �������
        user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        sessions_to_delete = []

        for session in user_sessions:
            session_data = session.get_decoded()
            if (
                "_auth_user_id" in session_data
                and str(request.user.id) == session_data["_auth_user_id"]
                and session.session_key != current_session_key
            ):
                sessions_to_delete.append(session.session_key)

        # ������� ������
        Session.objects.filter(session_key__in=sessions_to_delete).delete()
        ActiveSession.objects.filter(session_key__in=sessions_to_delete).delete()

        return Response({"success": True, "terminated_count": len(sessions_to_delete)})


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet ��� �������� �����������"""

    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationSettings.objects.filter(user=self.request.user)

    def get_object(self):
        """���������� ��������� ����������� ������������ ��� ������� ��"""
        settings, created = NotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class PrivacySettingsViewSet(viewsets.ModelViewSet):
    """ViewSet ��� �������� �����������"""

    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrivacySettings.objects.filter(user=self.request.user)

    def get_object(self):
        """���������� ��������� ����������� ������������ ��� ������� ��"""
        settings, created = PrivacySettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

    @action(detail=False, methods=["get"])
    def check_visibility(self, request):
        """���������, ��� ����� ������ ������ ������������"""
        target_user_id = request.query_params.get("user_id")

        if not target_user_id:
            return Response({"error": "user_id ����������"}, status=400)

        try:
            target_user = User.objects.get(id=target_user_id)

            # ���������, �������� �� ������������ ����������
            from social.models import PrivateChat
            from django.db.models import Q

            is_contact = PrivateChat.objects.filter(
                (Q(user1=request.user) & Q(user2=target_user))
                | (Q(user1=target_user) & Q(user2=request.user))
            ).exists()

            try:
                privacy_settings = target_user.privacy_settings
                visibility = {
                    "phone": self.check_field_visibility(
                        "who_can_see_phone", privacy_settings, is_contact
                    ),
                    "email": self.check_field_visibility(
                        "who_can_see_email", privacy_settings, is_contact
                    ),
                    "last_seen": self.check_field_visibility(
                        "who_can_see_last_seen", privacy_settings, is_contact
                    ),
                    "profile_photo": self.check_field_visibility(
                        "who_can_see_profile_photo", privacy_settings, is_contact
                    ),
                    "can_call": self.check_field_visibility(
                        "who_can_call", privacy_settings, is_contact
                    ),
                    "is_blocked": privacy_settings.blocked_users.filter(
                        id=request.user.id
                    ).exists(),
                }
            except Exception:
                # ���� ��������� ����������� �� ����������, ���������� �������� �� ���������
                visibility = {
                    "phone": True,  # contacts
                    "email": True,  # contacts
                    "last_seen": True,  # everyone
                    "profile_photo": True,  # everyone
                    "can_call": True,  # everyone
                    "is_blocked": False,
                }

            return Response(visibility)

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)

    def check_field_visibility(self, field_name, privacy_settings, is_contact):
        """�������� ��������� ����"""
        value = getattr(privacy_settings, field_name)

        if value == "everyone":
            return True
        elif value == "contacts":
            return is_contact
        else:  # nobody
            return False

    @action(detail=False, methods=["get"])
    def blocked_users(self, request):
        """�������� ������ ��������������� �������������"""
        try:
            privacy_settings = request.user.privacy_settings
            blocked_users = privacy_settings.blocked_users.all()
        except Exception:
            # ���� ��������� �� ����������, ���������� ������ ������
            blocked_users = []

        from .serializers import (
            UserSimpleSerializer,
        )  # �������� ������� ������������ ��� �������������

        serializer = UserSimpleSerializer(blocked_users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def block_user(self, request):
        """������������� ������������"""
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id ����������"}, status=400)

        try:
            user_to_block = User.objects.get(id=user_id)

            try:
                privacy_settings = request.user.privacy_settings

                if privacy_settings.blocked_users.filter(id=user_id).exists():
                    return Response(
                        {"error": "������������ ��� ������������"}, status=400
                    )

                privacy_settings.blocked_users.add(user_to_block)
            except Exception:
                # ���� ��������� �� ����������, ������� ��
                from .models import PrivacySettings

                privacy_settings, created = PrivacySettings.objects.get_or_create(
                    user=request.user
                )
                privacy_settings.blocked_users.add(user_to_block)

            # ������� �� ��������� (�������� ������������ �������� ������� ����, ������� ��� ������ ����)
            pass

            # ������� �� ����� ����� (������)
            from social.models import PrivateChat

            PrivateChat.objects.filter(
                (Q(user1=request.user) & Q(user2=user_to_block))
                | (Q(user1=user_to_block) & Q(user2=request.user))
            ).delete()

            return Response({"success": True})

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)

    @action(detail=False, methods=["post"])
    def unblock_user(self, request):
        """�������������� ������������"""
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id ����������"}, status=400)

        try:
            user_to_unblock = User.objects.get(id=user_id)

            try:
                privacy_settings = request.user.privacy_settings

                if not privacy_settings.blocked_users.filter(id=user_id).exists():
                    return Response(
                        {"error": "������������ �� ������������"}, status=400
                    )

                privacy_settings.blocked_users.remove(user_to_unblock)
            except Exception:
                # ���� ��������� �� ����������, ������������ �� ����� ���� ������������
                return Response({"error": "������������ �� ������������"}, status=400)

            return Response({"success": True})

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)


class UserThemeViewSet(viewsets.ModelViewSet):
    """ViewSet ��� ���������������� ���"""

    serializer_class = UserThemeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTheme.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatBackgroundViewSet(viewsets.ModelViewSet):
    """ViewSet ��� ����� �����"""

    serializer_class = ChatBackgroundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatBackground.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet ��� ��������� ������������"""

    serializer_class = UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAnalytics.objects.filter(user=self.request.user)


# ─── Admin permission ────────────────────────────────────────────────────────
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Проверка администратора (по is_staff или никнейму)"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.username == "kaiden812"
        )


class AdminDashboardView(APIView):
    """Дашборд админа: статистика, последние регистрации, активность"""

    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from notifications.models import Notification, Complaint

        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        # Последние регистрации
        recent_users = User.objects.order_by("-date_joined")[:20]
        recent_users_data = []
        for u in recent_users:
            recent_users_data.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "email": u.email,
                    "date_joined": u.date_joined.isoformat() if u.date_joined else None,
                    "is_online": u.is_online,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                }
            )

        # Активные сейчас
        online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)
        online_users_data = []
        for u in online_users:
            online_users_data.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "is_online": u.is_online,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                }
            )

        # Необработанные жалобы
        pending_complaints = Complaint.objects.filter(status="pending").count()

        return Response(
            {
                "stats": {
                    "total_users": User.objects.count(),
                    "online_now": online_users.count(),
                    "registered_today": User.objects.filter(
                        date_joined__gte=today
                    ).count(),
                    "registered_this_week": User.objects.filter(
                        date_joined__gte=week_ago
                    ).count(),
                    "pending_complaints": pending_complaints,
                },
                "recent_registrations": recent_users_data,
                "online_users": online_users_data,
            }
        )


class AdminComplaintsView(APIView):
    """Админ: список всех жалоб"""

    permission_classes = [IsAdminUser]

    def get(self, request):
        from notifications.models import Complaint
        from notifications.serializers import ComplaintSerializer
        from django.contrib.contenttypes.models import ContentType

        status_filter = request.query_params.get("status", "pending")
        qs = Complaint.objects.all().order_by("-created_at")
        if status_filter != "all":
            qs = qs.filter(status=status_filter)
        qs = qs[:100]

        data = []
        for c in qs:
            # Получаем информацию о контенте
            target_info = None
            target_user = None
            try:
                if c.content_object:
                    obj = c.content_object
                    if hasattr(obj, "author"):
                        target_user = obj.author
                        target_info = f"Автор: @{obj.author.username}"
                    elif hasattr(obj, "user"):
                        target_user = obj.user
                        target_info = f"Пользователь: @{obj.user.username}"
                    elif hasattr(obj, "username"):
                        target_info = f"Пользователь: @{obj.username}"
            except Exception:
                pass

            data.append(
                {
                    "id": c.id,
                    "complainant": {
                        "id": c.complainant.id,
                        "username": c.complainant.username,
                        "nickname": c.complainant.nickname,
                    },
                    "target_info": target_info,
                    "target_user": {
                        "id": target_user.id,
                        "username": target_user.username,
                    }
                    if target_user
                    else None,
                    "complaint_type": c.complaint_type,
                    "reason": c.reason,
                    "description": c.description,
                    "status": c.status,
                    "created_at": c.created_at.isoformat(),
                    "object_id": c.object_id,
                    "content_type_id": c.content_type_id,
                }
            )
        return Response({"results": data, "count": len(data)})

    def patch(self, request, complaint_id):
        """Update complaint status"""
        from notifications.models import Complaint

        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({"error": "Жалоба не найдена"}, status=404)
        new_status = request.data.get("status")
        if new_status in dict(Complaint.STATUS_CHOICES):
            complaint.status = new_status
            if new_status == "resolved":
                from django.utils import timezone

                complaint.resolved_at = timezone.now()
            complaint.save()
        return Response({"success": True, "status": complaint.status})


class AdminDeletePostView(APIView):
    """Админ: удаление поста"""

    permission_classes = [IsAdminUser]

    def delete(self, request, post_id):
        from social.models import Post

        try:
            post = Post.objects.get(id=post_id)
            post.delete()
            return Response({"success": True, "message": f"Пост #{post_id} удалён"})
        except Post.DoesNotExist:
            return Response({"error": "Пост не найден"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class HeartbeatView(APIView):
    """
    POST /api/users/heartbeat/
    Фронтенд шлёт этот эндпойнт каждые 30 секунд пока вкладка активна.
    Если вкладка не активна (пользователь отошёл) - шлёт с is_active=false
    Сбрасывает TTL ключа user_online:{id} в Redis:
    - is_active=true: 2 минуты
    - is_active=false: 5 минут
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from core.online_status import online_status, publish_user_online_event

        user = request.user

        # Получаем статус активности вкладки от фронтенда
        is_active = request.data.get("is_active", True)

        online_status.set_online(
            user.id,
            user.username,
            extra_data={"display_name": user.display_name or user.username},
            is_active=bool(is_active),
        )
        publish_user_online_event(user.id, user.username)
        return Response({"ok": True, "is_active": is_active})


# Импорт UserLibraryViewSet из отдельного модуля
from .views_library import UserLibraryViewSet


class AvatarUploadView(APIView):
    """Загрузка аватара пользователя"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        if "avatar" not in request.FILES:
            return Response(
                {"error": "Файл аватара не предоставлен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        avatar_file = request.FILES["avatar"]

        # Проверяем размер файла (максимум 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response(
                {"error": "Размер файла не должен превышать 5MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Проверяем тип файла
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if avatar_file.content_type not in allowed_types:
            return Response(
                {"error": "Допустимы только изображения (JPEG, PNG, GIF, WebP)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Удаляем старый аватар если есть
        if user.avatar:
            user.avatar.delete(save=False)

        # Сохраняем новый аватар
        user.avatar = avatar_file
        user.save(update_fields=["avatar"])

        return Response(
            {"success": True, "avatar_url": user.avatar.url if user.avatar else None}
        )

    def delete(self, request):
        """Удаление аватара"""
        user = request.user

        if user.avatar:
            user.avatar.delete(save=True)
            return Response({"success": True, "message": "Аватар удалён"})

        return Response({"error": "Аватар не найден"}, status=status.HTTP_404_NOT_FOUND)


class AvatarFromScreenshotView(APIView):
    """Установка аватара из скриншота Kodik с crop/position"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        image_data = request.data.get("image_data")
        crop_x = float(request.data.get("crop_x", 50))  # центр crop в процентах
        crop_y = float(request.data.get("crop_y", 50))
        zoom = float(request.data.get("zoom", 1.0))  # 1.0 = 100%

        if not image_data:
            return Response(
                {"error": "Данные изображения не предоставлены"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import base64
            from io import BytesIO
            from PIL import Image
            from django.core.files.base import ContentFile
            from django.utils import timezone

            # Декодируем base64
            if "," in image_data:
                _, data = image_data.split(",", 1)
            else:
                data = image_data

            image_bytes = base64.b64decode(data)
            img = Image.open(BytesIO(image_bytes))

            # Конвертируем в RGB если нужно
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Применяем crop с учётом position и zoom
            if zoom != 1.0 or crop_x != 50 or crop_y != 50:
                width, height = img.size
                # Размер crop-области (меньше при zoom > 1)
                crop_scale = 1.0 / max(zoom, 1.0)
                crop_w = int(width * crop_scale)
                crop_h = int(height * crop_scale)

                # Центр crop-областии
                center_x = int(width * crop_x / 100)
                center_y = int(height * crop_y / 100)

                left = max(0, center_x - crop_w // 2)
                top = max(0, center_y - crop_h // 2)
                right = min(width, left + crop_w)
                bottom = min(height, top + crop_h)

                # Корректируем если вышли за границы
                if right - left < crop_w:
                    left = max(0, right - crop_w)
                if bottom - top < crop_h:
                    top = max(0, bottom - crop_h)

                img = img.crop((left, top, right, bottom))

            # Ресайз до разумного размера для аватара (макс 512x512)
            img.thumbnail((512, 512), Image.LANCZOS)

            # Сохраняем в буфер
            output = BytesIO()
            img.save(output, format="JPEG", quality=90)
            output.seek(0)

            # Создаем файл
            filename = f"avatar_{user.id}_{timezone.now().timestamp()}.jpg"
            avatar_file = ContentFile(output.read(), name=filename)

            # Удаляем старый аватар если есть
            if user.avatar:
                user.avatar.delete(save=False)

            # Сохраняем новый аватар
            user.avatar = avatar_file
            user.save(update_fields=["avatar"])

            return Response(
                {"success": True, "avatar_url": user.avatar.url if user.avatar else None}
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Ошибка установки аватара: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CoverFromScreenshotView(APIView):
    """Установка обложки профиля из скриншота Kodik с crop/position"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        image_data = request.data.get("image_data")
        crop_x = float(request.data.get("crop_x", 50))
        crop_y = float(request.data.get("crop_y", 50))

        if not image_data:
            return Response(
                {"error": "Данные изображения не предоставлены"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import base64
            from io import BytesIO
            from PIL import Image
            from django.core.files.base import ContentFile
            from django.utils import timezone

            # Декодируем base64
            if "," in image_data:
                _, data = image_data.split(",", 1)
            else:
                data = image_data

            image_bytes = base64.b64decode(data)
            img = Image.open(BytesIO(image_bytes))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Фронтенд (ImageCropModal) уже сделал точный crop до 1920x600.
            # Не применяем повторный crop/resize - сохраняем как есть,
            # чтобы избежать двойного сжатия и искажения.
            # Если изображение сильно больше 1920x600 - делаем gentle downscale
            # с сохранением соотношения сторон, без обрезки.
            max_w, max_h = 1920, 600
            if img.width > max_w or img.height > max_h:
                # Сохраняем aspect ratio, уменьшаем до вписывания в max_w x max_h
                img.thumbnail((max_w, max_h), Image.LANCZOS)

            # Сохраняем
            output = BytesIO()
            img.save(output, format="JPEG", quality=92, optimize=True)
            output.seek(0)

            filename = f"cover_{user.id}_{timezone.now().timestamp()}.jpg"
            cover_file = ContentFile(output.read(), name=filename)

            # Удаляем старую обложку
            if user.cover_image:
                user.cover_image.delete(save=False)

            user.cover_image = cover_file
            # Обновляем позицию обложки
            user.cover_position_x = crop_x
            user.cover_position_y = crop_y
            user.save(update_fields=["cover_image", "cover_position_x", "cover_position_y"])

            return Response(
                {
                    "success": True,
                    "cover_image_url": user.cover_image.url if user.cover_image else None,
                    "cover_position_x": user.cover_position_x,
                    "cover_position_y": user.cover_position_y,
                }
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Ошибка установки обложки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChangePasswordView(APIView):
    """Смена пароля пользователя"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"error": "Необходимы current_password и new_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"error": "Неверный текущий пароль"}, status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {"error": "Новый пароль должен содержать минимум 8 символов"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({"success": True, "message": "Пароль успешно изменён"})


class TwoFactorAuthViewSet(viewsets.ViewSet):
    """ViewSet для двухфакторной аутентификации"""

    permission_classes = [IsAuthenticated]

    def status(self, request):
        user = request.user
        return Response(
            {
                "enabled": user.two_factor_enabled
                if hasattr(user, "two_factor_enabled")
                else False,
                "verified": True,
            }
        )

    def enable(self, request):
        return Response({"success": True, "message": "2FA включён"})

    def verify(self, request):
        return Response({"success": True})

    def verify_backup_code(self, request):
        return Response({"success": True})

    def backup_codes(self, request):
        return Response({"codes": []})

    def regenerate_backup_codes(self, request):
        return Response({"codes": []})

    def disable(self, request):
        user = request.user
        if hasattr(user, "two_factor_enabled"):
            user.two_factor_enabled = False
            user.save()
        return Response({"success": True})

    def update_settings(self, request):
        return Response({"success": True})

    def security_log(self, request):
        return Response({"logs": []})


class SessionViewSet(viewsets.ViewSet):
    """ViewSet для управления сессиями"""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response({"sessions": []})

    def terminate(self, request):
        return Response({"success": True})

    def terminate_all_others(self, request):
        return Response({"success": True})


class AccountDeletionView(APIView):
    """Удаление аккаунта"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        password = request.data.get("password")

        if not password or not user.check_password(password):
            return Response(
                {"error": "Неверный пароль"}, status=status.HTTP_400_BAD_REQUEST
            )

        user.delete()
        return Response({"success": True, "message": "Аккаунт удалён"})


class ThemeSettingsView(APIView):
    """Настройки темы"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"theme": "dark"})

    def post(self, request):
        return Response({"success": True})


class ChatBackgroundSettingsView(APIView):
    """Настройки фона чатов"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"background": None})

    def post(self, request):
        return Response({"success": True})


class FontSettingsView(APIView):
    """Настройки шрифтов"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"font": "default", "size": 14})

    def post(self, request):
        return Response({"success": True})


class StorageUsageView(APIView):
    """Использование памяти"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "used": 0,
                "total": 100 * 1024 * 1024,  # 100MB
                "percentage": 0,
            }
        )


class SyncSettingsView(APIView):
    """Настройки синхронизации"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"sync_enabled": True})

    def post(self, request):
        return Response({"success": True})


class ExportDataView(APIView):
    """Экспорт данных пользователя"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Экспорт запущен"})

    def post(self, request):
        return Response({"success": True, "message": "Экспорт данных запущен"})


class ClearCacheView(APIView):
    """Очистка кэша"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"success": True, "message": "Кэш очищен"})


class RealtimeUpdatesView(APIView):
    """Обновления в реальном времени"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"updates": []})


class HeadersDebugView(APIView):
    """Отладка заголовков"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        headers = {k: v for k, v in request.META.items() if k.startswith("HTTP_")}
        return Response({"headers": headers})


class AuthDebugView(APIView):
    """Отладка аутентификации"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "user": request.user.username,
                "authenticated": True,
                "is_staff": request.user.is_staff,
                "is_superuser": request.user.is_superuser,
            }
        )


class UserFeedView(APIView):
    """Лента пользователя"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        return Response({"posts": []})


class UserStatsView(APIView):
    """Статистика пользователя"""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            # Пробуем найти по ID
            try:
                user = User.objects.get(pk=int(pk))
            except (ValueError, User.DoesNotExist):
                # Пробуем найти по username
                user = User.objects.get(username=str(pk))
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Безопасное получение значений с fallback
        try:
            followers_count = user.followers_count
        except:
            followers_count = 0

        try:
            following_count = user.following_count
        except:
            following_count = 0

        try:
            level = user.level
        except:
            level = 1

        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "display_name": user.display_name or user.username,
                "posts_count": 0,
                "followers_count": followers_count,
                "following_count": following_count,
                "level": level,
            }
        )


class AllSettingsView(APIView):
    """Объединенные настройки"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "theme": "dark",
                "notifications": True,
                "privacy": "public",
            }
        )

    def put(self, request):
        return Response({"success": True})


class UsersListView(APIView):
    """Список пользователей с фильтрацией по онлайн статусу"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.online_status import online_status
        from django.db.models import Q

        # Получаем фильтр из query params (поддерживаем и status, и tab)
        tab = request.query_params.get("tab") or request.query_params.get(
            "status", "all"
        )
        search = request.query_params.get("search", "").strip()

        # Пагинация
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 24))

        # Получаем всех онлайн пользователей из Redis
        online_users_data = online_status.get_online_users()
        online_ids = set(
            u["user_id"]
            for u in online_users_data
            if isinstance(u, dict) and "user_id" in u
        )

        # Определяем базовый QuerySet в зависимости от фильтра
        if tab == "online":
            # Только онлайн
            users_qs = (
                User.objects.filter(id__in=list(online_ids))
                if online_ids
                else User.objects.none()
            )
        elif tab == "offline":
            # Только офлайн
            users_qs = (
                User.objects.exclude(id__in=list(online_ids))
                if online_ids
                else User.objects.all()
            )
        else:
            # all - все пользователи
            users_qs = User.objects.all().order_by("-last_login")

        # Поиск
        if search:
            users_qs = users_qs.filter(
                Q(username__icontains=search)
                | Q(nickname__icontains=search)
                | Q(display_name__icontains=search)
            )

        # Подсчёт общего количества
        total_count = users_qs.count()
        
        # Пагинация
        start = (page - 1) * page_size
        end = start + page_size
        users = users_qs[start:end]

        result = []
        for user in users:
            is_online = user.id in online_ids
            user_data = next(
                (u for u in online_users_data if u.get("user_id") == user.id), None
            )
            is_active = user_data.get("is_active", False) if user_data else False

            # Проверяем премиум статус
            is_premium = False
            try:
                from .models import Subscription
                sub = user.subscription
                is_premium = sub.is_premium
            except Exception:
                pass

            # Формируем avatar_url с фоллбэком на дефолтную аватарку
            avatar_url = None
            if user.avatar:
                avatar_url = user.avatar.url
            else:
                # Возвращаем путь к дефолтной аватарке из папки def_avatars
                def_ava_dir = settings.MEDIA_ROOT / "def_avatars"
                if def_ava_dir.exists():
                    jpg_files = list(def_ava_dir.glob("*.jpg")) + list(def_ava_dir.glob("*.jpeg"))
                    if jpg_files:
                        # Используем deterministic выбор на основе user.id
                        selected_avatar = jpg_files[user.id % len(jpg_files)]
                        avatar_url = f"/media/def_avatars/{selected_avatar.name}"

            result.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname or user.username,
                    "display_name": user.display_name or user.username,
                    "avatar_url": avatar_url,
                    "is_online": is_online,
                    "is_active": is_active,
                    "is_premium": is_premium,
                    "level": getattr(user, "level", 1),
                    "bio": getattr(user, "bio", None) or getattr(user.profile_settings, "bio", None) if hasattr(user, "profile_settings") else None,
                    "last_login": user.last_login.isoformat()
                    if user.last_login
                    else None,
                }
            )

        return Response(
            {
                "results": result,
                "count": total_count,
                "next": f"/api/users/users/?page={page + 1}&page_size={page_size}&tab={tab}&search={search}" if end < total_count else None,
                "previous": f"/api/users/users/?page={page - 1}&page_size={page_size}&tab={tab}&search={search}" if page > 1 else None,
            }
        )
