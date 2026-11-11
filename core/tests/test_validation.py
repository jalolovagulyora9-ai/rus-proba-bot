from django.test import TestCase
from core.services.validator import (
    normalize_uzbek_phone,
    validate_name_part,
    validate_school_number,
    validate_full_name,
    ValidationError
)

class ValidatorTestCase(TestCase):
    def test_phone_normalization_standard(self):
        self.assertEqual(normalize_uzbek_phone("+998901234567"), "+998901234567")

    def test_phone_normalization_without_plus(self):
        self.assertEqual(normalize_uzbek_phone("998901234567"), "+998901234567")

    def test_phone_normalization_nine_digits(self):
        self.assertEqual(normalize_uzbek_phone("901234567"), "+998901234567")

    def test_phone_normalization_with_formatting(self):
        self.assertEqual(normalize_uzbek_phone("+998 (97) 123-45-67"), "+998971234567")
        self.assertEqual(normalize_uzbek_phone("998 93 987 65 43"), "+998939876543")

    def test_phone_invalid_length(self):
        with self.assertRaises(ValidationError):
            normalize_uzbek_phone("12345")
        with self.assertRaises(ValidationError):
            normalize_uzbek_phone("+99890123456789")

    def test_phone_invalid_operator(self):
        with self.assertRaises(ValidationError):
            normalize_uzbek_phone("+998001234567")

    def test_name_part_validation(self):
        self.assertEqual(validate_name_part("jasur", "Ism"), "Jasur")
        self.assertEqual(validate_name_part("rustamov", "Familiya"), "Rustamov")
        self.assertEqual(validate_name_part("o'ktamov", "Familiya"), "O'ktamov")
        with self.assertRaises(ValidationError):
            validate_name_part("A", "Ism")  # too short
        with self.assertRaises(ValidationError):
            validate_name_part("Jasur123", "Ism")  # digits not allowed

    def test_school_number_validation(self):
        self.assertEqual(validate_school_number("15"), "15")
        self.assertEqual(validate_school_number("15-maktab"), "15-maktab")
        self.assertEqual(validate_school_number("Prezident maktabi"), "Prezident maktabi")
        with self.assertRaises(ValidationError):
            validate_school_number("")

    def test_full_name_validation_valid(self):
        self.assertEqual(validate_full_name("ali valiyev"), ("Ali", "Valiyev"))
        self.assertEqual(validate_full_name("Karimova Dilnoza"), ("Karimova", "Dilnoza"))
        self.assertEqual(validate_full_name("O'ktamov Jasur"), ("O'ktamov", "Jasur"))

    def test_full_name_validation_single_word(self):
        with self.assertRaises(ValidationError):
            validate_full_name("Jasur")
