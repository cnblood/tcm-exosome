# 🧬 TCM-Exosome 智能分析平台 v3.1

> Traditional Chinese Medicine × Exosome Research Intelligence

[![Papers](https://img.shields.io/badge/文献-3000+-blue)]()
[![Herbs](https://img.shields.io/badge/药典药材-635味-green)]()
[![Relations](https://img.shields.io/badge/基因关联-255条-orange)]()
[![Journals](https://img.shields.io/badge/专业期刊-25本-purple)]()

---

## 📦 平台功能

| 模块 | 功能 |
|------|------|
| 📄 文献库 | 3000+篇，25本EV专业期刊，自动爬虫6h/次 |
| 🧬 知识图谱 | 中药-基因-疾病-通路-复方 五维网络 |
| 🔍 全库搜索 | 跨文献/药材/基因/复方一键搜索 |
| 💊 复方关联 | 19个成方 × 130条基因关联 |
| 🌿 药典数据 | 635味药材，60%已富集 |
| ⭐ 收藏系统 | 文献标注/重要性/备注/标签 |
| 🤖 AI分析 | 1138篇研究类型/疾病领域自动分析 |

---

## 🚀 部署步骤（Windows → Docker Hub → Claw Cloud）

### 第一步：本地环境准备

确保已安装：
- [Git](https://git-scm.com/download/win)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.11+

### 第二步：克隆项目

```powershell
git clone https://github.com/your-repo/tcm-exosome.git
cd tcm-exosome
```

### 第三步：设置环境变量

```powershell
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_KEY="your-supabase-key"
$env:GEMINI_API_KEY="your-gemini-key"   # 可选，用于AI分析
```

### 第四步：构建并推送Docker镜像

```powershell
docker login
docker build -t your_dockerhub_username/tcm-exosome:latest .
docker push your_dockerhub_username/tcm-exosome:latest
```

### 第五步：Claw Cloud部署

1. 登录 [Claw Cloud](https://run.claw.cloud)
2. 创建新应用，选择 Docker 镜像
3. 镜像地址：`your_dockerhub_username/tcm-exosome:latest`
4. 端口：`8501`
5. 设置环境变量：`SUPABASE_URL` / `SUPABASE_KEY`
6. 点击部署

---

## 🗄️ 数据库结构（Supabase）

```
research_papers          # 研究文献 (3000+)
paper_ai_analysis        # AI分析结果
herb_gene_relations      # 中药-基因关联 (255条)
herb_disease_relations   # 中药-疾病关联 (286条)
herb_pathway_relations   # 中药-通路关联 (173条)
formula_gene_relations   # 复方-基因关联 (130条)
tcm_pharmacopoeia        # 药典药材 (635味)
tcm_compound_formula     # 成方制剂 (650条)
herb_name_mapping        # 中英文名对照
exosome_cargo            # 外泌体Cargo (385+)
pathway_enrichment       # 通路富集 (768+)
clinical_trials          # 临床试验 (16条)
user_bookmarks           # 用户收藏
```

---

## 🕷️ 爬虫说明

| 爬虫 | 频率 | 数据源 |
|------|------|--------|
| pubmed_crawler | 每6小时 | PubMed关键词搜索 |
| europepmc_crawler | 每6小时 | EuropePMC |
| biorxiv_crawler | 每6小时 | bioRxiv预印本 |
| journal_crawler | 每6天 | 25本专业EV期刊 |
| gene_crawler | 每6小时 | 基因组数据 |
| pathway_crawler | 每6小时 | KEGG通路 |

### 手动运行爬虫

```powershell
# 运行所有爬虫
python run_crawlers.py --once

# 只跑期刊爬虫
python run_crawlers.py --journals

# 只跑文献爬虫
python run_crawlers.py --literature
```

---

## 📊 数据统计（2026-03）

- 文献总量：**3,134篇**（持续增长）
- 专业期刊来源：Journal of Extracellular Vesicles, Theranostics, ACS Nano, Small...
- 中药-基因：**255条** / 50味中药
- 中药-疾病：**286条** / 68味中药
- 中药-通路：**173条** / 44味中药
- 复方-基因：**130条** / 19个复方
- 外泌体Cargo：**385条**
- KEGG通路：**768条**

---

## 🔧 本地开发

```powershell
# 安装依赖
pip install -r requirements.txt

# 本地运行
$env:SUPABASE_URL="..."
$env:SUPABASE_KEY="..."
streamlit run src/dashboard/app.py
```

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v3.1 | 2026-03 | 期刊爬虫(25本)，用户收藏系统，复方-基因关联 |
| v3.0 | 2026-02 | 知识图谱五维扩展，AI分析，全库搜索 |
| v2.0 | 2026-02 | 药典635味，自动爬虫，Overview重设计 |
| v1.0 | 2026-01 | 初版上线 |
