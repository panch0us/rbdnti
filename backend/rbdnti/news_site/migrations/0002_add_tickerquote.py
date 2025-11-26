from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('news_site', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TickerQuote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст цитаты')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
            ],
            options={
                'verbose_name': 'Цитата для бегущей строки',
                'verbose_name_plural': 'Цитаты для бегущей строки',
                'ordering': ['-created_at'],
            },
        ),
    ]
