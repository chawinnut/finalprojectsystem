from django.db import models
from financial_mnm.models import FinancialManagement
from django.utils import timezone

class DatabaseSubscription(models.Model):
    DS_ID = models.AutoField(primary_key=True, db_column='DS_ID', verbose_name="รหัสของฐานข้อมูล")
    DB_Name = models.CharField(max_length=255, db_column='DB_Name', verbose_name="ชื่อฐานข้อมูล")
    DB_Collection = models.CharField(max_length=255, blank=True, null=True, db_column='DB_Collection', verbose_name="Collection")
    DBJournal_List = models.TextField(db_column='DBJournal_List', blank=True, null=True, verbose_name="จำนวนชื่อเรื่องแบบวารสาร")
    DBEBook_List = models.TextField(db_column='DBEBook_List', blank=True, null=True, verbose_name="จำนวนชื่อเรื่องแบบ E-Books")
    subscription_start_date = models.DateField(blank=True, null=True, verbose_name="วันที่เริ่มต้นการบอกรับ")
    subscription_end_date = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุดการบอกรับ")
    renewal_date = models.DateField(blank=True, null=True, verbose_name="กำหนดการต่ออายุการบอกรับ")
    FinMnm_ID = models.ForeignKey(FinancialManagement, on_delete=models.SET_NULL, null=True, db_column='FinMnm_ID', verbose_name="รหัสการจัดการการเงิน", related_name='database_subscriptions')
    created_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")

    def __str__(self):
        return self.DB_Name

    class Meta:
        db_table = 'Database_Subscription'
        verbose_name = "ฐานข้อมูลที่บอกรับ"
        verbose_name_plural = "ฐานข้อมูลที่บอกรับ"
        ordering = ['created_at']

class DatabaseSubscriptionArchive(models.Model):
    database_subscription = models.ForeignKey(DatabaseSubscription, on_delete=models.CASCADE, related_name='archives', verbose_name="รหัสของฐานข้อมูล")
    archived_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่/เวลาที่ Archive")
    DB_Name = models.CharField(max_length=255, db_column='DB_Name', verbose_name="ชื่อฐานข้อมูล (ตอน Archive)")
    DB_Collection = models.CharField(max_length=255, blank=True, null=True, db_column='DB_Collection', verbose_name="Collection (ตอน Archive)")
    DBJournal_List = models.TextField(db_column='DBJournal_List', blank=True, null=True, verbose_name="จำนวนชื่อเรื่องแบบวารสาร (ตอน Archive)")
    DBEBook_List = models.TextField(db_column='DBEBook_List', blank=True, null=True, verbose_name="จำนวนชื่อเรื่องแบบ E-Books (ตอน Archive)")
    subscription_start_date = models.DateField(blank=True, null=True, verbose_name="วันที่เริ่มต้นการบอกรับ (ตอน Archive)")
    subscription_end_date = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุดการบอกรับ (ตอน Archive)")
    renewal_date = models.DateField(blank=True, null=True, verbose_name="กำหนดการต่ออายุการบอกรับ (ตอน Archive)")
    FinMnm_ID = models.ForeignKey(FinancialManagement, on_delete=models.SET_NULL, null=True, db_column='FinMnm_ID', verbose_name="รหัสการจัดการการเงิน (ตอน Archive)", related_name='+') # ใช้ '+' เพื่อป้องกันการสร้าง relation ย้อนกลับ
    year = models.IntegerField(null=True, blank=True, verbose_name='ปี')

    class Meta:
        verbose_name = "ประวัติฐานข้อมูลที่บอกรับ"
        verbose_name_plural = "ประวัติฐานข้อมูลที่บอกรับ"
        ordering = ['-archived_at']

    def save(self, *args, **kwargs):
        if not self.year:
            self.year = self.archived_at.year
        super().save(*args, **kwargs)
        
class UsageStatistics(models.Model):
    Usage_ID = models.AutoField(primary_key=True, db_column='Usage_ID', verbose_name="รหัสของการบันทึกข้อมูลการใช้งาน")
    Usage_Count = models.IntegerField(db_column='Usage_Count', default=0, verbose_name="จำนวนการใช้งานฐานข้อมูล")
    Usage_Type = models.CharField(max_length=255, db_column='Usage_Type', blank=True, null=True, verbose_name="ประเภทของการใช้งานฐานข้อมูล")
    Usage_HistoryDate = models.DateTimeField(db_column='Usage_HistoryDate', verbose_name="วันเวลาที่มีการใช้งาน")
    database_subscription = models.ForeignKey(DatabaseSubscription, on_delete=models.CASCADE, verbose_name="ฐานข้อมูลที่ใช้งาน")
    year = models.IntegerField(verbose_name="ปีที่ใช้งาน") # Added for easier filtering

    def __str__(self):
        return f"Usage ID: {self.Usage_ID} for {self.database_subscription.DB_Name} ({self.year})"

    class Meta:
        db_table = 'Usage_Statistics'
        verbose_name = "รายงานสถิติการใช้งาน"
        verbose_name_plural = "รายงานสถิติการใช้งาน"

class UsageStatisticsArchive(models.Model):
    usage_statistics = models.ForeignKey(UsageStatistics, on_delete=models.CASCADE, related_name='archives', verbose_name="รหัสของการบันทึกข้อมูลการใช้งาน")
    archived_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่/เวลาที่ Archive")
    Usage_Count = models.IntegerField(db_column='Usage_Count', default=0, verbose_name="จำนวนการใช้งานฐานข้อมูล (ตอน Archive)")
    Usage_Type = models.CharField(max_length=255, db_column='Usage_Type', blank=True, null=True, verbose_name="ประเภทของการใช้งานฐานข้อมูล (ตอน Archive)")
    Usage_HistoryDate = models.DateTimeField(db_column='Usage_HistoryDate', verbose_name="วันเวลาที่มีการใช้งาน (ตอน Archive)")
    database_subscription = models.ForeignKey(DatabaseSubscription, on_delete=models.SET_NULL, null=True, verbose_name="ฐานข้อมูลที่ใช้งาน (ตอน Archive)")
    year = models.IntegerField(verbose_name="ปีที่ใช้งาน (ตอน Archive)")

    class Meta:
        verbose_name = "ประวัติรายงานสถิติการใช้งาน"
        verbose_name_plural = "ประวัติรายงานสถิติการใช้งาน"
        ordering = ['-archived_at']