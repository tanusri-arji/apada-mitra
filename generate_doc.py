import markdown

with open(r'C:\Users\Tanusri\.gemini\antigravity-ide\brain\094442c4-c120-47f2-8e30-cd6094bee60f\apada_mitra_full_audit.md', 'r', encoding='utf-8') as f:
    text = f.read()

html = markdown.markdown(text, extensions=['tables', 'fenced_code'])

doc = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>APADA MITRA FINAL AUDIT REPORT</title>
<style>
    body {{
        font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 40px;
    }}
    h1, h2, h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 30px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 14px; page-break-inside: auto; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    th {{ background-color: #f8f9fa; font-weight: bold; }}
    tr {{ page-break-inside: avoid; page-break-after: auto; }}
    pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
    @media print {{
        body {{ max-width: 100%; padding: 0; }}
        a {{ text-decoration: none; color: black; }}
        .page-break {{ page-break-before: always; }}
    }}
</style>
</head>
<body>
<div style="text-align: center; margin-bottom: 50px;">
    <h1 style="border: none;">APADA MITRA</h1>
    <h2 style="border: none; margin-top: 0;">Final Project Audit Report</h2>
    <p>Generated based on complete codebase forensics.</p>
    <p><em>Confidential Internal Audit</em></p>
</div>
{html}
</body>
</html>'''

with open('APADA_MITRA_AUDIT_REPORT.html', 'w', encoding='utf-8') as f:
    f.write(doc)
print("Success!")
