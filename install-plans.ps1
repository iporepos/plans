# ============================================================================
# CONSTANTS
# ============================================================================

$SectionBar = "==================================================================="
$SubSectionBar = "----------------------------------------------------------------"

# ============================================================================
# BOOTSTRAP
# ============================================================================

# CONSTANTS
# ------------------------------------------------------------------------
# tool name
$ToolName = "plans"

# Tool name for calling in pip
$ToolNamePip = "plans"

# Directory where the tool will be installed (per-user, no admin required)
# LOCALAPPDATA is typically: C:\Users\<user>\AppData\Local

$ToolDir = "$env:LOCALAPPDATA\$ToolName"
$InstallDir = "$ToolDir\bin"
$VenvDir = "$ToolDir\.venv"

# Name of the PowerShell script once installed
$ScriptName = "$ToolName.ps1"

# INSTALLATION CLAUSE
# ------------------------------------------------------------------------
# If the file path is not $InstallDir, then is being called from outside
if ($MyInvocation.MyCommand.Path -notlike "$InstallDir*"){

	# CONFIRM INSTALLATION
	# ------------------------------------------------------------------------
    Write-Host ""
	Write-Host $SectionBar
	Write-Host " START INSTALLATION OF $ToolName "
	Write-Host ""
	Write-Host " >>> Target installation directory:"
	Write-Host ""
	Write-Host "     $ToolDir"
	Write-Host ""
	if (Test-Path $ToolDir) {
        Write-Warning "This directory exists already and will be overwritten!"
    }
    Write-Host ""
	$confirm = $Host.UI.PromptForChoice(
		"Confirm installation",
		"Do you want to install or re-install?",
		@(
			[System.Management.Automation.Host.ChoiceDescription]::new("&Yes", "Proceed with installation"),
			[System.Management.Automation.Host.ChoiceDescription]::new("&No",  "Abort installation")
		),
		1
	)

	if ($confirm -ne 0) {
		Write-Host " >>> Installation cancelled by user."
		Start-Sleep -Seconds 1
		exit 0
	}

	Write-Host " >>> Installation confirmed by user."
	Start-Sleep -Seconds 1

	# PYTHON AVAILABILITY / VERSION CHECK
	# ------------------------------------------------------------------------
	Write-Host ""
	Write-Host $SubSectionBar
	try {
		$version = python --version 2>&1
		Write-Host " >>> Python detected."
	}
	catch {
		Write-Error " >>> Python was not detected on this operating system"
		Write-Host " >>> Please install Python from: https://www.python.org ..."
		Write-Host " >>> ... And ensure it is added to PATH"
		Read-Host " >>> Press Enter to finish"
		Start-Sleep -Seconds 1
		exit 1
	}

	$pyVersion = python -c "import sys; print(sys.version_info.major, sys.version_info.minor)"
    Write-Host " >>> Python version found: $pyVersion"
	Start-Sleep -Seconds 1

	# SETUP
	# ------------------------------------------------------------------------
    Write-Host ""
	Write-Host $SubSectionBar
	Write-Host " >>> Setting up ..."

	# Delete if the current installation exists
	if (Test-Path $ToolDir) {
        Remove-Item $ToolDir -Recurse -Force
        Write-Host " >>> Existing directory deleted"
    }

	# Re-Create the installation directory if it does not already exist
    # -Force ensures no error if the directory already exists
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

	Write-Host " >>> Folder created at $InstallDir ... "
	Start-Sleep -Seconds 1

	# Define the destination path for the installed script
    $TargetScript = Join-Path $InstallDir $ScriptName

    # Copy the currently running script to the installation directory
    # This allows the script to "install itself"
    Copy-Item $MyInvocation.MyCommand.Path $TargetScript -Force

	Write-Host " >>> PowerShell script copied ... "
	Start-Sleep -Seconds 1

	# CREATE WRAPPER
	# ------------------------------------------------------------------------
	# Create a small CMD wrapper so the tool can be executed as a command
    # without requiring the .ps1 extension or execution policy changes

    $CmdPath = Join-Path $InstallDir "$ToolName.cmd"

    @"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0$ScriptName" %*
"@ | Set-Content -Encoding ASCII $CmdPath

	Write-Host ""
	Write-Host $SubSectionBar
	Write-Host " >>> CMD wrapper created ..."
	Start-Sleep -Seconds 1

	# UPDATE PATH
	# ------------------------------------------------------------------------
	# Retrieve the current user's PATH environment variable
    $UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")

	# Add the install directory to PATH if it is not already present
    if ($UserPath -notlike "*$InstallDir*") {
        [Environment]::SetEnvironmentVariable(
            "PATH",
            "$UserPath;$InstallDir",
            "User"
        )
    }

	Write-Host ""
	Write-Host $SubSectionBar
	Write-Host " >>> PATH updated ..."
	Write-Host " >>> Now the tool can be called directly from PowerShell"
	Start-Sleep -Seconds 1


	# CREATE PYTHON VENV + PYTHON ROUTINES
	# ------------------------------------------------------------------------
	Write-Host ""
	Write-Host $SubSectionBar
	Write-Host " >>> Virtual Environment: creating ..."
	& python -m venv $VenvDir

	Write-Host " >>> Virtual Environment: activating ..."
	& $VenvDir\Scripts\Activate.ps1

	Write-Host " >>> Virtual Environment: installing python packages ..."
	& python -m pip install --upgrade pip
	& python -m pip install $ToolNamePip

	# create the projects root folder
	# ------------------------------------------------------------------------
	python -c "from plans import config; config.install_projects_root()"
	python -c "from plans import config; print(f' >>> Projects root created at: {config.DEFAULT_PROJECTS_ROOT}')"

    & deactivate
	Write-Host " >>> Virtual Environment: python setup successfully installed!"
	Start-Sleep -Seconds 1

	# FINISH
	# ------------------------------------------------------------------------
	# Inform the user that installation is complete
	Write-Host ""
	Write-Host $SubSectionBar
    Write-Host " >>> $ToolName installed successfully!"
    Write-Host " >>> Restart your terminal, then run: $ToolName"
	Write-Host ""
	Read-Host " >>> Press Enter to finish"
	Write-Host ""
	Write-Host " >>> Finishing installation ..."
	Write-Host ""
	Start-Sleep -Seconds 1
	exit 0
}


