#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCM-Exosome PDF报告生成器
支持：单味中药报告、疾病方向报告、平台概览报告
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── 颜色主题 ──
C_PRIMARY   = colors.HexColor("#1a3a5a")
C_ACCENT    = colors.HexColor("#e94560")
C_GREEN     = colors.HexColor("#4ab880")
C_GOLD      = colors.HexColor("#e0904a")
C_BLUE      = colors.HexColor("#4a9ae0")
C_BG        = colors.HexColor("#f0f4f8")
C_DARKBG    = colors.HexColor("#1a2535")
C_TEXT      = colors.HexColor("#2c3e50")
C_LIGHT     = colors.HexColor("#7a9aaa")

def get_styles():
    styles = getSampleStyleSheet()
    custom = {
        "title": ParagraphStyle("title",
            fontSize=24, fontName="Helvetica-Bold",
            textColor=C_PRIMARY, spaceAfter=6, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle",
            fontSize=12, fontName="Helvetica",
            textColor=C_LIGHT, spaceAfter=20, alignment=TA_CENTER),
        "h1": ParagraphStyle("h1",
            fontSize=16, fontName="Helvetica-Bold",
            textColor=C_PRIMARY, spaceBefore=16, spaceAfter=8,
            borderPad=4),
        "h2": ParagraphStyle("h2",
            fontSize=13, fontName="Helvetica-Bold",
            textColor=C_ACCENT, spaceBefore=12, spaceAfter=6),
        "h3": ParagraphStyle("h3",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=C_TEXT, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body",
            fontSize=10, fontName="Helvetica",
            textColor=C_TEXT, spaceAfter=4, leading=14),
        "small": ParagraphStyle("small",
            fontSize=8, fontName="Helvetica",
            textColor=C_LIGHT, spaceAfter=2),
        "tag": ParagraphStyle("tag",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=C_BLUE, spaceAfter=4),
        "caption": ParagraphStyle("caption",
            fontSize=9, fontName="Helvetica-Oblique",
            textColor=C_LIGHT, alignment=TA_CENTER, spaceAfter=8),
    }
    return custom

def divider(color=C_PRIMARY, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=8, spaceBefore=4)

def metric_table(metrics):
    """生成指标卡片表格 [(label, value, color), ...]"""
    cols = min(len(metrics), 4)
    rows = [metrics[i:i+cols] for i in range(0, len(metrics), cols)]
    data = []
    for row in rows:
        data.append([
            Paragraph(f'<font color="{m[2]}" size="18"><b>{m[1]}</b></font><br/>'
                      f'<font color="#7a9aaa" size="8">{m[0]}</font>', 
                      ParagraphStyle("mc", alignment=TA_CENTER, spaceAfter=0))
            for m in row
        ])
    t = Table(data, colWidths=[A4[0]/cols - 20]*cols, rowHeights=50)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_BG),
        ("BOX", (0,0), (-1,-1), 0.5, C_LIGHT),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.white),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t

def header_block(title, subtitle, report_type="中药研究报告"):
    """页眉块"""
    elements = []
    # 顶部色条
    t = Table([[""]], colWidths=[A4[0]-40], rowHeights=6)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), C_PRIMARY)]))
    elements.append(t)
    elements.append(Spacer(1, 12))
    styles = get_styles()
    elements.append(Paragraph("TCM-Exosome Intelligence Platform", styles["small"]))
    elements.append(Paragraph(title, styles["title"]))
    elements.append(Paragraph(subtitle, styles["subtitle"]))
    elements.append(Paragraph(
        f'Report Type: {report_type} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        styles["small"]
    ))
    elements.append(divider(C_ACCENT, 2))
    return elements

