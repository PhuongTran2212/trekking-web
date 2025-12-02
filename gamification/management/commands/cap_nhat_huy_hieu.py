# gamification/management/commands/cap_nhat_huy_hieu.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gamification.services import BadgeEngine

class Command(BaseCommand):
    help = 'Quét và trao huy hiệu cho tất cả người dùng'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        engine = BadgeEngine()
        count = 0
        
        self.stdout.write("--- BẮT ĐẦU QUÉT ---")
        
        for user in users:
            try:
                new_badges = engine.check_all_badges(user)
                if new_badges:
                    self.stdout.write(self.style.SUCCESS(f"User {user.username}: Nhận {len(new_badges)} huy hiệu"))
                    count += len(new_badges)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Lỗi tại {user.username}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- HOÀN TẤT! Tổng cộng trao {count} huy hiệu mới ---"))