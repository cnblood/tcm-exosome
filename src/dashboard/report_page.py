#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成页面
集成到 src/dashboard/report_page.py
"""
import streamlit as st
import pandas as pd
import io
import sys, os
sys.path.insert(0, "/app")

def render_report_page(papers_df, herb_gene_df, trials_df, cargo_df, pathway_df,
                       herb_disease_df=None, herb_pathway_df=None):

    st.markdown("""<div style="background:linear-gradient(135deg,#0d1117,#1a2535);
        border:1px solid #2a4a3a;border-radius:16px;padding:24px;margin-bottom:20px">
        <div style="font-size:1.5rem;font-weight:800;color:#e8d5b7">📊 PDF报告生成</div>
        <div style="color:#6a9a8a;font-size:0.85rem;margin-top:4px">
            一键生成专业研究报告 — 单味中药 / 疾病方向 / 平台概览
        </div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🌿 单味中药报告", "📈 平台概览报告"])

    # ── Tab1: 单味中药 ──
    with tab1:
        st.markdown("### 选择中药生成研究报告")

        # 获取中药列表
        herbs = []
        if herb_disease_df is not None and not herb_disease_df.empty and "herb_name" in herb_disease_df.columns:
            herbs = sorted(herb_disease_df["herb_name"].unique().tolist())
        elif not herb_gene_df.empty and "herb_name" in herb_gene_df.columns:
            herbs = sorted(herb_gene_df["herb_name"].unique().tolist())

        if not herbs:
            st.warning("暂无中药数据")
            return

        col1, col2 = st.columns([2, 1])
        with col1:
            selected_herb = st.selectbox("选择中药", herbs, key="report_herb")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_btn = st.button("🖨️ 生成PDF报告", key="gen_herb_report",
                                     use_container_width=True, type="primary")

        if selected_herb:
            # 预览数据
            g_df = herb_gene_df[herb_gene_df["herb_name"]==selected_herb] if not herb_gene_df.empty else pd.DataFrame()
            d_df = herb_disease_df[herb_disease_df["herb_name"]==selected_herb] if herb_disease_df is not None and not herb_disease_df.empty else pd.DataFrame()
            p_df = herb_pathway_df[herb_pathway_df["herb_name"]==selected_herb] if herb_pathway_df is not None and not herb_pathway_df.empty else pd.DataFrame()

            # 文献
            rel_papers = pd.DataFrame()
            if not papers_df.empty:
                hn = selected_herb.split()[0].lower()
                mask = papers_df["title"].str.lower().str.contains(hn, na=False)
                if "abstract" in papers_df.columns:
                    mask |= papers_df["abstract"].str.lower().str.contains(hn, na=False)
                rel_papers = papers_df[mask]

            # 预览指标
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🧬 基因关联", len(g_df))
            m2.metric("🔴 疾病关联", len(d_df))
            m3.metric("🟡 通路关联", len(p_df))
            m4.metric("📄 相关文献", len(rel_papers))

            if generate_btn:
                with st.spinner("正在生成PDF报告..."):
                    try:
                        from src.dashboard.pdf_report import generate_herb_report
                        buf = generate_herb_report(
                            selected_herb, herb_gene_df, d_df, p_df, rel_papers
                        )
                        st.success("✅ 报告生成成功！")
                        st.download_button(
                            label=f"⬇️ 下载 {selected_herb} 研究报告.pdf",
                            data=buf,
                            file_name=f"TCM_{selected_herb.replace(' ','_')}_Report.pdf",
                            mime="application/pdf",
                            key="dl_herb_pdf",
                        )
                    except Exception as e:
                        st.error(f"生成失败: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    # ── Tab2: 平台概览 ──
    with tab2:
        st.markdown("### 平台研究数据概览报告")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📄 总文献", f"{len(papers_df):,}" if not papers_df.empty else "0")
        m2.metric("🧬 基因关联", f"{len(herb_gene_df):,}" if not herb_gene_df.empty else "0")
        m3.metric("⚕️ 临床试验", f"{len(trials_df):,}" if not trials_df.empty else "0")
        m4.metric("🔗 通路", f"{len(pathway_df):,}" if not pathway_df.empty else "0")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ 生成平台概览PDF", key="gen_overview", type="primary"):
            with st.spinner("正在生成概览报告..."):
                try:
                    from src.dashboard.pdf_report import generate_overview_report
                    buf = generate_overview_report(
                        papers_df, herb_gene_df, trials_df, cargo_df, pathway_df
                    )
                    st.success("✅ 报告生成成功！")
                    st.download_button(
                        label="⬇️ 下载平台概览报告.pdf",
                        data=buf,
                        file_name=f"TCM_Exosome_Overview_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        key="dl_overview_pdf",
                    )
                except Exception as e:
                    st.error(f"生成失败: {e}")
                    import traceback
                    st.code(traceback.format_exc())