# ─────────────────────────────────────────────────────────
# 1. 单味中药报告
# ─────────────────────────────────────────────────────────
def generate_herb_report(herb_name, herb_gene_df, herb_disease_df, herb_pathway_df, papers_df):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm)
    styles = get_styles()
    story = []

    # ── 封面 ──
    story += header_block(
        herb_name,
        "Traditional Chinese Medicine × Exosome Research Profile",
        "单味中药研究报告"
    )

    # ── 关键指标 ──
    genes = herb_gene_df[herb_gene_df["herb_name"]==herb_name] if not herb_gene_df.empty else []
    diseases = herb_disease_df[herb_disease_df["herb_name"]==herb_name] if not herb_disease_df.empty else []
    pathways = herb_pathway_df[herb_pathway_df["herb_name"]==herb_name] if not herb_pathway_df.empty else []

    # 相关文献
    rel_papers = []
    if not papers_df.empty:
        hn_simple = herb_name.split()[0].lower()
        mask = papers_df["title"].str.lower().str.contains(hn_simple, na=False)
        if "abstract" in papers_df.columns:
            mask |= papers_df["abstract"].str.lower().str.contains(hn_simple, na=False)
        rel_papers = papers_df[mask].head(10)

    n_genes = len(genes) if hasattr(genes, '__len__') else 0
    n_diseases = len(diseases) if hasattr(diseases, '__len__') else 0
    n_pathways = len(pathways) if hasattr(pathways, '__len__') else 0
    n_papers = len(rel_papers)

    story.append(metric_table([
        ("Related Genes",     str(n_genes),    "#4a9ae0"),
        ("Disease Relations", str(n_diseases), "#e94560"),
        ("Pathways",          str(n_pathways), "#e0b44a"),
        ("Literature",        str(n_papers),   "#4ab880"),
    ]))
    story.append(Spacer(1, 12))

    # ── 基因关联 ──
    if n_genes > 0:
        story.append(Paragraph("Gene Interaction Network", styles["h1"]))
        story.append(divider())
        gene_data = [["Gene Symbol", "Interaction Type", "Mechanism", "Confidence"]]
        for _, row in genes.iterrows():
            conf = row.get("confidence_score", 0)
            conf_color = "#4ab880" if conf >= 0.85 else "#e0904a" if conf >= 0.75 else "#e94560"
            gene_data.append([
                Paragraph(f'<b>{row.get("gene_symbol","")}</b>', styles["body"]),
                Paragraph(str(row.get("interaction_type","")), styles["body"]),
                Paragraph(str(row.get("mechanism",""))[:60], styles["body"]),
                Paragraph(f'<font color="{conf_color}"><b>{conf:.2f}</b></font>', styles["body"]),
            ])
        t = Table(gene_data, colWidths=[60, 80, 230, 60])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_PRIMARY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, C_LIGHT),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ── 疾病关联 ──
    if n_diseases > 0:
        story.append(Paragraph("Disease Association Profile", styles["h1"]))
        story.append(divider(C_ACCENT))
        dis_data = [["Disease", "Effect", "Mechanism", "Evidence", "Score"]]
        for _, row in diseases.iterrows():
            dis_data.append([
                Paragraph(f'<b>{row.get("disease","")}</b>', styles["body"]),
                Paragraph(str(row.get("effect",""))[:40], styles["body"]),
                Paragraph(str(row.get("mechanism",""))[:50], styles["body"]),
                Paragraph(str(row.get("evidence_level","")), styles["body"]),
                Paragraph(f'{row.get("confidence_score",0):.2f}', styles["body"]),
            ])
        t = Table(dis_data, colWidths=[65, 90, 130, 55, 45])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_ACCENT),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, C_LIGHT),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ── 通路关联 ──
    if n_pathways > 0:
        story.append(Paragraph("Signaling Pathway Regulation", styles["h1"]))
        story.append(divider(C_GOLD))
        path_data = [["Pathway", "KEGG ID", "Regulation", "Key Genes", "Score"]]
        for _, row in pathways.iterrows():
            reg = str(row.get("regulation",""))
            reg_color = "#4ab880" if "激活" in reg else "#e94560" if "抑制" in reg else "#4a9ae0"
            path_data.append([
                Paragraph(str(row.get("pathway_name",""))[:30], styles["body"]),
                Paragraph(str(row.get("pathway_id","")), styles["small"]),
                Paragraph(f'<font color="{reg_color}"><b>{reg}</b></font>', styles["body"]),
                Paragraph(str(row.get("key_genes",""))[:40], styles["small"]),
                Paragraph(f'{row.get("confidence_score",0):.2f}', styles["body"]),
            ])
        t = Table(path_data, colWidths=[120, 60, 60, 120, 45])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_GOLD),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, C_LIGHT),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    # ── 相关文献 ──
    if n_papers > 0:
        story.append(PageBreak())
        story.append(Paragraph("Related Literature", styles["h1"]))
        story.append(divider(C_GREEN))
        for i, (_, row) in enumerate(rel_papers.iterrows(), 1):
            title = str(row.get("title",""))[:120]
            authors = str(row.get("authors",""))[:80]
            pub_date = str(row.get("pub_date",""))[:7]
            source = str(row.get("source",""))
            url = str(row.get("url",""))
            story.append(KeepTogether([
                Paragraph(f'<b>{i}. {title}</b>', styles["body"]),
                Paragraph(f'{authors} | {source} | {pub_date}', styles["small"]),
                Paragraph(f'<link href="{url}" color="#4a9ae0">{url}</link>' if url else "", styles["small"]),
                Spacer(1, 4),
            ]))

    # ── 页脚 ──
    story.append(Spacer(1, 20))
    story.append(divider(C_LIGHT, 0.5))
    story.append(Paragraph(
        f"TCM-Exosome Intelligence Platform | {datetime.now().strftime('%Y-%m-%d')} | "
        f"Data Source: PubMed, EuropePMC, Journal of Extracellular Vesicles, etc.",
        styles["small"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────────────────
# 2. 平台概览报告
# ─────────────────────────────────────────────────────────
def generate_overview_report(papers_df, herb_gene_df, trials_df, cargo_df, pathway_df):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm)
    styles = get_styles()
    story = []

    story += header_block(
        "TCM-Exosome Platform Overview",
        f"Research Intelligence Summary | {datetime.now().strftime('%B %Y')}",
        "平台概览报告"
    )

    # 总体指标
    n_papers  = len(papers_df)  if not papers_df.empty  else 0
    n_herbs   = len(papers_df["source"].unique()) if not papers_df.empty and "source" in papers_df.columns else 0
    n_genes   = len(herb_gene_df) if not herb_gene_df.empty else 0
    n_trials  = len(trials_df) if not trials_df.empty else 0
    n_cargo   = len(cargo_df)  if not cargo_df.empty  else 0
    n_pathways= len(pathway_df) if not pathway_df.empty else 0

    story.append(metric_table([
        ("Total Papers",    f"{n_papers:,}",   "#4a9ae0"),
        ("Herb-Gene Links", f"{n_genes:,}",    "#4ab880"),
        ("Clinical Trials", f"{n_trials:,}",   "#e94560"),
        ("EV Cargo",        f"{n_cargo:,}",    "#e0904a"),
    ]))
    story.append(Spacer(1, 8))
    story.append(metric_table([
        ("KEGG Pathways",   f"{n_pathways:,}", "#9b59b6"),
        ("Journal Sources", f"{n_herbs}",      "#1abc9c"),
        ("TCM Herbs",       "100",             "#e67e22"),
        ("Languages",       "EN/CN/JP/RU",     "#3498db"),
    ]))
    story.append(Spacer(1, 12))

    # 文献来源分布
    if not papers_df.empty and "source" in papers_df.columns:
        story.append(Paragraph("Literature Source Distribution", styles["h1"]))
        story.append(divider())
        src = papers_df["source"].value_counts().head(15).reset_index()
        src.columns = ["Source", "Count"]
        src_data = [["Journal / Source", "Papers", "Proportion"]]
        total = src["Count"].sum()
        for _, row in src.iterrows():
            pct = row["Count"] / total * 100
            bar = "█" * int(pct / 2) + "░" * (25 - int(pct/2))
            src_data.append([
                Paragraph(str(row["Source"])[:55], styles["body"]),
                Paragraph(f'<b>{row["Count"]}</b>', styles["body"]),
                Paragraph(f'{bar} {pct:.1f}%', styles["small"]),
            ])
        t = Table(src_data, colWidths=[210, 60, 160])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_PRIMARY),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, C_LIGHT),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Top herbs by gene count
    if not herb_gene_df.empty and "herb_name" in herb_gene_df.columns:
        story.append(Paragraph("Top Herbs by Gene Association Count", styles["h1"]))
        story.append(divider(C_GREEN))
        top_herbs = herb_gene_df.groupby("herb_name").size().sort_values(ascending=False).head(20)
        herb_data = [["Herb Name", "Gene Count", "Visualization"]]
        max_cnt = top_herbs.max()
        for herb, cnt in top_herbs.items():
            bar = "█" * int(cnt / max_cnt * 20)
            herb_data.append([
                Paragraph(str(herb), styles["body"]),
                Paragraph(f'<b>{cnt}</b>', styles["body"]),
                Paragraph(f'<font color="#4a9ae0">{bar}</font>', styles["small"]),
            ])
        t = Table(herb_data, colWidths=[180, 80, 170])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_GREEN),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, C_LIGHT),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(t)

    story.append(Spacer(1, 20))
    story.append(divider(C_LIGHT, 0.5))
    story.append(Paragraph(
        f"TCM-Exosome Intelligence Platform | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["small"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf
