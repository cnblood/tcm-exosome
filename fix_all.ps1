# fix_all.ps1
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🔧 TCM-Exosome 一键修复脚本" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📌 步骤1: 修复论文分类和URL..." -ForegroundColor Yellow
python fix_papers_categories.py
Write-Host ""

Write-Host "📌 步骤2: 更新应用显示逻辑..." -ForegroundColor Yellow
python update_app.py
Write-Host ""

Write-Host "📌 步骤3: 重新部署应用..." -ForegroundColor Yellow
docker stop tcm-exosome-app 2>$null
docker rm tcm-exosome-app 2>$null
docker build -t tcm-exosome-app:latest .
docker run -d --name tcm-exosome-app -p 8501:8501 -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" -e SUPABASE_URL="https://vhwgmlfwnscnrvibdhgs.supabase.co" -e SUPABASE_KEY=os.environ.get("SUPABASE_KEY") -e DB_PATH="/app/data/tcm_exosome.db" tcm-exosome-app:latest
Write-Host ""

Write-Host "📌 步骤4: 查看日志..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
docker logs tcm-exosome-app --tail 20
Write-Host ""

Write-Host "✅ 修复完成！请访问: http://localhost:8501" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

