from rest_framework import viewsets, filters, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Category, Amenity, Property, PropertyImage, Activity, Banner, Profile
from .serializers import (
    UserSerializer, ProfileSerializer, CategorySerializer, AmenitySerializer,
    PropertySerializer, PropertyCreateSerializer, PropertyImageSerializer,
    ActivitySerializer, BannerSerializer, RegisterSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)

import secrets
from django.core.mail import send_mail
from django.core.cache import cache
from django.db.models import Q, Count, Sum


@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Profiles'])
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(tags=['Authentication'])
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            Profile.objects.create(user=user)

            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Authentication'])
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Вход выполнен успешно',
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Authentication'])
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {'refresh': {'type': 'string'}}
            }
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Authentication'])
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=ForgotPasswordSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            reset_token = secrets.token_urlsafe(32)
            cache.set(f'password_reset_{reset_token}', user.id, timeout=3600)

            reset_url = f"http://localhost:3000/reset-password?token={reset_token}"

            try:
                send_mail(
                    subject='Восстановление пароля - KVADRAT.KG',
                    message=f'Для восстановления пароля перейдите по ссылке: {reset_url}\nТокен действителен 1 час.',
                    from_email='noreply@kvadrat.kg',
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                return Response({
                    'message': 'Инструкции по восстановлению пароля отправлены на ваш email',
                    'token': reset_token
                })
            except:
                return Response({
                    'message': 'Email сервер не настроен. Вот ваш токен для тестов:',
                    'token': reset_token,
                    'reset_url': reset_url
                })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Authentication'])
class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=ResetPasswordSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            user_id = cache.get(f'password_reset_{token}')

            if not user_id:
                return Response({'error': 'Недействительный или просроченный токен'},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                cache.delete(f'password_reset_{token}')
                return Response({'message': 'Пароль успешно изменен'})
            except User.DoesNotExist:
                return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Authentication'])
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'old_password': {'type': 'string'},
                    'new_password': {'type': 'string'},
                    'confirm_password': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not request.user.check_password(old_password):
            return Response({'error': 'Старый пароль неверен'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'Пароли не совпадают'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'Пароль должен содержать минимум 8 символов'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({'message': 'Пароль успешно изменен'})


@extend_schema(tags=['Users'])
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


@extend_schema(tags=['Users'])
class CurrentProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: ProfileSerializer})
    def get(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)

        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    @extend_schema(request=ProfileSerializer, responses={200: ProfileSerializer})
    def patch(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(tags=['Categories']),
    create=extend_schema(tags=['Categories']),
    retrieve=extend_schema(tags=['Categories']),
    update=extend_schema(tags=['Categories']),
    partial_update=extend_schema(tags=['Categories']),
    destroy=extend_schema(tags=['Categories'])
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    list=extend_schema(tags=['Amenities']),
    create=extend_schema(tags=['Amenities']),
    retrieve=extend_schema(tags=['Amenities']),
    update=extend_schema(tags=['Amenities']),
    partial_update=extend_schema(tags=['Amenities']),
    destroy=extend_schema(tags=['Amenities'])
)
class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    list=extend_schema(tags=['Properties']),
    create=extend_schema(tags=['Properties']),
    retrieve=extend_schema(tags=['Properties']),
    update=extend_schema(tags=['Properties']),
    partial_update=extend_schema(tags=['Properties']),
    destroy=extend_schema(tags=['Properties'])
)
class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.filter(is_active=True)
    serializer_class = PropertySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'rooms', 'bedrooms', 'garage', 'category', 'is_featured']
    search_fields = ['title', 'address', 'description']
    ordering_fields = ['price', 'area', 'created_at']
    ordering = ['-created_at']
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PropertyCreateSerializer
        return PropertySerializer

    @extend_schema(
        tags=['Properties'],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'images': {'type': 'array', 'items': {'type': 'string', 'format': 'binary'}}
                }
            }
        }
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_images(self, request, pk=None):
        property_obj = self.get_object()
        images = request.FILES.getlist('images')

        for image in images:
            PropertyImage.objects.create(property=property_obj, image=image)

        return Response({'status': 'Images uploaded'}, status=status.HTTP_201_CREATED)

    @extend_schema(tags=['Properties'], responses={200: PropertySerializer(many=True)})
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_properties = Property.objects.filter(is_featured=True, is_active=True)
        serializer = self.get_serializer(featured_properties, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Activities']),
    create=extend_schema(tags=['Activities']),
    retrieve=extend_schema(tags=['Activities']),
    update=extend_schema(tags=['Activities']),
    partial_update=extend_schema(tags=['Activities']),
    destroy=extend_schema(tags=['Activities'])
)
class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [permissions.AllowAny]
    ordering = ['-created_at']


