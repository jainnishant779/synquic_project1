# Renders diagrams\src\*.mmd to diagrams\*.svg and *.png with the Mermaid CLI.
# tools\puppeteer.json points it at the installed Edge, so no browser download is needed.
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$config = (Join-Path $root 'tools\puppeteer.json') -replace '\\', '/'
foreach ($source in Get-ChildItem "$root\diagrams\src\*.mmd") {
    foreach ($extension in 'svg', 'png') {
        $output = "$root\diagrams\$($source.BaseName).$extension"
        & npx.cmd -y '@mermaid-js/mermaid-cli' -i $source.FullName -o $output -b white -s 2 -p $config
        if ($LASTEXITCODE -ne 0) { throw "render failed: $($source.Name)" }
    }
}
