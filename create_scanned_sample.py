#!/usr/bin/env python3
"""Create a sample scanned PDF to test OCR"""

from PIL import Image, ImageDraw, ImageFont
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile

def create_scanned_style_pdf(filename):
    """Create a PDF that simulates a scanned document"""
    
    # Create an image that looks like a scanned bank statement
    width, height = 2480, 3508  # A4 at 300 DPI
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font
    try:
        font_size = 40
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 35)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # Add some noise to simulate scan
    import random
    for _ in range(1000):
        x = random.randint(0, width)
        y = random.randint(0, height)
        gray = random.randint(200, 250)
        draw.point((x, y), fill=(gray, gray, gray))
    
    # Bank header
    y_pos = 200
    draw.text((200, y_pos), "FIRST NATIONAL BANK", font=font, fill='black')
    y_pos += 100
    draw.text((200, y_pos), "Account Statement", font=small_font, fill='black')
    y_pos += 80
    draw.text((200, y_pos), "Period: 01/01/2024 - 01/31/2024", font=small_font, fill='black')
    
    # Add a slight rotation to simulate imperfect scanning
    img = img.rotate(0.5, fillcolor='white')
    
    # Table header
    y_pos = 600
    draw = ImageDraw.Draw(img)  # Recreate draw after rotation
    draw.text((200, y_pos), "Date", font=small_font, fill='black')
    draw.text((600, y_pos), "Description", font=small_font, fill='black')
    draw.text((1800, y_pos), "Amount", font=small_font, fill='black')
    draw.text((2100, y_pos), "Balance", font=small_font, fill='black')
    
    # Add line
    y_pos += 60
    draw.line((200, y_pos, 2280, y_pos), fill='black', width=2)
    
    # Transactions
    transactions = [
        ("01/05/2024", "WALMART SUPERCENTER #4521", "-87.43", "4,125.67"),
        ("01/08/2024", "DIRECT DEPOSIT - EMPLOYER", "2,845.00", "6,970.67"),
        ("01/10/2024", "AMAZON.COM PURCHASE", "-156.89", "6,813.78"),
        ("01/12/2024", "STARBUCKS COFFEE #1234", "-12.45", "6,801.33"),
        ("01/15/2024", "UTILITY PAYMENT - ELECTRIC", "-234.56", "6,566.77"),
        ("01/18/2024", "ATM WITHDRAWAL", "-200.00", "6,366.77"),
        ("01/22/2024", "NETFLIX SUBSCRIPTION", "-15.99", "6,350.78"),
        ("01/25/2024", "GROCERY STORE #5678", "-145.23", "6,205.55"),
        ("01/28/2024", "GAS STATION #9012", "-67.89", "6,137.66"),
        ("01/30/2024", "RESTAURANT DINING", "-89.50", "6,048.16"),
    ]
    
    y_pos += 80
    for date, desc, amount, balance in transactions:
        draw.text((200, y_pos), date, font=small_font, fill='black')
        draw.text((600, y_pos), desc, font=small_font, fill='black')
        draw.text((1800, y_pos), amount, font=small_font, fill='black')
        draw.text((2100, y_pos), balance, font=small_font, fill='black')
        y_pos += 60
    
    # Add some blur to simulate scan quality
    from PIL import ImageFilter
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Save as temporary image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name, 'PNG')
        temp_image = tmp.name
    
    # Convert to PDF
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawImage(temp_image, 0, 0, width=letter[0], height=letter[1])
    c.save()
    
    # Clean up
    os.unlink(temp_image)
    
    print(f"Created scanned-style PDF: {filename}")

if __name__ == "__main__":
    output_file = "scanned_bank_statement.pdf"
    create_scanned_style_pdf(output_file)
    
    print("\nNow test OCR with:")
    print(f"python3 test_ocr_capabilities.py {output_file}")