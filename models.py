from dataclasses import dataclass


@dataclass
class EmailAnalysis:
    important: bool
    label: str
    summary: str
    tracking_number: str | None
    courier: str | None


@dataclass
class AnalysisRunResult:
    analysis: EmailAnalysis
    elapsed_seconds: float


@dataclass
class EmailProcessingResult:
    label: str
    important_summary: str | None = None
    package_summary: str | None = None
