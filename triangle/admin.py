from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Amenity, Property, PropertyImage, Activity, Banner, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3
    readonly_fields = ['uploaded_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent']
    list_filter = ['parent']
    search_fields = ['name']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'property_type', 'price', 'area', 'address', 'is_active', 'is_featured', 'created_at']
    list_filter = ['property_type', 'is_active', 'is_featured', 'created_at', 'category']
    search_fields = ['title', 'address', 'description']
    list_editable = ['is_active', 'is_featured', 'price']
    inlines = [PropertyImageInline]
    filter_horizontal = ['amenities']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'property_type', 'category', 'price', 'area', 'address')
        }),
        ('Детали', {
            'fields': ('rooms', 'bathrooms', 'bedrooms', 'kitchen_area', 'construction_year', 'garage', 'garage_spaces')
        }),
        ('Удобства', {
            'fields': ('amenities',)
        }),
        ('Статус', {
            'fields': ('is_active', 'is_featured')
        }),
    )


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['property', 'is_main', 'uploaded_at']
    list_filter = ['is_main', 'uploaded_at']
    search_fields = ['property__title']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title', 'content']
    list_filter = ['created_at']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']