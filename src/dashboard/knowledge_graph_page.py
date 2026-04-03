# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# 文件名称: knowledge_graph_page.py
# 所属系统: 中药外泌体智能分析系统软件 V1.0
# 模块功能: 基于 Vis.js 的交互式知识图谱可视化组件（已强化空数据防护）
# 开发日期: 2026-01-20
# 版本: V1.2（修复 edges/nodes 作用域错误）
# -------------------------------------------------------------------------

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import logging
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


def build_network_html(
    hg_df: pd.DataFrame,
    mapping_df: Optional[pd.DataFrame] = None,
    min_confidence: float = 0.7,
    selected_herb: str = "全部",
    selected_gene: str = "全部",
    disease_df: Optional[pd.DataFrame] = None,
    pathway_df_h: Optional[pd.DataFrame] = None,
    show_disease: bool = True,
    show_pathway: bool = True,
    max_nodes: int = 500,
    max_edges: int = 2000
) -> Tuple[Optional[str], int, int]:
    """
    构建中药外泌体智能知识图谱的 HTML 代码。
    返回 (html_str, n_herbs, n_genes)；失败时返回 (None, 0, 0)。
    """
    # ── 最先初始化，保证任何分支都可访问 ──
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_nodes: set = set()

    if hg_df is None or hg_df.empty:
        logger.warning("⚠️ hg_df 为空，无法构建知识图谱")
        return None, 0, 0

    try:
        df = hg_df.copy()

        # 1. 安全获取 herb_name 列
        herb_col = None
        for col in ["display_herb", "herb_name", "herb", "herb_name_cn"]:
            if col in df.columns:
                herb_col = col
                break

        if herb_col is None:
            st.error("❌ 数据中缺少中药名称列（herb_name / display_herb）")
            logger.error("hg_df 中没有 herb_name 相关列")
            return None, 0, 0

        # 2. 中英文名称映射
        if mapping_df is not None and not mapping_df.empty:
            try:
                cols = mapping_df.columns.tolist()
                en_col = next((c for c in cols if "en" in c.lower()), None)
                cn_col = next((c for c in cols if any(x in c.lower()
                               for x in ["cn", "chinese", "zh"])), None)
                if en_col and cn_col:
                    tmp = (mapping_df[[en_col, cn_col]]
                           .dropna(subset=[en_col, cn_col])
                           .rename(columns={en_col: "_en", cn_col: "_cn"}))
                    if not tmp.empty:
                        df = df.merge(tmp, left_on=herb_col, right_on="_en", how="left")
                        df["display_herb"] = df["_cn"].fillna(df[herb_col])
                    else:
                        df["display_herb"] = df[herb_col]
                else:
                    df["display_herb"] = df[herb_col]
            except Exception as e:
                logger.warning(f"⚠️ 名称映射处理异常: {e}")
                df["display_herb"] = df[herb_col]
        else:
            df["display_herb"] = df[herb_col]

        # 3. 数据过滤
        if "confidence_score" in df.columns:
            df = df[df["confidence_score"].fillna(0) >= min_confidence].copy()
        if selected_herb != "全部":
            df = df[df["display_herb"] == selected_herb]
        if selected_gene != "全部" and "gene_symbol" in df.columns:
            df = df[df["gene_symbol"] == selected_gene]

        if df.empty:
            logger.info("ℹ️ 筛选后无匹配数据")
            return None, 0, 0

        # 颜色映射
        color_map: Dict[str, str] = {
            "inhibit":     "#e94560",
            "activate":    "#4ab880",
            "upregulate":  "#4a9ae0",
            "downregulate":"#e0904a",
            "modulate":    "#a04ae0",
            "unknown":     "#888888",
        }

        # 4. 中药节点
        active_herbs = df["display_herb"].dropna().unique().tolist()[:max_nodes // 3]
        for h in active_herbs:
            if pd.isna(h) or not str(h).strip():
                continue
            node_id = f"herb_{str(h).strip()}"
            if node_id not in seen_nodes and len(seen_nodes) < max_nodes:
                nodes.append({
                    "id": node_id, "label": str(h)[:25], "group": "herb", "size": 28,
                    "color": {"background": "#4ab880", "border": "#2d8a5e"},
                    "font": {"color": "white", "size": 14, "bold": True},
                    "title": f"<b>中药</b><br/>{h}", "shape": "dot", "borderWidth": 2
                })
                seen_nodes.add(node_id)

        # 5. 基因节点
        active_genes: List[str] = []
        if "gene_symbol" in df.columns:
            gene_counts = df["gene_symbol"].value_counts()
            active_genes = [g for g, _ in gene_counts.head(max_nodes // 3).items()]

        for g in active_genes:
            if pd.isna(g) or not str(g).strip():
                continue
            node_id = f"gene_{str(g).strip()}"
            if node_id not in seen_nodes and len(seen_nodes) < max_nodes:
                degree = len(df[df["gene_symbol"] == g])
                nodes.append({
                    "id": node_id, "label": str(g)[:20], "group": "gene",
                    "size": 18 + min(degree * 2, 15),
                    "color": {"background": "#4a9ae0", "border": "#2d6ab0"},
                    "font": {"color": "white", "size": 12},
                    "title": f"<b>基因靶点</b><br/>{g}<br/>关联 {degree} 味中药",
                    "shape": "dot", "borderWidth": 2
                })
                seen_nodes.add(node_id)

        # 6. 疾病节点与连线（show_disease 开关）
        if show_disease and disease_df is not None and not disease_df.empty:
            try:
                d_herb_col = next(
                    (c for c in ["herb_name", "herb", "display_herb"] if c in disease_df.columns),
                    None
                )
                d_dis_col = next(
                    (c for c in ["disease", "disease_name"] if c in disease_df.columns),
                    None
                )
                if d_herb_col and d_dis_col:
                    for _, row in disease_df.iterrows():
                        if len(nodes) >= max_nodes:
                            break
                        dis_val = row.get(d_dis_col, "")
                        herb_val = row.get(d_herb_col, "")
                        if not dis_val or not herb_val:
                            continue
                        dis_id = f"dis_{str(dis_val).strip()}"
                        herb_id = f"herb_{str(herb_val).strip()}"
                        # 疾病节点
                        if dis_id not in seen_nodes:
                            nodes.append({
                                "id": dis_id, "label": str(dis_val)[:20],
                                "group": "disease", "size": 20,
                                "color": {"background": "#e0904a", "border": "#b86020"},
                                "font": {"color": "white", "size": 12},
                                "title": f"<b>疾病</b><br/>{dis_val}",
                                "shape": "diamond", "borderWidth": 2
                            })
                            seen_nodes.add(dis_id)
                        # 疾病连线（herb → disease）
                        if herb_id in seen_nodes and len(edges) < max_edges:
                            edges.append({
                                "from": herb_id, "to": dis_id,
                                "color": {"color": "#e0904a", "opacity": 0.6},
                                "width": 1, "arrows": "to", "dashes": True,
                                "title": f"<b>中药-疾病</b><br/>{herb_val} → {dis_val}"
                            })
            except Exception as e:
                logger.warning(f"⚠️ 疾病节点构建异常: {e}")

        # 7. 通路节点与连线（show_pathway 开关）
        if show_pathway and pathway_df_h is not None and not pathway_df_h.empty:
            try:
                p_herb_col = next(
                    (c for c in ["herb_name", "herb", "display_herb"] if c in pathway_df_h.columns),
                    None
                )
                p_path_col = next(
                    (c for c in ["pathway_name", "pathway"] if c in pathway_df_h.columns),
                    None
                )
                if p_herb_col and p_path_col:
                    for _, row in pathway_df_h.iterrows():
                        if len(nodes) >= max_nodes:
                            break
                        path_val = row.get(p_path_col, "")
                        herb_val = row.get(p_herb_col, "")
                        if not path_val or not herb_val:
                            continue
                        path_id = f"pw_{str(path_val).strip()}"
                        herb_id = f"herb_{str(herb_val).strip()}"
                        if path_id not in seen_nodes:
                            nodes.append({
                                "id": path_id, "label": str(path_val)[:22],
                                "group": "pathway", "size": 16,
                                "color": {"background": "#a04ae0", "border": "#6d20b8"},
                                "font": {"color": "white", "size": 11},
                                "title": f"<b>通路</b><br/>{path_val}",
                                "shape": "box", "borderWidth": 1
                            })
                            seen_nodes.add(path_id)
                        if herb_id in seen_nodes and len(edges) < max_edges:
                            edges.append({
                                "from": herb_id, "to": path_id,
                                "color": {"color": "#a04ae0", "opacity": 0.5},
                                "width": 1, "arrows": "to", "dashes": True,
                                "title": f"<b>中药-通路</b><br/>{herb_val} → {path_val}"
                            })
            except Exception as e:
                logger.warning(f"⚠️ 通路节点构建异常: {e}")

        # 8. 中药 → 基因 核心连线
        for _, row in df.iterrows():
            if len(edges) >= max_edges:
                break
            itype      = str(row.get("interaction_type", "modulate")).lower().strip()
            score_raw  = row.get("confidence_score", 0.7)
            score      = float(score_raw) if pd.notna(score_raw) else 0.7
            herb_key   = row.get("display_herb", "")
            gene_sym   = row.get("gene_symbol", "")
            if not herb_key or not gene_sym:
                continue
            from_id = f"herb_{str(herb_key).strip()}"
            to_id   = f"gene_{str(gene_sym).strip()}"
            if from_id in seen_nodes and to_id in seen_nodes:
                edge_color = color_map.get(itype, color_map["unknown"])
                edges.append({
                    "from": from_id, "to": to_id,
                    "color": {"color": edge_color, "opacity": 0.85},
                    "width": 2 + min(score * 3, 5),
                    "title": f"<b>互作关系</b><br/>类型: {itype}<br/>置信度: {score:.2f}",
                    "arrows": "to",
                    "label": itype[:1].upper() if itype != "unknown" else "?"
                })

        if not nodes:
            return None, 0, 0

        # 9. 生成 HTML
        nodes_json = json.dumps(nodes, ensure_ascii=False)
        edges_json = json.dumps(edges, ensure_ascii=False)

        html_template = f"""
<!DOCTYPE html><html><head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link  href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet"/>
<style>
  body,html{{margin:0;padding:0;background:#0d1117;}}
  #graph{{width:100%;height:700px;border:1px solid #30363d;background:#0d1117;}}
</style>
</head><body>
<div id="graph"></div>
<script>
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});
var options = {{
  physics:{{barnesHut:{{gravitationalConstant:-8000,springLength:120}},stabilization:{{iterations:200}}}},
  interaction:{{hover:true,tooltipDelay:100}},
  edges:{{smooth:{{type:"cubicBezier"}}}},
  groups:{{
    herb   :{{color:{{background:"#4ab880",border:"#2d8a5e"}},shape:"dot"}},
    gene   :{{color:{{background:"#4a9ae0",border:"#2d6ab0"}},shape:"dot"}},
    disease:{{color:{{background:"#e0904a",border:"#b86020"}},shape:"diamond"}},
    pathway:{{color:{{background:"#a04ae0",border:"#6d20b8"}},shape:"box"}}
  }}
}};
new vis.Network(document.getElementById("graph"),{{nodes:nodes,edges:edges}},options);
</script>
</body></html>
"""
        return html_template, len(active_herbs), len(active_genes)

    except Exception as e:
        logger.error(f"❌ 知识图谱构建异常: {type(e).__name__}: {e}")
        return None, 0, 0


# -------------------------------------------------------------------------
# 页面主渲染函数
# -------------------------------------------------------------------------
def render_knowledge_graph(
    hg_df: pd.DataFrame,
    mapping_df: Optional[pd.DataFrame] = None,
    disease_df: Optional[pd.DataFrame] = None,
    pathway_herb_df: Optional[pd.DataFrame] = None
) -> None:
    st.header("🕸️ TCM-Exosome 知识图谱")
    st.caption("中药 · 基因 · 疾病 · 通路 多维关联网络可视化")

    if hg_df is None or hg_df.empty:
        st.warning("⚠️ 当前没有中药-基因关联数据，无法显示知识图谱")
        st.info(
            "💡 建议运行以下初始化脚本补充数据：\n"
            "• `python src/database/init_db.py`\n"
            "• `python herb_gene_final7.py`"
        )
        return

    with st.expander("🛠️ 图谱控制面板", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            herb_options = ["全部"] + sorted(
                hg_df.get("display_herb", hg_df.get("herb_name",
                pd.Series(dtype=str))).dropna().unique().tolist()
            )
            sel_herb = st.selectbox("🌿 筛选中药", herb_options, key="kg_herb")
        with col2:
            gene_options = ["全部"]
            if "gene_symbol" in hg_df.columns:
                gene_options += sorted(hg_df["gene_symbol"].dropna().unique().tolist())
            sel_gene = st.selectbox("🧬 筛选基因", gene_options, key="kg_gene")
        with col3:
            conf = st.slider("置信度阈值", 0.0, 1.0, 0.7, 0.05, key="kg_conf")

        c4, c5 = st.columns(2)
        show_dis = c4.checkbox("显示疾病节点", value=True,  key="kg_dis")
        show_pw  = c5.checkbox("显示通路节点", value=False, key="kg_pw")

        if st.button("🔄 重置筛选", use_container_width=True):
            st.rerun()

    with st.spinner("🔄 正在构建知识图谱..."):
        html_code, n_h, n_g = build_network_html(
            hg_df=hg_df,
            mapping_df=mapping_df,
            min_confidence=conf,
            selected_herb=sel_herb,
            selected_gene=sel_gene,
            disease_df=disease_df,
            pathway_df_h=pathway_herb_df,
            show_disease=show_dis,
            show_pathway=show_pw,
        )

    # ── 修复点：用返回值 n_h/n_g 判断，不再引用局部变量 nodes ──
    if html_code and n_h > 0:
        st.success(f"✅ 图谱生成成功：**{n_h}** 味中药 · **{n_g}** 个基因")
        components.html(html_code, height=720, scrolling=False)
    else:
        st.warning("⚠️ 当前数据不足或筛选后无结果，请降低置信度阈值或重置筛选条件")


if __name__ == "__main__":
    test_df = pd.DataFrame({
        "herb_name":        ["Curcumin", "Berberine", "Ginseng"],
        "gene_symbol":      ["PTEN",     "AKT1",      "TP53"],
        "interaction_type": ["inhibit",  "activate",  "modulate"],
        "confidence_score": [0.92,       0.85,        0.78],
    })
    render_knowledge_graph(hg_df=test_df)
