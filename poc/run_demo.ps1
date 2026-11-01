# Runs both demos. No keys and no spend. Run from the repo root.
$ErrorActionPreference = 'Stop'

Write-Output "`n=== Video flow [MOCK clips, real QC and assembly] ==="
python -m poc.video.cli --fresh --seconds 30 --fault sc01_sh02:1:black --fault sc02_sh01:1:frozen
if ($LASTEXITCODE -ne 0) { throw 'video demo failed' }

Write-Output "`n=== Social 360 flow [SIMULATED days, tiny CPU classifier] ==="
python -m poc.social360.run_daily
if ($LASTEXITCODE -ne 0) { throw 'social360 demo failed' }

Write-Output "`n=== Tests, excluding the slow 5-minute render ==="
python -m pytest poc/tests -q -p no:cacheprovider -k "not five_minute"
if ($LASTEXITCODE -ne 0) { throw 'tests failed' }

Write-Output "`nDemo complete."
