from django.db import models

# Create your models here.
class Comment(models.Model):
    cmtid = models.PositiveIntegerField("cmtid", primary_key=True)
    postid = models.PositiveIntegerField("postid", db_index=True)
    date = models.DateTimeField("date", null=True, blank=True)
    author = models.CharField('author', max_length=16, null=True, blank=True)
    text = models.TextField("text")
    subject = models.CharField('subject', max_length=256, null=True, blank=True)
    screened = models.BooleanField("screened", default=False)

