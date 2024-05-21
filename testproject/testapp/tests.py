from datetime import date

import time_machine
from django.test import TestCase
from model_bakery import baker

from .models import Book, Person


@time_machine.travel("2000-01-01")
class DBFunctionTestCase(TestCase):
    def test_instance_is_returned(self):
        book = baker.make(Book)
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        self.assertEqual(person.book_of_year, book)

    def test_field_type_int(self):
        baker.make(Book, rating=5)
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        self.assertEqual(person.book_of_year.rating, 5)

    def test_field_type_date(self):
        baker.make(Book, published="2005-01-01")
        baker.make(Person, birth="2005-06-01")

        person = Person.objects.with_book_of_the_year().get()
        self.assertEqual(person.book_of_year.published, date(2005, 1, 1))

    def test_field_type_bool(self):
        baker.make(Book, has_cover=False)
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        self.assertIs(person.book_of_year.has_cover, False)

    def test_field_null(self):
        baker.make(Book, rating=None)
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        self.assertIsNone(person.book_of_year.rating)

    def test_no_matching_book(self):
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        self.assertIsNone(person.book_of_year)

    def test_multiple_matching_books(self):
        baker.make(Book, rating=10, title="best")
        baker.make(Book, rating=1, title="worst")
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        self.assertEqual(person.book_of_year.title, "best")

    def test_returned_instance_is_updateable(self):
        book = baker.make(Book, title="test")
        baker.make(Person)

        person = Person.objects.with_book_of_the_year().get()
        person.book_of_year.title = "updated"
        person.book_of_year.save()
        book.refresh_from_db()
        self.assertEqual(book.title, "updated")

    def test_deffered_fields(self):
        book = baker.make(Book, title="test", rating=5)
        baker.make(Person)

        person = Person.objects.with_book_of_the_year(fields=["id"]).get()
        with self.assertNumQueries(0):
            self.assertEqual(person.book_of_year.pk, book.pk)
        with self.assertNumQueries(1):
            self.assertEqual(person.book_of_year.title, "test")
        with self.assertNumQueries(1):
            self.assertEqual(person.book_of_year.rating, 5)
