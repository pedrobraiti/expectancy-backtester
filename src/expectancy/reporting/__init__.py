"""Reporting layer: terminal summary, matplotlib figures and the PDF report."""

from expectancy.reporting.terminal import format_report, print_report
from expectancy.reporting.figures import generate_figures
from expectancy.reporting.pdf import build_pdf_report

__all__ = ["format_report", "print_report", "generate_figures", "build_pdf_report"]
