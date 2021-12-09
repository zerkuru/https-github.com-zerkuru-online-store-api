from django.conf import settings
from django.db import models

from mainapp.models import Product


class Order(models.Model):
    FORMING = 'FM'
    SENT_TO_PROCEED = 'STP'
    PROCEEDED = 'PRD'
    PAID = 'PD'
    READY = 'RDY'
    CANCEL = 'CNC'
    FINISHED = 'FSD'

    ORDER_STATUS = (
        (FORMING, 'формируется'),
        (SENT_TO_PROCEED, 'отправлен в обработку'),
        (PAID, 'оплачен'),
        (PROCEEDED, 'обрабатывается'),
        (READY, 'готов к выдаче'),
        (FINISHED, 'завершен'),
        (CANCEL, 'отменен')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(
        verbose_name='создан',
        auto_now_add=True,
    )
    updated = models.DateTimeField(
        verbose_name='изменен',
        auto_now=True,
    )
    status = models.CharField(
        verbose_name='статус',
        max_length=3,
        choices=ORDER_STATUS,
        default=FORMING,
    )
    is_active = models.BooleanField(verbose_name='активен', default=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'Заказ {self.user.username} №{self.id} от {self.created}'

    def get_summary(self):
        items = self.orderitems.select_related()
        return {
            'total_cost': sum(list(map(lambda x: x.quantity * x.product.price, items))),
            'total_quantity': sum(list(map(lambda x: x.quantity, items))),
        }

    def get_total_quantity(self):
        items = self.orderitems.select_related()
        return sum(list(map(lambda x: x.quantity, items)))

    def get_product_type_quantity(self):
        items = self.orderitems.select_related()
        return len(items)

    def get_total_cost(self):
        items = self.orderitems.select_related()
        return sum(list(map(lambda x: x.quantity * x.product.price, items)))


class OrderItemQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        for obj in self:
            obj.product.quantity += obj.quantity
            obj.product.save()
        super(OrderItemQuerySet, self).delete()


class OrderItem(models.Model):
    objects = OrderItemQuerySet.as_manager()

    order = models.ForeignKey(
        Order,
        related_name="orderitems",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name='продукт',
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(
        verbose_name='количество',
        default=0,
    )

    @staticmethod
    def get_item(pk):
        return OrderItem.objects.filter(pk=pk).first()

    def get_product_cost(self):
        return self.product.price * self.quantity


