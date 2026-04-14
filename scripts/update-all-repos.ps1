<#
.SYNOPSIS
    批量更新所有系统代码仓库。
.DESCRIPTION
    遍历 systems/ 下各系统的 code/ 目录，对每个 git 仓库执行 git pull 更新。
    适用于迭代启动前批量同步最新代码。
.EXAMPLE
    powershell -File scripts/update-all-repos.ps1
    powershell -File scripts/update-all-repos.ps1 -Branch develop
#>

param(
    [string]$Branch = "main",
    [string]$RootDir = (Join-Path $PSScriptRoot "..\systems")
)

$RootDir = Resolve-Path $RootDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  代码仓库批量更新工具" -ForegroundColor Cyan
Write-Host "  根目录: $RootDir" -ForegroundColor Cyan
Write-Host "  目标分支: $Branch" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0
$skipCount = 0
$results = @()

# 遍历 systems/ 下的每个系统目录
Get-ChildItem -Path $RootDir -Directory | Where-Object { $_.Name -ne "_shared" } | ForEach-Object {
    $systemName = $_.Name
    $codeDir = Join-Path $_.FullName "code"

    if (-not (Test-Path $codeDir)) {
        return
    }

    # 遍历 code/ 下的每个子目录（每个子目录是一个 git 仓库）
    Get-ChildItem -Path $codeDir -Directory | ForEach-Object {
        $repoDir = $_.FullName
        $repoName = $_.Name
        $gitDir = Join-Path $repoDir ".git"

        if (-not (Test-Path $gitDir)) {
            Write-Host "  [跳过] $systemName/$repoName (非 git 仓库)" -ForegroundColor Yellow
            $skipCount++
            $results += [PSCustomObject]@{
                System = $systemName
                Repo = $repoName
                Status = "跳过"
                Message = "非 git 仓库"
            }
            return
        }

        Write-Host "  [更新] $systemName/$repoName ..." -ForegroundColor White -NoNewline

        try {
            # 检查当前分支
            $currentBranch = git -C $repoDir rev-parse --abbrev-ref HEAD 2>&1

            # 如果不在目标分支，先切换
            if ($currentBranch -ne $Branch) {
                $checkoutResult = git -C $repoDir checkout $Branch 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host " 失败 (无法切换到 $Branch)" -ForegroundColor Red
                    $failCount++
                    $results += [PSCustomObject]@{
                        System = $systemName
                        Repo = $repoName
                        Status = "失败"
                        Message = "无法切换到分支 $Branch"
                    }
                    return
                }
            }

            # 执行 pull
            $pullResult = git -C $repoDir pull origin $Branch 2>&1
            if ($LASTEXITCODE -eq 0) {
                $shortResult = if ($pullResult -match "Already up to date") { "已是最新" } else { "已更新" }
                Write-Host " $shortResult" -ForegroundColor Green
                $successCount++
                $results += [PSCustomObject]@{
                    System = $systemName
                    Repo = $repoName
                    Status = "成功"
                    Message = $shortResult
                }
            } else {
                Write-Host " 失败" -ForegroundColor Red
                $failCount++
                $results += [PSCustomObject]@{
                    System = $systemName
                    Repo = $repoName
                    Status = "失败"
                    Message = ($pullResult | Out-String).Trim()
                }
            }
        } catch {
            Write-Host " 异常: $($_.Exception.Message)" -ForegroundColor Red
            $failCount++
            $results += [PSCustomObject]@{
                System = $systemName
                Repo = $repoName
                Status = "异常"
                Message = $_.Exception.Message
            }
        }
    }
}

# 输出汇总
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  更新完成" -ForegroundColor Cyan
Write-Host "  成功: $successCount  失败: $failCount  跳过: $skipCount" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($results.Count -gt 0) {
    Write-Host ""
    Write-Host "详细结果:" -ForegroundColor White
    $results | Format-Table -AutoSize
}

if ($failCount -gt 0) {
    exit 1
}
