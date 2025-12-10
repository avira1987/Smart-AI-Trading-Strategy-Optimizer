"""
Utility functions for gamification system
"""
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserScore, Achievement, UserAchievement, Result


def get_or_create_user_score(user: User) -> UserScore:
    """دریافت یا ایجاد امتیاز کاربر"""
    score, created = UserScore.objects.get_or_create(user=user)
    if created:
        score.level = score.calculate_level()
        score.save()
    return score


def calculate_backtest_points(result: Result) -> int:
    """محاسبه امتیاز بر اساس نتایج بک‌تست"""
    points = 0
    
    # امتیاز پایه برای انجام بک‌تست
    points += 10
    
    # امتیاز بر اساس تعداد معاملات
    if result.total_trades > 0:
        points += min(result.total_trades // 5, 20)  # حداکثر 20 امتیاز
    
    # امتیاز بر اساس بازدهی
    if result.total_return > 0:
        if result.total_return >= 50:
            points += 50
        elif result.total_return >= 30:
            points += 30
        elif result.total_return >= 20:
            points += 20
        elif result.total_return >= 10:
            points += 15
        elif result.total_return >= 5:
            points += 10
        else:
            points += 5
    elif result.total_return < -20:
        # برای ضررهای بزرگ، امتیاز منفی نمی‌دهیم اما امتیاز کمتری می‌دهیم
        points = max(points - 5, 0)
    
    # امتیاز بر اساس نرخ برد
    if result.win_rate >= 70:
        points += 20
    elif result.win_rate >= 60:
        points += 15
    elif result.win_rate >= 50:
        points += 10
    elif result.win_rate >= 40:
        points += 5
    
    # امتیاز بر اساس نسبت سود/ضرر (Profit Factor)
    # استفاده از profit_factor واقعی به جای نسبت تعداد معاملات
    profit_factor = getattr(result, 'profit_factor', 0.0)
    if profit_factor > 0:
        if profit_factor >= 2.0:
            points += 15
        elif profit_factor >= 1.5:
            points += 10
        elif profit_factor >= 1.0:
            points += 5
    
    return points


def award_backtest_points(user: User, result: Result) -> Dict[str, Any]:
    """اعطای امتیاز برای انجام بک‌تست"""
    score = get_or_create_user_score(user)
    points = calculate_backtest_points(result)
    
    # به‌روزرسانی آمار
    score.backtests_completed += 1
    score.total_trades += result.total_trades
    
    if result.total_return > score.best_return:
        score.best_return = result.total_return
    
    # افزودن امتیاز (این متد فقط total_points و level را ذخیره می‌کند)
    level_up = score.add_points(points, f"بک‌تست با بازدهی {result.total_return:.2f}%")
    
    # ذخیره فیلدهای به‌روزرسانی شده (backtests_completed, best_return, total_trades)
    score.save(update_fields=['backtests_completed', 'best_return', 'total_trades', 'updated_at'])
    
    # بررسی دستاوردها
    new_achievements = check_and_award_achievements(user, result)
    
    return {
        'points_awarded': points,
        'total_points': score.total_points,
        'level': score.level,
        'level_up': level_up,
        'new_achievements': new_achievements
    }


def check_and_award_achievements(user: User, result: Optional[Result] = None) -> list:
    """بررسی و اعطای دستاوردهای جدید"""
    score = get_or_create_user_score(user)
    new_achievements = []
    
    # دریافت همه دستاوردهای فعال
    achievements = Achievement.objects.filter(is_active=True)
    
    for achievement in achievements:
        # بررسی اینکه آیا کاربر قبلاً این دستاورد را دریافت کرده است
        if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            continue
        
        # بررسی شرط دستاورد
        should_award = False
        
        if achievement.condition_type == 'backtest_count':
            should_award = score.backtests_completed >= achievement.condition_value
        elif achievement.condition_type == 'return_threshold' and result:
            should_award = result.total_return >= achievement.condition_value
        elif achievement.condition_type == 'win_rate_threshold' and result:
            should_award = result.win_rate >= achievement.condition_value
        elif achievement.condition_type == 'trades_count' and result:
            should_award = result.total_trades >= achievement.condition_value
        elif achievement.condition_type == 'strategy_count':
            should_award = score.strategies_created >= achievement.condition_value
        elif achievement.condition_type == 'optimization_count':
            should_award = score.optimizations_completed >= achievement.condition_value
        elif achievement.condition_type == 'level':
            should_award = score.level >= achievement.condition_value
        
        if should_award:
            # اعطای دستاورد
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                unlocked_at=timezone.now()
            )
            
            # افزودن امتیاز جایزه
            if achievement.points_reward > 0:
                score.add_points(achievement.points_reward, f"دستاورد: {achievement.name}")
            
            new_achievements.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points_reward': achievement.points_reward
            })
    
    return new_achievements


