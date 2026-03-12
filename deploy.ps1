# deploy.ps1 - 完整的部署脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🚀 TCM-Exosome 部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$SUPABASE_URL = "https://vhwgmlfwnscnrvibdhgs.supabase.co"
$SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
$PORT = 8501
$CONTAINER_NAME = "tcm-exosome-app"
$IMAGE_NAME = "tcm-exosome-app:latest"

Write-Host "📌 部署配置：" -ForegroundColor Yellow
Write-Host "   📍 容器名称: $CONTAINER_NAME"
Write-Host "   📍 镜像名称: $IMAGE_NAME"
Write-Host "   📍 端口: $PORT"
Write-Host "   📍 Supabase: 已配置"
Write-Host "   📍 外部访问: http://185.100.234.55:$PORT"
Write-Host ""

# 步骤1: 停止并删除旧容器
Write-Host "📦 [1/6] 清理旧容器..." -ForegroundColor Yellow
$oldContainer = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>$null
if ($oldContainer) {
    Write-Host "   找到旧容器，正在停止..."
    docker stop $CONTAINER_NAME 2>$null
    docker rm $CONTAINER_NAME 2>$null
    Write-Host "   ✅ 旧容器已删除"
} else {
    Write-Host "   ✅ 没有旧容器需要清理"
}
Write-Host ""

# 步骤2: 创建必要目录
Write-Host "📁 [2/6] 创建数据目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path data, logs | Out-Null
Write-Host "   ✅ 目录已创建:"
Write-Host "      - data/ (数据库文件)"
Write-Host "      - logs/ (日志文件)"
Write-Host ""

# 步骤3: 检查必要文件
Write-Host "🔍 [3/6] 检查必要文件..." -ForegroundColor Yellow
$filesToCheck = @(
    @{Path="requirements.txt"; Name="Python依赖"},
    @{Path="docker-entrypoint.sh"; Name="启动脚本"},
    @{Path="src/dashboard/app.py"; Name="主应用"},
    @{Path="src/database/init_db.py"; Name="数据库初始化"},
    @{Path="run_crawlers.py"; Name="爬虫脚本"}
)

$allFilesExist = $true
foreach ($file in $filesToCheck) {
    if (Test-Path $file.Path) {
        Write-Host "   ✅ $($file.Name) ($($file.Path))"
    } else {
        Write-Host "   ❌ $($file.Name) ($($file.Path)) - 缺失" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "`n❌ 必要文件缺失，请检查后重试" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤4: 构建Docker镜像
Write-Host "🏗️ [4/6] 构建Docker镜像..." -ForegroundColor Yellow
Write-Host "   正在构建，这可能需要几分钟..."
Write-Host ""

docker build -t $IMAGE_NAME .

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 镜像构建失败！" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 镜像构建成功"
Write-Host ""

# 步骤5: 运行容器
Write-Host "▶️ [5/6] 启动容器..." -ForegroundColor Yellow
docker run -d `
  --name $CONTAINER_NAME `
  -p ${PORT}:8501 `
  -v "${PWD}/data:/app/data" `
  -v "${PWD}/logs:/app/logs" `
  -e SUPABASE_URL="$SUPABASE_URL" `
  -e SUPABASE_KEY="$SUPABASE_KEY" `
  -e DB_PATH="/app/data/tcm_exosome.db" `
  $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 容器启动失败！" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 容器已启动"
Write-Host ""

# 步骤6: 检查容器状态
Write-Host "🔧 [6/6] 检查容器状态..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$containerStatus = docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
if ($containerStatus -like "*$CONTAINER_NAME*") {
    Write-Host "   ✅ 容器运行中"
    Write-Host ""
    Write-Host "$containerStatus"
} else {
    Write-Host "   ❌ 容器未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "查看错误日志："
    docker logs $CONTAINER_NAME --tail 20
    exit 1
}
Write-Host ""

# 完成
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ✅ 部署成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 本地访问: http://localhost:$PORT"
Write-Host "🌐 远程访问: http://185.100.234.55:$PORT"
Write-Host ""
Write-Host "📝 查看日志: docker logs -f $CONTAINER_NAME"
Write-Host "🛑 停止容器: docker stop $CONTAINER_NAME"
Write-Host "▶️ 启动容器: docker start $CONTAINER_NAME"
Write-Host "🔄 重启容器: docker restart $CONTAINER_NAME"
Write-Host ""

# 询问是否查看日志
$viewLogs = Read-Host "是否查看实时日志？(y/n)"
if ($viewLogs -eq "y") {
    Write-Host "查看日志 (按 Ctrl+C 退出)..."
    docker logs -f $CONTAINER_NAME
}

