# Generated by Django 5.1.7 on 2025-03-17 16:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rastaaslan_app', '0004_auto_20250316_1251'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTopicView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_viewed', models.DateTimeField(auto_now=True)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_views', to='rastaaslan_app.forumtopic')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_views', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vue de sujet par utilisateur',
                'verbose_name_plural': 'Vues de sujets par utilisateurs',
                'unique_together': {('user', 'topic')},
            },
        ),
        migrations.CreateModel(
            name='PostReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction_type', models.CharField(choices=[('like', '👍 Like'), ('thanks', '🙏 Merci'), ('funny', '😂 Drôle'), ('insightful', '💡 Pertinent')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='rastaaslan_app.forumpost')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_reactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Réaction à un message',
                'verbose_name_plural': 'Réactions aux messages',
                'unique_together': {('post', 'user', 'reaction_type')},
            },
        ),
        migrations.AddField(
            model_name='forumpost',
            name='mentioned_users',
            field=models.ManyToManyField(blank=True, related_name='post_mentions', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateurs mentionnés'),
        ),
        migrations.AddIndex(
            model_name='forumpost',
            index=models.Index(fields=['topic', 'created_at'], name='rastaaslan__topic_i_f31384_idx'),
        ),
        migrations.AddIndex(
            model_name='forumtopic',
            index=models.Index(fields=['category', 'created_at'], name='rastaaslan__categor_dd7b5c_idx'),
        ),
        migrations.AddIndex(
            model_name='forumtopic',
            index=models.Index(fields=['is_pinned', 'created_at'], name='rastaaslan__is_pinn_d33aca_idx'),
        ),
    ]