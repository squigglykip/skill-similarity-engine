# PowerShell Script to Test User Story 1: Top N Discovery Mode
# Tests the configurable Top N analysis with different parameters and tie-breaking options
# Outputs are captured to JSON files for easy analysis

Write-Host "🚀 Testing User Story 1: Top N Discovery Mode" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

# Create output directory
$outputDir = "test_results_top_n_discovery"
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Set working directory
Set-Location "skill-similarity-engine\src\skill_similarity_engine\webapp\career_analysis"

# Test configuration
$testJob = "R0102.3"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "📋 Test Configuration:" -ForegroundColor Yellow
Write-Host "   Source Job: $testJob" -ForegroundColor White
Write-Host "   Output Directory: $outputDir" -ForegroundColor White
Write-Host "   Timestamp: $timestamp" -ForegroundColor White
Write-Host ""

# Function to run test and capture output
function Run-Test {
    param(
        [string]$TestName,
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "🧪 Running: $TestName" -ForegroundColor Cyan
    Write-Host "   $Description" -ForegroundColor Gray
    
    $outputFile = "$outputDir\${TestName}_${timestamp}.txt"
    
    try {
        # Run the command and capture output
        $output = Invoke-Expression $Command 2>&1
        
        # Create test result object
        $testResult = @{
            test_name = $TestName
            description = $Description
            command = $Command
            timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            success = $LASTEXITCODE -eq 0
            output_file = $outputFile
            summary = @{
                total_lines = ($output | Measure-Object).Count
                contains_opportunities = ($output -join " ") -match "Generated \d+ opportunities"
                contains_debug = ($output -join " ") -match "DEBUG INFO"
                contains_error = ($output -join " ") -match "Error|❌"
            }
        }
        
        # Extract key metrics from output
        $outputText = $output -join "`n"
        if ($outputText -match "🎯 Generated (\d+) opportunities \(requested top (\d+)\)") {
            $testResult.summary.generated_count = [int]$Matches[1]
            $testResult.summary.requested_count = [int]$Matches[2]
        }
        
        if ($outputText -match "Pathway Analysis: Top (\d+) Strategic Opportunities") {
            $testResult.summary.section_title_top_n = [int]$Matches[1]
        }
        
        # Save output to file
        $output | Out-File -FilePath $outputFile -Encoding UTF8
        
        Write-Host "   ✅ Completed - Output saved to: $outputFile" -ForegroundColor Green
        
        return $testResult
        
    } catch {
        Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        
        return @{
            test_name = $TestName
            description = $Description
            command = $Command
            timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            success = $false
            error = $_.Exception.Message
            output_file = $null
        }
    }
}

# Test Results Collection
$allResults = @()

Write-Host "📊 Phase 1: Basic Top N Discovery Mode Tests" -ForegroundColor Magenta
Write-Host ("-" * 50) -ForegroundColor Magenta

# Test 1: Default Top 3
$result = Run-Test -TestName "top_3_default" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 3 --pathway" `
    -Description "Default Top 3 Discovery Mode (baseline test)"
$allResults += $result

# Test 2: Top 5
$result = Run-Test -TestName "top_5_enhanced" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --pathway" `
    -Description "Top 5 Discovery Mode (enhanced analysis)"
$allResults += $result

# Test 3: Top 7
$result = Run-Test -TestName "top_7_comprehensive" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 7 --pathway" `
    -Description "Top 7 Discovery Mode (comprehensive analysis)"
$allResults += $result

# Test 4: Top 10
$result = Run-Test -TestName "top_10_maximum" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 10 --pathway" `
    -Description "Top 10 Discovery Mode (maximum analysis scope)"
$allResults += $result

Write-Host ""
Write-Host "🔧 Phase 2: Tie-Breaking Options Tests" -ForegroundColor Magenta
Write-Host ("-" * 50) -ForegroundColor Magenta

# Test 5: Same Function Priority
$result = Run-Test -TestName "top_5_same_function" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --same-function-priority --pathway" `
    -Description "Top 5 with Same Function Priority tie-breaking"
$allResults += $result

# Test 6: Career Progression Priority
$result = Run-Test -TestName "top_5_career_progression" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --career-progression-priority --pathway" `
    -Description "Top 5 with Career Progression Priority tie-breaking"
$allResults += $result

# Test 7: Multiple Tie-Breaking Options
$result = Run-Test -TestName "top_5_multiple_tiebreaking" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --same-function-priority --career-progression-priority --minimal-level-jump --pathway" `
    -Description "Top 5 with Multiple Tie-Breaking Options"
$allResults += $result

# Test 8: Skills Overlap Detail
$result = Run-Test -TestName "top_5_skills_detail" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --skills-overlap-detail --pathway" `
    -Description "Top 5 with Skills Overlap Detail transparency"
$allResults += $result

Write-Host ""
Write-Host "📈 Phase 3: Similarity Range Variations" -ForegroundColor Magenta
Write-Host ("-" * 50) -ForegroundColor Magenta

# Test 9: Narrow similarity range
$result = Run-Test -TestName "top_5_narrow_range" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --similarity-min 50 --similarity-max 70 --pathway" `
    -Description "Top 5 with Narrow Similarity Range (50%-70%)"
$allResults += $result

# Test 10: Wide similarity range
$result = Run-Test -TestName "top_8_wide_range" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 8 --similarity-min 30 --similarity-max 90 --pathway" `
    -Description "Top 8 with Wide Similarity Range (30%-90%)"
$allResults += $result

# Test 11: High similarity range
$result = Run-Test -TestName "top_3_high_range" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 3 --similarity-min 60 --similarity-max 95 --pathway" `
    -Description "Top 3 with High Similarity Range (60%-95%)"
$allResults += $result

Write-Host ""
Write-Host "📄 Phase 4: Full Document Generation" -ForegroundColor Magenta
Write-Host ("-" * 50) -ForegroundColor Magenta

# Test 12: Word document with Top 5
$result = Run-Test -TestName "word_doc_top_5" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 5 --word" `
    -Description "Complete Word Document Generation with Top 5"
$allResults += $result

# Test 13: Word document with Top 7
$result = Run-Test -TestName "word_doc_top_7" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 7 --word" `
    -Description "Complete Word Document Generation with Top 7"
$allResults += $result

# Test 14: Clean copy with Top 10
$result = Run-Test -TestName "clean_copy_top_10" `
    -Command "python test_career_analysis.py --job-from $testJob --mode top_matches --top-n 10 --copy" `
    -Description "Clean Copy Display with Top 10 (no debug)"
$allResults += $result

Write-Host ""
Write-Host "🔄 Phase 5: Different Source Jobs Comparison" -ForegroundColor Magenta
Write-Host ("-" * 50) -ForegroundColor Magenta

# Test 15: Different job
$result = Run-Test -TestName "alt_job_R0100_2_top_5" `
    -Command "python test_career_analysis.py --job-from R0100.2 --mode top_matches --top-n 5 --pathway" `
    -Description "Alternative Job (R0100.2) with Top 5"
$allResults += $result

# Test 16: Another job
$result = Run-Test -TestName "alt_job_R0025_1_top_8" `
    -Command "python test_career_analysis.py --job-from R0025.1 --mode top_matches --top-n 8 --pathway" `
    -Description "Alternative Job (R0025.1) with Top 8"
$allResults += $result

Write-Host ""
Write-Host "💾 Generating Summary Report..." -ForegroundColor Yellow

# Create comprehensive summary
$summary = @{
    test_suite = "User Story 1: Top N Discovery Mode"
    execution_timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    total_tests = $allResults.Count
    successful_tests = ($allResults | Where-Object { $_.success }).Count
    failed_tests = ($allResults | Where-Object { -not $_.success }).Count
    output_directory = $outputDir
    test_results = $allResults
    key_findings = @{
        top_n_configurations_tested = @(3, 5, 7, 8, 10)
        tie_breaking_options_tested = @("same_function_priority", "career_progression_priority", "minimal_level_jump", "skills_overlap_detail")
        similarity_ranges_tested = @("30%-90%", "40%-90%", "50%-70%", "60%-95%")
        source_jobs_tested = @($testJob, "R0100.2", "R0025.1")
        document_formats_tested = @("console_output", "word_document", "clean_copy")
    }
}

# Save summary as JSON
$summaryFile = "$outputDir\test_summary_${timestamp}.json"
$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryFile -Encoding UTF8

Write-Host "📊 Test Suite Summary:" -ForegroundColor Green
Write-Host "   Total Tests: $($summary.total_tests)" -ForegroundColor White
Write-Host "   Successful: $($summary.successful_tests)" -ForegroundColor Green
Write-Host "   Failed: $($summary.failed_tests)" -ForegroundColor $(if($summary.failed_tests -gt 0) {'Red'} else {'Green'})
Write-Host "   Summary Report: $summaryFile" -ForegroundColor White
Write-Host ""

# Display quick findings
Write-Host "🔍 Quick Findings:" -ForegroundColor Yellow
foreach ($result in $allResults) {
    $status = if ($result.success) { "✅" } else { "❌" }
    $extra = ""
    if ($result.summary.generated_count -and $result.summary.requested_count) {
        $extra = " (Generated: $($result.summary.generated_count)/$($result.summary.requested_count))"
    }
    Write-Host "   $status $($result.test_name)$extra" -ForegroundColor $(if($result.success) {'Green'} else {'Red'})
}

Write-Host ""
Write-Host "📁 All test outputs saved to: $outputDir" -ForegroundColor Cyan
Write-Host "📄 Summary report: $summaryFile" -ForegroundColor Cyan

# Return to original directory
Set-Location ..\..\..\..\..

Write-Host ""
Write-Host "🎉 User Story 1 Testing Complete!" -ForegroundColor Green
Write-Host "   Review the JSON summary and individual output files for detailed analysis" -ForegroundColor White