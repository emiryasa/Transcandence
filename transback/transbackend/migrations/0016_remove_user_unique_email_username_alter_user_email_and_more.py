# Generated by Django 4.2.16 on 2024-11-22 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transbackend', '0015_remove_user_unique_email_remove_user_unique_username_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='user',
            name='unique_email_username',
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=True),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True), _negated=True), fields=('email',), name='unique_email'),
        ),
    ]