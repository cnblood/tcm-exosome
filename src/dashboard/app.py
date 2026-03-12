import streamlit as st
import pandas as pd
import io
import plotly.express as px
import os, sys
sys.path.insert(0, "/app")
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="TCM-Exosome", page_icon="🧬", layout="wide")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

st.markdown("""<style>
.mc{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #0f3460;border-radius:12px;padding:20px;text-align:center;color:white;}
.mv{font-size:2.2rem;font-weight:bold;color:#e94560;}
.ml{font-size:0.9rem;color:#a8b2d8;margin-top:5px;}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=600)
def load_table(table_name):
    client = get_supabase()
    if not client:
        return pd.DataFrame()
    all_data = []
    try:
        for i in range(0, 10000, 1000):
            res = client.table(table_name).select("*").range(i, i+999).execute()
            if not res.data:
                break
            all_data.extend(res.data)
            if len(res.data) < 1000:
                break
        return pd.DataFrame(all_data)
    except:
        return pd.DataFrame()

def add_bookmark(paper_id, importance, notes, tag="default"):
    client = get_supabase()
    if not client: return False
    try:
        client.table("user_bookmarks").upsert({
            "paper_id": paper_id,
            "importance": importance,
            "notes": notes,
            "user_tag": tag,
        }, on_conflict="paper_id,user_tag").execute()
        return True
    except: return False

def remove_bookmark(paper_id, tag="default"):
    client = get_supabase()
    if not client: return False
    try:
        client.table("user_bookmarks").delete().eq("paper_id", paper_id).eq("user_tag", tag).execute()
        return True
    except: return False

with st.sidebar:
    st.markdown("## TCM-Exosome")
    st.markdown("---")
    page = st.radio("Navigation", [
        "Overview", "🔍 Search", "Literature", "Clinical Trials",
        "Genomics", "Pharmacopoeia", "Knowledge Graph", "📊 Reports", "Crawler Status",
    ])
    st.markdown("---")
    st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

papers_df = load_table("research_papers")
trials_df = load_table("clinical_trials")
herb_gene_df = load_table("herb_gene_relations")
mirna_df = load_table("mirna")
cargo_df = load_table("exosome_cargo")
pathway_df = load_table("pathway_enrichment")
herb_disease_df = load_table("herb_disease_relations")
herb_pathway_df = load_table("herb_pathway_relations")

if page == "🔍 Search":
    from src.dashboard.search_page import render_search
    render_search()

elif page == "Overview":
    # Hero header
    st.markdown("""<div style="background:linear-gradient(135deg,#0d1117,#1a2535,#0d2020);
        border:1px solid #2a4a3a;border-radius:16px;padding:32px;margin-bottom:24px;position:relative;overflow:hidden;">
        <div style="position:absolute;right:32px;top:50%;transform:translateY(-50%);font-size:120px;opacity:0.04">🧬</div>
        <div style="font-size:1.9rem;font-weight:800;color:#e8d5b7;margin-bottom:6px">TCM-Exosome Platform</div>
        <div style="color:#6a9a8a;font-size:0.9rem;margin-bottom:16px">Traditional Chinese Medicine × Exosome Research Intelligence</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
            <span style="background:rgba(74,184,128,0.12);border:1px solid rgba(74,184,128,0.3);border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#7adbb0">🌿 166味中药</span>
            <span style="background:rgba(74,154,224,0.12);border:1px solid rgba(74,154,224,0.3);border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#7ab0e0">📄 3000+篇文献</span>
            <span style="background:rgba(233,69,96,0.12);border:1px solid rgba(233,69,96,0.3);border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#e07a8a">🧬 949条基因关联</span>
            <span style="background:rgba(160,74,224,0.12);border:1px solid rgba(160,74,224,0.3);border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#c07ae0">💊 635味药典药材</span>
            <span style="background:rgba(224,144,74,0.12);border:1px solid rgba(224,144,74,0.3);border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#e0b07a">⚗️ 自动爬虫 6h/次</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # 数据指标卡
    cols = st.columns(6)
    data = [
        ("Papers", "📚", len(papers_df), "#4a9ae0"),
        ("Trials", "🏥", len(trials_df), "#4ab880"),
        ("Herb-Gene", "🧬", len(herb_gene_df), "#e94560"),
        ("miRNA", "🔬", len(mirna_df), "#a04ae0"),
        ("Cargo", "📦", len(cargo_df), "#e0904a"),
        ("Pathways", "🔗", len(pathway_df), "#4ab8b8"),
    ]
    for col, (label, icon, val, color) in zip(cols, data):
        col.markdown(f"""<div style="background:linear-gradient(135deg,#0d1117,#1a2535);
            border:1px solid {color}40;border-radius:12px;padding:18px;text-align:center;
            transition:border-color 0.2s;">
            <div style="font-size:2rem;font-weight:800;color:{color}">{icon} {val:,}</div>
            <div style="font-size:0.82rem;color:#a8b2d8;margin-top:4px">{label}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 第一行：来源分布 + 年度趋势
    l, r = st.columns(2)
    with l:
        st.markdown("### 📊 来源分布")
        if not papers_df.empty and "source" in papers_df.columns:
            df_src = papers_df.groupby("source").size().reset_index(name="count").sort_values("count", ascending=False)
            fig = px.pie(df_src, names="source", values="count", hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma_r)
            fig.update_layout(paper_bgcolor="#0d1117", font_color="white", margin=dict(t=20,b=20))
            st.plotly_chart(fig, use_container_width=True)
    with r:
        st.markdown("### 📈 年度趋势")
        if not papers_df.empty and "pub_date" in papers_df.columns:
            df2 = papers_df.copy()
            df2["year"] = df2["pub_date"].astype(str).str[:4]
            df2 = df2[df2["year"].str.match(r"^\d{4}$", na=False)].groupby("year").size().reset_index(name="count").sort_values("year")
            if not df2.empty:
                fig2 = px.bar(df2, x="year", y="count", color="count", color_continuous_scale="Viridis")
                fig2.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white", margin=dict(t=20,b=20))
                st.plotly_chart(fig2, use_container_width=True)

    # 第二行：AI分析统计
    analysis_df = load_table("paper_ai_analysis")
    if not analysis_df.empty:
        st.markdown("### 🤖 AI分析洞察")
        ai_l, ai_m, ai_r = st.columns(3)
        with ai_l:
            if "study_type" in analysis_df.columns:
                st_dist = analysis_df["study_type"].value_counts().reset_index()
                st_dist.columns = ["type","count"]
                fig_st = px.pie(st_dist, names="type", values="count", hole=0.45,
                               title="研究类型分布",
                               color_discrete_sequence=px.colors.sequential.Teal)
                fig_st.update_layout(paper_bgcolor="#0d1117", font_color="white",
                                     margin=dict(t=40,b=10), height=280)
                st.plotly_chart(fig_st, use_container_width=True)
        with ai_m:
            if "disease_area" in analysis_df.columns:
                da_dist = analysis_df["disease_area"].value_counts().reset_index()
                da_dist.columns = ["disease","count"]
                fig_da = px.bar(da_dist, x="disease", y="count", color="count",
                               color_continuous_scale="RdYlGn", title="疾病领域分布",
                               labels={"disease":"","count":"文献数"})
                fig_da.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                                     font_color="white", margin=dict(t=40,b=10),
                                     height=280, coloraxis_showscale=False,
                                     xaxis_tickangle=-30)
                st.plotly_chart(fig_da, use_container_width=True)
        with ai_r:
            # 药典数据层级
            herb_df = load_table("tcm_single_herb")
            if not herb_df.empty and "data_level" in herb_df.columns:
                level_dist = herb_df["data_level"].value_counts().reset_index()
                level_dist.columns = ["level","count"]
                color_map = {"enriched":"#4ab880","aligned":"#4a9ae0","skeleton":"#e94560"}
                fig_lv = px.pie(level_dist, names="level", values="count", hole=0.45,
                               title="药典数据质量",
                               color="level", color_discrete_map=color_map)
                fig_lv.update_layout(paper_bgcolor="#0d1117", font_color="white",
                                     margin=dict(t=40,b=10), height=280)
                st.plotly_chart(fig_lv, use_container_width=True)

    # 第三行：热门中药靶点 + 最新文献
    hg_l, hg_r = st.columns([1,2])
    with hg_l:
        st.markdown("### 🌿 中药靶点排名")
        if not herb_gene_df.empty and "herb_name" in herb_gene_df.columns:
            top_herbs = herb_gene_df.groupby("herb_name").size().reset_index(name="targets")
            top_herbs = top_herbs.sort_values("targets", ascending=True).tail(10)
            fig_h = px.bar(top_herbs, x="targets", y="herb_name", orientation="h",
                          color="targets", color_continuous_scale="Viridis",
                          labels={"herb_name":"","targets":"靶点数"})
            fig_h.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                               font_color="white", margin=dict(t=10,b=10),
                               height=320, coloraxis_showscale=False)
            st.plotly_chart(fig_h, use_container_width=True)
    with hg_r:
        st.markdown("### 📄 最新文献")
        if not papers_df.empty:
            df3 = papers_df.sort_values("created_at", ascending=False).head(8) if "created_at" in papers_df.columns else papers_df.head(8)
            for _, row in df3.iterrows():
                title = str(row.get("title",""))[:90] + ("..." if len(str(row.get("title",""))) > 90 else "")
                src = row.get("source","")
                date = str(row.get("pub_date",""))[:7]
                url = row.get("url","")
                link = f"[🔗]({url})" if url else ""
                st.markdown(f"""<div style="padding:8px 0;border-bottom:1px solid #1a2535">
                    <span style="background:#1a3a5a;border-radius:8px;padding:1px 7px;font-size:0.7rem;color:#4a9ae0">{src}</span>
                    <span style="color:#888;font-size:0.72rem;margin-left:6px">{date}</span>
                    <span style="float:right;font-size:0.72rem">{link}</span>
                    <div style="color:#c8d8e8;font-size:0.82rem;margin-top:3px">{title}</div>
                </div>""", unsafe_allow_html=True)

elif page == "Literature":
    st.markdown("# Literature Database")

    # 加载AI分析数据
    analysis_df = load_table("paper_ai_analysis")

    lit_tab1, lit_tab2, lit_tab3 = st.tabs(["📄 文献列表", "🤖 AI分析统计", "⭐ 我的收藏"])

    with lit_tab1:
        c1, c2, c3 = st.columns([3,1,1])
        with c1: search = st.text_input("Search", "")
        with c2:
            sources = ["All"] + sorted([s for s in papers_df["source"].unique() if pd.notna(s)]) if not papers_df.empty and "source" in papers_df.columns else ["All"]
            sel = st.selectbox("Source", sources)
        with c3: lim = st.selectbox("Show", [25, 50, 100, 200])
        if not papers_df.empty:
            df = papers_df.copy()
            if search: df = df[df["title"].str.contains(search, case=False, na=False)]
            if sel != "All": df = df[df["source"] == sel]
            if "created_at" in df.columns: df = df.sort_values("created_at", ascending=False)
            df = df.head(lim)
            # 加载收藏状态
            bookmarks_df = load_table("user_bookmarks")
            bookmarked_ids = set(bookmarks_df["paper_id"].tolist()) if not bookmarks_df.empty else set()

            cap_col, btn_col = st.columns([4,1])
            cap_col.caption(f"Total: {len(papers_df):,} | Showing: {len(df)} | ⭐ 已收藏: {len(bookmarked_ids)}")
            export_cols = [c for c in ["title","authors","abstract","pub_date","source","doi","pmid","url"] if c in df.columns]
            csv_data = df[export_cols].to_csv(index=False).encode("utf-8-sig")
            btn_col.download_button("⬇️ 导出CSV", csv_data, f"papers_{sel}_{len(df)}.csv", "text/csv", key="dl_papers")

            # 文献列表+收藏按钮
            for i, (_, row) in enumerate(df.iterrows()):
                pid = row.get("id")
                title = str(row.get("title",""))
                authors = str(row.get("authors",""))[:80]+"..." if len(str(row.get("authors","")))>80 else str(row.get("authors",""))
                pub_date = str(row.get("pub_date",""))[:7]
                source = str(row.get("source",""))
                url = row.get("url","")
                is_bookmarked = pid in bookmarked_ids

                col_info, col_star = st.columns([11, 1])
                with col_info:
                    link = f" [🔗]({url})" if url else ""
                    star = "⭐" if is_bookmarked else ""
                    st.markdown(f"""<div style="padding:6px 0;border-bottom:1px solid #1a2535">
                        <span style="background:#1a3a5a;border-radius:8px;padding:1px 7px;font-size:0.7rem;color:#4a9ae0">{source}</span>
                        <span style="color:#888;font-size:0.72rem;margin-left:6px">{pub_date}</span>
                        <span style="float:right">{star}</span>
                        <div style="color:#c8d8e8;font-size:0.82rem;margin-top:3px">{title[:100]}{link}</div>
                        <div style="color:#7a9aaa;font-size:0.75rem">{authors}</div>
                    </div>""", unsafe_allow_html=True)
                with col_star:
                    if is_bookmarked:
                        if st.button("★", key=f"unbm_{i}_{pid}", help="取消收藏"):
                            remove_bookmark(pid)
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        if st.button("☆", key=f"bm_{i}_{pid}", help="收藏"):
                            st.session_state[f"bm_modal_{pid}"] = True
                            st.rerun()

                # 收藏弹窗
                if st.session_state.get(f"bm_modal_{pid}"):
                    with st.form(key=f"bm_form_{pid}"):
                        st.markdown(f"**收藏：** {title[:60]}...")
                        imp = st.slider("重要性", 1, 5, 3, key=f"imp_{pid}")
                        note = st.text_input("备注", key=f"note_{pid}")
                        tag = st.selectbox("标签", ["default","重要","待读","已读","引用"], key=f"tag_{pid}")
                        c1f, c2f = st.columns(2)
                        if c1f.form_submit_button("✅ 确认收藏"):
                            if add_bookmark(pid, imp, note, tag):
                                st.session_state.pop(f"bm_modal_{pid}", None)
                                st.cache_data.clear()
                                st.success("已收藏！")
                                st.rerun()
                        if c2f.form_submit_button("❌ 取消"):
                            st.session_state.pop(f"bm_modal_{pid}", None)
                            st.rerun()

    with lit_tab2:
        st.markdown("### 🤖 AI分析结果统计")
        if not analysis_df.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("已分析文献", len(analysis_df))
            m2.metric("覆盖率", f"{len(analysis_df)*100//len(papers_df)}%" if not papers_df.empty else "0%")
            high_conf = len(analysis_df[analysis_df["confidence"] >= 0.6]) if "confidence" in analysis_df.columns else 0
            m3.metric("高相关文献", high_conf)
            m4.metric("平均置信度", f"{analysis_df['confidence'].mean():.2f}" if "confidence" in analysis_df.columns else "N/A")

            col_l, col_r = st.columns(2)
            with col_l:
                if "study_type" in analysis_df.columns:
                    st_dist = analysis_df["study_type"].value_counts().reset_index()
                    st_dist.columns = ["type","count"]
                    fig_st = px.pie(st_dist, names="type", values="count", hole=0.4,
                                   title="研究类型分布",
                                   color_discrete_sequence=px.colors.sequential.Teal)
                    fig_st.update_layout(paper_bgcolor="#0d1117", font_color="white", margin=dict(t=40,b=10))
                    st.plotly_chart(fig_st, use_container_width=True)
            with col_r:
                if "disease_area" in analysis_df.columns:
                    da_dist = analysis_df["disease_area"].value_counts().reset_index()
                    da_dist.columns = ["disease","count"]
                    fig_da = px.bar(da_dist, x="disease", y="count", color="count",
                                   color_continuous_scale="RdYlGn", title="疾病领域分布",
                                   labels={"disease":"疾病","count":"文献数"})
                    fig_da.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                                        font_color="white", margin=dict(t=40,b=20),
                                        coloraxis_showscale=False)
                    st.plotly_chart(fig_da, use_container_width=True)

            # 按疾病/研究类型筛选
            st.markdown("### 🔍 按分析结果筛选文献")
            f1, f2 = st.columns(2)
            with f1:
                sel_disease = st.selectbox("疾病领域", ["全部"] + sorted(analysis_df["disease_area"].dropna().unique().tolist()), key="lit_disease")
            with f2:
                sel_stype = st.selectbox("研究类型", ["全部"] + sorted(analysis_df["study_type"].dropna().unique().tolist()), key="lit_stype")

            filtered = analysis_df.copy()
            if sel_disease != "全部": filtered = filtered[filtered["disease_area"] == sel_disease]
            if sel_stype != "全部": filtered = filtered[filtered["study_type"] == sel_stype]

            if not filtered.empty and not papers_df.empty:
                paper_ids = filtered["paper_id"].tolist()
                merged = papers_df[papers_df["id"].isin(paper_ids)].merge(
                    filtered[["paper_id","study_type","disease_area","confidence","tcm_herbs","target_genes"]],
                    left_on="id", right_on="paper_id", how="left"
                )
                merged = merged.sort_values("confidence", ascending=False)
                res_cap, res_btn = st.columns([4,1])
                res_cap.caption(f"筛选结果: {len(merged)} 篇")
                show_cols = [c for c in ["title","pub_date","source","study_type","disease_area","confidence","tcm_herbs","target_genes","url"] if c in merged.columns]
                export_csv = merged[show_cols].to_csv(index=False).encode("utf-8-sig")
                res_btn.download_button("⬇️ 导出CSV", export_csv,
                    f"analysis_{sel_disease}_{sel_stype}_{len(merged)}.csv", "text/csv", key="dl_analysis")
                st.dataframe(merged[show_cols].head(100), use_container_width=True, hide_index=True,
                    column_config={"url": st.column_config.LinkColumn("Link")})

                # Excel导出
                with io.BytesIO() as buf:
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        merged[show_cols].to_excel(writer, index=False, sheet_name="文献分析")
                        if not analysis_df.empty:
                            summary = pd.DataFrame({
                                "疾病领域": analysis_df["disease_area"].value_counts().index,
                                "文献数": analysis_df["disease_area"].value_counts().values
                            })
                            summary.to_excel(writer, index=False, sheet_name="疾病统计")
                    excel_data = buf.getvalue()
                st.download_button("⬇️ 导出Excel（含统计）", excel_data,
                    f"analysis_{sel_disease}_{sel_stype}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel")
        else:
            st.info("暂无AI分析数据")

    with lit_tab3:
        st.markdown("### ⭐ 我的收藏文献")
        bm_df = load_table("user_bookmarks")
        if bm_df.empty:
            st.info("暂无收藏，点击文献列表中的 ☆ 按钮收藏文献")
        else:
            # 统计
            bm1, bm2, bm3 = st.columns(3)
            bm1.metric("收藏总数", len(bm_df))
            bm2.metric("高重要性(4-5⭐)", len(bm_df[bm_df["importance"]>=4]) if "importance" in bm_df.columns else 0)
            bm3.metric("有备注", len(bm_df[bm_df["notes"].str.len()>0]) if "notes" in bm_df.columns else 0)

            # 标签筛选
            tags = ["全部"] + sorted(bm_df["user_tag"].dropna().unique().tolist()) if "user_tag" in bm_df.columns else ["全部"]
            sel_tag = st.selectbox("筛选标签", tags, key="bm_tag")
            sort_by = st.radio("排序", ["收藏时间↓", "重要性↓"], horizontal=True, key="bm_sort")

            filtered_bm = bm_df.copy()
            if sel_tag != "全部": filtered_bm = filtered_bm[filtered_bm["user_tag"] == sel_tag]
            if sort_by == "重要性↓" and "importance" in filtered_bm.columns:
                filtered_bm = filtered_bm.sort_values("importance", ascending=False)
            elif "created_at" in filtered_bm.columns:
                filtered_bm = filtered_bm.sort_values("created_at", ascending=False)

            # 合并文献信息
            if not papers_df.empty and "paper_id" in filtered_bm.columns:
                merged_bm = filtered_bm.merge(
                    papers_df[["id","title","authors","pub_date","source","url"]],
                    left_on="paper_id", right_on="id", how="left"
                )
                for _, row in merged_bm.iterrows():
                    imp = row.get("importance", 3)
                    stars = "⭐" * int(imp)
                    tag_val = row.get("user_tag","")
                    note_val = row.get("notes","")
                    title_val = str(row.get("title",""))
                    url_val = row.get("url","")
                    pid = row.get("paper_id")
                    link = f"[🔗]({url_val})" if url_val else ""
                    tag_color = {"重要":"#e94560","待读":"#e0904a","已读":"#4ab880","引用":"#4a9ae0"}.get(tag_val,"#6a8a9a")
                    st.markdown(f"""<div style="background:#0d1a2a;border:1px solid #1e3a5a;border-radius:10px;padding:12px 16px;margin:6px 0">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span>{stars}</span>
                            <span style="background:{tag_color}25;border:1px solid {tag_color}60;border-radius:10px;padding:1px 8px;font-size:0.72rem;color:{tag_color}">{tag_val}</span>
                        </div>
                        <div style="color:#e8d5b7;font-size:0.85rem;font-weight:600;margin:4px 0">{title_val[:100]} {link}</div>
                        {"<div style='color:#7a9aaa;font-size:0.75rem;font-style:italic;margin-top:4px'>📝 " + note_val + "</div>" if note_val else ""}
                    </div>""", unsafe_allow_html=True)
                    if st.button(f"🗑️ 取消收藏", key=f"del_bm_{pid}"):
                        remove_bookmark(pid, tag_val)
                        st.cache_data.clear()
                        st.rerun()

            # 导出收藏
            if not filtered_bm.empty:
                export_bm = filtered_bm.merge(
                    papers_df[["id","title","authors","pub_date","source","doi","url"]],
                    left_on="paper_id", right_on="id", how="left"
                )
                st.download_button("⬇️ 导出收藏列表",
                    export_bm.to_csv(index=False).encode("utf-8-sig"),
                    "my_bookmarks.csv", "text/csv", key="dl_bookmarks")

elif page == "Clinical Trials":
    st.markdown("# Clinical Trials")
    if not trials_df.empty:
        df = trials_df.copy()
        c1, c2 = st.columns(2)
        c1.metric("Total", len(df))
        c2.metric("Recruiting", len(df[df["status"].str.contains("Recruiting|Active", na=False)]) if "status" in df.columns else 0)
        if "status" in df.columns:
            fig = px.bar(df.groupby("status").size().reset_index(name="n"), x="status", y="n", color="n", color_continuous_scale="Blues")
            fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[[c for c in ["nct_id","title","status","phase","condition","sponsor","start_date","url"] if c in df.columns]], use_container_width=True, hide_index=True, column_config={"url": st.column_config.LinkColumn("Details")})
    else:
        st.info("No data yet.")

elif page == "Genomics":
    st.markdown("# Genomics Analysis")
    st.caption("TCM x Exosome x Gene Network")
    genes_df = load_table("genes")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Genes", len(genes_df))
    c2.metric("miRNA", len(mirna_df))
    c3.metric("Cargo", len(cargo_df))
    c4.metric("Herb-Gene", len(herb_gene_df))

    tab1, tab2, tab3, tab4 = st.tabs(["Genes", "Herb-Gene Network", "miRNA & Cargo", "Pathways"])
    with tab1:
        if not genes_df.empty:
            st.dataframe(genes_df[[c for c in ["gene_symbol","gene_name","chromosome","ncbi_gene_id","uniprot_id"] if c in genes_df.columns]], use_container_width=True, hide_index=True)
        else:
            st.info("No gene data.")
    with tab2:
        if not herb_gene_df.empty:
            st.dataframe(herb_gene_df[[c for c in ["herb_name","gene_symbol","interaction_type","mechanism","confidence_score"] if c in herb_gene_df.columns]], use_container_width=True, hide_index=True)
        else:
            st.info("No herb-gene data.")
    with tab3:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### miRNA")
            if not mirna_df.empty:
                st.dataframe(mirna_df[[c for c in ["mirna_id","function_note","is_exosome_cargo"] if c in mirna_df.columns]], use_container_width=True, hide_index=True)
            else:
                st.info("No miRNA data.")
        with col_r:
            st.markdown("### Exosome Cargo")
            if not cargo_df.empty:
                st.dataframe(cargo_df[[c for c in ["cargo_name","cargo_type","tcm_herb","target_gene","biological_effect"] if c in cargo_df.columns]], use_container_width=True, hide_index=True)
            else:
                st.info("No cargo data.")
    with tab4:
        if not pathway_df.empty:
            st.dataframe(pathway_df[[c for c in ["herb_name","pathway_name","enrichment_score","p_value"] if c in pathway_df.columns]], use_container_width=True, hide_index=True)
            if "pathway_name" in pathway_df.columns and "enrichment_score" in pathway_df.columns:
                fig = px.bar(pathway_df.sort_values("enrichment_score", ascending=False).head(20), x="enrichment_score", y="pathway_name", orientation="h", color="herb_name" if "herb_name" in pathway_df.columns else None, title="Top Enriched Pathways")
                fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white", height=500)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pathway data.")

elif page == "Pharmacopoeia":
    from src.dashboard.pharmacopoeia_page import render_pharmacopoeia
    render_pharmacopoeia()

elif page == "Knowledge Graph":
    from src.dashboard.knowledge_graph_page import render_knowledge_graph
    render_knowledge_graph()

elif page == "📊 Reports":
    from src.dashboard.report_page import render_report_page
    render_report_page(papers_df, herb_gene_df, trials_df, cargo_df, pathway_df,
                       herb_disease_df, herb_pathway_df)

elif page == "Crawler Status":
    st.markdown("# Crawler Status")
    df = load_table("crawler_logs")
    if not df.empty:
        if "created_at" in df.columns: df = df.sort_values("created_at", ascending=False)
        st.dataframe(df[[c for c in ["source","status","records_found","records_added","created_at"] if c in df.columns]].head(50), use_container_width=True, hide_index=True)
    st.markdown("---")
    for t in ["research_papers","clinical_trials","genes","mirna","herb_gene_relations","exosome_cargo","pathway_enrichment","tcm_single_herb","tcm_compound_formula","tcm_extracts"]:
        t_df = load_table(t)
        st.markdown(f"- **{t}**: {len(t_df):,} records")
