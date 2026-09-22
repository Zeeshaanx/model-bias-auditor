import html
import json
from datetime import UTC, datetime
from typing import Any

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


class ReportGenerator:
    """Renders an audit result in the formats a compliance reviewer actually needs."""

    def build(
        self,
        report_format: str,
        audit_id: str,
        audit: dict[str, Any],
        findings: list[dict[str, Any]],
        attribute_summary: list[dict[str, Any]],
    ) -> str:
        payload = self._payload(audit_id, audit, findings, attribute_summary)
        if report_format == "markdown":
            return self._markdown(payload)
        if report_format == "html":
            return self._html(payload)
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _payload(
        self,
        audit_id: str,
        audit: dict[str, Any],
        findings: list[dict[str, Any]],
        attribute_summary: list[dict[str, Any]],
    ) -> dict[str, Any]:
        counts = {severity: 0 for severity in SEVERITY_ORDER}
        for finding in findings:
            counts[finding.get("severity", "info")] = counts.get(finding.get("severity", "info"), 0) + 1
        ranked = sorted(findings, key=lambda finding: finding.get("disparity_score", 0.0), reverse=True)
        return {
            "audit_id": audit_id,
            "audit": audit,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_findings": len(findings),
                "severity_counts": counts,
                "highest_disparity": ranked[0].get("disparity_score", 0.0) if ranked else 0.0,
                "attributes_affected": sorted({finding.get("attribute", "unknown") for finding in findings}),
            },
            "attribute_summary": attribute_summary,
            "findings": ranked,
            "disclaimer": (
                "Disparity scores are heuristic measurements over paired prompts. They indicate where a "
                "model treats matched requests differently and warrant human review; they are not a legal "
                "determination of discrimination."
            ),
        }

    def build_json(
        self,
        audit_id: str,
        audit: dict[str, Any],
        findings: list[dict[str, Any]],
        attribute_summary: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self._payload(audit_id, audit, findings, attribute_summary)

    def _markdown(self, payload: dict[str, Any]) -> str:
        summary = payload["summary"]
        lines = [
            f"# Bias Audit Report - {payload['audit'].get('name', payload['audit_id'])}",
            "",
            f"- Audit ID: `{payload['audit_id']}`",
            f"- Generated: {payload['generated_at']}",
            f"- Target: {payload['audit'].get('target_name', 'unknown')} ({payload['audit'].get('provider', 'unknown')})",
            f"- Evaluator: {payload['audit'].get('evaluator_id', 'unknown')}",
            "",
            "## Summary",
            "",
            f"- Findings: **{summary['total_findings']}**",
            f"- Highest disparity score: **{summary['highest_disparity']:.3f}**",
            f"- Attributes affected: {', '.join(summary['attributes_affected']) or 'none'}",
            "",
            "| Severity | Count |",
            "| --- | --- |",
        ]
        for severity in SEVERITY_ORDER:
            lines.append(f"| {severity} | {summary['severity_counts'].get(severity, 0)} |")

        lines += ["", "## Coverage By Attribute", "", "| Attribute | Probes run | Findings | Max disparity |", "| --- | --- | --- | --- |"]
        for row in payload["attribute_summary"]:
            lines.append(f"| {row['attribute']} | {row['probes_run']} | {row['findings']} | {row['max_disparity']:.3f} |")

        lines += ["", "## Findings", ""]
        if not payload["findings"]:
            lines.append("No disparity above the warning threshold was measured.")
        for finding in payload["findings"]:
            lines += [
                f"### {finding.get('probe_name', finding.get('probe_id'))}",
                "",
                f"- Attribute: `{finding.get('attribute')}`",
                f"- Severity: **{finding.get('severity')}**",
                f"- Disparity score: **{finding.get('disparity_score'):.3f}** (confidence {finding.get('confidence')})",
                f"- Dominant metric: `{finding.get('dominant_metric', finding.get('metric'))}`",
                f"- Arms compared: {finding.get('arm_count', 0)}",
                "",
                finding.get("summary", ""),
                "",
                "Group measurements:",
                "",
            ]
            for group, value in (finding.get("group_metrics") or {}).items():
                lines.append(f"- `{group}`: {value}")
            lines.append("")
            for warning in finding.get("warnings") or []:
                lines += [f"> **{warning}**", ""]

        lines += ["---", "", payload["disclaimer"], ""]
        return "\n".join(lines)

    def _html(self, payload: dict[str, Any]) -> str:
        summary = payload["summary"]
        rows = "".join(
            f"<tr><td>{html.escape(str(row['attribute']))}</td><td>{row['probes_run']}</td>"
            f"<td>{row['findings']}</td><td>{row['max_disparity']:.3f}</td></tr>"
            for row in payload["attribute_summary"]
        )
        findings = "".join(
            "<article>"
            f"<h3>{html.escape(str(finding.get('probe_name', finding.get('probe_id'))))}</h3>"
            f"<p><strong>{html.escape(str(finding.get('severity')))}</strong> &middot; "
            f"disparity {finding.get('disparity_score'):.3f} &middot; "
            f"attribute {html.escape(str(finding.get('attribute')))}</p>"
            f"<p>{html.escape(str(finding.get('summary', '')))}</p>"
            "</article>"
            for finding in payload["findings"]
        ) or "<p>No disparity above the warning threshold was measured.</p>"

        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bias Audit Report {html.escape(payload['audit_id'])}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 60rem; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #d0d7de; padding: .4rem .6rem; text-align: left; }}
article {{ border-left: 4px solid #d0d7de; padding-left: 1rem; margin: 1rem 0; }}
footer {{ color: #57606a; font-size: .9rem; margin-top: 2rem; }}
</style>
</head>
<body>
<h1>Bias Audit Report</h1>
<p>Audit <code>{html.escape(payload['audit_id'])}</code> &middot; generated {html.escape(payload['generated_at'])}</p>
<h2>Summary</h2>
<ul>
<li>Findings: <strong>{summary['total_findings']}</strong></li>
<li>Highest disparity score: <strong>{summary['highest_disparity']:.3f}</strong></li>
<li>Attributes affected: {html.escape(', '.join(summary['attributes_affected']) or 'none')}</li>
</ul>
<h2>Coverage By Attribute</h2>
<table><thead><tr><th>Attribute</th><th>Probes run</th><th>Findings</th><th>Max disparity</th></tr></thead>
<tbody>{rows}</tbody></table>
<h2>Findings</h2>
{findings}
<footer>{html.escape(payload['disclaimer'])}</footer>
</body>
</html>"""
