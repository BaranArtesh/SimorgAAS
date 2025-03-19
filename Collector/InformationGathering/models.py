from django.db import models


class Item:
    def __init__(self, id, name):
        self.id = id
        self.name = name



items = [
    Item(1, "Item 1"),
    Item(2, "Item 2"),
    Item(3, "Item 3"),
]