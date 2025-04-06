import json

class HTMLReport:
    _instance = None

    def __init__(self, title="LLM Results Report", storage_file="report_sections.json"):
        self.title = title
        self.storage_file = storage_file
        self.current_section = {}
        self.sections = []

    @classmethod
    def get_instance(cls, title="LLM Results Report", storage_file="report_sections.json"):
        if cls._instance is None:
            cls._instance = cls(title, storage_file)
        return cls._instance

    def load_sections(self):
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def new_section(self):
        self.current_section = {}

    def add_to_section(self, key: str, text: str):
        self.current_section[key] = text

    def add_section(self, section: dict):
        self.sections.append(section)

    def save_section(self):
        self.add_section(self.current_section)
        self.new_section()

    def clear_sections(self):
        self.sections = []

    def generate_report(self, filename="report.html"):
        # Build a basic HTML template with CSS styling.
        html = f"""<!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>{self.title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
            .section {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
            .question {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; }}
            .original-query {{ background-color: #ffc8c8; padding: 5px; }}
            .corrected-query {{ background-color: #c8ffc8; padding: 5px; margin-top: 5px; }}
            .response {{ padding: 5px; margin-top: 5px; }}
        </style>
        </head>
        <body>
        <div class="header">{self.title}</div>
        """

        for section in self.sections:
            question = section.get("question", "")
            original_query = section.get("original_query", "")
            corrected_query = section.get("corrected_query", "")
            expected_answer = section.get("expected_answer", "")
            actual_answer = section.get("actual_answer", "")
            html += f"""
            <div class="section">
                <div class="question">Question: {question}</div>
                <div class="original-query">Original Query: {original_query}</div>
                <div class="corrected-query">Corrected Query: {corrected_query}</div>
                <div class="response">Expected Response: {expected_answer}</div>
                <div class="response">Actual Response: {actual_answer}</div>
            </div>
            """
        html += "</body></html>"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
