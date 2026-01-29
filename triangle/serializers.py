from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Amenity, Property, PropertyImage, Activity, Banner, Profile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined']
        read_only_fields = ['is_staff', 'is_superuser', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'phone', 'avatar', 'position']
        read_only_fields = ['user']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon']


class PropertyImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'is_main', 'uploaded_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'

    def get_main_image(self, obj):
        main_img = obj.images.filter(is_main=True).first()
        if main_img:
            return main_img.image.url
        return None


class PropertyCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Property
        exclude = ['created_at', 'updated_at']

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        property_obj = Property.objects.create(**validated_data)

        for i, image in enumerate(images):
            PropertyImage.objects.create(
                property=property_obj,
                image=image,
                is_main=(i == 0)
            )

        return property_obj


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, min_length=4)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")

        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует")

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        login = data.get('login')
        password = data.get('password')

        user = None
        if '@' in login:
            try:
                user = User.objects.get(email=login)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(username=login)
            except User.DoesNotExist:
                pass

        if user and user.check_password(password):
            data['user'] = user
            return data

        raise serializers.ValidationError("Неверные учетные данные")


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            data['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return data


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data