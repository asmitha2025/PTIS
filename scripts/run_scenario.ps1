$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "backend"
$env:PYTHONDONTWRITEBYTECODE = "1"

function Test-PythonCommand($exe, $versionArgs) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $exe @versionArgs *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $previous
    }
}

$script:PythonExe = "python"
$script:PythonArgs = @("-B")
if (-not (Test-PythonCommand "python" @("--version"))) {
    $script:PythonExe = "py"
    $script:PythonArgs = @("-3", "-B")
    if (-not (Test-PythonCommand "py" @("-3", "--version"))) {
        throw "Python 3 was not found. Install Python or enable the py launcher."
    }
}

function Invoke-PtisPython {
    & $script:PythonExe @script:PythonArgs @args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Invoke-PtisPython -m ptis_core.cli run-suite scenarios --output evidence\suite_report.json
Invoke-PtisPython -m ptis_core.cli run-batch scenarios\silk_board_whitefield.json --output evidence\batch_report.json --vehicles 240 --seed 42
Invoke-PtisPython -m ptis_core.cli write-proof-report --suite evidence\suite_report.json --batch evidence\batch_report.json --manifest data\dataset_manifest.json --output evidence\PROOF_REPORT.md