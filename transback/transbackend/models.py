from django.db import models

class User(models.Model):
    userId = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    changed_at = models.DateTimeField(auto_now=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True, 
        default='profile_pictures/default_profile.png'
    )

    def __str__(self):
        return self.username