def get_user_rank(user: User) -> int:
    """دریافت رتبه کاربر در لیدربورد"""
    try:
        score = UserScore.objects.get(user=user)
        # تعداد کاربرانی که امتیاز بیشتری دارند + 1
        rank = UserScore.objects.filter(total_points__gt=score.total_points).count() + 1
        return rank
    except UserScore.DoesNotExist:
        return None


def get_leaderboard(limit: int = 10) -> list:
    """دریافت لیدربورد"""
    scores = UserScore.objects.select_related('user').order_by('-total_points')[:limit]
    leaderboard = []
    for idx, score in enumerate(scores, 1):
        leaderboard.append({
            'rank': idx,
            'username': score.user.username,
            'nickname': getattr(score.user.profile, 'nickname', None) if hasattr(score.user, 'profile') else None,
            'total_points': score.total_points,
            'level': score.level,
            'backtests_completed': score.backtests_completed,
            'best_return': score.best_return
        })
    return leaderboard


def initialize_default_achievements():
    """ایجاد دستاوردهای پیش‌فرض"""
    default_achievements = [
        {
            'code': 'first_backtest',
            'name': 'اولین قدم',
            'description': 'انجام اولین بک‌تست',
            'icon': '🎯',
            'category': 'backtest',
            'condition_type': 'backtest_count',
            'condition_value': 1.0,
            'points_reward': 50
        },
        {
            'code': 'backtest_10',
            'name': 'تجربه‌مند',
            'description': 'انجام 10 بک‌تست',
            'icon': '📊',
            'category': 'backtest',
            'condition_type': 'backtest_count',
            'condition_value': 10.0,
            'points_reward': 100
        },
        {
            'code': 'backtest_50',
            'name': 'حرفه‌ای',
            'description': 'انجام 50 بک‌تست',
            'icon': '🏆',
            'category': 'backtest',
            'condition_type': 'backtest_count',
            'condition_value': 50.0,
            'points_reward': 500
        },
        {
            'code': 'return_10',
            'name': 'سودآور',
            'description': 'دستیابی به بازدهی 10%',
            'icon': '💰',
            'category': 'backtest',
            'condition_type': 'return_threshold',
            'condition_value': 10.0,
            'points_reward': 100
        },
        {
            'code': 'return_30',
            'name': 'بازدهی عالی',
            'description': 'دستیابی به بازدهی 30%',
            'icon': '💎',
            'category': 'backtest',
            'condition_type': 'return_threshold',
            'condition_value': 30.0,
            'points_reward': 300
        },
        {
            'code': 'return_50',
            'name': 'بازدهی استثنایی',
            'description': 'دستیابی به بازدهی 50%',
            'icon': '👑',
            'category': 'backtest',
            'condition_type': 'return_threshold',
            'condition_value': 50.0,
            'points_reward': 500
        },
        {
            'code': 'win_rate_60',
            'name': 'دقت بالا',
            'description': 'دستیابی به نرخ برد 60%',
            'icon': '🎯',
            'category': 'backtest',
            'condition_type': 'win_rate_threshold',
            'condition_value': 60.0,
            'points_reward': 150
        },
        {
            'code': 'win_rate_70',
            'name': 'دقت استثنایی',
            'description': 'دستیابی به نرخ برد 70%',
            'icon': '⭐',
            'category': 'backtest',
            'condition_type': 'win_rate_threshold',
            'condition_value': 70.0,
            'points_reward': 300
        },
        {
            'code': 'trades_100',
            'name': 'معامله‌گر فعال',
            'description': 'انجام 100 معامله',
            'icon': '📈',
            'category': 'trading',
            'condition_type': 'trades_count',
            'condition_value': 100.0,
            'points_reward': 200
        },
    ]
    
    for ach_data in default_achievements:
        Achievement.objects.get_or_create(
            code=ach_data['code'],
            defaults=ach_data
        )

