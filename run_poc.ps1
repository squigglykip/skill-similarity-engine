#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run the Skill Similarity Engine POC.

.DESCRIPTION
    This script provides an easy way to run the Skill Similarity Engine POC.
    It can either run the analysis pipeline directly or start the web interface.

.PARAMETER Mode
    The mode to run in: "analysis" or "webapp". Default is "analysis".

.PARAMETER SkillsFile
    Path to the skills data CSV file.

.PARAMETER JobsFile
    Path to the jobs data CSV file.

.PARAMETER JobSkillsFile
    Path to the job-skills mapping CSV file.

.PARAMETER Department
    Filter analysis by department.

.PARAMETER OutputDir
    Directory for output files. Default is "./data/poc/output".

.PARAMETER NoVisualizations
    Skip generating visualizations.

.PARAMETER Verbose
    Enable verbose logging.

.EXAMPLE
    ./run_poc.ps1 -Mode analysis -SkillsFile "data/poc/skills_data_20250331_175651.csv" -JobsFile "data/poc/jobs_data_20250331_175651.csv"

.EXAMPLE
    ./run_poc.ps1 -Mode webapp
#>

param (
    [Parameter()]
    [ValidateSet("analysis", "webapp")]
    [string]$Mode = "analysis",

    [Parameter()]
    [string]$SkillsFile,

    [Parameter()]
    [string]$JobsFile,

    [Parameter()]
    [string]$JobSkillsFile,

    [Parameter()]
    [string]$Department,

    [Parameter()]
    [string]$OutputDir = "./data/poc/output",

    [Parameter()]
    [switch]$NoVisualizations,

    [Parameter()]
    [switch]$Verbose
)

# Set current directory to script location
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

function EnsurePythonEnvironment {
    # Check if Python is installed
    try {
        $pythonVersion = python --version
        Write-Host "Using $pythonVersion"
    }
    catch {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }

    # Check required packages
    $requiredPackages = @("pandas", "numpy", "matplotlib", "seaborn")
    if ($Mode -eq "webapp") {
        $requiredPackages += "streamlit"
    }

    foreach ($package in $requiredPackages) {
        $checkCmd = "python -c ""import $package"" 2>$null"
        $result = Invoke-Expression $checkCmd
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing required package: $package"
            python -m pip install $package
        }
    }
}

function RunAnalysis {
    # Prepare the command
    $cmd = "python main.py"
    
    # Add required parameters
    if ($SkillsFile) {
        $cmd += " --skills-file ""$SkillsFile"""
    }
    
    if ($JobsFile) {
        $cmd += " --jobs-file ""$JobsFile"""
    }
    
    if ($JobSkillsFile) {
        $cmd += " --job-skills-file ""$JobSkillsFile"""
    }
    
    if ($Department) {
        $cmd += " --department ""$Department"""
    }
    
    if ($OutputDir) {
        $cmd += " --output-dir ""$OutputDir"""
    }
    
    if ($NoVisualizations) {
        $cmd += " --no-visualizations"
    }
    
    if ($Verbose) {
        $cmd += " --verbose"
    }
    
    # Run the command
    Write-Host "Running analysis with command: $cmd"
    Invoke-Expression $cmd
}

function RunWebApp {
    # Run the Streamlit app
    $cmd = "python -m streamlit run webapp.py"
    
    Write-Host "Starting web interface with command: $cmd"
    Invoke-Expression $cmd
}

# Main script execution
Write-Host "Skill Similarity Engine POC Runner"
Write-Host "=================================="
Write-Host "Mode: $Mode"

# Ensure Python environment
EnsurePythonEnvironment

if ($Mode -eq "analysis") {
    # Check if required parameters are provided
    if (-not $SkillsFile -or -not $JobsFile) {
        Write-Error "Skills file and Jobs file are required for analysis mode."
        Write-Host "Usage examples:"
        Write-Host "  ./run_poc.ps1 -Mode analysis -SkillsFile 'data/poc/skills_data_20250331_175651.csv' -JobsFile 'data/poc/jobs_data_20250331_175651.csv'"
        exit 1
    }
    
    RunAnalysis
} 
elseif ($Mode -eq "webapp") {
    RunWebApp
}
else {
    Write-Error "Invalid mode: $Mode"
    exit 1
} 