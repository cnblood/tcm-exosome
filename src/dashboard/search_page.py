# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import os, re, json
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=1800)
def load_table(table):
    client = get_supabase()
    if not client:
        return pd.DataFrame()
    all_data = []
    try:
        for i in range(0, 10000, 1000):
            res = client.table(table).select("*").range(i, i+999).execute()
            if not res.data: break
            all_data.extend(res.data)
            if len(res.data) < 1000: break
        return pd.DataFrame(all_data)
    except:
        return pd.DataFrame()

def highlight_text(text, query):
    """高亮关键词"""
    if not text or not query:
        return str(text)[:200]
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    snippet = str(text)[:300]
    highlighted = pattern.sub(
        lambda m: f"**{m.group()}**", snippet
    )
    return highlighted

def search_papers(df, query, field="all"):
    """搜索文献"""
    if df.empty or not query:
        return pd.DataFrame()
    query_lower = query.lower()
    mask = pd.Series([False] * len(df), index=df.index)
    if field in ("all", "title") and "title" in df.columns:
        mask |= df["title"].str.lower().str.contains(query_lower, na=False)
    if field in ("all", "abstract") and "abstract" in df.columns:
        mask |= df["abstract"].str.lower().str.contains(query_lower, na=False)
    if field in ("all", "keywords") and "keywords" in df.columns:
        mask |= df["keywords"].str.lower().str.contains(query_lower, na=False)
    if field in ("all", "authors") and "authors" in df.columns:
        mask |= df["authors"].str.lower().str.contains(query_lower, na=False)
    return df[mask].copy()

def search_herbs(df, query):
    """搜索药典"""
    if df.empty or not query:
        return pd.DataFrame()
    query_lower = query.lower()
    mask = pd.Series([False] * len(df), index=df.index)
    for col in ["name_cn", "name_latin", "pinyin", "functions", "flavor", "nature", "meridian", "active_compounds", "category"]:
        if col in df.columns:
            mask |= df[col].astype(str).str.lower().str.contains(query_lower, na=False)
    return df[mask].copy()

def search_genes(df, query):
    """搜索基因关联"""
    if df.empty or not query:
        return pd.DataFrame()
    query_lower = query.lower()
    mask = pd.Series([False] * len(df), index=df.index)
    for col in ["herb_name", "gene_symbol", "interaction_type", "mechanism"]:
        if col in df.columns:
            mask |= df[col].astype(str).str.lower().str.contains(query_lower, na=False)
    return df[mask].copy()

def search_formulas(df, query):
    """搜索成方制剂"""
    if df.empty or not query:
        return pd.DataFrame()
    query_lower = query.lower()
    mask = pd.Series([False] * len(df), index=df.index)
    for col in ["name_cn", "functions", "category"]:
        if col in df.columns:
            mask |= df[col].astype(str).str.lower().str.contains(query_lower, na=False)
    return df[mask].copy()

