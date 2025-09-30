# treks/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import CungDuongDanhGia

@receiver([post_save, post_delete], sender=CungDuongDanhGia)
def update_trek_rating(sender, instance, **kwargs):
    trek = instance.cung_duong
    aggregates = CungDuongDanhGia.objects.filter(cung_duong=trek).aggregate(avg_rating=Avg('diem_danh_gia'), count_rating=Count('id'))
    trek.danh_gia_trung_binh = aggregates.get('avg_rating') or 0.00
    trek.so_luot_danh_gia = aggregates.get('count_rating') or 0
    trek.save()