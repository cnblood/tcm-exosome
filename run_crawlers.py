#!/usr/bin/env python3
"""
TCM-Exosome 爬虫调度器 v3.0
用法:
  python run_crawlers.py --once           # 运行一次所有爬虫
  python run_crawlers.py --daemon         # 守护进程模式（每6小时）
  python run_crawlers.py --literature     # 只跑文献爬虫
  python run_crawlers.py --genomics       # 只跑基因爬虫
"""
import sys, os, time, argparse, logging

sys.path.insert(0, "/app")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/crawler.log"),
        logging.StreamHandler()
    ]
)

def run_literature():
    """运行所有文献爬虫"""
    results = {}
    crawlers = []

    try:
        from src.crawler.pubmed_crawler import run as run_pubmed
        crawlers.append(("PubMed", run_pubmed))
    except Exception as e:
        logging.warning(f"PubMed import failed: {e}")

    try:
        from src.crawler.europepmc_crawler import run as run_europepmc
        crawlers.append(("EuropePMC", run_europepmc))
    except Exception as e:
        logging.warning(f"EuropePMC import failed: {e}")

    try:
        from src.crawler.biorxiv_crawler import run as run_biorxiv
        crawlers.append(("bioRxiv", run_biorxiv))
    except Exception as e:
        logging.warning(f"bioRxiv import failed: {e}")

    try:
        from src.crawler.clinicaltrials_crawler import run as run_clinicaltrials
        crawlers.append(("ClinicalTrials", run_clinicaltrials))
    except Exception as e:
        logging.warning(f"ClinicalTrials import failed: {e}")

    try:
        from src.crawler.chinese_crawler import run as run_chinese
        crawlers.append(("ChineseLiterature", run_chinese))
    except Exception as e:
        logging.warning(f"Chinese crawler import failed: {e}")

    for name, fn in crawlers:
        try:
            logging.info(f"Running: {name}")
            count = fn()
            results[name] = count or 0
            logging.info(f"  {name}: +{results[name]} new records")
        except Exception as e:
            logging.error(f"  {name} failed: {e}")
            results[name] = 0

    return results

def run_genomics():
    """运行基因组学爬虫"""
    results = {}
    crawlers = []

    try:
        from src.crawler.gene_crawler import run as run_gene
        crawlers.append(("Gene", run_gene))
    except Exception as e:
        logging.warning(f"Gene crawler import failed: {e}")

    try:
        from src.crawler.mirna_crawler import run as run_mirna
        crawlers.append(("miRNA", run_mirna))
    except Exception as e:
        logging.warning(f"miRNA crawler import failed: {e}")

    try:
        from src.crawler.herb_gene_crawler import run as run_herb_gene
        crawlers.append(("HerbGene", run_herb_gene))
    except Exception as e:
        logging.warning(f"HerbGene crawler import failed: {e}")

    try:
        from src.crawler.pathway_crawler import run as run_pathway
        crawlers.append(("Pathway", run_pathway))
    except Exception as e:
        logging.warning(f"Pathway crawler import failed: {e}")

    for name, fn in crawlers:
        try:
            logging.info(f"Running: {name}")
            count = fn()
            results[name] = count or 0
            logging.info(f"  {name}: +{results[name]} records")
        except Exception as e:
            logging.error(f"  {name} failed: {e}")
            results[name] = 0

    return results

def run_all():
    logging.info("=" * 50)
    logging.info("Starting all crawlers...")
    logging.info("=" * 50)

    lit_results = run_literature()
    gen_results = run_genomics()

    all_results = {**lit_results, **gen_results}
    total = sum(all_results.values())

    logging.info("=" * 50)
    logging.info("Crawl Summary:")
    for name, count in all_results.items():
        logging.info(f"  {name}: +{count}")
    logging.info(f"  TOTAL NEW: {total}")
    logging.info("=" * 50)

    return total

def daemon_mode(interval_hours=6):
    logging.info(f"Daemon mode: every {interval_hours} hours")
    while True:
        try:
            run_all()
        except Exception as e:
            logging.error(f"Crawl cycle failed: {e}")

        try:
            from src.crawler.fill_key_findings import run as fkf
            fkf(50)
            logging.info("key_findings batch done")
        except Exception as ke:
            logging.warning("kf fill: %s", ke)
        logging.info(f"Sleeping {interval_hours}h...")
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", type=int, default=6, help="Hours between runs")
    parser.add_argument("--literature", action="store_true", help="Literature crawlers only")
    parser.add_argument("--genomics", action="store_true", help="Genomics crawlers only")
    args = parser.parse_args()

    if args.literature:
        run_literature()
    elif args.genomics:
        run_genomics()
    elif args.daemon:
        daemon_mode(args.interval)
    else:
        run_all()
