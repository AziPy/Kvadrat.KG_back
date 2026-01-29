from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name="Родительская категория")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Amenity(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Удобство"
        verbose_name_plural = "Удобства"


class Property(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Квартира'),
        ('house', 'Дом'),
        ('villa', 'Вилла'),
        ('commercial', 'Коммерческое'),
        ('land', 'Участок'),
        ('office', 'Офис'),
    ]

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание", blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Цена ($)")
    area = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Площадь (м²)")
    address = models.CharField(max_length=500, verbose_name="Адрес")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, verbose_name="Тип недвижимости")

    rooms = models.IntegerField(verbose_name="Комнаты", default=1)
    bathrooms = models.IntegerField(verbose_name="Ванные", default=1)
    bedrooms = models.IntegerField(verbose_name="Спальни", default=1)
    kitchen_area = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Площадь кухни (м²)", null=True,
                                       blank=True)
    construction_year = models.IntegerField(verbose_name="Год постройки", null=True, blank=True)
    garage = models.BooleanField(verbose_name="Гараж", default=False)
    garage_spaces = models.IntegerField(verbose_name="Мест в гараже", default=0)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    amenities = models.ManyToManyField(Amenity, blank=True, verbose_name="Удобства")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемое")

    def __str__(self):
        return f"{self.title} - ${self.price}"

    class Meta:
        verbose_name = "Объект недвижимости"
        verbose_name_plural = "Объекты недвижимости"
        ordering = ['-created_at']


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/%Y/%m/%d/', verbose_name="Фотография")
    is_main = models.BooleanField(default=False, verbose_name="Главное фото")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    def __str__(self):
        return f"Фото для {self.property.title}"

    class Meta:
        verbose_name = "Фотография объекта"
        verbose_name_plural = "Фотографии объектов"
        ordering = ['-is_main', 'uploaded_at']


class Activity(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    image = models.ImageField(upload_to='activities/%Y/%m/%d/', null=True, blank=True, verbose_name="Изображение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Активность"
        verbose_name_plural = "Активности"
        ordering = ['-created_at']


class Banner(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание", blank=True)
    image = models.ImageField(upload_to='banners/', verbose_name="Изображение")
    link = models.CharField(max_length=500, blank=True, verbose_name="Ссылка")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ['-created_at']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватар")
    position = models.CharField(max_length=100, default="Админ", verbose_name="Должность")

    def __str__(self):
        return f"{self.user.username} - {self.position}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"