# Signal Hub Development Environment Setup Script for Windows
# Requires PowerShell 5.0+ and Windows 10/11 with WSL2

param(
    [switch]$SkipWSL = $false
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }
function Write-Warning { Write-Host "! $args" -ForegroundColor Yellow }
function Write-Step { Write-Host "==> $args" -ForegroundColor Blue }

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check Windows version
function Test-WindowsVersion {
    Write-Step "Checking Windows version..."
    
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $version = [version]$os.Version
    
    if ($version.Major -lt 10) {
        Write-Error "Windows 10 or higher is required"
        exit 1
    }
    
    Write-Success "Windows $($os.Caption) detected"
}

# Check and enable WSL2
function Setup-WSL {
    if ($SkipWSL) {
        Write-Warning "Skipping WSL setup"
        return
    }
    
    Write-Step "Checking WSL2..."
    
    # Check if WSL is installed
    $wslStatus = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
    
    if ($wslStatus.State -ne "Enabled") {
        Write-Warning "WSL is not enabled. Enabling..."
        
        if (-not (Test-Administrator)) {
            Write-Error "Administrator privileges required to enable WSL"
            Write-Host "Please run this script as Administrator"
            exit 1
        }
        
        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
        
        Write-Warning "WSL enabled. Please restart your computer and run this script again."
        exit 0
    }
    
    # Check WSL version
    try {
        $wslVersion = wsl --status | Select-String "Default Version: 2"
        if ($wslVersion) {
            Write-Success "WSL2 is configured as default"
        } else {
            Write-Step "Setting WSL2 as default..."
            wsl --set-default-version 2
            Write-Success "WSL2 set as default"
        }
    } catch {
        Write-Warning "Could not verify WSL version"
    }
}

# Check Python
function Test-Python {
    Write-Step "Checking Python installation..."
    
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.(\d+)") {
            $minorVersion = [int]$matches[1]
            if ($minorVersion -ge 11) {
                Write-Success "$pythonVersion"
            } else {
                Write-Error "Python 3.11 or higher is required (found $pythonVersion)"
                Write-Host "Download from: https://www.python.org/downloads/"
                exit 1
            }
        }
    } catch {
        Write-Error "Python is not installed"
        Write-Host "Download from: https://www.python.org/downloads/"
        exit 1
    }
}

# Check and install Poetry
function Setup-Poetry {
    Write-Step "Checking Poetry installation..."
    
    try {
        $poetryVersion = poetry --version 2>&1
        Write-Success "$poetryVersion"
    } catch {
        Write-Warning "Poetry is not installed. Installing..."
        
        # Install Poetry
        (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
        
        # Add to PATH
        $poetryPath = "$env:APPDATA\Python\Scripts"
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*$poetryPath*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$poetryPath", "User")
            $env:Path = "$env:Path;$poetryPath"
        }
        
        Write-Success "Poetry installed"
        Write-Warning "You may need to restart your terminal for PATH changes to take effect"
    }
}

# Check Docker Desktop
function Test-Docker {
    Write-Step "Checking Docker Desktop..."
    
    try {
        $dockerVersion = docker --version 2>&1
        Write-Success "$dockerVersion"
        
        # Check if Docker daemon is running
        docker info > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker daemon is running"
        } else {
            Write-Error "Docker daemon is not running"
            Write-Host "Please start Docker Desktop"
            exit 1
        }
    } catch {
        Write-Error "Docker Desktop is not installed"
        Write-Host "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
}

# Setup environment files
function Setup-Environment {
    Write-Step "Setting up environment configuration..."
    
    # Create config directory if not exists
    if (-not (Test-Path "config")) {
        New-Item -ItemType Directory -Path "config" | Out-Null
    }
    
    # Copy .env.example to .env if not exists
    if (-not (Test-Path "config\.env")) {
        if (Test-Path "config\.env.example") {
            Copy-Item "config\.env.example" "config\.env"
            Write-Success "Created config\.env from template"
            Write-Warning "Please update API keys in config\.env"
        }
    } else {
        Write-Success "config\.env already exists"
    }
    
    # Create dev.yaml if not exists
    if (-not (Test-Path "config\dev.yaml")) {
        @"
# Signal Hub Development Configuration
edition: basic
early_access: true
env: development
debug: true

server:
  host: localhost
  port: 3333
  name: "Signal Hub Dev"

logging:
  level: INFO
  format: rich

vector_store:
  type: chromadb
  host: localhost
  port: 8000

embeddings:
  provider: openai
  model: text-embedding-3-small

cache:
  enabled: true
  ttl: 3600

models:
  default_provider: anthropic
  haiku_threshold: 0.3
  sonnet_threshold: 0.7
"@ | Out-File -FilePath "config\dev.yaml" -Encoding utf8
        Write-Success "Created config\dev.yaml"
    } else {
        Write-Success "config\dev.yaml already exists"
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Step "Installing Python dependencies..."
    
    try {
        poetry install
        Write-Success "Dependencies installed"
    } catch {
        Write-Error "Failed to install dependencies"
        Write-Host $_.Exception.Message
        exit 1
    }
}

# Create directories
function Setup-Directories {
    Write-Step "Creating necessary directories..."
    
    $dirs = @("data", "data\cache", "data\logs", "data\embeddings")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Directories created"
}

# Start Docker services
function Start-Services {
    Write-Step "Starting Docker services..."
    
    Set-Location docker
    
    try {
        docker compose up -d chromadb redis postgres
        Write-Success "Services started"
        
        # Wait for services
        Write-Step "Waiting for services to be ready..."
        Start-Sleep -Seconds 5
        
        # Check services
        try {
            Invoke-RestMethod -Uri "http://localhost:8000/api/v1/heartbeat" -ErrorAction SilentlyContinue
            Write-Success "ChromaDB is ready"
        } catch {
            Write-Warning "ChromaDB is not responding yet"
        }
        
    } catch {
        Write-Error "Failed to start services"
        Write-Host $_.Exception.Message
    } finally {
        Set-Location ..
    }
}

# Main setup
function Main {
    Write-Host ""
    Write-Host "🚀 Signal Hub Development Environment Setup for Windows" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Change to script directory
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location (Join-Path $scriptPath "..")
    
    # Run checks and setup
    Test-WindowsVersion
    Setup-WSL
    Test-Python
    Setup-Poetry
    Test-Docker
    Setup-Environment
    Install-Dependencies
    Setup-Directories
    Start-Services
    
    Write-Host ""
    Write-Host "✅ Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Update API keys in config\.env"
    Write-Host "2. Run '.\scripts\validate.ps1' to verify setup"
    Write-Host "3. Run 'poetry run pytest' to run tests"
    Write-Host "4. Run 'poetry run signal-hub serve' to start the server"
    Write-Host ""
    Write-Host "For WSL development (recommended):"
    Write-Host "  wsl"
    Write-Host "  cd /mnt/c/path/to/signal-hub"
    Write-Host "  ./scripts/setup.sh"
    Write-Host ""
}

# Run main
Main