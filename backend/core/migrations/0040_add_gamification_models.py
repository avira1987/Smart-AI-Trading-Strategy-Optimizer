# Generated migration for gamification models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_add_use_ai_cache_to_system_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='کد یکتا برای دستاورد', max_length=100, unique=True)),
                ('name', models.CharField(help_text='نام دستاورد', max_length=200)),
                ('description', models.TextField(help_text='توضیحات دستاورد')),
                ('icon', models.CharField(default='🏆', help_text='آیکون دستاورد', max_length=10)),
                ('points_reward', models.IntegerField(default=0, help_text='امتیاز جایزه')),
                ('category', models.CharField(choices=[('backtest', 'بک‌تست'), ('strategy', 'استراتژی'), ('optimization', 'بهینه‌سازی'), ('trading', 'معاملات'), ('social', 'اجتماعی'), ('level', 'سطح')], default='backtest', help_text='دسته‌بندی دستاورد', max_length=50)),
                ('condition_type', models.CharField(choices=[('backtest_count', 'تعداد بک‌تست'), ('return_threshold', 'آستانه بازدهی'), ('win_rate_threshold', 'آستانه نرخ برد'), ('trades_count', 'تعداد معاملات'), ('strategy_count', 'تعداد استراتژی'), ('optimization_count', 'تعداد بهینه‌سازی'), ('level', 'سطح')], help_text='نوع شرط برای دریافت دستاورد', max_length=50)),
                ('condition_value', models.FloatField(help_text='مقدار شرط')),
                ('is_active', models.BooleanField(default=True, help_text='آیا دستاورد فعال است')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'دستاورد',
                'verbose_name_plural': 'دستاوردها',
                'ordering': ['category', 'points_reward'],
            },
        ),
        migrations.CreateModel(
            name='UserScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_points', models.IntegerField(default=0, help_text='مجموع امتیازات کاربر')),
                ('level', models.IntegerField(default=1, help_text='سطح کاربر (بر اساس امتیاز)')),
                ('backtests_completed', models.IntegerField(default=0, help_text='تعداد بک‌تست‌های انجام شده')),
                ('strategies_created', models.IntegerField(default=0, help_text='تعداد استراتژی‌های ایجاد شده')),
                ('optimizations_completed', models.IntegerField(default=0, help_text='تعداد بهینه‌سازی‌های انجام شده')),
                ('best_return', models.FloatField(default=0.0, help_text='بهترین بازدهی در بک‌تست')),
                ('total_trades', models.IntegerField(default=0, help_text='مجموع معاملات انجام شده')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_score', to='auth.user')),
            ],
            options={
                'verbose_name': 'امتیاز کاربر',
                'verbose_name_plural': 'امتیازات کاربران',
                'ordering': ['-total_points'],
            },
        ),
        migrations.CreateModel(
            name='UserAchievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unlocked_at', models.DateTimeField(auto_now_add=True)),
                ('achievement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_achievements', to='core.achievement')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements', to='auth.user')),
            ],
            options={
                'verbose_name': 'دستاورد کاربر',
                'verbose_name_plural': 'دستاوردهای کاربران',
                'ordering': ['-unlocked_at'],
                'unique_together': {('user', 'achievement')},
            },
        ),
    ]

