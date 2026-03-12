import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, json

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

@st.cache_data(ttl=1800)
def load_table(table):
    client = get_supabase()
    if not client:
        return pd.DataFrame()
    all_data = []
    try:
        for i in range(0, 2000, 1000):
            res = client.table(table).select("*").range(i, i+999).execute()
            if not res.data: break
            all_data.extend(res.data)
            if len(res.data) < 1000: break
        return pd.DataFrame(all_data)
    except:
        return pd.DataFrame()

def build_network_html(hg_df, mapping_df, min_confidence=0.7, selected_herb="全部", selected_gene="全部", disease_df=None, pathway_df_h=None, show_disease=True, show_pathway=True):
    """用纯HTML+JS (vis.js) 构建交互网络图"""

    # 合并中文名 - 安全版本
    try:
        if not mapping_df.empty:
            cols = mapping_df.columns.tolist()
            en_col = next((c for c in cols if "en" in c.lower()), None)
            cn_col = next((c for c in cols if "cn" in c.lower() or "chinese" in c.lower()), None)
            if en_col and cn_col:
                tmp = mapping_df[[en_col, cn_col]].rename(columns={en_col:"_name_en", cn_col:"_name_cn"})
                hg_df = hg_df.merge(tmp, left_on="herb_name", right_on="_name_en", how="left")
                hg_df["display_herb"] = hg_df["_name_cn"].fillna(hg_df["herb_name"])
            else:
                hg_df["display_herb"] = hg_df["herb_name"]
        else:
            hg_df["display_herb"] = hg_df["herb_name"]
    except Exception:
        hg_df["display_herb"] = hg_df["herb_name"]

    # 过滤
    df = hg_df.copy()
    if "confidence_score" in df.columns:
        df = df[df["confidence_score"] >= min_confidence]
    if selected_herb != "全部":
        df = df[df["display_herb"] == selected_herb]
    if selected_gene != "全部":
        df = df[df["gene_symbol"] == selected_gene]

    if df.empty:
        return None, 0, 0

    # 颜色映射
    color_map = {
        "inhibit": "#e94560",
        "activate": "#4ab880",
        "upregulate": "#4a9ae0",
        "downregulate": "#e0904a",
        "modulate": "#a04ae0",
    }

    # 构建节点和边
    herbs = df["display_herb"].unique().tolist()
    genes = df["gene_symbol"].unique().tolist()

    nodes = []
    for h in herbs:
        nodes.append({
            "id": f"herb_{h}", "label": h,
            "group": "herb", "size": 20,
            "color": {"background": "#4ab880", "border": "#2d8a5e"},
            "font": {"color": "white", "size": 14},
            "title": f"中药: {h}"
        })
    for g in genes:
        # 计算基因连接度
        degree = len(df[df["gene_symbol"] == g])
        nodes.append({
            "id": f"gene_{g}", "label": g,
            "group": "gene", "size": 12 + degree * 3,
            "color": {"background": "#4a9ae0", "border": "#2d6ab0"},
            "font": {"color": "white", "size": 12},
            "title": f"基因: {g} (关联{degree}味中药)"
        })

    # 疾病节点
    if show_disease and disease_df is not None and not disease_df.empty:
        import pandas as _pd
        d_df = disease_df.copy()
        if selected_herb != "全部":
            herb_en = hg_df[hg_df.get("display_herb", hg_df.columns[0]) == selected_herb]["herb_name"].iloc[0] if "display_herb" in hg_df.columns and len(hg_df[hg_df.get("display_herb","") == selected_herb]) > 0 else selected_herb
            d_df = d_df[d_df["herb_name"].isin(herbs_en if "herbs_en" in dir() else herbs)]
        d_df = d_df[d_df["confidence_score"] >= min_confidence] if "confidence_score" in d_df.columns else d_df
        diseases_list = d_df["disease"].unique().tolist() if "disease" in d_df.columns else []
        for disease in diseases_list:
            cnt = len(d_df[d_df["disease"] == disease])
            nodes.append({"id": f"dis_{disease}", "label": disease, "group": "disease",
                "size": 14 + cnt*2,
                "color": {"background": "#e94560", "border": "#b02040"},
                "font": {"color": "white", "size": 12},
                "title": f"疾病: {disease} (关联{cnt}味中药)"})
        for _, row in d_df.iterrows():
            herb_id = f"herb_{row.get('display_herb', row['herb_name'])}"
            all_node_ids = [n["id"] for n in nodes]
            if herb_id not in all_node_ids:
                herb_id = f"herb_{row['herb_name']}"
            edges.append({"from": herb_id, "to": f"dis_{row['disease']}",
                "color": {"color": "#e94560", "opacity": 0.6},
                "width": 1.5, "dashes": True,
                "title": row.get("effect",""), "arrows": "to"})

    # 通路节点
    if show_pathway and pathway_df_h is not None and not pathway_df_h.empty:
        p_df = pathway_df_h.copy()
        p_df = p_df[p_df["confidence_score"] >= min_confidence] if "confidence_score" in p_df.columns else p_df
        if selected_herb != "全部":
            p_df = p_df[p_df["herb_name"].isin([h for h in herbs])]
        pathways_list = p_df["pathway_name"].unique().tolist() if "pathway_name" in p_df.columns else []
        for pathway in pathways_list:
            cnt = len(p_df[p_df["pathway_name"] == pathway])
            nodes.append({"id": f"pw_{pathway}", "label": pathway[:12], "group": "pathway",
                "size": 13 + cnt*2, "shape": "diamond",
                "color": {"background": "#e0b030", "border": "#a07010"},
                "font": {"color": "white", "size": 11},
                "title": f"通路: {pathway}"})
        for _, row in p_df.iterrows():
            reg_color = "#4ab880" if row.get("regulation") == "激活" else "#e94560" if row.get("regulation") == "抑制" else "#a04ae0"
            edges.append({"from": f"herb_{row['herb_name']}", "to": f"pw_{row['pathway_name']}",
                "color": {"color": reg_color, "opacity": 0.5},
                "width": 1.2, "dashes": [5,5],
                "title": row.get("regulation",""), "arrows": "to"})

    edges_gene = []
    for _, row in df.iterrows():
        itype = row.get("interaction_type", "modulate")
        color = color_map.get(itype, "#888888")
        mechanism = row.get("mechanism", "")
        score = row.get("confidence_score", 0)
        edges.append({
            "from": f"herb_{row['display_herb']}",
            "to": f"gene_{row['gene_symbol']}",
            "color": {"color": color, "opacity": 0.8},
            "width": 1.5 + float(score or 0.7) * 2,
            "title": f"{itype}: {mechanism[:50] if mechanism else ''}",
            "arrows": "to",
        })

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css">
<style>
  body {{ margin:0; padding:0; background:#0d1117; }}
  #network {{ width:100%; height:580px; background:#0d1117; border:1px solid #2a3a4a; border-radius:8px; }}
  #legend {{ position:absolute; top:10px; right:10px; background:rgba(0,0,0,0.7); padding:10px; border-radius:6px; font-family:sans-serif; font-size:12px; color:white; }}
  .legend-item {{ display:flex; align-items:center; margin:4px 0; }}
  .legend-dot {{ width:12px; height:12px; border-radius:50%; margin-right:8px; }}
  #info {{ position:absolute; bottom:10px; left:10px; background:rgba(0,0,0,0.7); padding:8px 12px; border-radius:6px; font-family:sans-serif; font-size:12px; color:#aaa; }}
</style>
</head>
<body>
<div style="position:relative">
<div id="network"></div>
<div id="legend">
  <div style="font-weight:bold;margin-bottom:6px;color:#e8d5b7">互作类型</div>
  <div class="legend-item"><div class="legend-dot" style="background:#e94560"></div>inhibit（抑制）</div>
  <div class="legend-item"><div class="legend-dot" style="background:#4ab880"></div>activate（激活）</div>
  <div class="legend-item"><div class="legend-dot" style="background:#4a9ae0"></div>upregulate（上调）</div>
  <div class="legend-item"><div class="legend-dot" style="background:#e0904a"></div>downregulate（下调）</div>
  <div class="legend-item"><div class="legend-dot" style="background:#a04ae0"></div>modulate（调节）</div>
  <hr style="border-color:#333;margin:6px 0">
  <div class="legend-item"><div class="legend-dot" style="background:#4ab880;border:2px solid #2d8a5e"></div>中药节点</div>
  <div class="legend-item"><div class="legend-dot" style="background:#4a9ae0;border:2px solid #2d6ab0"></div>基因节点</div>
</div>
<div id="info">拖拽移动 · 滚轮缩放 · 悬停查看详情 · 点击高亮</div>
</div>
<script>
var nodes = new vis.DataSet({json.dumps(nodes, ensure_ascii=False)});
var edges = new vis.DataSet({json.dumps(edges, ensure_ascii=False)});
var container = document.getElementById('network');
var data = {{ nodes: nodes, edges: edges }};
var options = {{
  physics: {{
    enabled: true,
    barnesHut: {{
      gravitationalConstant: -3000,
      centralGravity: 0.3,
      springLength: 120,
      springConstant: 0.04,
      damping: 0.09
    }},
    stabilization: {{ iterations: 150 }}
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    navigationButtons: false,
    zoomView: true
  }},
  nodes: {{
    shape: 'dot',
    borderWidth: 2,
    shadow: true
  }},
  edges: {{
    smooth: {{ type: 'continuous' }},
    shadow: false
  }}
}};
var network = new vis.Network(container, data, options);
network.on('click', function(params) {{
  if (params.nodes.length > 0) {{
    var nodeId = params.nodes[0];
    var connectedEdges = network.getConnectedEdges(nodeId);
    var connectedNodes = network.getConnectedNodes(nodeId);
    network.selectNodes([nodeId].concat(connectedNodes));
    network.selectEdges(connectedEdges);
  }}
}});
</script>
</body>
</html>
"""
    return html, len(herbs), len(genes)


def render_knowledge_graph():
    st.markdown("""<style>
    .kg-header{background:linear-gradient(135deg,#0d1117,#1a2535,#0d2020);border:1px solid #2a4a3a;border-radius:16px;padding:28px;margin-bottom:20px;position:relative;overflow:hidden;}
    .kg-header::before{content:'知';position:absolute;right:24px;top:50%;transform:translateY(-50%);font-size:100px;color:rgba(255,255,255,0.03);font-family:serif;}
    .kg-title{font-size:1.7rem;font-weight:700;color:#e8d5b7;margin:0 0 6px 0;}
    .kg-sub{color:#6a9a8a;font-size:0.88rem;}
    .stat-pill{display:inline-block;background:rgba(74,184,128,0.12);border:1px solid rgba(74,184,128,0.3);border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#7adbb0;margin:4px 4px 0 0;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""<div class="kg-header">
        <div class="kg-title">🕸️ TCM-Exosome 知识图谱</div>
        <div class="kg-sub">中药 × 复方 × 基因靶点 × 外泌体 · 交互网络可视化</div>
        <div style="margin-top:10px">
            <span class="stat-pill">🌿 50味中药</span>
            <span class="stat-pill">🧬 255条基因关联</span>
            <span class="stat-pill">🔴 80条疾病关联</span>
            <span class="stat-pill">🟡 74条通路关联</span>
            <span class="stat-pill">💊 130条复方关联</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # 加载数据
    hg_df = load_table("herb_gene_relations")
    mapping_df = load_table("herb_name_mapping")
    pathway_df = load_table("pathway_enrichment")
    cargo_df = load_table("exosome_cargo")
    fg_df = load_table("formula_gene_relations")
    disease_df = load_table("herb_disease_relations")
    pathway_herb_df = load_table("herb_pathway_relations")

    if hg_df.empty:
        st.info("暂无关联数据")
        return

    # 合并中文名用于筛选器
    try:
        if not mapping_df.empty:
            cols = mapping_df.columns.tolist()
            en_col = next((c for c in cols if "en" in c.lower()), None)
            cn_col = next((c for c in cols if "cn" in c.lower() or "chinese" in c.lower()), None)
            if en_col and cn_col:
                tmp = mapping_df[[en_col, cn_col]].rename(columns={en_col:"_name_en", cn_col:"_name_cn"})
                hg_merged = hg_df.merge(tmp, left_on="herb_name", right_on="_name_en", how="left")
                hg_merged["display_herb"] = hg_merged["_name_cn"].fillna(hg_merged["herb_name"])
            else:
                hg_merged = hg_df.copy()
                hg_merged["display_herb"] = hg_merged["herb_name"]
        else:
            hg_merged = hg_df.copy()
            hg_merged["display_herb"] = hg_merged["herb_name"]
    except Exception:
        hg_merged = hg_df.copy()
        hg_merged["display_herb"] = hg_merged["herb_name"]

    tab1, tab2, tab3, tab4 = st.tabs(["🕸️ 单药网络", "💊 复方网络", "📊 关联统计", "🔗 通路-外泌体网络"])

    with tab1:
        # 控制面板
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            all_herbs = ["全部"] + sorted(hg_merged["display_herb"].dropna().unique().tolist())
            sel_herb = st.selectbox("筛选中药", all_herbs, key="kg_herb")
        with c2:
            all_genes = ["全部"] + sorted(hg_df["gene_symbol"].dropna().unique().tolist())
            sel_gene = st.selectbox("筛选基因", all_genes, key="kg_gene")
        with c3:
            min_conf = st.slider("最低置信度", 0.5, 1.0, 0.65, 0.05, key="kg_conf")

        sw1, sw2 = st.columns(2)
        show_dis = sw1.checkbox("🔴 显示疾病节点", value=True)
        show_pw = sw2.checkbox("🟡 显示通路节点", value=True)

        # 生成网络图
        html_content, n_herbs, n_genes = build_network_html(
            hg_merged.copy(), mapping_df, min_conf, sel_herb, sel_gene,
            disease_df=disease_df, pathway_df_h=pathway_herb_df,
            show_disease=show_dis, show_pathway=show_pw
        )

        if html_content:
            n_dis = len(disease_df["disease"].unique()) if show_dis and not disease_df.empty else 0
            n_pw = len(pathway_herb_df["pathway_name"].unique()) if show_pw and not pathway_herb_df.empty else 0
            st.caption(f"显示 {n_herbs} 味中药 · {n_genes} 个基因 · {n_dis} 个疾病 · {n_pw} 条通路 · 置信度≥{min_conf}")
            components.html(html_content, height=600, scrolling=False)
        else:
            st.warning("当前筛选条件下无数据，请调整筛选器")

        # 机制详情表
        with st.expander("📋 查看关联详情", expanded=False):
            show_df = hg_merged.copy()
            if sel_herb != "全部": show_df = show_df[show_df["display_herb"] == sel_herb]
            if sel_gene != "全部": show_df = show_df[show_df["gene_symbol"] == sel_gene]
            if "confidence_score" in show_df.columns:
                show_df = show_df[show_df["confidence_score"] >= min_conf]
            cols = [c for c in ["display_herb","gene_symbol","interaction_type","mechanism","confidence_score"] if c in show_df.columns]
            st.dataframe(show_df[cols].rename(columns={"display_herb":"中药","gene_symbol":"基因","interaction_type":"互作类型","mechanism":"机制","confidence_score":"置信度"}),
                        use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### 💊 复方-基因关联网络")
        if fg_df.empty:
            st.info("暂无复方-基因关联数据")
        else:
            fm1, fm2, fm3 = st.columns(3)
            fm1.metric("复方数", fg_df["formula_name"].nunique() if "formula_name" in fg_df.columns else 0)
            fm2.metric("基因靶点", fg_df["gene_symbol"].nunique() if "gene_symbol" in fg_df.columns else 0)
            fm3.metric("总关联", len(fg_df))

            # 复方筛选
            f_col1, f_col2 = st.columns([3,1])
            with f_col1:
                all_formulas = ["全部"] + sorted(fg_df["formula_name"].dropna().unique().tolist())
                sel_formula = st.selectbox("筛选复方", all_formulas, key="kg_formula")
            with f_col2:
                min_conf_f = st.slider("置信度", 0.5, 1.0, 0.75, 0.05, key="kg_fconf")

            # 构建复方网络图
            df_f = fg_df.copy()
            if sel_formula != "全部": df_f = df_f[df_f["formula_name"] == sel_formula]
            if "confidence_score" in df_f.columns: df_f = df_f[df_f["confidence_score"] >= min_conf_f]

            if not df_f.empty:
                formulas = df_f["formula_name"].unique().tolist()
                genes_f = df_f["gene_symbol"].unique().tolist()
                color_map_f = {"inhibit":"#e94560","activate":"#4ab880","upregulate":"#4a9ae0","downregulate":"#e0904a","modulate":"#a04ae0"}
                nodes_f = []
                for fm in formulas:
                    cnt = len(df_f[df_f["formula_name"]==fm])
                    nodes_f.append({"id":f"f_{fm}","label":fm,"group":"formula","size":18+cnt*2,
                        "color":{"background":"#a04ae0","border":"#7a2ab0"},
                        "font":{"color":"white","size":13},"title":f"复方:{fm}({cnt}个靶点)"})
                for g in genes_f:
                    cnt_g = len(df_f[df_f["gene_symbol"]==g])
                    nodes_f.append({"id":f"fg_{g}","label":g,"group":"gene","size":12+cnt_g*4,
                        "color":{"background":"#4a9ae0","border":"#2d6ab0"},
                        "font":{"color":"white","size":12},"title":f"基因:{g}(关联{cnt_g}复方)"})
                edges_f = []
                for _, row in df_f.iterrows():
                    itype = row.get("interaction_type","modulate")
                    score = row.get("confidence_score",0.7)
                    edges_f.append({"from":f"f_{row['formula_name']}","to":f"fg_{row['gene_symbol']}",
                        "color":{"color":color_map_f.get(itype,"#888"),"opacity":0.8},
                        "width":1.5+float(score)*2,"title":f"{itype}","arrows":"to"})
                import json as _json
                html_f = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css">
<style>body{{margin:0;background:#0d1117}}#net{{width:100%;height:560px;background:#0d1117;border:1px solid #2a3a4a;border-radius:8px}}</style>
</head><body><div id="net"></div><script>
var nodes=new vis.DataSet({_json.dumps(nodes_f,ensure_ascii=False)});
var edges=new vis.DataSet({_json.dumps(edges_f,ensure_ascii=False)});
var network=new vis.Network(document.getElementById('net'),{{nodes,edges}},{{
  physics:{{barnesHut:{{gravitationalConstant:-3500,springLength:130}},stabilization:{{iterations:150}}}},
  interaction:{{hover:true,tooltipDelay:100}},
  nodes:{{shape:'dot',borderWidth:2,shadow:true}},
  edges:{{smooth:{{type:'continuous'}}}}
}});
</script></body></html>"""
                st.caption(f"显示 {len(formulas)} 个复方 · {len(genes_f)} 个基因靶点")
                import streamlit.components.v1 as _comp
                _comp.html(html_f, height=580, scrolling=False)

            # 复方靶点详情
            with st.expander("📋 复方-基因关联详情", expanded=False):
                show_f = df_f[[c for c in ["formula_name","gene_symbol","interaction_type","mechanism","confidence_score"] if c in df_f.columns]]
                st.dataframe(show_f.rename(columns={"formula_name":"复方","gene_symbol":"基因","interaction_type":"互作","mechanism":"机制","confidence_score":"置信度"}),
                    use_container_width=True, hide_index=True)

            # 复方vs基因热力图
            st.markdown("#### 🔥 复方-基因互作热力图")
            pivot = df_f.pivot_table(index="formula_name", columns="gene_symbol",
                values="confidence_score", aggfunc="max").fillna(0)
            if not pivot.empty:
                fig_heat = px.imshow(pivot, color_continuous_scale="RdYlGn",
                    labels=dict(x="基因", y="复方", color="置信度"),
                    title="复方-基因置信度热力图", aspect="auto")
                fig_heat.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    font_color="white", height=max(300, len(pivot)*30+100),
                    margin=dict(t=40,b=20))
                st.plotly_chart(fig_heat, use_container_width=True)

    with tab3:
        st.markdown("### 📊 网络统计分析")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("中药节点", hg_merged["display_herb"].nunique())
        c2.metric("基因节点", hg_df["gene_symbol"].nunique() if "gene_symbol" in hg_df.columns else 0)
        c3.metric("总关联边", len(hg_df))
        c4.metric("平均置信度", f"{hg_df['confidence_score'].mean():.2f}" if "confidence_score" in hg_df.columns else "N/A")

        col_l, col_r = st.columns(2)
        with col_l:
            # 中药连接度排名
            herb_degree = hg_merged.groupby("display_herb").size().reset_index(name="targets")
            herb_degree = herb_degree.sort_values("targets", ascending=False)
            fig1 = px.bar(herb_degree, x="display_herb", y="targets", color="targets",
                         color_continuous_scale="Viridis", title="中药靶点数量排名",
                         labels={"display_herb":"中药","targets":"靶点数"})
            fig1.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                               font_color="white", margin=dict(t=40,b=20),
                               xaxis_tickangle=-45, coloraxis_showscale=False)
            st.plotly_chart(fig1, use_container_width=True)

        with col_r:
            # 基因被靶向排名
            gene_degree = hg_df.groupby("gene_symbol").size().reset_index(name="herbs")
            gene_degree = gene_degree.sort_values("herbs", ascending=False).head(15)
            fig2 = px.bar(gene_degree, x="gene_symbol", y="herbs", color="herbs",
                         color_continuous_scale="Plasma", title="基因被靶向频次 Top15",
                         labels={"gene_symbol":"基因","herbs":"中药数"})
            fig2.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                               font_color="white", margin=dict(t=40,b=20),
                               xaxis_tickangle=-45, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        # 互作类型桑基图
        if "interaction_type" in hg_merged.columns:
            st.markdown("### 互作类型分布")
            itype_dist = hg_merged.groupby(["display_herb","interaction_type"]).size().reset_index(name="count")
            color_map = {"inhibit":"#e94560","activate":"#4ab880","upregulate":"#4a9ae0",
                        "downregulate":"#e0904a","modulate":"#a04ae0"}
            fig3 = px.bar(itype_dist, x="display_herb", y="count", color="interaction_type",
                         color_discrete_map=color_map, title="各中药互作类型分布",
                         labels={"display_herb":"中药","count":"数量","interaction_type":"互作类型"})
            fig3.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                               font_color="white", margin=dict(t=40,b=20),
                               xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        st.markdown("### 🔗 通路-外泌体关联网络")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### KEGG通路富集")
            if not pathway_df.empty:
                show_cols = [c for c in ["herb_name","pathway_name","enrichment_score","p_value"] if c in pathway_df.columns]
                if "enrichment_score" in pathway_df.columns:
                    top_pw = pathway_df.sort_values("enrichment_score", ascending=False).head(20)
                    fig4 = px.scatter(top_pw, x="enrichment_score",
                                     y="pathway_name" if "pathway_name" in top_pw.columns else top_pw.columns[1],
                                     color="herb_name" if "herb_name" in top_pw.columns else None,
                                     size="enrichment_score",
                                     title="通路富集气泡图",
                                     labels={"enrichment_score":"富集分数"})
                    fig4.update_layout(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                                       font_color="white", height=450, margin=dict(t=40,b=20))
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.dataframe(pathway_df[show_cols].head(20), use_container_width=True, hide_index=True)
            else:
                st.info("暂无通路数据")

        with col_r:
            st.markdown("#### 外泌体Cargo")
            if not cargo_df.empty:
                show_cols2 = [c for c in ["cargo_name","cargo_type","tcm_herb","target_gene","biological_effect"] if c in cargo_df.columns]
                if "cargo_type" in cargo_df.columns:
                    type_dist = cargo_df["cargo_type"].value_counts().reset_index()
                    type_dist.columns = ["type","count"]
                    fig5 = px.pie(type_dist, names="type", values="count", hole=0.45,
                                 title="Cargo类型分布",
                                 color_discrete_sequence=px.colors.sequential.Teal)
                    fig5.update_layout(paper_bgcolor="#0d1117", font_color="white", margin=dict(t=40,b=10))
                    st.plotly_chart(fig5, use_container_width=True)
                st.dataframe(cargo_df[show_cols2].head(20), use_container_width=True, hide_index=True)
            else:
                st.info("暂无Cargo数据")
