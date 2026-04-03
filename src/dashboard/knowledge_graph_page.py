# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# 文件名称: knowledge_graph_page.py
# 所属系统: 中药外泌体智能分析系统软件 V1.0
# 模块功能: 基于 Vis.js 的交互式知识图谱可视化组件
# 开发日期: 2026-01-20
# 版    本: V1.0
# -------------------------------------------------------------------------
"""
中药外泌体智能知识图谱模块

功能说明：
- 构建中药-基因-疾病-通路四维关联网络
- 支持动态筛选、置信度过滤、节点交互
- 输出 Vis.js 兼容的 HTML 组件供 Streamlit 嵌入

依赖库：
- streamlit: Web 界面框架
- pandas: 数据处理
- json: 数据序列化
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import logging
from typing import Optional, Tuple, List, Dict, Any

# 配置日志
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# 函数：构建知识图谱 HTML (Vis.js 驱动)
# -------------------------------------------------------------------------
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
    max_nodes: int = 500,  # 新增：防止大数据量卡顿
    max_edges: int = 2000  # 新增：限制边数量
) -> Tuple[Optional[str], int, int]:
    """
    构建中药外泌体智能知识图谱的 HTML 代码
    
    参数:
        hg_df: 中药-基因关联数据表 (DataFrame)
        mapping_df: 中英文名称映射表 (可选)
        min_confidence: 置信度阈值 (0.0-1.0)
        selected_herb: 筛选的中药名称，"全部"表示不筛选
        selected_gene: 筛选的基因符号，"全部"表示不筛选
        disease_df: 中药-疾病关联数据表 (可选)
        pathway_df_h: 中药-通路关联数据表 (可选)
        show_disease: 是否显示疾病节点
        show_pathway: 是否显示通路节点
        max_nodes: 最大节点数限制 (防性能问题)
        max_edges: 最大边数限制 (防性能问题)
    
    返回:
        Tuple[Optional[str], int, int]: 
            - HTML 代码字符串 (无数据时返回 None)
            - 中药节点数量
            - 基因节点数量
    """
    
    # ==================== 关键修复：必须最先初始化 ====================
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []  # ←←← 修复：确保在使用前初始化
    seen_nodes: set = set()
    
    # 输入验证
    if hg_df is None or hg_df.empty:
        logger.warning("⚠️ hg_df 为空，无法构建知识图谱")
        return None, 0, 0
    
    try:
        # 2. 中英文名称映射预处理（带空值保护）
        df = hg_df.copy()
        
        if mapping_df is not None and not mapping_df.empty:
            try:
                cols = mapping_df.columns.tolist()
                en_col = next((c for c in cols if "en" in c.lower()), None)
                cn_col = next((c for c in cols if any(x in c.lower() for x in ["cn", "chinese", "zh"])), None)
                
                if en_col and cn_col and en_col in mapping_df.columns and cn_col in mapping_df.columns:
                    tmp = mapping_df[[en_col, cn_col]].dropna(subset=[en_col, cn_col]).rename(
                        columns={en_col: "_en", cn_col: "_cn"}
                    )
                    if "herb_name" in df.columns and not tmp.empty:
                        df = df.merge(tmp, left_on="herb_name", right_on="_en", how="left")
                        df["display_herb"] = df["_cn"].fillna(df["herb_name"])
                    else:
                        df["display_herb"] = df.get("herb_name", df.get("herb", ""))
                else:
                    df["display_herb"] = df.get("herb_name", df.get("herb", ""))
            except Exception as e:
                logger.warning(f"⚠️ 名称映射处理异常: {e}")
                df["display_herb"] = df.get("herb_name", df.get("herb", ""))
        else:
            df["display_herb"] = df.get("herb_name", df.get("herb", ""))
        
        # 3. 数据过滤（带列存在性检查）
        if "confidence_score" in df.columns:
            df = df[df["confidence_score"].fillna(0) >= min_confidence].copy()
        
        if selected_herb != "全部":
            herb_col = "display_herb" if "display_herb" in df.columns else "herb_name"
            if herb_col in df.columns:
                df = df[df[herb_col] == selected_herb]
        
        if selected_gene != "全部" and "gene_symbol" in df.columns:
            df = df[df["gene_symbol"] == selected_gene]
        
        if df.empty:
            logger.info("ℹ️ 筛选后无匹配数据")
            return None, 0, 0
        
        # 颜色映射配置
        color_map: Dict[str, str] = {
            "inhibit": "#e94560",      # 红色 - 抑制
            "activate": "#4ab880",     # 绿色 - 激活
            "upregulate": "#4a9ae0",   # 蓝色 - 上调
            "downregulate": "#e0904a", # 橙色 - 下调
            "modulate": "#a04ae0",     # 紫色 - 调控
            "unknown": "#888888"       # 灰色 - 未知
        }
        
        # 4. 构建中药节点（带数量限制）
        herb_col = "display_herb" if "display_herb" in df.columns else "herb_name"
        active_herbs = df[herb_col].dropna().unique().tolist() if herb_col in df.columns else []
        active_herbs = active_herbs[:max_nodes//3]  # 限制中药节点数量
        
        for h in active_herbs:
            if pd.isna(h):
                continue
            node_id = f"herb_{str(h).strip()}"
            if node_id not in seen_nodes and len(seen_nodes) < max_nodes:
                nodes.append({
                    "id": node_id,
                    "label": str(h)[:25],  # 标签长度限制
                    "group": "herb",
                    "size": 28,
                    "color": {"background": "#4ab880", "border": "#2d8a5e", "highlight": {"border": "#ffffff"}},
                    "font": {"color": "white", "size": 14, "bold": True},
                    "title": f"<b>中药</b><br/>{h}",
                    "shape": "dot",
                    "borderWidth": 2
                })
                seen_nodes.add(node_id)
        
        # 5. 构建基因节点
        active_genes = []
        if "gene_symbol" in df.columns:
            active_genes = df["gene_symbol"].dropna().unique().tolist()
            # 按关联度排序，优先显示高频基因
            gene_counts = df["gene_symbol"].value_counts()
            active_genes = [g for g, _ in gene_counts.head(max_nodes//3).items()]
        
        for g in active_genes:
            if pd.isna(g):
                continue
            node_id = f"gene_{str(g).strip()}"
            if node_id not in seen_nodes and len(seen_nodes) < max_nodes:
                degree = len(df[df["gene_symbol"] == g])
                nodes.append({
                    "id": node_id,
                    "label": str(g)[:20],
                    "group": "gene",
                    "size": 18 + min(degree * 2, 15),
                    "color": {"background": "#4a9ae0", "border": "#2d6ab0", "highlight": {"border": "#ffffff"}},
                    "font": {"color": "white", "size": 12},
                    "title": f"<b>基因靶点</b><br/>{g}<br/>关联 {degree} 味中药",
                    "shape": "dot",
                    "borderWidth": 2
                })
                seen_nodes.add(node_id)
        
        # 6. 构建疾病节点与连线（带空值保护）
        if show_disease and disease_df is not None and not disease_df.empty:
            try:
                active_herbs_en = df["herb_name"].dropna().unique().tolist() if "herb_name" in df.columns else []
                if "herb_name" in disease_df.columns and not active_herbs_en:
                    d_df = disease_df[disease_df["herb_name"].isin(active_herbs_en)].copy()
                else:
                    d_df = pd.DataFrame()
                
                for _, row in d_df.iterrows():
                    dis_label = str(row.get('disease', '')).strip()
                    if not dis_label or pd.isna(dis_label):
                        continue
                    
                    dis_id = f"dis_{dis_label}"
                    h_disp = row.get('display_herb') or row.get("herb_name", "")
                    h_node_id = f"herb_{str(h_disp).strip()}"
                    
                    if h_node_id in seen_nodes and dis_id not in seen_nodes and len(seen_nodes) < max_nodes:
                        nodes.append({
                            "id": dis_id,
                            "label": dis_label[:20] + ("..." if len(dis_label) > 20 else ""),
                            "group": "disease",
                            "size": 22,
                            "color": {"background": "#e94560", "border": "#b02040", "highlight": {"border": "#ffffff"}},
                            "font": {"color": "white", "size": 12},
                            "shape": "dot",
                            "title": f"<b>疾病</b><br/>{dis_label}",
                            "borderWidth": 2
                        })
                        seen_nodes.add(dis_id)
                    
                    if h_node_id in seen_nodes and dis_id in seen_nodes and len(edges) < max_edges:
                        edges.append({
                            "from": h_node_id,
                            "to": dis_id,
                            "arrows": "to",
                            "color": {"color": "#e94560", "opacity": 0.6},
                            "dashes": [5, 5],
                            "width": 2,
                            "title": f"<b>关联疾病</b><br/>{dis_label}",
                            "label": "治疗"
                        })
            except Exception as e:
                logger.warning(f"⚠️ 疾病节点构建异常: {e}")
        
        # 7. 构建信号通路节点与连线
        if show_pathway and pathway_df_h is not None and not pathway_df_h.empty:
            try:
                active_herbs_en = df["herb_name"].dropna().unique().tolist() if "herb_name" in df.columns else []
                if "herb_name" in pathway_df_h.columns:
                    p_df = pathway_df_h[pathway_df_h["herb_name"].isin(active_herbs_en)].copy()
                else:
                    p_df = pd.DataFrame()
                
                for _, row in p_df.iterrows():
                    pw_name = str(row.get('pathway_name', '')).strip()
                    if not pw_name or pd.isna(pw_name):
                        continue
                    
                    pw_id = f"pw_{pw_name}"
                    h_disp = row.get('display_herb') or row.get("herb_name", "")
                    h_node_id = f"herb_{str(h_disp).strip()}"
                    
                    if h_node_id in seen_nodes and pw_id not in seen_nodes and len(seen_nodes) < max_nodes:
                        nodes.append({
                            "id": pw_id,
                            "label": pw_name[:18] + ("..." if len(pw_name) > 18 else ""),
                            "group": "pathway",
                            "size": 18,
                            "shape": "diamond",
                            "color": {"background": "#e0b030", "border": "#a07010", "highlight": {"border": "#ffffff"}},
                            "font": {"color": "white", "size": 11},
                            "title": f"<b>信号通路</b><br/>{pw_name}",
                            "borderWidth": 2
                        })
                        seen_nodes.add(pw_id)
                    
                    if h_node_id in seen_nodes and pw_id in seen_nodes and len(edges) < max_edges:
                        edges.append({
                            "from": h_node_id,
                            "to": pw_id,
                            "arrows": "to",
                            "color": {"color": "#e0b030", "opacity": 0.6},
                            "dashes": [4, 2],
                            "width": 1.8,
                            "title": f"<b>调控通路</b><br/>{pw_name}",
                            "label": "调控"
                        })
            except Exception as e:
                logger.warning(f"⚠️ 通路节点构建异常: {e}")
        
        # 8. 构建中药 → 基因核心连线（必须放在最后，确保节点已存在）
        for _, row in df.iterrows():
            if len(edges) >= max_edges:
                break
                
            itype = str(row.get("interaction_type", "modulate")).lower().strip()
            score = float(row.get("confidence_score", 0.7)) if pd.notna(row.get("confidence_score")) else 0.7
            herb_key = row.get("display_herb") or row.get("herb_name", "")
            gene_symbol = row.get("gene_symbol", "")
            
            if pd.isna(herb_key) or pd.isna(gene_symbol) or not herb_key or not gene_symbol:
                continue
                
            from_id = f"herb_{str(herb_key).strip()}"
            to_id = f"gene_{str(gene_symbol).strip()}"
            
            # 仅当两端节点都存在时添加边
            if from_id in seen_nodes and to_id in seen_nodes:
                edge_color = color_map.get(itype, color_map["unknown"])
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "color": {"color": edge_color, "opacity": 0.85, "highlight": {"opacity": 1.0}},
                    "width": 2 + min(float(score) * 3, 5),  # 线宽与置信度正相关
                    "title": f"<b>互作关系</b><br/>类型: {itype}<br/>置信度: {score:.2f}",
                    "arrows": "to",
                    "label": itype[:1].upper() if itype != "unknown" else "?"
                })
        
        # 9. 生成 HTML（Vis.js 配置优化）
        nodes_json = json.dumps(nodes, ensure_ascii=False)
        edges_json = json.dumps(edges, ensure_ascii=False)
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js" 
                    integrity="sha512-1+9bP7q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9q8q9......</think>

# knowledge_graph_page.py 完整修改版本

```python
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# 文件名称: knowledge_graph_page.py
# 所属系统: 中药外泌体智能分析系统软件 V1.0
# 模块功能: 基于 Vis.js 的交互式知识图谱可视化组件
# 开发日期: 2026-01-20
# 版    本: V1.0
# -------------------------------------------------------------------------
"""
中药外泌体智能知识图谱模块