# ============================================================================
# APP TOOL
# ============================================================================
# Normal program starts here

# Parse arguments
$Command = $args[0]

    switch ($Command) {

    "uninstall" {

        Write-Host ""
        Write-Host " >>> Uninstall requested for:"
        Write-Host "  $ToolDir"
        Write-Host ""

        if (-not (Test-Path $ToolDir -PathType Container)) {
            Write-Host " >>> Directory does not exist. Nothing to uninstall."
            return
        }

        $confirmation = Read-Host "Are you sure you want to permanently remove this directory? (Y/N)"

        if ($confirmation -notin @("Y","y")) {
            Write-Host " >>> Uninstall cancelled."
            return
        }

        Write-Host " >>> Scheduling removal ..."

        $cleanupCommand = @"
Start-Sleep -Seconds 2
Remove-Item -LiteralPath '$ToolDir' -Recurse -Force -ErrorAction SilentlyContinue
"@

        Start-Process powershell `
            -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `$ErrorActionPreference = 'SilentlyContinue'; $cleanupCommand" `
            -WindowStyle Hidden

        Write-Host " >>> Uninstall process initiated."
        exit
    }

    "run" {
        Write-Host " >>> Running the program ..."
        # activating the venv
        & $VenvDir\Scripts\Activate.ps1
		# calling a python command
		python -c "import numpy as np; print(np.random.rand(50))"

        & deactivate
    }

    "update" {
        Write-Host "Checking for updates..."
    }

    "check" {
        Write-Host " >>> Checking $ToolName ..."
        & $VenvDir\Scripts\Activate.ps1
		# calling a python command
		python -c "from plans import config; config.live_check()"
        & deactivate
        Write-Host " >>> $ToolName is up and running!"
    }

    "help" {
        Write-Host start "https://iporepos.github.io/plans"
    }

    default {
        Write-Host "Unknown command. Try: $ToolName help"
    }
}