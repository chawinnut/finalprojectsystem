from django.db import models

# Create your models here.
from django.db import models
from database_subscription.models import DatabaseSubscription

class DatabaseSearch(models.Model):
    database_subscription = models.ForeignKey(DatabaseSubscription, on_delete=models.CASCADE)  # เชื่อมโยงกับ DatabaseSubscription
    search_query = models.CharField(max_length=255, blank=True, null=True, verbose_name="คำค้นหา")  # ตัวอย่างฟิลด์สำหรับเก็บคำค้นหา
    result_count = models.IntegerField(default=0, verbose_name="จำนวนผลลัพธ์")  # ตัวอย่างฟิลด์สำหรับเก็บจำนวนผลลัพธ์

    def __str__(self):
        return f"ผลการค้นหาสำหรับ {self.database_subscription.DB_Name}"

    class Meta:
        verbose_name = "การค้นหาฐานข้อมูล"
        verbose_name_plural = "การค้นหาฐานข้อมูล"
        db_table = 'database_search'