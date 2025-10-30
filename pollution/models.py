from django.db import models

from config.settings import AUTH_USER_MODEL
from users.models import Organization


class PollutionPoint(models.Model):
    """Точка загрязнения на карте."""

    TYPE_CHOICES = (
        ('trash', 'Бытовой мусор'),
        ('oil', 'Нефтяное пятно'),
        ('industrial', 'Промышленные отходы'),
        ('chemical', 'Химикаты'),
        ('plastic', 'Пластик'),
        ('other', 'Другое'),
    )

    STATUS_CHOICES = (
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('cleaned', 'Очищено'),
    )

    reporter = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pollution_reports',
        null=True,
        blank=True
    )
    anonymous_name = models.CharField(max_length=255, blank=True, null=True)
    pollution_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    handled_by = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_points',
        verbose_name="Организация, обрабатывающая точку"
    )
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    photo = models.ImageField(upload_to='pollution_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    started_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата начала работ")
    cleaned_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата очистки")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.reporter.username if self.reporter else self.anonymous_name or "Аноним"
        return f"{self.get_pollution_type_display()} ({self.latitude}, {self.longitude}) — {name}"


class Comment(models.Model):
    """Комментарий от пользователей (НКО, волонтёров и т.д.)"""
    point = models.ForeignKey(PollutionPoint, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    photo = models.ImageField(upload_to='comment_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on point {self.point.id}"
