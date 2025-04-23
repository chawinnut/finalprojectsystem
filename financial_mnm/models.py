from django.db import models

class Vendor(models.Model):
    Vendor_ID = models.AutoField(primary_key=True, db_column='Vendor_ID', verbose_name="รหัสผู้ขาย")
    Vendor_Name = models.CharField(max_length=255, db_column='Vendor_Name', verbose_name="ชื่อผู้ขาย")
    Vendor_Contact = models.TextField(db_column='Vendor_Contact', blank=True, null=True, verbose_name="ข้อมูลการติดต่อ")
    Vendor_Paycon = models.TextField(db_column='Vendor_Paycon', blank=True, null=True, verbose_name="ข้อตกลงการจ่ายเงิน")

    def __str__(self):
        return self.Vendor_Name

    class Meta:
        db_table = 'Vendor'
        verbose_name = "ผู้ขาย"
        verbose_name_plural = "ข้อมูลผู้ขาย"

class Funder(models.Model):
    Funder_ID = models.AutoField(primary_key=True, db_column='Funder_ID', verbose_name="รหัสผู้ให้ทุน")
    Funder_Name = models.CharField(max_length=255, db_column='Funder_Name', verbose_name="ชื่อผู้ให้ทุน")
    Funder_Budget = models.DecimalField(max_digits=15, decimal_places=2, db_column='Funder_Budget', default=0.00, verbose_name="งบประมาณที่ได้รับ")
    Funder_History = models.TextField(db_column='Funder_History', blank=True, null=True, verbose_name="ประวัติการให้ทุน")

    def __str__(self):
        return self.Funder_Name

    class Meta:
        db_table = 'Funder'
        verbose_name = "ผู้ให้ทุน"
        verbose_name_plural = "ข้อมูลผู้ให้ทุน"

class Payment(models.Model):
    Payment_ID = models.AutoField(primary_key=True, db_column='Payment_ID', verbose_name="รหัสการชำระเงิน")
    Payment_Date = models.DateField(db_column='Payment_Date', verbose_name="วันที่ชำระเงิน")
    Payment_Amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='Payment_Amount', verbose_name="จำนวนเงินที่ชำระ")
    Payment_Method = models.CharField(max_length=255, db_column='Payment_Method', verbose_name="วิธีการชำระเงิน")
    Vendor_ID = models.ForeignKey(Vendor, on_delete=models.CASCADE, db_column='Vendor_ID', verbose_name="ผู้ขาย")
    payment_document = models.FileField(upload_to='payments/', blank=True, null=True, verbose_name="เอกสารการชำระเงิน")
    currency = models.CharField(max_length=3, default='THB', verbose_name="สกุลเงิน")
    database_subscription = models.ForeignKey('database_subscription.DatabaseSubscription', on_delete=models.CASCADE, verbose_name="ฐานข้อมูลที่บอกรับ") # ใช้ String แทนการ Import โดยตรง

    def __str__(self):
        return f"Payment ID: {self.Payment_ID} for {self.database_subscription.DB_Name} on {self.Payment_Date}"

    class Meta:
        db_table = 'Payment'
        verbose_name = "การชำระเงิน"
        verbose_name_plural = "ข้อมูลการชำระเงิน"

class FinancialManagement(models.Model):
    FinMnm_ID = models.AutoField(primary_key=True, db_column='FinMnm_ID', verbose_name="รหัสการจัดการการเงิน")
    Negotiation_Details = models.TextField(db_column='Negotiation_Details', blank=True, null=True, verbose_name="รายละเอียดการเจรจาต่อรอง")
    Perpetual_License = models.BooleanField(default=False, db_column='Perpetual_License', verbose_name="สัญญาซื้อขาด")
    Usage_Terms = models.TextField(db_column='Usage_Terms', blank=True, null=True, verbose_name="ข้อกำหนดการใช้งาน")
    Vendor_ID = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, db_column='Vendor_ID', verbose_name="ผู้ขาย")
    Funder_ID = models.ForeignKey(Funder, on_delete=models.SET_NULL, null=True, db_column='Funder_ID', verbose_name="ผู้ให้ทุน")

    def __str__(self):
        return f"Financial Management ID: {self.FinMnm_ID}"

    class Meta:
        db_table = 'Financial_Management'
        verbose_name = "การจัดการการเงิน"
        verbose_name_plural = "ข้อมูลการจัดการการเงิน"

# ปฏิทินส่วนกลางไว้ดูและสร้างกำหนดการ
from django.conf import settings  # Import settings

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