
from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='อีเมล')
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="customuser",
    )

    def __str__(self):
        return self.username


class LoginHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_history')
    login_datetime = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)  # เก็บ IP Address
    user_agent = models.TextField(blank=True, null=True)  # เก็บ User Agent String

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_datetime}"