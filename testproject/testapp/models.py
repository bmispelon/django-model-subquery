from datetime import date

from django.db import models
from django.db.models.functions import ExtractYear

from modelsubquery import ModelSubquery


class Book(models.Model):
    title = models.CharField(max_length=100)
    rating = models.IntegerField(blank=True, null=True)
    published = models.DateField(default=date.today)
    has_cover = models.BooleanField(default=True)


class PersonQuerySet(models.QuerySet):
    def with_book_of_the_year(self, fields=None):
        """
        Annotate each person in the queryset with the best rated book of the
        year they were born.
        """
        year = ExtractYear(models.OuterRef("birth"))
        all_books = Book.objects.filter(published__year=year).order_by("-rating")
        return self.annotate(book_of_year=ModelSubquery(all_books, fields=fields))


class Person(models.Model):
    name = models.CharField(max_length=100)
    birth = models.DateField(default=date.today)

    objects = PersonQuerySet.as_manager()
