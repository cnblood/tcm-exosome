import streamlit as st
import pandas as pd
import plotly.express as px
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

@st.cache_resource
def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

@st.cache_data(ttl=3600)
def load_all(table):
    client = get_supabase()
    if not client:
        return pd.DataFrame()
    all_data = []
    try:
        for i in range(0, 5000, 1000):
            res = client.table(table).select("*").range(i, i+999).execute()
            if not res.data:
                break
            all_data.extend(res.data)
            if len(res.data) < 1000:
                break
        return pd.DataFrame(all_data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_linked_herbs():
    client = get_supabase()
    if not client:
        return pd.DataFrame(), pd.DataFrame()
    try:
        mapping = pd.DataFrame(client.table("herb_name_mapping").select("*").execute().data)
        hg = pd.DataFrame(client.table("herb_gene_relations").select("*").execute().data)
        if mapping.empty or hg.empty:
            return mapping, pd.DataFrame()
        merged = hg.merge(mapping[["name_en","name_cn"]], left_on="herb_name", right_on="name_en", how="left")
        return mapping, merged
    except:
        return pd.DataFrame(), pd.DataFrame()

def render_pharmacopoeia():
    st.markdown("""<style>
    .pharm-header{background:linear-gradient(135deg,#1b2838 0%,#2d1b4e 50%,#1a3a2e 100%);border:1px solid #4a3060;border-radius:16px;padding:32px;margin-bottom:24px;position:relative;overflow:hidden;}
    .pharm-header::before{content:'典';position:absolute;right:32px;top:50%;transform:translateY(-50%);font-size:120px;color:rgba(255,255,255,0.04);font-family:serif;line-height:1;}
    .pharm-title{font-size:1.8rem;font-weight:700;color:#e8d5b7;letter-spacing:0.05em;margin:0 0 8px 0;}
    .pharm-sub{color:#8899aa;font-size:0.9rem;margin:0;}
    .stat-pill{display:inline-block;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);border-radius:20px;padding:4px 14px;font-size:0.8rem;color:#a0b4c8;margin:4px 4px 0 0;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""<div class="pharm-header">
        <div class="pharm-title">🏛️ 中国药典 2025 — 权威药材数据库</div>
        <div class="pharm-sub">Chinese Pharmacopoeia 2025 · Master Index · Linked to Gene Network</div>
        <div style="margin-top:12px">
            <span class="stat-pill">📦 614 药材饮片</span>
            <span class="stat-pill">🧪 47 提取物</span>
            <span class="stat-pill">💊 650 成方制剂</span>
            <span class="stat-pill">🧬 8 药材已关联基因</span>
        </div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌿 药材饮片 (614)", "🧬 中药-基因关联", "🧪 提取物 (47)", "💊 成方制剂 (650)"
    ])

    with tab1:
        herb_df = load_all("tcm_single_herb")
        if not herb_df.empty:
            col1, col2 = st.columns([3, 1])
            with col1:
                search = st.text_input("搜索药材", "", placeholder="输入药名或拼音…", key="herb_search")
            with col2:
                cats = ["全部"] + sorted(herb_df["category"].dropna().unique().tolist()) if "category" in herb_df.columns else ["全部"]
                cat = st.selectbox("分类", cats, key="herb_cat")
            df = herb_df.copy()
            if search:
                mask = df["name_cn"].str.contains(search, na=False)
                if "pinyin" in df.columns: mask |= df["pinyin"].str.contains(search, case=False, na=False)
                if "pinyin_initial" in df.columns: mask |= df["pinyin_initial"].str.contains(search, case=False, na=False)
                df = df[mask]
            if cat != "全部" and "category" in df.columns:
                df = df[df["category"] == cat]
            # 数据层级统计
            c1, c2, c3 = st.columns(3)
            enriched_n = len(herb_df[herb_df["data_level"]=="enriched"]) if "data_level" in herb_df.columns else 0
            aligned_n = len(herb_df[herb_df["data_level"]=="aligned"]) if "data_level" in herb_df.columns else 0
            c1.metric("🌟 Enriched（完整）", f"{enriched_n} ({enriched_n*100//len(herb_df)}%)")
            c2.metric("✅ Aligned（拉丁名）", f"{aligned_n} ({aligned_n*100//len(herb_df)}%)")
            c3.metric("📊 总计", len(herb_df))

            # 药性 & 归经分布图
            if "nature" in herb_df.columns and herb_df["nature"].notna().sum() > 0:
                col_l, col_r = st.columns(2)
                with col_l:
                    nature_dist = herb_df["nature"].dropna().value_counts().reset_index()
                    nature_dist.columns = ["nature", "count"]
                    fig_n = px.bar(nature_dist, x="nature", y="count", color="count",
                                   color_continuous_scale="RdYlGn", title="药性分布",
                                   labels={"nature":"药性","count":"数量"})
                    fig_n.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                                        font_color="white", margin=dict(t=40,b=20),
                                        showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig_n, use_container_width=True)
                with col_r:
                    if "meridian" in herb_df.columns and herb_df["meridian"].notna().sum() > 0:
                        meridian_counts = {}
                        for m in herb_df["meridian"].dropna():
                            for item in str(m).replace("、",",").split(","):
                                item = item.strip().replace("经","")
                                if item and len(item) <= 4:
                                    meridian_counts[item] = meridian_counts.get(item, 0) + 1
                        if meridian_counts:
                            mer_items = sorted(meridian_counts.items(), key=lambda x: -x[1])[:12]
                            mer_pd = pd.DataFrame(mer_items, columns=["归经","频次"])
                            fig_m = px.bar(mer_pd, x="归经", y="频次", color="频次",
                                           color_continuous_scale="Blues", title="归经频次 Top12")
                            fig_m.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                                                font_color="white", margin=dict(t=40,b=20),
                                                showlegend=False, coloraxis_showscale=False)
                            st.plotly_chart(fig_m, use_container_width=True)

            st.caption(f"共 {len(herb_df)} 条 · 显示 {len(df)} 条")
            show_cols = [c for c in ["name_cn","pinyin","category","name_latin","nature","flavor","meridian","functions","active_compounds","data_level"] if c in df.columns]
            col_config = {
                "name_cn": st.column_config.TextColumn("药材名", width=80),
                "pinyin": st.column_config.TextColumn("拼音", width=80),
                "category": st.column_config.TextColumn("分类", width=80),
                "name_latin": st.column_config.TextColumn("拉丁学名", width=180),
                "nature": st.column_config.TextColumn("药性", width=60),
                "flavor": st.column_config.TextColumn("药味", width=80),
                "meridian": st.column_config.TextColumn("归经", width=150),
                "functions": st.column_config.TextColumn("功效", width=250),
                "active_compounds": st.column_config.TextColumn("活性成分", width=200),
                "data_level": st.column_config.TextColumn("层级", width=70),
            }
            st.dataframe(df[show_cols], use_container_width=True, hide_index=True, column_config=col_config)
        else:
            st.info("暂无数据")

    with tab2:
        st.markdown("### 🧬 中药-基因靶点关联网络")
        st.caption("通过 herb_name_mapping 打通药典中文名与基因数据库")
        mapping_df, merged_df = load_linked_herbs()

        if not merged_df.empty:
            linked_herbs = merged_df["name_cn"].dropna().unique()
            c1, c2 = st.columns([2, 1])
            with c1:
                sel_herb = st.selectbox("选择药材", ["全部"] + sorted(linked_herbs.tolist()))
            with c2:
                itypes = ["全部"] + sorted(merged_df["interaction_type"].dropna().unique().tolist()) if "interaction_type" in merged_df.columns else ["全部"]
                sel_type = st.selectbox("互作类型", itypes)

            df_show = merged_df.copy()
            if sel_herb != "全部": df_show = df_show[df_show["name_cn"] == sel_herb]
            if sel_type != "全部": df_show = df_show[df_show["interaction_type"] == sel_type]
            st.caption(f"共 {len(merged_df)} 条关联 · 显示 {len(df_show)} 条")

            if not df_show.empty:
                color_map = {"inhibit":"#e94560","activate":"#4ab880","upregulate":"#4a9ae0","downregulate":"#e0904a","modulate":"#a04ae0"}
                fig = px.scatter(df_show, x="name_cn", y="gene_symbol", color="interaction_type",
                                 title="中药-基因互作矩阵", color_discrete_map=color_map)
                fig.update_traces(marker=dict(size=16, symbol="square"))
                fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#141d2b", font_color="white",
                                  height=420, xaxis_title="中药", yaxis_title="基因靶点", margin=dict(t=50,b=20))
                st.plotly_chart(fig, use_container_width=True)

                show_cols = [c for c in ["name_cn","herb_name","gene_symbol","interaction_type","mechanism","confidence_score"] if c in df_show.columns]
                st.dataframe(df_show[show_cols], use_container_width=True, hide_index=True,
                             column_config={
                                 "name_cn": st.column_config.TextColumn("中文药名"),
                                 "herb_name": st.column_config.TextColumn("英文名"),
                                 "gene_symbol": st.column_config.TextColumn("基因"),
                                 "interaction_type": st.column_config.TextColumn("互作类型"),
                                 "mechanism": st.column_config.TextColumn("作用机制"),
                                 "confidence_score": st.column_config.NumberColumn("置信度", format="%.2f"),
                             })

            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("已关联药材", len(linked_herbs))
            c2.metric("覆盖基因", merged_df["gene_symbol"].nunique() if "gene_symbol" in merged_df.columns else 0)
            c3.metric("总关联条数", len(merged_df))

            if "interaction_type" in merged_df.columns:
                dist = merged_df.groupby("interaction_type").size().reset_index(name="count")
                color_map2 = {"inhibit":"#e94560","activate":"#4ab880","upregulate":"#4a9ae0","downregulate":"#e0904a","modulate":"#a04ae0"}
                fig2 = px.pie(dist, names="interaction_type", values="count", hole=0.5,
                              title="互作类型分布", color_discrete_map=color_map2)
                fig2.update_layout(paper_bgcolor="#0d1117", font_color="white", margin=dict(t=40,b=10))
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("暂无关联数据")

    with tab3:
        ext_df = load_all("tcm_extracts")
        if not ext_df.empty:
            search2 = st.text_input("搜索提取物", "", placeholder="输入名称…", key="ext_search")
            df2 = ext_df[ext_df["name_cn"].str.contains(search2, na=False)] if search2 else ext_df
            st.caption(f"共 {len(ext_df)} 条 · 显示 {len(df2)} 条")
            show_cols2 = [c for c in ["name_cn","pinyin","source_herb","extract_type","active_component","data_level"] if c in df2.columns]
            st.dataframe(df2[show_cols2], use_container_width=True, hide_index=True)
        else:
            st.info("暂无数据")

    with tab4:
        formula_df = load_all("tcm_compound_formula")
        if not formula_df.empty:
            col1, col2 = st.columns([3, 1])
            with col1:
                search3 = st.text_input("搜索成方", "", placeholder="方名或拼音首字母（如XFZY）…", key="formula_search")
            with col2:
                dosage_forms = ["全部"] + sorted(formula_df["dosage_form"].dropna().unique().tolist()) if "dosage_form" in formula_df.columns else ["全部"]
                dosage = st.selectbox("剂型", dosage_forms, key="dosage_sel")
            df3 = formula_df.copy()
            if search3:
                mask3 = df3["name_cn"].str.contains(search3, na=False)
                if "pinyin" in df3.columns: mask3 |= df3["pinyin"].str.contains(search3, case=False, na=False)
                if "pinyin_initial" in df3.columns: mask3 |= df3["pinyin_initial"].str.contains(search3, case=False, na=False)
                df3 = df3[mask3]
            if dosage != "全部" and "dosage_form" in df3.columns:
                df3 = df3[df3["dosage_form"] == dosage]
            st.caption(f"共 {len(formula_df)} 条 · 显示 {len(df3)} 条")
            if "dosage_form" in formula_df.columns:
                dist = formula_df.groupby("dosage_form").size().reset_index(name="count").sort_values("count", ascending=False).head(10)
                fig = px.bar(dist, x="dosage_form", y="count", color="count", color_continuous_scale="Teal", title="剂型分布 Top 10")
                fig.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="white",
                                  margin=dict(t=40,b=20), showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            show_cols3 = [c for c in ["name_cn","pinyin","pinyin_initial","dosage_form","indications","key_herbs","data_level"] if c in df3.columns]
            st.dataframe(df3[show_cols3], use_container_width=True, hide_index=True)
        else:
            st.info("暂无数据")
