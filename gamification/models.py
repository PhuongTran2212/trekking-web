# gamification/models.py
from django.db import models
from django.contrib.auth.models import User

class GameHuyHieu(models.Model):
    ten = models.CharField(max_length=100, unique=True)
    mo_ta = models.TextField()
    anh_huy_hieu = models.CharField(max_length=200)

    def __str__(self):
        return self.ten

class GameHuyHieuNguoiDung(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    huy_hieu = models.ForeignKey(GameHuyHieu, on_delete=models.CASCADE)
    ngay_dat_duoc = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'huy_hieu')
