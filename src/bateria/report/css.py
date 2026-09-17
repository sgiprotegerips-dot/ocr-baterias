"""Hoja de estilos del informe carta imprimible."""

REPORT_CSS = r"""
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: letter portrait; margin: 12mm 14mm; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #0f172a; background: #e2e8f0; line-height: 1.45; font-size: 10pt;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.print-toolbar {
    position: sticky; top: 0; z-index: 9999; background: #0f172a; color: #f8fafc;
    padding: 10px 20px; display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 16px rgba(0,0,0,.25); font-size: 9pt;
}
.toolbar-info { display: flex; align-items: center; gap: 12px; }
.toolbar-brand { font-weight: 700; letter-spacing: .5px; color: #14b8a6; }
.toolbar-badge { padding: 3px 8px; border-radius: 4px; font-size: 7.5pt; font-weight: 600; text-transform: uppercase; }
.toolbar-badge.sealed { background: rgba(20,184,166,.2); color: #2dd4bf; border: 1px solid rgba(20,184,166,.4); }
.toolbar-badge.draft { background: rgba(245,158,11,.2); color: #fbbf24; border: 1px solid rgba(245,158,11,.4); }
.toolbar-tip { color: #94a3b8; font-size: 8pt; }
.toolbar-actions { display: flex; gap: 10px; }
.btn-print-primary {
    background: #0f766e; color: #fff; border: 1px solid #14b8a6; padding: 7px 16px;
    border-radius: 6px; font-weight: 600; font-size: 8.5pt; cursor: pointer;
}
.btn-print-ghost {
    background: transparent; color: #cbd5e1; border: 1px solid #334155; padding: 7px 14px;
    border-radius: 6px; font-size: 8.5pt; cursor: pointer; text-decoration: none;
}
.report-page {
    width: 216mm; min-height: 279mm; margin: 16px auto; background: #fff;
    padding: 14mm 16mm 16mm; box-shadow: 0 8px 24px rgba(0,0,0,.08);
    position: relative; page-break-after: always; break-after: page;
}
.report-page:last-child { page-break-after: avoid; break-after: avoid; margin-bottom: 40px; }
.header-box {
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 2.5px solid #0f766e; padding-bottom: 10px; margin-bottom: 14px;
}
.ips-data h2 { font-size: 12pt; color: #0f766e; letter-spacing: .4px; margin-bottom: 2px; }
.ips-data p { font-size: 8pt; color: #475569; line-height: 1.3; }
.title-data { text-align: right; }
.title-data h1 { font-size: 11pt; color: #0f172a; margin-bottom: 2px; }
.title-data span { font-size: 7.5pt; color: #64748b; text-transform: uppercase; letter-spacing: .4px; }
.section-hdr {
    font-size: 10pt; color: #0f766e; border-left: 4px solid #0f766e; padding-left: 8px;
    margin: 12px 0 8px; text-transform: uppercase; letter-spacing: .35px; font-weight: 700;
}
.section-hdr.sub { font-size: 9pt; color: #334155; border-left-color: #94a3b8; text-transform: none; }
.prose { font-size: 8.6pt; color: #1e293b; text-align: justify; line-height: 1.5; margin-bottom: 8px; }
.prose p { margin-bottom: 7px; }
.muted { color: #64748b; font-size: 8pt; }
.table-meta { width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 8.2pt; }
.table-meta td { padding: 4px 7px; border: 1px solid #cbd5e1; vertical-align: middle; }
.table-meta td.label { background: #f8fafc; font-weight: 700; width: 24%; color: #334155; }
.data-table { width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 8pt; }
.data-table thead th {
    background: #f1f5f9; color: #1e293b; padding: 5px 3px; text-align: center;
    border: 1px solid #94a3b8; font-size: 7pt; text-transform: uppercase; font-weight: 700;
}
.data-table thead th.dim-col { text-align: left; width: 40%; padding-left: 7px; }
.data-table tbody td { padding: 4px 5px; border: 1px solid #e2e8f0; vertical-align: middle; }
.data-table tbody td.num { text-align: center; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 8pt; }
.val-none { color: #047857; } .val-low { color: #1d4ed8; } .val-med { color: #b45309; }
.val-high { color: #c2410c; font-weight: 700; background: #fff7ed; }
.val-vhigh { color: #b91c1c; font-weight: 800; background: #fef2f2; }
.data-table tr.critico { background: #fffbeb; }
.badge-critico {
    display: inline-block; font-size: 6.5pt; font-weight: 700; color: #b91c1c;
    background: #fef2f2; border: 1px solid #fecaca; padding: 1px 4px; border-radius: 3px; margin-left: 4px;
}
.clinical-prose {
    background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 10px 12px;
    font-size: 8.4pt; line-height: 1.5; color: #1e293b; margin-bottom: 10px;
    white-space: pre-line; text-align: justify;
}
.cover {
    display: flex; flex-direction: column; justify-content: space-between; min-height: 240mm;
}
.cover-kicker { font-size: 8pt; letter-spacing: 2px; text-transform: uppercase; color: #0f766e; font-weight: 700; }
.cover h1 { font-size: 22pt; line-height: 1.15; color: #0f172a; margin: 12px 0 8px; }
.cover h2 { font-size: 14pt; color: #0f766e; font-weight: 600; margin-bottom: 18px; }
.cover-meta { font-size: 10pt; color: #334155; line-height: 1.6; }
.cover-stamp {
    border: 2px solid #0f766e; padding: 10px 14px; display: inline-block; color: #0f766e;
    font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 9pt;
}
.toc-table td { padding: 3px 6px; border-bottom: 1px dotted #cbd5e1; font-size: 8.5pt; }
.toc-table td.num { text-align: right; width: 40px; font-variant-numeric: tabular-nums; color: #0f766e; font-weight: 700; }
.bar-legend { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 8px; font-size: 7.5pt; color: #475569; }
.leg-chip { display: inline-flex; align-items: center; gap: 4px; }
.leg-chip i { width: 10px; height: 10px; display: inline-block; border-radius: 2px; }
.bar-svg, .hbar-svg { display: block; margin: 4px 0 8px; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 8px 0 12px; }
.kpi { border: 1px solid #cbd5e1; border-radius: 4px; padding: 8px; background: #f8fafc; }
.kpi .k { font-size: 7.5pt; color: #64748b; text-transform: uppercase; letter-spacing: .3px; }
.kpi .v { font-size: 14pt; font-weight: 700; color: #0f766e; }
.dim-block { margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; }
.dim-block h3 { font-size: 10pt; color: #0f172a; margin-bottom: 4px; }
.signatures-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 28px; }
.sig-box { border-top: 1.5px solid #334155; padding-top: 8px; font-size: 8pt; line-height: 1.4; }
.sig-box strong { display: block; font-size: 9pt; margin-bottom: 2px; }
.custody-certificate {
    background: #f0fdfa; border: 1.5px solid #0f766e; border-radius: 6px; padding: 12px 14px;
    margin-top: 16px; font-size: 7.5pt; color: #134e4a; line-height: 1.4;
}
.custody-certificate h4 { font-size: 8.5pt; color: #0f766e; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
.custody-hash-code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 7.5pt;
    background: #fff; padding: 3px 6px; border: 1px solid #99f6e4; border-radius: 3px;
    word-break: break-all; display: block; margin-top: 4px; color: #042f2e; font-weight: 600;
}
.page-footer {
    position: absolute; bottom: 8mm; left: 16mm; right: 16mm; display: flex;
    justify-content: space-between; font-size: 7pt; color: #94a3b8;
    border-top: 1px solid #e2e8f0; padding-top: 3px;
}
.ol-legal { margin: 0 0 8px 16px; font-size: 8.5pt; color: #1e293b; }
.ol-legal li { margin-bottom: 5px; }
@media print {
    html, body { background: #fff !important; padding: 0 !important; margin: 0 !important; }
    .print-toolbar { display: none !important; }
    .report-page {
        margin: 0 !important; padding: 0 !important; box-shadow: none !important;
        border: none !important; width: 100% !important; min-height: auto !important;
        page-break-after: always !important; break-after: page !important;
    }
    .report-page:last-child { page-break-after: avoid !important; break-after: avoid !important; }
    thead { display: table-header-group; }
    tr, .signatures-grid, .custody-certificate, .dim-block { page-break-inside: avoid; break-inside: avoid; }
    .page-footer { position: relative !important; bottom: auto !important; margin-top: 10px !important; }
}
"""
