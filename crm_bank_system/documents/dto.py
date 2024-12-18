from dataclasses import dataclass

@dataclass
class ReportDTO:
    user: id
    description: str
    screenshot: str