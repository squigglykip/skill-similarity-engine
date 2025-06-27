# PowerShell Script to Test User Story 1: Top N Discovery Mode
# Tests the configurable Top N analysis with different tie-breaking parameters
# Based on successful manual testing - captures all output properly

Write-Host "🚀 Testing User Story 1: Top N Discovery Mode" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

# Create output directory in the project root
$outputDir = "test_results_top_n_discovery"
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Test configuration
$testJob = "R0102.3"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "📋 Test Configuration:" -ForegroundColor Yellow
Write-Host "   Source Job: $testJob" -ForegroundColor White
Write-Host "   Output Directory: $outputDir" -ForegroundColor White
Write-Host "   Timestamp: $timestamp" -ForegroundColor White
Write-Host ""

# Define test scenarios with proper arguments that actually work
$testScenarios = @(
    @{
        Name = "Default (No Tie-Breaking)"
        Args = "--job-from $testJob --mode top_matches --top-n 5 --pathway"
        Description = "Baseline test with no tie-breaking preferences"
    },
    @{
        Name = "Same Function Priority"
        Args = "--job-from $testJob --mode top_matches --top-n 5 --pathway --same-function-priority"
        Description = "Prioritises roles within the same function family"
    },
    @{
        Name = "Career Progression Priority"
        Args = "--job-from $testJob --mode top_matches --top-n 5 --pathway --career-progression-priority"
        Description = "Prioritises logical career advancement paths"
    },
    @{
        Name = "Minimal Level Jump"
        Args = "--job-from $testJob --mode top_matches --top-n 5 --pathway --minimal-level-jump"
        Description = "Prefers smaller organisational level changes"
    },
    @{
        Name = "Skills Overlap Detail"
        Args = "--job-from $testJob --mode top_matches --top-n 5 --pathway --skills-overlap-detail"
        Description = "Provides detailed skills transition analysis"
    },
    @{
        Name = "Combined Tie-Breaking"
        Args = "--job-from $testJob --mode top_matches --top-n 5 --pathway --same-function-priority --career-progression-priority --minimal-level-jump --skills-overlap-detail"
        Description = "All tie-breaking options combined for maximum refinement"
    },
    @{
        Name = "Top 3 Enhanced"
        Args = "--job-from $testJob --mode top_matches --top-n 3 --pathway --same-function-priority --career-progression-priority"
        Description = "Focused top 3 results with key tie-breaking"
    },
    @{
        Name = "Top 10 Maximum"
        Args = "--job-from $testJob --mode top_matches --top-n 10 --pathway"
        Description = "Maximum results to see full tie-breaking impact"
    }
)

# Summary for tracking results
$summary = @{
    TestRun = $timestamp
    SourceJob = $testJob
    TotalTests = $testScenarios.Count
    Results = @()
}

Write-Host "🧪 Running $($testScenarios.Count) Test Scenarios..." -ForegroundColor Cyan
Write-Host ""

# Run each test scenario
for ($i = 0; $i -lt $testScenarios.Count; $i++) {
    $scenario = $testScenarios[$i]
    $testNumber = $i + 1
    
    Write-Host "[$testNumber/$($testScenarios.Count)] $($scenario.Name)" -ForegroundColor Yellow
    Write-Host "   Description: $($scenario.Description)" -ForegroundColor Gray
    Write-Host "   Arguments: $($scenario.Args)" -ForegroundColor Gray
    
    # Create output filename
    $safeName = $scenario.Name -replace '[^a-zA-Z0-9]', '_'
    $outputFile = "$outputDir\${safeName}_${timestamp}.txt"
    
    try {
        # Run the Python test with proper directory and capture ALL output
        $command = "python src\skill_similarity_engine\webapp\career_analysis\test_career_analysis.py $($scenario.Args)"
        
        Write-Host "   Running: $command" -ForegroundColor Gray
        
        # Set UTF-8 encoding and execute command
        $env:PYTHONIOENCODING = "utf-8"
        $output = & cmd /c "chcp 65001 >nul && $command 2>&1"
        
        if ($LASTEXITCODE -eq 0) {
            # Save output to file
            $output | Out-File -FilePath $outputFile -Encoding UTF8
            
            # Extract key metrics from output
            $metrics = @{
                TestName = $scenario.Name
                OutputFile = $outputFile
                Success = $true
                JobsFound = ($output | Select-String "Strategic Opportunity" | Measure-Object).Count
                SimilarityScores = @()
                TieBreakingActive = ($output | Select-String "Tie-Breaking Options:" | Measure-Object).Count -gt 0
                LinesOfOutput = ($output | Measure-Object -Line).Lines
            }
            
            # Extract similarity scores if available
            $scoreMatches = $output | Select-String "Similarity Score: ([\d.]+)%"
            foreach ($match in $scoreMatches) {
                $score = [decimal]$match.Matches[0].Groups[1].Value
                $metrics.SimilarityScores += $score
            }
            
            Write-Host "   ✅ Success: $($metrics.JobsFound) opportunities found, $($metrics.LinesOfOutput) lines of output" -ForegroundColor Green
            
            if ($metrics.TieBreakingActive) {
                Write-Host "   🔧 Tie-breaking options detected in output" -ForegroundColor Cyan
            }
            
        } else {
            # Handle errors
            $metrics = @{
                TestName = $scenario.Name
                OutputFile = $outputFile
                Success = $false
                Error = $output -join "`n"
                LinesOfOutput = ($output | Measure-Object -Line).Lines
            }
            
            # Still save error output for debugging
            $output | Out-File -FilePath $outputFile -Encoding UTF8
            
            Write-Host "   ❌ Error: Exit code $LASTEXITCODE" -ForegroundColor Red
            Write-Host "   📄 Error details saved to: $outputFile" -ForegroundColor Yellow
        }
        
        $summary.Results += $metrics
        
    } catch {
        Write-Host "   ❌ Exception: $($_.Exception.Message)" -ForegroundColor Red
        
        $metrics = @{
            TestName = $scenario.Name
            OutputFile = $outputFile
            Success = $false
            Exception = $_.Exception.Message
        }
        $summary.Results += $metrics
    }
    
    Write-Host ""
}

# Save summary as JSON
$summaryFile = "$outputDir\test_summary_${timestamp}.json"
$summary | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryFile -Encoding UTF8

# Display final results
Write-Host "📊 Test Results Summary:" -ForegroundColor Green
Write-Host "   Total Tests: $($summary.TotalTests)" -ForegroundColor White
Write-Host "   Successful: $(($summary.Results | Where-Object {$_.Success}).Count)" -ForegroundColor Green
Write-Host "   Failed: $(($summary.Results | Where-Object {!$_.Success}).Count)" -ForegroundColor Red
Write-Host "   Output Directory: $outputDir" -ForegroundColor White
Write-Host "   Summary File: $summaryFile" -ForegroundColor White

Write-Host ""
Write-Host "🎉 User Story 1 Testing Complete!" -ForegroundColor Green
Write-Host "   Review the individual output files for detailed tie-breaking analysis" -ForegroundColor White
