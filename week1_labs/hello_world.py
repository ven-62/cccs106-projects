# hello_world.py
# CCCS 106 - Week 1 Lab Exercise
# Student: Ven John Rey C. Lavapie
# Date: August 27, 2025

print("=" * 50)
print("CCCS 106: Application Development and Emerging Technologies")
print("Week 1 Lab - Hello World Program")
print("=" * 50)

# Basic output
print("Hello, World!")
print("Welcome to Python programming!")

# Student information (replace with your details)
student_name = "Ven John Rey C. Lavapie"
student_id = "231002321"
program = "Bachelor of Science in Computer Science"
year_level = "3rd Year"

print(f"\nStudent Information:")
print(f"Name: {student_name}")
print(f"Student ID: {student_id}")
print(f"Program: {program}")
print(f"Year Level: {year_level}")

# Basic calculations
current_year = 2025
birth_year = 2005  # Replace with your birth year
age = current_year - birth_year

print(f"\nAge Calculation:")
print(f"Birth Year: {birth_year}")
print(f"Current Year: {current_year}")
print(f"Age: {age} years old")

# Python version information
import sys
print(f"\nTechnical Information:")
print(f"Python Version: {sys.version.split()[0]}")
print(f"Platform: {sys.platform}")

print("\n" + "=" * 50)
print("Program completed successfully!")
print("=" * 50)