from django.db import models


class ProductCat(models.Model):
    pcatid = models.AutoField(primary_key=True)
    category = models.CharField(max_length=20)

    class Meta:
        db_table = 'product_cat'
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['category']

    def __str__(self):
        return self.category


class Product(models.Model):
    prid = models.AutoField(primary_key=True)
    pcatid = models.ForeignKey(
        ProductCat,
        on_delete=models.CASCADE,
        db_column='pcatid',
        related_name='products'
    )
    prname = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    price = models.FloatField()
    srno = models.CharField(max_length=20)
    img = models.ImageField(upload_to='products/', blank=True, null=True)
    des = models.CharField(max_length=50)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['prname']

    def __str__(self):
        return f"{self.prname} ({self.model})"


class SparePart(models.Model):
    spareid = models.AutoField(primary_key=True)
    prid = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='prid',
        related_name='spare_parts'
    )
    partsname = models.CharField(max_length=20)
    price = models.FloatField()
    qty = models.IntegerField(default=0)

    class Meta:
        db_table = 'Spare_parts'
        verbose_name = 'Spare Part'
        verbose_name_plural = 'Spare Parts'
        ordering = ['partsname']

    def __str__(self):
        return f"{self.partsname} - ₹{self.price:.2f} (Stock: {self.qty})"

