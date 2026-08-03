import json
from pathlib import Path

from extract_report import extract_report


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "data" / "reports"
OUTPUT_PATH = BASE_DIR / "data" / "all_extracted_reports.json"


def main():
    all_reports = []

    report_files = REPORTS_DIR.glob("*.txt")

    for report_file in report_files:
        report_text = report_file.read_text(encoding="utf-8")
        result = extract_report(report_text)
        all_reports.append(result.model_dump())
    
    json_text = json.dumps(all_reports, indent=2)
    
    OUTPUT_PATH.write_text(
        json_text,
        encoding = "utf-8"
    )


if __name__ == "__main__":
    main()