@extend_schema_view(
    list=extend_schema(tags=['Banners']),
    create=extend_schema(tags=['Banners']),
    retrieve=extend_schema(tags=['Banners']),
    update=extend_schema(tags=['Banners']),
    partial_update=extend_schema(tags=['Banners']),
    destroy=extend_schema(tags=['Banners'])
)
class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Admin'])
class AdminStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        stats = {
            'total_properties': Property.objects.count(),
            'active_properties': Property.objects.filter(is_active=True).count(),
            'featured_properties': Property.objects.filter(is_featured=True).count(),
            'total_activities': Activity.objects.count(),
            'total_banners': Banner.objects.count(),
            'total_users': User.objects.count(),
            'properties_by_type': list(Property.objects.values('property_type').annotate(count=Count('id'))),
            'total_value': Property.objects.aggregate(total=Sum('price'))['total'] or 0,
        }
        return Response(stats)


@extend_schema(tags=['Properties'])
class PropertyFilterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'property_type': {'type': 'string',
                                      'enum': ['apartment', 'house', 'villa', 'commercial', 'land', 'office']},
                    'min_price': {'type': 'number'},
                    'max_price': {'type': 'number'},
                    'min_area': {'type': 'number'},
                    'max_area': {'type': 'number'},
                    'rooms': {'type': 'integer'},
                    'bathrooms': {'type': 'integer'},
                    'bedrooms': {'type': 'integer'},
                    'amenities': {'type': 'array', 'items': {'type': 'integer'}}
                }
            }
        },
        responses={200: PropertySerializer(many=True)}
    )
    def post(self, request):
        filters = Q(is_active=True)

        property_type = request.data.get('property_type')
        if property_type:
            filters &= Q(property_type=property_type)

        min_price = request.data.get('min_price')
        max_price = request.data.get('max_price')
        if min_price:
            filters &= Q(price__gte=min_price)
        if max_price:
            filters &= Q(price__lte=max_price)

        min_area = request.data.get('min_area')
        max_area = request.data.get('max_area')
        if min_area:
            filters &= Q(area__gte=min_area)
        if max_area:
            filters &= Q(area__lte=max_area)

        rooms = request.data.get('rooms')
        if rooms:
            filters &= Q(rooms=rooms)

        bathrooms = request.data.get('bathrooms')
        if bathrooms:
            filters &= Q(bathrooms=bathrooms)

        bedrooms = request.data.get('bedrooms')
        if bedrooms:
            filters &= Q(bedrooms=bedrooms)

        amenities = request.data.get('amenities', [])
        if amenities:
            filters &= Q(amenities__id__in=amenities)

        properties = Property.objects.filter(filters).distinct()
        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Properties'])
class PropertySearchView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Search query', type=str),
            OpenApiParameter(name='property_type', description='Type filter', type=str),
            OpenApiParameter(name='min_price', description='Min price', type=int),
            OpenApiParameter(name='max_price', description='Max price', type=int),
        ]
    )
    def get(self, request):
        filters = Q(is_active=True)

        query = request.GET.get('q', '')
        if query:
            filters &= Q(title__icontains=query) | Q(description__icontains=query) | Q(address__icontains=query)

        property_type = request.GET.get('property_type')
        if property_type:
            filters &= Q(property_type=property_type)

        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            filters &= Q(price__gte=min_price)
        if max_price:
            filters &= Q(price__lte=max_price)

        properties = Property.objects.filter(filters).distinct()
        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)