from django.db import models

class Target(models.Model):
    name = models.CharField(max_length=255, unique=True)
    host = models.GenericIPAddressField()
    type = models.CharField(max_length=50)
    is_local = models.BooleanField(default=False)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name





# from django.db import models

# class User(models.Model):
#     username = models.CharField(max_length=150, unique=True)
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=255)
#     is_admin = models.BooleanField(default=False)

#     def __str__(self):
#         return self.username
