from django.db import models


class Item(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    def __init__(self, id, name):
        self.id = id
        self.name = name

items = [
    Item(1, "Item 1"),
    Item(2, "Item 2"),
    Item(3, "Item 3"),

    
]


 