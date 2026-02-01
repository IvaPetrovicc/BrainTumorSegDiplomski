"""Placeholder for automatic PDF report generation using ReportLab."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from parameters import REPORTS_DIR

def generate_simple_report(text: str, filename: str = "report.pdf") -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 12)
    y = height - 50
    for line in text.split("\n"):
        c.drawString(50, y, line)
        y -= 20
    c.showPage()
    c.save()
    return path

if __name__ == "__main__":
    p = generate_simple_report("YOLO brain tumor segmentation report.")
    print("Report saved to:", p)