def render_search():
    st.markdown("""<style>
    .search-header{background:linear-gradient(135deg,#0d1117,#1a2535);border:1px solid #2a3a5a;
        border-radius:16px;padding:28px;margin-bottom:20px;}
    .search-title{font-size:1.8rem;font-weight:700;color:#e8d5b7;margin:0 0 6px 0;}
    .result-card{background:#0d1a2a;border:1px solid #1e3a5a;border-radius:10px;
        padding:14px 16px;margin:8px 0;transition:border-color 0.2s;}
    .result-card:hover{border-color:#4a9ae0;}
    .result-source{display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;}
    .src-paper{background:rgba(74,154,224,0.15);color:#4a9ae0;}
    .src-herb{background:rgba(74,184,128,0.15);color:#4ab880;}
    .src-gene{background:rgba(233,69,96,0.15);color:#e94560;}
    .src-formula{background:rgba(160,74,224,0.15);color:#a04ae0;}
    .result-count{font-size:0.85rem;color:#6a8a9a;margin:4px 0 12px 0;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""<div class="search-header">
        <div class="search-title">🔍 全库检索</div>
        <div style="color:#6a9a8a;font-size:0.88rem">跨文献 · 药典 · 基因靶点 · 成方制剂 · 一键搜索</div>
    </div>""", unsafe_allow_html=True)

    # 搜索框
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input("", placeholder="输入关键词：如 curcumin / 姜黄素 / VEGFA / 肿瘤 / 活血...",
                              label_visibility="collapsed", key="global_search")
    with col_btn:
        do_search = st.button("搜索", type="primary", use_container_width=True)

    # 高级选项
    with st.expander("⚙️ 搜索范围", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        search_papers_cb = c1.checkbox("📄 文献", value=True)
        search_herbs_cb = c2.checkbox("🌿 药典药材", value=True)
        search_genes_cb = c3.checkbox("🧬 基因关联", value=True)
        search_formulas_cb = c4.checkbox("💊 成方制剂", value=True)
        field_opt = st.radio("文献搜索范围", ["全部字段", "标题", "摘要", "作者"], horizontal=True)
        field_map = {"全部字段": "all", "标题": "title", "摘要": "abstract", "作者": "authors"}

    if not query and not do_search:
        # 展示搜索建议
        st.markdown("#### 💡 热门搜索")
        suggestions = ["curcumin", "exosome", "VEGFA", "astragalus", "inflammation",
                       "姜黄素", "黄芪", "丹参", "活血化瘀", "肿瘤", "berberine", "ginger"]
        cols = st.columns(6)
        for i, s in enumerate(suggestions):
            cols[i % 6].code(s)
        return

    if not query:
        st.warning("请输入搜索关键词")
        return

    # 加载数据
    with st.spinner(f"正在全库检索「{query}」..."):
        papers_df = load_table("research_papers") if search_papers_cb else pd.DataFrame()
        herbs_df = load_table("tcm_single_herb") if search_herbs_cb else pd.DataFrame()
        gene_df = load_table("herb_gene_relations") if search_genes_cb else pd.DataFrame()
        formula_df = load_table("tcm_compound_formula") if search_formulas_cb else pd.DataFrame()

        r_papers = search_papers(papers_df, query, field_map.get(field_opt, "all"))
        r_herbs = search_herbs(herbs_df, query)
        r_genes = search_genes(gene_df, query)
        r_formulas = search_formulas(formula_df, query)

    total = len(r_papers) + len(r_herbs) + len(r_genes) + len(r_formulas)

    if total == 0:
        st.warning(f"未找到与「{query}」相关的结果，请尝试其他关键词")
        return

    # 结果概览
    st.markdown(f"### 找到 **{total}** 条结果")
    ov1, ov2, ov3, ov4 = st.columns(4)
    ov1.metric("📄 文献", len(r_papers))
    ov2.metric("🌿 药材", len(r_herbs))
    ov3.metric("🧬 基因关联", len(r_genes))
    ov4.metric("💊 成方制剂", len(r_formulas))

    # 结果分布图
    if total > 0:
        dist_data = pd.DataFrame({
            "来源": ["文献", "药材", "基因关联", "成方制剂"],
            "数量": [len(r_papers), len(r_herbs), len(r_genes), len(r_formulas)],
            "颜色": ["#4a9ae0", "#4ab880", "#e94560", "#a04ae0"]
        })
        dist_data = dist_data[dist_data["数量"] > 0]
        fig = px.bar(dist_data, x="来源", y="数量", color="来源",
                     color_discrete_map={"文献":"#4a9ae0","药材":"#4ab880","基因关联":"#e94560","成方制剂":"#a04ae0"},
                     height=200)
        fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white",
                          margin=dict(t=10,b=10,l=0,r=0), showlegend=False,
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    # 分Tab展示结果
    tabs = []
    tab_labels = []
    if len(r_papers) > 0: tab_labels.append(f"📄 文献 ({len(r_papers)})")
    if len(r_herbs) > 0: tab_labels.append(f"🌿 药材 ({len(r_herbs)})")
    if len(r_genes) > 0: tab_labels.append(f"🧬 基因关联 ({len(r_genes)})")
    if len(r_formulas) > 0: tab_labels.append(f"💊 成方制剂 ({len(r_formulas)})")

    if not tab_labels:
        return

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    # 文献结果
    if len(r_papers) > 0:
        with tabs[tab_idx]:
            tab_idx += 1
            c_cap, c_dl = st.columns([4, 1])
            c_cap.caption(f"共 {len(r_papers)} 篇文献包含「{query}」")
            export_cols = [c for c in ["title","authors","abstract","pub_date","source","doi","pmid","url"] if c in r_papers.columns]
            c_dl.download_button("⬇️ 导出", r_papers[export_cols].to_csv(index=False).encode("utf-8-sig"),
                                 f"search_{query}_papers.csv", "text/csv", key="dl_search_papers")

            r_papers_show = r_papers.sort_values("pub_date", ascending=False) if "pub_date" in r_papers.columns else r_papers
            for _, row in r_papers_show.head(50).iterrows():
                title = row.get("title", "")
                authors = row.get("authors", "")[:60] + "..." if len(str(row.get("authors",""))) > 60 else row.get("authors","")
                pub_date = row.get("pub_date", "")
                source = row.get("source", "")
                abstract = row.get("abstract", "")
                url = row.get("url", "")

                snippet = ""
                if abstract and len(abstract) > 10:
                    idx = abstract.lower().find(query.lower())
                    if idx >= 0:
                        start = max(0, idx - 80)
                        end = min(len(abstract), idx + 120)
                        snippet = "..." + abstract[start:end] + "..."

                link = f" · [🔗]({url})" if url else ""
                st.markdown(f"""<div class="result-card">
                    <span class="result-source src-paper">📄 {source}</span>
                    <span style="color:#aaa;font-size:0.75rem;margin-left:8px">{pub_date}</span>
                    <div style="font-weight:600;color:#e8d5b7;margin:6px 0 2px 0">{title[:120]}{link}</div>
                    <div style="color:#7a9aaa;font-size:0.78rem">{authors}</div>
                    {"<div style='color:#6a8a9a;font-size:0.78rem;margin-top:4px;font-style:italic'>" + snippet + "</div>" if snippet else ""}
                </div>""", unsafe_allow_html=True)

    # 药材结果
    if len(r_herbs) > 0:
        with tabs[tab_idx]:
            tab_idx += 1
            st.caption(f"共 {len(r_herbs)} 味药材包含「{query}」")
            show_cols = [c for c in ["name_cn","name_latin","category","nature","flavor","meridian","functions","active_compounds","data_level"] if c in r_herbs.columns]
            col_config = {
                "name_cn": st.column_config.TextColumn("药材名", width=80),
                "name_latin": st.column_config.TextColumn("拉丁学名", width=180),
                "category": st.column_config.TextColumn("分类", width=80),
                "nature": st.column_config.TextColumn("药性", width=60),
                "flavor": st.column_config.TextColumn("药味", width=80),
                "meridian": st.column_config.TextColumn("归经", width=150),
                "functions": st.column_config.TextColumn("功效", width=250),
                "active_compounds": st.column_config.TextColumn("活性成分", width=200),
                "data_level": st.column_config.TextColumn("层级", width=70),
            }
            st.dataframe(r_herbs[show_cols], use_container_width=True, hide_index=True, column_config=col_config)

    # 基因关联结果
    if len(r_genes) > 0:
        with tabs[tab_idx]:
            tab_idx += 1
            st.caption(f"共 {len(r_genes)} 条基因关联包含「{query}」")
            show_cols = [c for c in ["herb_name","gene_symbol","interaction_type","mechanism","confidence_score"] if c in r_genes.columns]
            st.dataframe(r_genes[show_cols].rename(columns={
                "herb_name":"中药","gene_symbol":"基因","interaction_type":"互作类型",
                "mechanism":"机制","confidence_score":"置信度"
            }), use_container_width=True, hide_index=True)

    # 成方制剂结果
    if len(r_formulas) > 0:
        with tabs[tab_idx]:
            tab_idx += 1
            st.caption(f"共 {len(r_formulas)} 条成方制剂包含「{query}」")
            show_cols = [c for c in ["name_cn","category","functions","data_level"] if c in r_formulas.columns]
            st.dataframe(r_formulas[show_cols], use_container_width=True, hide_index=True)
