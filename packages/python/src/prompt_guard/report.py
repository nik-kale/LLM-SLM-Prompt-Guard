"""
Detection reporting utilities for PII analysis and compliance auditing.
"""

from typing import List, Dict
from .types import DetectorResult, DetectionReport, RiskLevel


# High-risk PII types that trigger higher risk scores
HIGH_RISK_ENTITIES = {
    "SSN",
    "CREDIT_CARD",
    "BANK_ACCOUNT",
    "CVV",
    "PASSPORT",
    "DRIVER_LICENSE",
    "MEDICAL_RECORD",
    "TAX_ID",
    "CRYPTO_ADDRESS",
}

MEDIUM_RISK_ENTITIES = {
    "EMAIL",
    "PHONE",
    "IBAN",
    "IP_ADDRESS",
    "API_KEY",
    "PASSWORD",
}


def generate_detection_report(
    text: str,
    entities: List[DetectorResult],
    include_preview: bool = False,
) -> DetectionReport:
    """
    Generate a comprehensive detection report from PII detection results.
    
    Args:
        text: Original text that was analyzed
        entities: List of detected PII entities
        include_preview: Include text preview in report (first 100 chars)
    
    Returns:
        DetectionReport with statistics and risk assessment
    """
    # Calculate summary (count per entity type)
    summary: Dict[str, int] = {}
    for entity in entities:
        summary[entity.entity_type] = summary.get(entity.entity_type, 0) + 1
    
    # Calculate PII coverage
    total_chars = len(text)
    pii_chars = sum(entity.end - entity.start for entity in entities)
    coverage = (pii_chars / total_chars) if total_chars > 0 else 0.0
    
    # Assess risk level
    risk_score = _calculate_risk_level(entities, coverage)
    
    # Optional text preview
    text_preview = ""
    if include_preview:
        text_preview = text[:100] + ("..." if len(text) > 100 else "")
    
    return DetectionReport(
        entities=entities,
        summary=summary,
        coverage=coverage,
        risk_score=risk_score,
        total_chars=total_chars,
        pii_chars=pii_chars,
        text_preview=text_preview,
    )


def _calculate_risk_level(
    entities: List[DetectorResult],
    coverage: float,
) -> RiskLevel:
    """
    Calculate risk level based on entity types and coverage.
    
    Risk assessment criteria:
    - CRITICAL: Any high-risk entity (SSN, credit card, etc.)
    - HIGH: Multiple medium-risk entities or >30% coverage
    - MEDIUM: Any medium-risk entity or >10% coverage
    - LOW: Only low-risk entities or <10% coverage
    """
    if not entities:
        return RiskLevel.LOW
    
    entity_types = {e.entity_type for e in entities}
    
    # Check for high-risk entities
    if entity_types & HIGH_RISK_ENTITIES:
        return RiskLevel.CRITICAL
    
    # Check for medium-risk entities
    medium_risk_found = bool(entity_types & MEDIUM_RISK_ENTITIES)
    
    # Assess based on coverage and entity types
    if coverage > 0.3:  # >30% of text is PII
        return RiskLevel.HIGH
    elif medium_risk_found and len(entities) > 5:
        return RiskLevel.HIGH
    elif medium_risk_found or coverage > 0.1:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def format_report_text(report: DetectionReport) -> str:
    """
    Format a detection report as human-readable text.
    
    Args:
        report: DetectionReport to format
    
    Returns:
        Formatted text representation of the report
    """
    lines = []
    lines.append("=" * 60)
    lines.append("PII Detection Report")
    lines.append("=" * 60)
    lines.append("")
    
    # Summary statistics
    lines.append(f"Total Entities: {len(report.entities)}")
    lines.append(f"PII Coverage: {report.coverage * 100:.1f}%")
    lines.append(f"Risk Level: {report.risk_score.value.upper()}")
    lines.append(f"Text Length: {report.total_chars} characters")
    lines.append(f"PII Characters: {report.pii_chars}")
    lines.append("")
    
    # Entity breakdown
    if report.summary:
        lines.append("Entity Types Detected:")
        for entity_type, count in sorted(report.summary.items(), key=lambda x: -x[1]):
            lines.append(f"  - {entity_type}: {count}")
        lines.append("")
    
    # Risk indicators
    if report.risk_score in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        lines.append("⚠️  WARNING: High-risk PII detected!")
        high_risk_found = [
            entity.entity_type
            for entity in report.entities
            if entity.entity_type in HIGH_RISK_ENTITIES
        ]
        if high_risk_found:
            unique_types = sorted(set(high_risk_found))
            lines.append(f"   High-risk types: {', '.join(unique_types)}")
        lines.append("")
    
    # Text preview
    if report.text_preview:
        lines.append("Text Preview:")
        lines.append(f"  {report.text_preview}")
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


def format_report_html(report: DetectionReport) -> str:
    """
    Format a detection report as HTML.
    
    Args:
        report: DetectionReport to format
    
    Returns:
        HTML representation of the report
    """
    risk_colors = {
        RiskLevel.LOW: "#28a745",
        RiskLevel.MEDIUM: "#ffc107",
        RiskLevel.HIGH: "#fd7e14",
        RiskLevel.CRITICAL: "#dc3545",
    }
    
    risk_color = risk_colors.get(report.risk_score, "#6c757d")
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h1 style="border-bottom: 3px solid {risk_color};">PII Detection Report</h1>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h2>Summary</h2>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Total Entities:</strong></td>
                    <td>{len(report.entities)}</td>
                </tr>
                <tr>
                    <td><strong>PII Coverage:</strong></td>
                    <td>{report.coverage * 100:.1f}%</td>
                </tr>
                <tr>
                    <td><strong>Risk Level:</strong></td>
                    <td style="color: {risk_color}; font-weight: bold;">
                        {report.risk_score.value.upper()}
                    </td>
                </tr>
                <tr>
                    <td><strong>Text Length:</strong></td>
                    <td>{report.total_chars} characters</td>
                </tr>
            </table>
        </div>
    """
    
    if report.summary:
        html += """
        <div style="margin: 20px 0;">
            <h2>Entity Types Detected</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #e9ecef;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #dee2e6;">
                            Entity Type
                        </th>
                        <th style="padding: 10px; text-align: right; border: 1px solid #dee2e6;">
                            Count
                        </th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for entity_type, count in sorted(report.summary.items(), key=lambda x: -x[1]):
            is_high_risk = entity_type in HIGH_RISK_ENTITIES
            bg_color = "#fff3cd" if is_high_risk else "white"
            html += f"""
                    <tr style="background-color: {bg_color};">
                        <td style="padding: 8px; border: 1px solid #dee2e6;">
                            {entity_type}
                            {'<span style="color: #dc3545;">⚠️</span>' if is_high_risk else ''}
                        </td>
                        <td style="padding: 8px; text-align: right; border: 1px solid #dee2e6;">
                            {count}
                        </td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    if report.risk_score in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        html += f"""
        <div style="background-color: #f8d7da; color: #721c24; padding: 15px; 
                    border-radius: 5px; margin: 20px 0; border-left: 4px solid {risk_color};">
            <strong>⚠️ WARNING:</strong> High-risk PII detected! 
            Review and secure this data immediately.
        </div>
        """
    
    html += """
    </div>
    """
    
    return html

