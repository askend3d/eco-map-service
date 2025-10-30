import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    kind = models.CharField(
        max_length=32,
        choices=[("ngo", "НКО"), ("municipal", "Муниципалитет"), ("community", "Сообщество")],
        default="ngo",
    )
    contact_email = models.EmailField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def members(self):
        """Все пользователи, принадлежащие организации"""
        return self.user_set.all()


class User(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Обычный пользователь / волонтёр'),
        ('ngo', 'Экоактивист / НКО'),
        ('admin', 'Администратор'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        verbose_name='Фото профиля'
    )

    def __str__(self):
        return f"{self.username}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