功能说明：
- 构建中药-基因-疾病-通路四维关联网络
- 支持动态筛选、置信度过滤、节点交互
- 输出 Vis.js 兼容的 HTML 组件供 Streamlit 嵌入

依赖库：
- streamlit: Web 界面框架
- pandas: 数据处理
- json: 数据序列化
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import logging
from typing import Optional, Tuple, List, Dict, Any

# 配置日志
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# 函数：构建知识图谱 HTML (Vis.js 驱动)
# -------------------------------------------------------------------------
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
    max_nodes: int = 500,  # 新增：防止大数据量卡顿
    max_edges: int = 2000  # 新增：限制边数量
) -> Tuple[Optional[str], int, int]:
    """
    构建中药外泌体智能知识图谱的 HTML 代码
    
    参数:
        hg_df: 中药-基因关联数据表 (DataFrame)
        mapping_df: 中英文名称映射表 (可选)
        min_confidence: 置信度阈值 (0.0-1.0)
        selected_herb: 筛选的中药名称，"全部"表示不筛选
        selected_gene: 筛选的基因符号，"全部"表示不筛选
        disease_df: 中药-疾病关联数据表 (可选)
        pathway_df_h: 中药-通路关联数据表 (可选)
        show_disease: 是否显示疾病节点
        show_pathway: 是否显示通路节点
        max_nodes: 最大节点数限制 (防性能问题)
        max_edges: 最大边数限制 (防性能问题)
    
    返回:
        Tuple[Optional[str], int, int]: 
            - HTML 代码字符串 (无数据时返回 None)
            - 中药节点数量
            - 基因节点数量
    """
    
    # ==================== 关键修复：必须最先初始化 ====================
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []  # ←←← 修复：确保在使用前初始化
    seen_nodes: set = set()
    
    # 输入验证
    if hg_df is None or hg_df.empty:
        logger.warning("⚠️ hg_df 为空，无法构建知识图谱")
        return None, 0, 0
    
    try:
        # 2. 中英文名称映射预处理（带空值保护）
        df = hg_df.copy()
        
        if mapping_df is not None and not mapping_df.empty:
            try:
                cols = mapping_df.columns.tolist()
                en_col = next((c for c in cols if "en" in c.lower()), None)
                cn_col = next((c for c in cols if any(x in c.lower() for x in ["cn", "chinese", "zh"])), None)
                
                if en_col and cn_col and en_col in mapping_df.columns and cn_col in mapping_df.columns:
                    tmp = mapping_df[[en_col, cn_col]].dropna(subset=[en_col, cn_col]).rename(
                        columns={en_col: "_en", cn_col: "_cn"}
                    )
                    if "herb_name" in df.columns and not tmp.empty:
                        df = df.merge(tmp, left_on="herb_name", right_on="_en", how="left")
                        df["display_herb"] = df["_cn"].fillna(df["herb_name"])
                    else:
                        df["display_herb"] = df.get("herb_name", df.get("herb", ""))
                else:
                    df["display_herb"] = df.get("herb_name", df.get("herb", ""))
            except Exception as e:
                logger.warning(f"⚠️ 名称映射处理异常: {e}")
                df["display_herb"] = df.get("herb_name", df.get("herb", ""))
        else:
            df["display_herb"] = df.get("herb_name", df.get("herb", ""))
        
        # 3. 数据过滤（带列存在性检查）
        if "confidence_score" in df.columns:
            df = df[df["confidence_score"].fillna(0) >= min_confidence].copy()
        
        if selected_herb != "全部":
            herb_col = "display_herb" if "display_herb" in df.columns else "herb_name"
            if herb_col in df.columns:
                df = df[df[herb_col] == selected_herb]
        
        if selected_gene != "全部" and "gene_symbol" in df.columns:
            df = df[df["gene_symbol"] == selected_gene]
        
        if df.empty:
            logger.info("ℹ️ 筛选后无匹配数据")
            return None, 0, 0
        
        # 颜色映射配置
        color_map: Dict[str, str] = {
            "inhibit": "#e94560",      # 红色 - 抑制
            "activate": "#4ab880",     # 绿色 - 激活
            "upregulate": "#4a9ae0",   # 蓝色 - 上调
            "downregulate": "#e0904a", # 橙色 - 下调
            "modulate": "#a04ae0",     # 紫色 - 调控
            "unknown": "#888888"       # 灰色 - 未知
        }
        
        # 4. 构建中药节点（带数量限制）
        herb_col = "display_herb" if "display_herb" in df.columns else "herb_name"
        active_herbs = df[herb_col].dropna().unique().tolist() if herb_col in df.columns else []
        active_herbs = active_herbs[:max_nodes//3]  # 限制中药节点数量
        
        for h in active_herbs:
            if pd.isna(h):
                continue
            node_id = f"herb_{str(h).strip()}"
            if node_id not in seen_nodes and len(seen_nodes) < max_nodes:
                nodes.append({
                    "id": node_id,
                    "label": str(h)[:25],  # 标签长度限制
                    "group": "herb",
                    "size": 28,
                    "color": {"background": "#4ab880", "border": "#2d8a5e", "highlight": {"border": "#ffffff"}},
                    "font": {"color": "white", "size": 14, "bold": True},
                    "title": f"<b>中药</b><br/>{h}",
                    "shape": "dot",
                    "borderWidth": 2
                })
                seen_nodes.add(node_id)
        
        # 5. 构建基因节点
        active_genes = []
        if "gene_symbol" in df.columns:
            active_genes = df["gene_symbol"].dropna().unique().tolist()
            # 按关联度排序，优先显示高频基因
            gene_counts = df["gene_symbol"].value_counts()
            active_genes = [g for g, _ in gene_counts.head(max_nodes//3).items()]
        
        for g in active_genes:
            if pd.isna(g):
                continue
            node_id = f"gene_{str(g).strip()}"
            if node_id not in seen_nodes and len(seen_nodes) < max_nodes:
                degree = len(df[df["gene_symbol"] == g])
                nodes.append({
                    "id": node_id,
                    "label": str(g)[:20],
                    "group": "gene",
                    "size": 18 + min(degree * 2, 15),
                    "color": {"background": "#4a9ae0", "border": "#2d6ab0", "highlight": {"border": "#ffffff"}},
                    "font": {"color": "white", "size": 12},
                    "title": f"<b>基因靶点</b><br/>{g}<br/>关联 {degree} 味中药",
                    "shape": "dot",
                    "borderWidth": 2
                })
                seen_nodes.add(node_id)
        
        # 6. 构建疾病节点与连线（带空值保护）
        if show_disease and disease_df is not None and not disease_df.empty:
            try:
                active_herbs_en = df["herb_name"].dropna().unique().tolist() if "herb_name" in df.columns else []
                if "herb_name" in disease_df.columns and active_herbs_en:
                    d_df = disease_df[disease_df["herb_name"].isin(active_herbs_en)].copy()
                else:
                    d_df = pd.DataFrame()
                
                for _, row in d_df.iterrows():
                    dis_label = str(row.get('disease', '')).strip()
                    if not dis_label or pd.isna(dis_label):
                        continue
                    
                    dis_id = f"dis_{dis_label}"
                    h_disp = row.get('display_herb') or row.get("herb_name", "")
                    h_node_id = f"herb_{str(h_disp).strip()}"
                    
                    if h_node_id in seen_nodes and dis_id not in seen_nodes and len(seen_nodes) < max_nodes:
                        nodes.append({
                            "id": dis_id,
                            "label": dis_label[:20] + ("..." if len(dis_label) > 20 else ""),
                            "group": "disease",
                            "size": 22,
                            "color": {"background": "#e94560", "border": "#b02040", "highlight": {"border": "#ffffff"}},
                            "font": {"color": "white", "size": 12},
                            "shape": "dot",
                            "title": f"<b>疾病</b><br/>{dis_label}",
                            "borderWidth": 2
                        })
                        seen_nodes.add(dis_id)
                    
                    if h_node_id in seen_nodes and dis_id in seen_nodes and len(edges) < max_edges:
                        edges.append({
                            "from": h_node_id,
                            "to": dis_id,
                            "arrows": "to",
                            "color": {"color": "#e94560", "opacity": 0.6},
                            "dashes": [5, 5],
                            "width": 2,
                            "title": f"<b>关联疾病</b><br/>{dis_label}",
                            "label": "治疗"
                        })
            except Exception as e:
                logger.warning(f"⚠️ 疾病节点构建异常: {e}")
        
        # 7. 构建信号通路节点与连线
        if show_pathway and pathway_df_h is not None and not pathway_df_h.empty:
            try:
                active_herbs_en = df["herb_name"].dropna().unique().tolist() if "herb_name" in df.columns else []
                if "herb_name" in pathway_df_h.columns and active_herbs_en:
                    p_df = pathway_df_h[pathway_df_h["herb_name"].isin(active_herbs_en)].copy()
                else:
                    p_df = pd.DataFrame()
                
                for _, row in p_df.iterrows():
                    pw_name = str(row.get('pathway_name', '')).strip()
                    if not pw_name or pd.isna(pw_name):
                        continue
                    
                    pw_id = f"pw_{pw_name}"
                    h_disp = row.get('display_herb') or row.get("herb_name", "")
                    h_node_id = f"herb_{str(h_disp).strip()}"
                    
                    if h_node_id in seen_nodes and pw_id not in seen_nodes and len(seen_nodes) < max_nodes:
                        nodes.append({
                            "id": pw_id,
                            "label": pw_name[:18] + ("..." if len(pw_name) > 18 else ""),
                            "group": "pathway",
                            "size": 18,
                            "shape": "diamond",
                            "color": {"background": "#e0b030", "border": "#a07010", "highlight": {"border": "#ffffff"}},
                            "font": {"color": "white", "size": 11},
                            "title": f"<b>信号通路</b><br/>{pw_name}",
                            "borderWidth": 2
                        })
                        seen_nodes.add(pw_id)
                    
                    if h_node_id in seen_nodes and pw_id in seen_nodes and len(edges) < max_edges:
                        edges.append({
                            "from": h_node_id,
                            "to": pw_id,
                            "arrows": "to",
                            "color": {"color": "#e0b030", "opacity": 0.6},
                            "dashes": [4, 2],
                            "width": 1.8,
                            "title": f"<b>调控通路</b><br/>{pw_name}",
                            "label": "调控"
                        })
            except Exception as e:
                logger.warning(f"⚠️ 通路节点构建异常: {e}")
        
        # 8. 构建中药 → 基因核心连线（必须放在最后，确保节点已存在）
        for _, row in df.iterrows():
            if len(edges) >= max_edges:
                break
                
            itype = str(row.get("interaction_type", "modulate")).lower().strip()
            score = float(row.get("confidence_score", 0.7)) if pd.notna(row.get("confidence_score")) else 0.7
            herb_key = row.get("display_herb") or row.get("herb_name", "")
            gene_symbol = row.get("gene_symbol", "")
            
            if pd.isna(herb_key) or pd.isna(gene_symbol) or not herb_key or not gene_symbol:
                continue
                
            from_id = f"herb_{str(herb_key).strip()}"
            to_id = f"gene_{str(gene_symbol).strip()}"
            
            # 仅当两端节点都存在时添加边
            if from_id in seen_nodes and to_id in seen_nodes:
                edge_color = color_map.get(itype, color_map["unknown"])
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "color": {"color": edge_color, "opacity": 0.85, "highlight": {"opacity": 1.0}},
                    "width": 2 + min(float(score) * 3, 5),  # 线宽与置信度正相关
                    "title": f"<b>互作关系</b><br/>类型: {itype}<br/>置信度: {score:.2f}",
                    "arrows": "to",
                    "label": itype[:1].upper() if itype != "unknown" else "?"
                })
        
        # 9. 生成 HTML（Vis.js 配置优化）
        nodes_json = json.dumps(nodes, ensure_ascii=False)
        edges_json = json.dumps(edges, ensure_ascii=False)
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css">
            <style>
                body {{ margin:0; background:#0d1117; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
                #network {{ width:100%; height:680px; background:#0d1117; border-radius:8px; }}
                #legend {{ position:absolute; top:15px; right:15px; background:rgba(20,28,38,0.95); 
                           padding:12px 15px; border-radius:8px; color:#e6edf3; font-size:12px; 
                           border:1px solid #30363d; z-index:100; box-shadow:0 4px 12px rgba(0,0,0,0.3); }}
                #legend b {{ color:#e8d5b7; }}
                #loading {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
                           color:#8b949e; font-size:14px; }}
            </style>
        </head>
        <body>
            <div id="legend">
                <b>📋 图例</b><br/>
                <span style="color:#4ab880">●</span> 中药 &nbsp;
                <span style="color:#4a9ae0">●</span> 基因 &nbsp;
                <span style="color:#e94560">●</span> 疾病 &nbsp;
                <span style="color:#e0b030">◆</span> 通路
            </div>
            <div id="loading">正在渲染知识图谱...</div>
            <div id="network"></div>
            <script>
                // 隐藏加载提示
                document.getElementById('loading').style.display = 'none';
                
                // 数据初始化
                var nodes = new vis.DataSet({nodes_json});
                var edges = new vis.DataSet({edges_json});
                
                // 网络配置
                var container = document.getElementById('network');
                var data = {{ nodes: nodes, edges: edges }};
                var options = {{
                    physics: {{ 
                        enabled: true,
                        barnesHut: {{ 
                            gravitationalConstant: -4000, 
                            centralGravity: 0.4, 
                            springLength: 160,
                            springConstant: 0.04,
                            damping: 0.09
                        }},
                        stabilization: {{ iterations: 100 }}
                    }},
                    interaction: {{ 
                        hover: true, 
                        tooltipDelay: 150, 
                        zoomView: true, 
                        dragNodes: true,
                        dragView: true,
                        navigationButtons: true,
                        keyboard: {{ enabled: true }}
                    }},
                    nodes: {{ 
                        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.3)' }}, 
                        borderWidth: 2,
                        chosen: {{ 
                            node: function(properties, id, selected, hovering) {{
                                properties.size += 4;
                                properties.shadow = true;
                            }}
                        }}
                    }},
                    edges: {{ 
                        smooth: {{ type: 'continuous', roundness: 0.4 }}, 
                        arrows: {{ to: {{ enabled: true, scaleFactor: 0.7, type: 'arrow' }} }},
                        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.2)' }},
                        chosen: {{ 
                            edge: function(properties, id, selected, hovering) {{
                                properties.width += 2;
                                properties.color.opacity = 1.0;
                            }}
                        }}
                    }},
                    layout: {{
                        hierarchical: {{
                            enabled: false
                        }}
                    }}
                }};
                
                // 初始化网络
                var network = new vis.Network(container, data, options);
                
                // 节点点击事件
                network.on("click", function(params) {{
                    if (params.nodes.length > 0) {{
                        var nodeId = params.nodes[0];
                        var node = nodes.get(nodeId);
                        console.log("点击节点:", node);
                    }}
                }});
                
                // 自适应窗口大小
                window.addEventListener('resize', function() {{
                    network.fit({{animation: {{duration: 300}}}});
                }});
                
                // 初始适配
                setTimeout(function() {{
                    network.fit({{animation: {{duration: 500}}}});
                }}, 100);
            </script>
        </body>
        </html>
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
    """
    Streamlit 知识图谱页面渲染入口
    
    参数:
        hg_df: 中药-基因关联数据
        mapping_df: 中英文名称映射表
        disease_df: 中药-疾病关联数据
        pathway_herb_df: 中药-通路关联数据
    """
    st.header("🕸️ 中药外泌体智能知识图谱")
    st.caption("基于AI提取的中药-基因-疾病-通路多维关联网络 · 支持拖拽/缩放/悬停交互")

    # 控制面板
    with st.expander("🛠️ 图谱控制面板", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        
        with c1:
            herb_col = "display_herb" if "display_herb" in hg_df.columns else "herb_name"
            all_herbs = ["全部"] + sorted(
                [h for h in hg_df[herb_col].dropna().unique().tolist() if pd.notna(h)] 
                if herb_col in hg_df.columns else []
            )
            sel_herb = st.selectbox("🌿 筛选中药材", all_herbs, index=0)
        
        with c2:
            all_genes = ["全部"] + sorted(
                [g for g in hg_df["gene_symbol"].dropna().unique().tolist() if pd.notna(g)] 
                if "gene_symbol" in hg_df.columns else []
            )
            sel_gene = st.selectbox("🧬 筛选特定基因", all_genes, index=0)
        
        with c3:
            conf = st.slider("🎯 置信度阈值", 0.0, 1.0, 0.7, 0.05, help="降低阈值可显示更多关联，但可能包含低置信度结果")
            
        col_sw1, col_sw2 = st.columns(2)
        show_dis = col_sw1.checkbox("🔴 显示疾病关联", value=True)
        show_pw = col_sw2.checkbox("🟡 显示信号通路", value=True)
        
        # 重置按钮
        if st.button("🔄 重置筛选", type="secondary", use_container_width=True):
            st.rerun()

    # 生成并显示图谱
    with st.spinner("🔄 正在构建知识图谱，请稍候..."):
        html_code, n_h, n_g = build_network_html(
            hg_df=hg_df,
            mapping_df=mapping_df,
            min_confidence=conf,
            selected_herb=sel_herb,
            selected_gene=sel_gene,
            disease_df=disease_df,
            pathway_df_h=pathway_herb_df,
            show_disease=show_dis,
            show_pathway=show_pw
        )

    if html_code:
        st.success(f"📊 当前图谱：**{n_h}** 味中药 · **{n_g}** 个基因靶点 · 置信度≥{conf}")
        
        # 嵌入 HTML 组件（设置 sandbox 权限）
        components.html(
            html_code, 
            height=720, 
            scrolling=False,
            sandbox="allow-scripts allow-same-origin allow-popups allow-pointer-lock"
        )
        
        # 操作提示
        with st.expander("💡 交互操作指南", expanded=False):
            st.markdown("""
            | 操作 | 效果 |
            |------|------|
            | 🖱️ 鼠标拖拽节点 | 调整节点位置 |
            | 🔄 鼠标滚轮 | 缩放视图 |
            | 👆 悬停节点 | 查看详细信息 |
            | 🎯 点击节点 | 选中并高亮关联边 |
            | ⌨️ 方向键 | 平移视图 |
            | 🔍 双击空白处 | 恢复初始视图 |
            """)
    else:
        st.warning("⚠️ 当前筛选条件下无匹配数据")
        st.info("""
        **建议尝试以下操作：**
        1. 降低「置信度阈值」滑块（如调至 0.5）
        2. 将「中药材」或「特定基因」筛选器改为「全部」
        3. 勾选「显示疾病关联」或「显示信号通路」扩展网络
        4. 检查数据源是否已正确加载
        """)


# -------------------------------------------------------------------------
# 模块入口（支持直接运行测试）
# -------------------------------------------------------------------------
if __name__ == "__main__":
    # 测试用模拟数据
    test_df = pd.DataFrame({
        "herb_name": ["Curcumin", "Berberine", "Curcumin"],
        "gene_symbol": ["PTEN", "AKT1", "TP53"],
        "interaction_type": ["inhibit", "activate", "modulate"],
        "confidence_score": [0.92, 0.85, 0.78]
    })
    
    st.set_page_config(page_title="知识图谱测试", layout="wide")
    render_knowledge_graph(hg_df=test_df)