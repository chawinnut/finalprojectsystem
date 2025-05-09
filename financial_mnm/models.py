from django.db import models
from django.utils import timezone
from django.conf import settings

class FinancialManagement(models.Model):
    FM_ID = models.AutoField(primary_key=True, db_column='FM_ID', verbose_name="รหัสการจัดการงบประมาณ")
    Budget_Year = models.IntegerField(db_column='Budget_Year', verbose_name="ปีงบประมาณ", unique=True)
    Total_Budget = models.DecimalField(max_digits=30, decimal_places=2, db_column='Total_Budget', verbose_name="งบประมาณทั้งหมด")
    Used_Budget = models.DecimalField(max_digits=30, decimal_places=2, db_column='Used_Budget', default=0.00, verbose_name="งบประมาณที่ใช้ไป")
    Remaining_Budget = models.DecimalField(max_digits=30, decimal_places=2, db_column='Remaining_Budget', verbose_name="งบประมาณคงเหลือ")

    def __str__(self):
        return f"ปีงบประมาณ {self.Budget_Year}: {self.Total_Budget}"

    class Meta:
        db_table = 'Financial_Management'
        verbose_name = "การจัดการงบประมาณ"
        verbose_name_plural = "การจัดการงบประมาณ"
        ordering = ['-Budget_Year']


class CalendarEvent(models.Model):
    title = models.CharField(max_length=255, verbose_name="หัวข้อ")
    date = models.DateField(verbose_name="วันที่")
    time = models.TimeField(null=True, blank=True, verbose_name="เวลา")
    note = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ผู้สร้าง") # อัปเดตตรงนี้

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "กำหนดการส่วนกลาง"
        verbose_name_plural = "ข้อมูลกำหนดการส่วนกลาง"
        ordering = ['date', 'time']