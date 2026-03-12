import sqlite3
conn = sqlite3.connect('data/tcm_exosome.db')

total = conn.execute("SELECT COUNT(*) FROM research_papers").fetchone()[0]
dup_pmid = conn.execute("""
    SELECT COUNT(*) FROM research_papers 
    WHERE pmid IS NOT NULL AND pmid != ''
    AND pmid IN (
        SELECT pmid FROM research_papers 
        WHERE pmid IS NOT NULL AND pmid != ''
        GROUP BY pmid HAVING COUNT(*) > 1
    )
""").fetchone()[0]
dup_title = conn.execute("""
    SELECT COUNT(*) FROM research_papers
    WHERE title IN (
        SELECT title FROM research_papers
        GROUP BY title HAVING COUNT(*) > 1
    )
""").fetchone()[0]
dup_doi = conn.execute("""
    SELECT COUNT(*) FROM research_papers
    WHERE doi IS NOT NULL AND doi != ''
    AND doi IN (
        SELECT doi FROM research_papers
        WHERE doi IS NOT NULL AND doi != ''
        GROUP BY doi HAVING COUNT(*) > 1
    )
""").fetchone()[0]

print(f"Total: {total}")
print(f"Duplicate pmid rows: {dup_pmid}")
print(f"Duplicate title rows: {dup_title}")
print(f"Duplicate doi rows: {dup_doi}")
conn.close()
