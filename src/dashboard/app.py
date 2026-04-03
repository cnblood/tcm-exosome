# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# 文件名称: app_v2.py
# 所属系统: 中药外泌体智能分析系统软件 V1.0
# 模块功能: Streamlit 主应用入口，页面路由与全局状态管理
# 开发日期: 2026-01-20
# -------------------------------------------------------------------------
import os
import sys
import warnings


# 忽略特定 RuntimeWarning（expire_cache）
warnings.filterwarnings("ignore", message="coroutine 'expire_cache' was never awaited")


# 添加项目路径（防止 src 模块问题）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

print(f"🔧 项目根路径已添加: {project_root}")
# =====================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
import logging
from datetime import datetime
from functools import lru_cache

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到路径（兼容本地/容器部署）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client, Client

# ====================== 页面配置 ======================
st.set_page_config(
    page_title="TCM-Exosome 中药外泌体智能分析平台",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== 全局样式 ======================
st.markdown("""
<style>
    /* 全局主题色 */
    :root {
        --primary: #4ab880;
        --secondary: #4a9ae0;
        --accent: #e94560;
        --bg-dark: #0d1117;
        --bg-card: #161b22;
        --text-main: #e6edf3;
        --text-muted: #8b949e;
    }
    /* 指标卡片样式 */
    .metric-card {
        background: linear-gradient(135deg, var(--bg-card), #1a2535);
        border: 1px solid var(--secondary)40;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        transition: border-color 0.2s, transform 0.2s;
    }
    .metric-card:hover {
        border-color: var(--secondary);
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: var(--secondary);
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.82rem;
        color: var(--text-muted);
        margin-top: 4px;
    }
    /* Hero 区域渐变背景 */
    .hero {
        background: linear-gradient(135deg, #0d1117, #1a2535, #0d2020);
        border: 1px solid #2a4a3a;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: "🧬";
        position: absolute;
        right: 32px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 120px;
        opacity: 0.04;
        pointer-events: none;
    }
    /* 文献列表项 */
    .paper-item {
        padding: 10px 0;
        border-bottom: 1px solid #1a2535;
    }
    .paper-item:last-child { border-bottom: none; }
    .paper-source {
        background: #1a3a5a;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.7rem;
        color: #4a9ae0;
    }
    .paper-date { color: #6b7280; font-size: 0.72rem; margin-left: 6px; }
    .paper-title { color: #c8d8e8; font-size: 0.85rem; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ====================== 数据库连接（带缓存） ======================
@st.cache_resource
def get_supabase():
    """获取 Supabase 客户端实例（单例缓存）"""
    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    supabase_key = os.environ.get("SUPABASE_KEY", "").strip()
    
    if not supabase_url or not supabase_key:
        logger.warning("⚠️ SUPABASE_URL 或 SUPABASE_KEY 未配置，数据库功能将受限")
        st.sidebar.warning("⚠️ 环境变量未配置完整，部分功能可能不可用")
        return None
    
    try:
        client = create_client(supabase_url, supabase_key)
        # 测试连接
        client.table("research_papers").select("id").limit(1).execute()
        logger.info("✓ Supabase 连接成功")
        return client
    except Exception as e:
        logger.error(f"✗ Supabase 连接失败: {e}")
        st.sidebar.error(f"数据库连接异常: {str(e)[:100]}")
        return None

# ====================== 数据加载（带缓存+分页+异常处理） ======================
@st.cache_data(ttl=600, show_spinner="正在加载数据...")
def load_table(table_name: str, limit: int = 5000):
    """
    分页加载指定表数据，支持大数据量场景
    
    参数:
        table_name: Supabase 表名
        limit: 单次加载最大记录数（防内存溢出）
    
    返回:
        pd.DataFrame: 查询结果
    """
    client = get_supabase()
    if not client:
        return pd.DataFrame()
    
    all_data = []
    page_size = 1000
    
    try:
        for offset in range(0, limit, page_size):
            response = client.table(table_name)\
                .select("*")\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if not response.data:
                break
                
            all_data.extend(response.data)
            
            # 提前终止：如果返回数据不足一页，说明已到末尾
            if len(response.data) < page_size:
                break
                
        if not all_data:
            logger.info(f"表 [{table_name}] 无数据或查询为空")
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        logger.info(f"✓ 加载 [{table_name}] {len(df)} 条记录")
        return df
        
    except Exception as e:
        logger.error(f"✗ 加载表 [{table_name}] 失败: {e}")
        st.toast(f"⚠️ 数据加载异常: {table_name}", icon="⚠️")
        return pd.DataFrame()

# ====================== 书签管理功能 ======================
def add_bookmark(paper_id: str, importance: int = 3, notes: str = "", tag: str = "default") -> bool:
    """添加文献收藏"""
    client = get_supabase()
    if not client:
        return False
    try:
        client.table("user_bookmarks").upsert({
            "paper_id": paper_id,
            "importance": importance,
            "notes": notes,
            "user_tag": tag,
            "updated_at": datetime.now().isoformat()
        }, on_conflict="paper_id,user_tag").execute()
        logger.info(f"✓ 添加收藏: paper_id={paper_id}")
        return True
    except Exception as e:
        logger.error(f"✗ 添加收藏失败: {e}")
        return False

def remove_bookmark(paper_id: str, tag: str = "default") -> bool:
    """移除文献收藏"""
    client = get_supabase()
    if not client:
        return False
    try:
        client.table("user_bookmarks")\
            .delete()\
            .eq("paper_id", paper_id)\
            .eq("user_tag", tag)\
            .execute()
        logger.info(f"✓ 移除收藏: paper_id={paper_id}")
        return True
    except Exception as e:
        logger.error(f"✗ 移除收藏失败: {e}")
        return False

# ====================== 侧边栏导航 ======================
with st.sidebar:
    st.markdown("## 🧬 TCM-Exosome")
    st.markdown("---")
    
    page = st.radio(
        "导航菜单",
        [
            "🏠 系统概览",
            "🔍 智能检索", 
            "📚 文献库",
            "🏥 临床试验",
            "🧬 基因组学",
            "📖 药典查询",
            "🕸️ 知识图谱",
            "📊 分析报告",
            "⚙️ 爬虫监控"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # 数据更新时间
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.caption(f"🔄 数据更新: {last_update}")
    
    # 系统状态指示
    client = get_supabase()
    status_color = "🟢" if client else "🔴"
    st.caption(f"{status_color} 数据库: {'已连接' if client else '未连接'}")

# ====================== 核心数据预加载 ======================
# 使用 st.spinner 提供加载反馈
with st.spinner("正在初始化数据..."):
    papers_df = load_table("research_papers")
    trials_df = load_table("clinical_trials")
    herb_gene_df = load_table("herb_gene_relations")
    mirna_df = load_table("mirna")
    cargo_df = load_table("exosome_cargo")
    pathway_df = load_table("pathway_enrichment")
    herb_disease_df = load_table("herb_disease_relations")
    herb_pathway_df = load_table("herb_pathway_relations")

# ====================== 页面路由分发 ======================

# ─────────────────────────────────────────────────────
# 🏠 系统概览 (Overview)
# ─────────────────────────────────────────────────────
if page == "🏠 系统概览":
    # Hero 区域
    st.markdown("""
    <div class="hero">
        <div style="font-size:1.9rem;font-weight:800;color:#e8d5b7;margin-bottom:6px">
            TCM-Exosome Intelligence Platform
        </div>
        <div style="color:#6a9a8a;font-size:0.9rem;margin-bottom:16px">
            中药 × 外泌体 × 人工智能 科研情报系统
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
            <span style="background:rgba(74,184,128,0.12);border:1px solid rgba(74,184,128,0.3);
                border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#7adbb0">🌿 166味中药</span>
            <span style="background:rgba(74,154,224,0.12);border:1px solid rgba(74,154,224,0.3);
                border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#7ab0e0">📄 4,164篇文献</span>
            <span style="background:rgba(233,69,96,0.12);border:1px solid rgba(233,69,96,0.3);
                border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#e07a8a">🧬 949条基因关联</span>
            <span style="background:rgba(160,74,224,0.12);border:1px solid rgba(160,74,224,0.3);
                border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#c07ae0">💊 635味药典药材</span>
            <span style="background:rgba(224,144,74,0.12);border:1px solid rgba(224,144,74,0.3);
                border-radius:20px;padding:3px 12px;font-size:0.78rem;color:#e0b07a">⚗️ 6小时自动更新</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 六大核心指标卡片
    st.markdown("### 📊 核心数据概览")
    cols = st.columns(6)
    metrics = [
        ("文献总量", "📚", len(papers_df), "#4a9ae0"),
        ("临床试验", "🏥", len(trials_df), "#4ab880"), 
        ("中药-基因", "🧬", len(herb_gene_df), "#e94560"),
        ("miRNA", "🔬", len(mirna_df), "#a04ae0"),
        ("Cargo成分", "📦", len(cargo_df), "#e0904a"),
        ("信号通路", "🔗", len(pathway_df), "#4ab8b8"),
    ]
    
    for col, (label, icon, value, color) in zip(cols, metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:{color}">{icon} {value:,}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 图表区域：来源分布 + 年度趋势
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 📰 文献来源分布")
        if not papers_df.empty and "source" in papers_df.columns:
            src_counts = papers_df["source"].value_counts().reset_index()
            src_counts.columns = ["source", "count"]
            fig_pie = px.pie(
                src_counts.head(10),  # 仅展示TOP10
                names="source", 
                values="count", 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig_pie.update_layout(
                paper_bgcolor="#0d1117",
                plot_bgcolor="#0d1117", 
                font_color="#e6edf3",
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无来源分布数据")
    
    with col_right:
        st.markdown("#### 📈 发表年度趋势")
        if not papers_df.empty and "pub_date" in papers_df.columns:
            df_year = papers_df.copy()
            # 安全提取年份
            df_year["year"] = df_year["pub_date"].astype(str).str[:4]
            df_year = df_year[df_year["year"].str.match(r"^\d{4}$", na=False)]
            
            if not df_year.empty:
                year_counts = df_year.groupby("year").size().reset_index(name="count")
                year_counts = year_counts.sort_values("year")
                
                fig_bar = px.bar(
                    year_counts,
                    x="year", y="count",
                    color="count",
                    color_continuous_scale="Viridis",
                    labels={"year": "年份", "count": "文献数"}
                )
                fig_bar.update_layout(
                    paper_bgcolor="#0d1117",
                    plot_bgcolor="#0d1117",
                    font_color="#e6edf3",
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=300,
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("暂无有效年份数据")
        else:
            st.info("暂无年度趋势数据")

    # AI分析洞察（三栏布局）
    analysis_df = load_table("paper_ai_analysis")
    if not analysis_df.empty:
        st.markdown("### 🤖 AI分析洞察")
        ai_c1, ai_c2, ai_c3 = st.columns(3)
        
        with ai_c1:
            if "study_type" in analysis_df.columns:
                type_dist = analysis_df["study_type"].value_counts().head(8).reset_index()
                type_dist.columns = ["type", "count"]
                fig_type = px.pie(
                    type_dist, names="type", values="count", hole=0.45,
                    title="研究类型分布",
                    color_discrete_sequence=px.colors.sequential.Teal
                )
                fig_type.update_layout(
                    paper_bgcolor="#0d1117", font_color="#e6edf3",
                    margin=dict(t=40, b=10), height=280, legend=dict(font_size=9)
                )
                st.plotly_chart(fig_type, use_container_width=True)
        
        with ai_c2:
            if "disease_area" in analysis_df.columns:
                disease_dist = analysis_df["disease_area"].value_counts().head(10).reset_index()
                disease_dist.columns = ["disease", "count"]
                fig_dis = px.bar(
                    disease_dist, x="count", y="disease", orientation="h",
                    color="count", color_continuous_scale="RdYlGn",
                    title="高频疾病领域",
                    labels={"disease": "", "count": "文献数"}
                )
                fig_dis.update_layout(
                    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    font_color="#e6edf3", margin=dict(t=40, b=10),
                    height=280, coloraxis_showscale=False
                )
                st.plotly_chart(fig_dis, use_container_width=True)
        
        with ai_c3:
            herb_df = load_table("tcm_single_herb")
            if not herb_df.empty and "data_level" in herb_df.columns:
                level_dist = herb_df["data_level"].value_counts().reset_index()
                level_dist.columns = ["level", "count"]
                color_map = {"enriched": "#4ab880", "aligned": "#4a9ae0", "skeleton": "#e94560"}
                fig_level = px.pie(
                    level_dist, names="level", values="count", hole=0.45,
                    title="药典数据质量",
                    color="level", color_discrete_map=color_map
                )
                fig_level.update_layout(
                    paper_bgcolor="#0d1117", font_color="#e6edf3",
                    margin=dict(t=40, b=10), height=280
                )
                st.plotly_chart(fig_level, use_container_width=True)

    # 底部区域：热门中药 + 最新文献
    bottom_l, bottom_r = st.columns([1, 2])
    
    with bottom_l:
        st.markdown("#### 🌿 热门中药靶点")
        if not herb_gene_df.empty and "herb_name" in herb_gene_df.columns:
            top_herbs = herb_gene_df.groupby("herb_name").size().reset_index(name="target_count")
            top_herbs = top_herbs.sort_values("target_count", ascending=True).tail(10)
            
            fig_herb = px.bar(
                top_herbs, x="target_count", y="herb_name", orientation="h",
                color="target_count", color_continuous_scale="Viridis",
                labels={"herb_name": "中药", "target_count": "靶点数"}
            )
            fig_herb.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font_color="#e6edf3", margin=dict(t=10, b=10),
                height=320, coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"}
            )
            st.plotly_chart(fig_herb, use_container_width=True)
        else:
            st.info("暂无中药-基因关联数据")
    
    with bottom_r:
        st.markdown("#### 📄 最新入库文献")
        if not papers_df.empty:
            # 安全排序：优先按 created_at，若无则按索引
            sort_col = "created_at" if "created_at" in papers_df.columns else papers_df.columns[0]
            latest = papers_df.sort_values(sort_col, ascending=False, na_position='last').head(8)
            
            for _, row in latest.iterrows():
                title = str(row.get("title", "Untitled"))[:85]
                title += "..." if len(str(row.get("title", ""))) > 85 else ""
                source = row.get("source", "Unknown")
                pub_date = str(row.get("pub_date", ""))[:7]
                url = row.get("url", "")
                paper_id = row.get("id", "")
                
                link_html = f'<a href="{url}" target="_blank" style="color:#4a9ae0;text-decoration:none">🔗</a>' if url else ""
                
                st.markdown(f"""
                <div class="paper-item">
                    <span class="paper-source">{source}</span>
                    <span class="paper-date">{pub_date}</span>
                    <span style="float:right">{link_html}</span>
                    <div class="paper-title">{title}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无文献数据")

# ─────────────────────────────────────────────────────
# 🔍 智能检索 / 📚 文献库（合并简化版）
# ─────────────────────────────────────────────────────
elif page in ["🔍 智能检索", "📚 文献库"]:
    st.markdown("# 📚 文献数据库")
    
    # 搜索框 + 筛选器
    search_col, filter_col = st.columns([3, 1])
    with search_col:
        query = st.text_input("🔍 搜索关键词", placeholder="输入中药名/疾病/基因/关键词，支持中英文混合")
    with filter_col:
        source_filter = st.multiselect("来源平台", 
            options=papers_df["source"].unique().tolist() if not papers_df.empty and "source" in papers_df.columns else [],
            default=[]
        )
    
    # 执行搜索
    if query or source_filter:
        results_df = papers_df.copy()
        
        # 关键词模糊匹配（多字段）
        if query:
            query_lower = query.lower()
            mask = pd.Series([False] * len(results_df))
            for col in ["title", "abstract", "chinese_summary", "herb_name"]:
                if col in results_df.columns:
                    mask |= results_df[col].astype(str).str.lower().str.contains(query_lower, na=False)
            results_df = results_df[mask]
        
        # 来源筛选
        if source_filter:
            results_df = results_df[results_df["source"].isin(source_filter)]
        
        st.caption(f"找到 {len(results_df)} 条相关文献")
        
        # 结果展示
        if not results_df.empty:
            for _, row in results_df.head(20).iterrows():  # 限制展示数量
                with st.expander(f"📄 {row.get('title', 'Untitled')[:100]}"):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"**来源**: {row.get('source')} | **发表**: {str(row.get('pub_date', ''))[:10]}")
                        if "chinese_summary" in row and pd.notna(row["chinese_summary"]):
                            st.success(f"🤖 AI摘要: {row['chinese_summary']}")
                        elif "abstract" in row and pd.notna(row["abstract"]):
                            st.markdown(f"*摘要*: {row['abstract'][:300]}...")
                    with col_b:
                        if st.button("⭐ 收藏", key=f"bm_{row.get('id')}"):
                            if add_bookmark(str(row.get("id")), notes=query):
                                st.toast("✓ 已加入收藏", icon="✅")
                            else:
                                st.toast("✗ 收藏失败", icon="❌")
        else:
            st.info("🔍 未找到匹配结果，请尝试更换关键词")
    else:
        # 默认展示最新文献
        st.markdown("### 🕐 最新文献")
        if not papers_df.empty:
            sort_col = "created_at" if "created_at" in papers_df.columns else papers_df.columns[0]
            for _, row in papers_df.sort_values(sort_col, ascending=False).head(10).iterrows():
                st.markdown(f"- **{row.get('title', 'Untitled')[:80]}** `[{row.get('source')}]`")
        else:
            st.info("暂无文献数据")

# ─────────────────────────────────────────────────────
# 🏥 临床试验
# ─────────────────────────────────────────────────────
elif page == "🏥 临床试验":
    st.markdown("# 🏥 临床试验数据库")
    
    if not trials_df.empty:
        # 统计卡片
        stat_c1, stat_c2, stat_c3 = st.columns(3)
        stat_c1.metric("试验总数", f"{len(trials_df):,}")
        
        if "status" in trials_df.columns:
            recruiting = trials_df["status"].str.contains("Recruiting|Active|Not yet recruiting", na=False, case=False).sum()
            stat_c2.metric("进行中", f"{recruiting:,}")
        
        if "phase" in trials_df.columns:
            phase3 = (trials_df["phase"].str.contains("Phase 3|Phase III", na=False, case=False)).sum()
            stat_c3.metric("III期试验", f"{phase3:,}")
        
        # 状态分布图
        if "status" in trials_df.columns:
            status_dist = trials_df["status"].value_counts().head(8).reset_index()
            status_dist.columns = ["status", "count"]
            fig_status = px.bar(status_dist, x="status", y="count", color="count", 
                              color_continuous_scale="Blues", title="试验状态分布")
            fig_status.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font_color="#e6edf3", margin=dict(t=30, b=20),
                xaxis_tickangle=-45, height=300
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        # 数据表格
        display_cols = [c for c in ["nct_id", "title", "status", "phase", "condition", "intervention", "start_date", "url"] 
                       if c in trials_df.columns]
        st.dataframe(
            trials_df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "url": st.column_config.LinkColumn("详情", display_text="🔗"),
                "title": st.column_config.TextColumn("研究标题", width="large")
            }
        )
    else:
        st.info("📭 暂无临床试验数据，系统正在持续采集中...")

# ─────────────────────────────────────────────────────
# 🧬 基因组学
# ─────────────────────────────────────────────────────
elif page == "🧬 基因组学":
    st.markdown("# 🧬 基因组学分析")
    st.caption("中药 × 外泌体 × 靶点 × 疾病 多维关联网络")
    
    # 数据概览
    overview_c1, overview_c2, overview_c3, overview_c4 = st.columns(4)
    overview_c1.metric("关联基因", f"{len(herb_gene_df):,}" if not herb_gene_df.empty else "0")
    overview_c2.metric("miRNA", f"{len(mirna_df):,}" if not mirna_df.empty else "0")
    overview_c3.metric("Cargo成分", f"{len(cargo_df):,}" if not cargo_df.empty else "0")
    overview_c4.metric("信号通路", f"{len(pathway_df):,}" if not pathway_df.empty else "0")
    
    # 功能标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 靶点查询", "🕸️ 关联网络", "🧫 miRNA分析", "🔗 通路富集"])
    
    with tab1:
        st.markdown("### 中药靶点检索")
        herb_input = st.text_input("输入中药名称", placeholder="如: Curcumin / 姜黄")
        if herb_input and not herb_gene_df.empty:
            results = herb_gene_df[herb_gene_df["herb_name"].str.contains(herb_input, case=False, na=False)]
            if not results.empty:
                st.dataframe(
                    results[["herb_name", "gene_symbol", "interaction_type", "mechanism", "confidence_score"]],
                    use_container_width=True, hide_index=True
                )
            else:
                st.warning(f"未找到与「{herb_input}」相关的靶点记录")
        elif herb_gene_df.empty:
            st.info("暂无中药-基因关联数据")
    
    with tab2:
        st.markdown("### 关联网络预览")
        if not herb_gene_df.empty:
            # 简化网络统计
            herb_counts = herb_gene_df["herb_name"].value_counts().head(10)
            gene_counts = herb_gene_df["gene_symbol"].value_counts().head(10)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🌿 高频中药**")
                st.bar_chart(herb_counts)
            with c2:
                st.markdown("**🧬 高频靶点**")
                st.bar_chart(gene_counts)
            
            st.info("💡 完整交互图谱请前往「🕸️ 知识图谱」模块查看")
        else:
            st.info("暂无关联网络数据")
    
    with tab3:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### 🔬 miRNA 数据")
            if not mirna_df.empty:
                display_cols = [c for c in ["mirna_id", "sequence", "target_genes", "is_exosome_cargo", "regulation_direction"] 
                               if c in mirna_df.columns]
                st.dataframe(mirna_df[display_cols].head(50), use_container_width=True, hide_index=True)
            else:
                st.info("miRNA 数据正在AI挖掘扩充中...")
        
        with col_m2:
            st.markdown("#### 📦 Exosome Cargo")
            if not cargo_df.empty:
                display_cols = [c for c in ["cargo_name", "cargo_type", "tcm_herb", "target_gene", "biological_effect"] 
                               if c in cargo_df.columns]
                st.dataframe(cargo_df[display_cols].head(50), use_container_width=True, hide_index=True)
            else:
                st.info("Cargo 数据持续采集中...")
    
    with tab4:
        st.markdown("### 通路富集分析")
        if not pathway_df.empty and "pathway_name" in pathway_df.columns:
            # 展示TOP通路
            top_pathways = pathway_df.sort_values("enrichment_score" if "enrichment_score" in pathway_df.columns else "p_value", 
                                                 ascending="enrichment_score" in pathway_df.columns).head(20)
            
            if "enrichment_score" in top_pathways.columns:
                fig_path = px.bar(
                    top_pathways, 
                    x="enrichment_score", y="pathway_name", orientation="h",
                    color="herb_name" if "herb_name" in top_pathways.columns else None,
                    title="Top 20 富集通路",
                    labels={"pathway_name": "通路名称", "enrichment_score": "富集评分"}
                )
                fig_path.update_layout(
                    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                    font_color="#e6edf3", margin=dict(t=30, b=20),
                    height=500, yaxis={"categoryorder": "total ascending"}
                )
                st.plotly_chart(fig_path, use_container_width=True)
            else:
                st.dataframe(pathway_df.head(50), use_container_width=True, hide_index=True)
        else:
            st.info("暂无通路富集数据")

# ─────────────────────────────────────────────────────
# 🕸️ 知识图谱（修复 import 路径 + 错误处理）
# ─────────────────────────────────────────────────────
elif page == "🕸️ 知识图谱":
    st.markdown("# 🕸️ 知识图谱")
    st.caption("药材 ⇄ 靶点 ⇄ 疾病 多维关联可视化")
    
    try:
        # ✅ 统一使用相对路径导入，兼容本地/容器环境
        from src.dashboard.knowledge_graph_page import render_knowledge_graph
        
        render_knowledge_graph(
            hg_df=herb_gene_df,
            mapping_df=None,  # 如有 mapping 表可传入
            disease_df=herb_disease_df,
            pathway_herb_df=herb_pathway_df
        )
    except ImportError as e:
        st.error(f"❌ 知识图谱模块加载失败: {e}")
        st.info("💡 请确认 `src/dashboard/knowledge_graph_page.py` 文件存在且包含 `render_knowledge_graph` 函数")
    except Exception as e:
        st.error(f"❌ 图谱渲染异常: {type(e).__name__}: {e}")
        st.code(str(e), language="text")
        st.info("🔧 建议: 检查 `knowledge_graph_page.py` 中 `build_network_html()` 函数是否正确初始化 `edges` 和 `nodes` 变量")

# ─────────────────────────────────────────────────────
# 📖 药典查询 / 📊 分析报告 / ⚙️ 爬虫监控
# ─────────────────────────────────────────────────────
elif page == "📖 药典查询":
    try:
        from src.dashboard.pharmacopoeia_page import render_pharmacopoeia
        render_pharmacopoeia()
    except ImportError:
        st.info("📖 药典查询模块开发中...")

elif page == "📊 分析报告":
    try:
        from src.dashboard.report_page import render_report_page
        render_report_page(
            papers_df, herb_gene_df, trials_df, 
            cargo_df, pathway_df, herb_disease_df, herb_pathway_df
        )
    except ImportError:
        st.info("📊 分析报告模块开发中...")

elif page == "⚙️ 爬虫监控":
    st.markdown("# ⚙️ 爬虫运行状态")
    
    # 爬虫日志
    logs_df = load_table("crawler_logs")
    if not logs_df.empty:
        if "created_at" in logs_df.columns:
            logs_df = logs_df.sort_values("created_at", ascending=False)
        
        display_cols = [c for c in ["source", "status", "records_found", "records_added", "error_msg", "created_at"] 
                       if c in logs_df.columns]
        st.dataframe(
            logs_df[display_cols].head(100),
            use_container_width=True,
            hide_index=True,
            column_config={
                "status": st.column_config.SelectboxColumn("状态", options=["success", "running", "failed"]),
                "created_at": st.column_config.DatetimeColumn("运行时间")
            }
        )
    else:
        st.info("暂无爬虫日志记录")
    
    # 各表数据量统计
    st.markdown("### 📦 数据库存储统计")
    tables = [
        ("research_papers", "研究文献"),
        ("clinical_trials", "临床试验"), 
        ("herb_gene_relations", "中药-基因"),
        ("mirna", "miRNA"),
        ("exosome_cargo", "Cargo成分"),
        ("pathway_enrichment", "信号通路"),
        ("herb_disease_relations", "中药-疾病"),
        ("tcm_single_herb", "药典药材")
    ]
    
    for table_name, label in tables:
        df = load_table(table_name)
        count = len(df) if not df.empty else 0
        st.markdown(f"- **{label}** (`{table_name}`): `{count:,}` 条记录")

# ─────────────────────────────────────────────────────
# 默认兜底页面
# ─────────────────────────────────────────────────────
else:
    st.markdown("# 👋 欢迎使用 TCM-Exosome")
    st.info("请选择左侧导航菜单进入功能模块")
    
    # 快速入口
    st.markdown("### 🚀 快速开始")
    c1, c2, c3 = st.columns(3)
    c1.metric("📚 文献检索", "4,164+", "篇学术文献")
    c2.metric("🧬 靶点关联", "949+", "条中药-基因关系")
    c3.metric("🤖 AI摘要", "自动", "中文摘要生成")
    
    if st.button("🔍 开始检索文献", type="primary"):
        st.switch_page("🔍 智能检索")  # Streamlit 1.24+ 支持
