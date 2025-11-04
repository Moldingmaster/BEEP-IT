#!/usr/bin/env python3
"""Unit tests for job number validation."""
import unittest
import sys
import re


def validate_job_number(job_number):
    """Validate job number according to business rules.
    
    Rules:
    - Must be 5 to 8 characters in length
    - No symbols other than "-"
    - Must have at least 5 digits before "-" (if dash exists)
    - If "-" exists, suffix must be single digit 1-9, optionally followed by "R"
    - No letters (except "R" immediately after digit in suffix)
    - Must start with 5, 6, 7, or 8
    
    Returns: (is_valid, error_message)
    """
    # Check length
    if len(job_number) < 5 or len(job_number) > 8:
        return False, "Job number must be 5-8 characters"
    
    # Must start with 5, 6, 7, or 8
    if job_number[0] not in ['5', '6', '7', '8']:
        return False, "Job number must start with 5, 6, 7, or 8"
    
    # Check for invalid symbols (only digits, "-", and "R" allowed)
    if not re.match(r'^[5-8][0-9\-R]+$', job_number):
        return False, "Invalid characters (only digits, '-', and 'R' allowed)"
    
    # Split on dash if present
    if '-' in job_number:
        parts = job_number.split('-')
        
        # Only one dash allowed
        if len(parts) != 2:
            return False, "Only one '-' allowed"
        
        prefix, suffix = parts
        
        # Prefix must be at least 5 digits
        if not prefix.isdigit() or len(prefix) < 5:
            return False, "At least 5 digits required before '-'"
        
        # Suffix must be single digit 1-9, optionally followed by R
        if not re.match(r'^[1-9]R?$', suffix):
            return False, "After '-': single digit 1-9, optionally followed by 'R'"
    else:
        # No dash: must be all digits (R not allowed without dash)
        if not job_number.isdigit():
            return False, "Job number without '-' must be all digits"
    
    return True, ""


class TestJobNumberValidation(unittest.TestCase):
    """Test cases for job number validation."""
    
    def test_valid_basic_numbers(self):
        """Test valid job numbers without dashes."""
        valid_numbers = [
            "50000",
            "567890",
            "87654321",
            "60000",
            "70000",
            "80000",
            "555555",
            "5678901"  # 7 chars
        ]
        for num in valid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertTrue(is_valid, f"{num} should be valid but got: {msg}")
    
    def test_valid_with_dash_and_digit(self):
        """Test valid job numbers with dash and single digit suffix."""
        valid_numbers = [
            "50000-1",
            "50000-2",
            "50000-9",
            "567890-5",
            "87654-1",  # 5 digits before dash
        ]
        for num in valid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertTrue(is_valid, f"{num} should be valid but got: {msg}")
    
    def test_valid_with_dash_digit_and_r(self):
        """Test valid job numbers with dash, digit, and R suffix."""
        valid_numbers = [
            "50000-1R",  # 8 chars total
            "50000-9R",  # 8 chars total
            "87654-2R",  # 8 chars total
        ]
        for num in valid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertTrue(is_valid, f"{num} should be valid but got: {msg}")
    
    def test_invalid_length_too_short(self):
        """Test job numbers that are too short."""
        invalid_numbers = [
            "5000",   # 4 chars
            "500",    # 3 chars
            "50",     # 2 chars
            "5",      # 1 char
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (too short)")
                self.assertIn("5-8 characters", msg)
    
    def test_invalid_length_too_long(self):
        """Test job numbers that are too long."""
        invalid_numbers = [
            "567890123",  # 9 chars
            "5678901234", # 10 chars
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (too long)")
                self.assertIn("5-8 characters", msg)
    
    def test_invalid_first_digit(self):
        """Test job numbers that don't start with 5, 6, 7, or 8."""
        invalid_numbers = [
            "00000",   # starts with 0
            "10000",   # starts with 1
            "20000",   # starts with 2
            "30000",   # starts with 3
            "40000",   # starts with 4
            "90000",   # starts with 9
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (wrong first digit)")
                self.assertIn("start with 5, 6, 7, or 8", msg)
    
    def test_invalid_symbols(self):
        """Test job numbers with invalid symbols."""
        invalid_numbers = [
            "50000#1",   # has #
            "50000@1",   # has @
            "50000.1",   # has .
            "50000_1",   # has _
            "50000/1",   # has /
            "50000*1",   # has *
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (invalid symbols)")
    
    def test_invalid_dash_prefix_too_short(self):
        """Test job numbers with less than 5 digits before dash."""
        invalid_numbers = [
            "5000-1",   # 4 digits before dash (also too short overall)
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (prefix too short)")
                self.assertIn("5 digits required before", msg)
    
    def test_invalid_dash_suffix_zero(self):
        """Test job numbers with 0 in suffix."""
        invalid_numbers = [
            "50000-0",
            "567890-0",
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (suffix can't be 0)")
    
    def test_invalid_dash_suffix_multiple_digits(self):
        """Test job numbers with multiple digits in suffix."""
        invalid_numbers = [
            "50000-10",
            "50000-12",
            "50000-99",
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (suffix must be single digit)")
    
    def test_invalid_r_without_digit(self):
        """Test job numbers with R not preceded by digit in suffix."""
        invalid_numbers = [
            "50000-R",   # R without digit
            "50000R",    # R without dash
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (R misplaced)")
    
    def test_invalid_multiple_dashes(self):
        """Test job numbers with multiple dashes."""
        invalid_numbers = [
            "50000-1-2",
            "50000--1",
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (multiple dashes)")
    
    def test_invalid_letters_in_prefix(self):
        """Test job numbers with letters in prefix."""
        invalid_numbers = [
            "5000A",
            "5000B-1",
            "ABC50000",
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (letters in wrong place)")
    
    def test_invalid_r_in_wrong_position(self):
        """Test job numbers with R in wrong position in suffix."""
        invalid_numbers = [
            "50000-1RR",   # double R
            "50000-R1",    # R before digit
            "50000-1R2",   # R in middle
        ]
        for num in invalid_numbers:
            with self.subTest(num=num):
                is_valid, msg = validate_job_number(num)
                self.assertFalse(is_valid, f"{num} should be invalid (R in wrong position)")
    
    def test_edge_case_exact_lengths(self):
        """Test edge cases with exact min and max lengths."""
        # Minimum length (5 chars)
        is_valid, _ = validate_job_number("50000")
        self.assertTrue(is_valid, "5 character job number should be valid")
        
        # Maximum length without dash (8 chars)
        is_valid, _ = validate_job_number("56789012")
        self.assertTrue(is_valid, "8 character job number should be valid")
        
        # Maximum length with dash (8 chars)
        is_valid, _ = validate_job_number("50000-1R")
        self.assertTrue(is_valid, "8 character job number with dash should be valid")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
