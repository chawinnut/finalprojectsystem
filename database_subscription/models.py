from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from decimal import Decimal, ROUND_HALF_UP

class Collection(models.Model):
    collection_id = models.AutoField(primary_key=True, verbose_name="รหัส Collection")
    name = models.CharField(max_length=255, unique=True, verbose_name="ชื่อ Collection")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        ordering = ['name']

class CollectionDetail(models.Model):
    database_subscription = models.ForeignKey('DatabaseSubscription', on_delete=models.CASCADE, related_name='collection_details', verbose_name="ฐานข้อมูล")
    collection_name = models.CharField(max_length=255, verbose_name="ชื่อ Collection")
    journal_count = models.IntegerField(blank=True, null=True, verbose_name="จำนวน E-Journals")
    ebook_count = models.IntegerField(blank=True, null=True, verbose_name="จำนวน E-Books")

    class Meta:
        verbose_name = "รายละเอียด Collection"
        verbose_name_plural = "รายละเอียด Collections"
        unique_together = ('database_subscription', 'collection_name')
        
class DatabaseSubscription(models.Model):
    STATUS_CHOICES = [
        ('expired', 'หมดอายุ'),
        ('current', 'กำลังบอกรับอยู่ในปัจจุบัน'),
        ('future', 'กำลังจะบอกรับในอนาคต'),
    ]

    DS_ID = models.AutoField(primary_key=True, db_column='DS_ID', verbose_name="รหัสของฐานข้อมูล")
    DB_Name = models.CharField(max_length=255, db_column='DB_Name', verbose_name="ชื่อฐานข้อมูล")
    raw_collections_data = models.TextField(blank=True, null=True, verbose_name="ข้อมูล Collections (ชื่อ, วารสาร, E-Books ต่อบรรทัด)")
    subscription_start_date = models.DateField(blank=True, null=True, verbose_name="วันที่เริ่มต้นการบอกรับ")
    subscription_end_date = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุดการบอกรับ")
    renewal_date = models.DateField(blank=True, null=True, verbose_name="กำหนดการต่ออายุการบอกรับ")
    renewal_year = models.CharField(max_length=20, blank=True, null=True, verbose_name="ปีที่บอกรับ")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")
    subscription_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='current',
        verbose_name="สถานะการบอกรับ"
    )
    has_perpetual_license = models.BooleanField(default=False, verbose_name="มีสิทธิ์ perpetual license")
    perpetual_license_terms = models.TextField(blank=True, null=True, verbose_name="เงื่อนไข perpetual license")
    concurrent_users = models.CharField(max_length=50, blank=True, null=True, verbose_name="จำนวนผู้ใช้งานพร้อมกัน")
    remote_access_allowed = models.BooleanField(default=False, verbose_name="อนุญาตการเข้าถึงจากภายนอก")
    download_allowed = models.BooleanField(default=False, verbose_name="อนุญาตการดาวน์โหลด")
    print_allowed = models.BooleanField(default=False, verbose_name="อนุญาตการพิมพ์")
    copy_allowed = models.BooleanField(default=False, verbose_name="อนุญาตการทำสำเนา")
    interlibrary_loan_allowed = models.BooleanField(default=False, verbose_name="บริการยืมทรัพยากรระหว่างห้องสมุด (ILL)")
    usage_conditions_text = models.TextField(blank=True, null=True, verbose_name="เงื่อนไขการใช้งานอื่น ๆ ")
    license_agreement_file = models.FileField(upload_to='licenses/', blank=True, null=True, verbose_name="ไฟล์ข้อตกลงสิทธิ์การใช้งาน")
    payment_method = models.CharField(max_length=20, default="wire transfer", verbose_name="วิธีการชำระเงิน", editable=False)
    payment_date = models.DateField(blank=True, null=True, verbose_name="วันที่ชำระเงิน")
    amount_paid_thb = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="จำนวนเงินที่ชำระ (บาท)")
    amount_original_currency = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="จำนวนเงิน (สกุลเงินต้นทาง)")
    budget_allocated = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="งบประมาณที่ตั้งเบิก")
    notes = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    original_currency = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        choices=[('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR'), ('THB', 'THB')],
        verbose_name='สกุลเงินต้นทาง'
    )

    def __str__(self):
        return f"{self.DB_Name} ({self.get_subscription_status_display()})"

    class Meta:
        db_table = 'Database_Subscription'
        verbose_name = "ฐานข้อมูลที่บอกรับ"
        verbose_name_plural = "ฐานข้อมูลที่บอกรับ"
        ordering = ['DB_Name', '-renewal_year']

    def should_notify_renewal(self, months_before):
        if self.renewal_date:
            notification_date = self.renewal_date - timezone.timedelta(days=months_before * 30)
            today = timezone.now().date()
            return notification_date == today
        return False

    def get_notification_dates(self):
        if self.renewal_date:
            one_month_before = self.renewal_date - timezone.timedelta(days=30)
            three_months_before = self.renewal_date - timezone.timedelta(days=90)
            return one_month_before, three_months_before
        return None, None

    def _get_previous_year_subscription_instance(self):
        if not self.renewal_year or not self.DB_Name:
            return None
        try:
            current_year_int = int(self.renewal_year)
            previous_year_str = str(current_year_int - 1)
        except ValueError:
            return None
        previous_subscription = DatabaseSubscription.objects.filter(
            DB_Name=self.DB_Name,
            renewal_year=previous_year_str
        ).exclude(DS_ID=self.DS_ID).order_by('-subscription_start_date', '-DS_ID').first()
        return previous_subscription

    @property
    def percentage_price_increase_thb(self):
        if self.amount_paid_thb is None:
            return None

        previous_subscription = self._get_previous_year_subscription_instance()

        if previous_subscription and \
           previous_subscription.amount_paid_thb is not None and \
           previous_subscription.amount_paid_thb > Decimal('0.00'):

            current_price = self.amount_paid_thb
            previous_price = previous_subscription.amount_paid_thb

            percentage_increase = ((current_price - previous_price) / previous_price) * Decimal('100.0')
            return percentage_increase.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) # ปัดเศษทศนิยม 2 ตำแหน่ง
        return None

    @property
    def percentage_price_increase_original_currency(self):
        if self.amount_original_currency is None or self.original_currency is None:
            return None

        previous_subscription = self._get_previous_year_subscription_instance()

        if previous_subscription and previous_subscription.amount_original_currency is not None:
            if previous_subscription.original_currency == self.original_currency:
                if previous_subscription.amount_original_currency > Decimal('0.00'):
                    current_price = self.amount_original_currency
                    previous_price = previous_subscription.amount_original_currency
                    percentage_increase = ((current_price - previous_price) / previous_price) * Decimal('100.0')
                    return percentage_increase.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                return "Currency mismatch"
        return None


class DatabaseSubscriptionChangeLog(models.Model):
    database_subscription = models.ForeignKey('DatabaseSubscription', on_delete=models.CASCADE, related_name='change_logs', verbose_name="รหัสของฐานข้อมูล")

    archived_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่/เวลาที่เปลี่ยนแปลง")
    change_details = JSONField(null=True, blank=True, verbose_name="รายละเอียดการเปลี่ยนแปลง")

    class Meta:
        verbose_name = "ประวัติการเปลี่ยนแปลงฐานข้อมูลที่บอกรับ"
        verbose_name_plural = "ประวัติการเปลี่ยนแปลงฐานข้อมูลที่บอกรับ"
        ordering = ['-archived_at'] 

    def __str__(self):
        try:
            db_name = self.database_subscription.DB_Name
            return f"Change log for {db_name} at {self.archived_at.strftime('%Y-%m-%d %H:%M')}"
        except AttributeError:
            return f"Change log (Database missing) at {self.archived_at.strftime('%Y-%m-%d %H:%M')}"
