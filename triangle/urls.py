from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .views import (
    UserViewSet, ProfileViewSet, CategoryViewSet, AmenityViewSet,
    PropertyViewSet, ActivityViewSet, BannerViewSet,
    RegisterView, LoginView, LogoutView, ForgotPasswordView, ResetPasswordView, ChangePasswordView,
    CurrentUserView, CurrentProfileView, AdminStatsView, PropertyFilterView, PropertySearchView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'banners', BannerViewSet, basename='banner')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('user/me/', CurrentUserView.as_view(), name='current_user'),
    path('user/profile/', CurrentProfileView.as_view(), name='current_profile'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('properties/filter/', PropertyFilterView.as_view(), name='property_filter'),
    path('properties/search/', PropertySearchView.as_view(), name='property_search'),
    path('', include(router.urls)),
]