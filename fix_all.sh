#!/bin/bash
echo "========================================="
echo "🔧 TCM-Exosome 一键修复脚本"
echo "========================================="

echo "📌 步骤1: 修复论文分类和URL..."
python fix_papers_categories.py

echo "📌 步骤2: 更新应用显示逻辑..."
python update_app.py

echo "📌 步骤3: 重新部署应用..."
docker stop tcm-exosome-app 2>/dev/null
docker rm tcm-exosome-app 2>/dev/null
docker build -t tcm-exosome-app:latest .
docker run -d --name tcm-exosome-app -p 8501:8501 -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs -e SUPABASE_URL="https://vhwgmlfwnscnrvibdhgs.supabase.co" -e SUPABASE_KEY=$env:SUPABASE_KEY -e DB_PATH="/app/data/tcm_exosome.db" tcm-exosome-app:latest

echo "📌 步骤4: 查看日志..."
sleep 3
docker logs tcm-exosome-app --tail 20

echo ""
echo "✅ 修复完成！请访问: http://localhost:8501"
echo "========================================="
