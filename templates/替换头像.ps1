# 替换头像为base64
$base64File = "C:\Users\Stellaris\Downloads\新建 文本文档 (2).txt"
$indexPath = "D:\VPN\免费VPN爬虫\templates\index.html"

# 读取base64字符串
$base64 = Get-Content $base64File -Raw

# 读取index.html
$html = Get-Content $indexPath -Raw

# 构造新的img标签
$newImg = "<img src=`"$base64`" alt=`"avatar`">"

# 替换旧的img标签（包括onerror属性）
$pattern = [regex]::Escape("<img src=`"头像路径.jpg`" alt=`"avatar`" onerror=`"this.parentNode.innerHTML='<span style=\'color:#666;font-size:12px\'>头像</span>'`">")
$html = $html -replace $pattern, $newImg

# 保存
$html | Out-File -FilePath $indexPath -Encoding UTF8

Write-Host "✅ 头像已替换为base64！" -ForegroundColor Green
Start-Sleep 3