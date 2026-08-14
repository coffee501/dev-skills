[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$skillRoot = Split-Path -Parent $PSScriptRoot
$skillRootFull = [System.IO.Path]::GetFullPath($skillRoot).TrimEnd('\') + '\'
$suiteRoot = Split-Path -Parent $skillRoot
$devLcRoot = [System.IO.Path]::GetFullPath((Join-Path $suiteRoot 'dev-lc')).TrimEnd('\') + '\'
$skillPath = Join-Path $skillRoot 'SKILL.md'
$manifestPath = Join-Path $skillRoot 'agents\openai.yaml'
$reversePath = Join-Path $skillRoot 'references\implementation-to-requirements.md'
$outputPath = Join-Path $skillRoot 'references\output-contracts.md'
$behaviorCasesPath = Join-Path $skillRoot 'tests\behavior-cases.json'
$failures = [System.Collections.Generic.List[string]]::new()

function Assert-Condition {
    param(
        [Parameter(Mandatory)]
        [bool]$Condition,
        [Parameter(Mandatory)]
        [string]$Message
    )

    if (-not $Condition) {
        $script:failures.Add($Message)
    }
}

function Assert-Contains {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Content,
        [Parameter(Mandatory)]
        [string]$Pattern,
        [Parameter(Mandatory)]
        [string]$Message
    )

    Assert-Condition -Condition ($Content -match $Pattern) -Message $Message
}

function Read-RequiredText {
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $script:failures.Add("Missing $Label.")
        return ''
    }

    try {
        return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
    }
    catch {
        $script:failures.Add("Unable to read $Label`: $($_.Exception.Message)")
        return ''
    }
}

$skill = Read-RequiredText -Path $skillPath -Label 'SKILL.md'
$manifest = Read-RequiredText -Path $manifestPath -Label 'agents/openai.yaml'
$reverse = Read-RequiredText -Path $reversePath -Label 'reverse-requirement reference'
$output = Read-RequiredText -Path $outputPath -Label 'output-contract reference'
if (-not (Test-Path -LiteralPath $behaviorCasesPath -PathType Leaf)) {
    $failures.Add('Missing behavior regression cases.')
}

$frontmatterMatch = [regex]::Match($skill, '(?ms)\A---[ \t]*\r?\n(?<body>.*?)\r?\n---[ \t]*\r?\n')
Assert-Condition -Condition $frontmatterMatch.Success -Message 'SKILL.md must start with frontmatter.'
$frontmatterLines = @(
    $frontmatterMatch.Groups['body'].Value -split "`r?`n" |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
)
$frontmatterKeys = @(
    [regex]::Matches($frontmatterMatch.Groups['body'].Value, '(?m)^([a-zA-Z0-9_-]+):') |
        ForEach-Object { $_.Groups[1].Value } |
        Sort-Object
)
Assert-Condition -Condition ($frontmatterKeys.Count -eq 2 -and ($frontmatterKeys -join ',') -eq 'description,name') -Message 'SKILL.md frontmatter must contain only name and description.'
Assert-Condition -Condition ($frontmatterLines.Count -eq 2) -Message 'SKILL.md frontmatter fields must each use one line.'
$nameLines = @($frontmatterLines | Where-Object { $_ -match '^name:\s*dev-req\s*$' })
$descriptionLines = @($frontmatterLines | Where-Object { $_ -match '^description:\s*\S.*$' })
Assert-Condition -Condition ($nameLines.Count -eq 1) -Message 'SKILL.md must declare name: dev-req.'
Assert-Condition -Condition ($descriptionLines.Count -eq 1) -Message 'SKILL.md must declare a non-empty single-line description.'
if ($descriptionLines.Count -eq 1) {
    $descriptionValue = ($descriptionLines[0] -replace '^description:\s*', '').Trim()
    $balancedDoubleQuotes = -not $descriptionValue.StartsWith('"') -or $descriptionValue.EndsWith('"')
    $balancedSingleQuotes = -not $descriptionValue.StartsWith("'") -or $descriptionValue.EndsWith("'")
    Assert-Condition -Condition ($balancedDoubleQuotes -and $balancedSingleQuotes) -Message 'SKILL.md description has an unterminated quote.'
}
Assert-Contains $skill 'P0' 'P0 blocking semantics are missing.'
Assert-Contains $skill 'Given\s*/\s*When\s*/\s*Then' 'Given / When / Then acceptance guidance is missing.'
Assert-Contains $skill 'references/requirement-framework\.md' 'SKILL.md must route to the requirement framework reference.'
Assert-Contains $skill 'references/output-contracts\.md' 'SKILL.md must route to the output contract reference.'
Assert-Contains $skill 'existing implementations' 'Reverse-requirement trigger text is missing from the description.'
Assert-Contains $skill 'do not use for general code comprehension, debugging, refactoring, code review, or architecture analysis' 'Negative trigger boundary is missing.'
Assert-Contains $skill 'references/implementation-to-requirements\.md' 'SKILL.md must route to the reverse-requirement reference.'
Assert-Contains $skill 'CAND-\*' 'Candidate-only identifier guidance is missing.'
Assert-Contains $skill 'source excerpts' 'Requirement-content and implementation-evidence boundary is missing.'
Assert-Contains $reverse 'CAND-001' 'Reverse-requirement candidate model is missing.'
Assert-Contains $reverse 'REQ/RULE/AC' 'Formal promotion boundary is missing.'
Assert-Contains $reverse 'As-Is' 'As-Is evidence guidance is missing.'
Assert-Contains $reverse 'To-Be' 'To-Be separation guidance is missing.'
Assert-Contains $reverse 'Feature Flag' 'Conditional behavior guidance is missing.'
Assert-Contains $output 'CAND-\*' 'Reverse-requirement output contract must require candidate identifiers.'

$confirmationWord = ([string][char]0x786E) + ([string][char]0x8BA4)
$migrationWord = ([string][char]0x8FC1) + ([string][char]0x79FB)
$architectureMigration = ([string][char]0x67B6) + ([string][char]0x6784) + $migrationWord
$technicalMigration = ([string][char]0x6280) + ([string][char]0x672F) + $migrationWord
Assert-Condition -Condition ($reverse -match "$confirmationWord.*REQ/RULE/AC|REQ/RULE/AC.*$confirmationWord") -Message 'Formal promotion must require explicit confirmation.'
$devHldLines = $reverse -split "`r?`n" | Where-Object { $_ -match 'dev-hld' }
Assert-Condition -Condition ([bool]($devHldLines | Where-Object { $_.Contains($architectureMigration) -or $_.Contains($technicalMigration) })) -Message 'dev-hld handoff must be limited to architecture or technical migration.'
$genericMigrationHandoffs = $devHldLines | Where-Object {
    $_.Contains($migrationWord) -and
    -not $_.Contains($architectureMigration) -and
    -not $_.Contains($technicalMigration)
}
Assert-Condition -Condition ($genericMigrationHandoffs.Count -eq 0) -Message 'Generic migration handoff to dev-hld is forbidden.'
Assert-Contains $manifest 'default_prompt:\s*".*\$dev-req' 'default_prompt must mention $dev-req explicitly.'
Assert-Contains $manifest 'allow_implicit_invocation:\s*true' 'Implicit invocation policy must remain explicit.'

$behaviorCases = @()
if (Test-Path -LiteralPath $behaviorCasesPath -PathType Leaf) {
    try {
        $behaviorDocument = Get-Content -Raw -Encoding UTF8 -LiteralPath $behaviorCasesPath | ConvertFrom-Json
        Assert-Condition -Condition ($behaviorDocument.schema_version -eq 1) -Message 'Unsupported behavior-case schema version.'
        $behaviorCases = @($behaviorDocument.cases)
    }
    catch {
        $failures.Add("Invalid behavior-case JSON: $($_.Exception.Message)")
    }
}

$requiredBehaviorCases = @{
    'diagnosis-unconfirmed-assumptions' = 'requirement-diagnosis'
    'complete-output-with-p0' = 'complete-output'
    'review-without-rewrite' = 'requirement-review'
    'negative-general-code-debugging' = 'negative-trigger'
    'reverse-conflicting-evidence' = 'reverse-discovery'
    'reverse-conditional-configuration' = 'reverse-discovery'
    'reverse-partial-promotion' = 'incremental-refinement'
    'reverse-evidence-content-boundary' = 'reverse-discovery'
}
$allowedBehaviorModes = @(
    'requirement-diagnosis',
    'incremental-refinement',
    'complete-output',
    'requirement-review',
    'reverse-discovery',
    'negative-trigger'
)
foreach ($requiredCase in $requiredBehaviorCases.GetEnumerator()) {
    $matchingCases = @($behaviorCases | Where-Object { $_.id -eq $requiredCase.Key })
    Assert-Condition -Condition ($matchingCases.Count -eq 1) -Message "Missing or duplicate behavior case: $($requiredCase.Key)"
    if ($matchingCases.Count -eq 1) {
        Assert-Condition -Condition ($matchingCases[0].mode -eq $requiredCase.Value) -Message "Unexpected behavior mode for case: $($requiredCase.Key)"
    }
}
foreach ($case in $behaviorCases) {
    Assert-Condition -Condition (-not [string]::IsNullOrWhiteSpace($case.request)) -Message "Behavior case has no request: $($case.id)"
    Assert-Condition -Condition ($allowedBehaviorModes -contains $case.mode) -Message "Unsupported behavior mode: $($case.mode)"
    Assert-Condition -Condition (@($case.expected_invariants).Count -ge 2) -Message "Behavior case needs at least two expected invariants: $($case.id)"
    Assert-Condition -Condition (@($case.forbidden_outcomes).Count -ge 1) -Message "Behavior case needs a forbidden outcome: $($case.id)"
}

$markdownFiles = Get-ChildItem -LiteralPath $skillRoot -Recurse -File -Filter '*.md'
foreach ($file in $markdownFiles) {
    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName
    $links = [regex]::Matches($content, '\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)')
    foreach ($link in $links) {
        $target = $link.Groups[1].Value
        if ($target -match '^[a-z][a-z0-9+.-]*:' -or $target.StartsWith('#')) {
            continue
        }

        $resolved = [System.IO.Path]::GetFullPath((Join-Path $file.DirectoryName $target))
        if (-not $resolved.StartsWith($skillRootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            if ($resolved.StartsWith($devLcRoot, [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $devLcRoot)) {
                Assert-Condition -Condition (Test-Path -LiteralPath $resolved) -Message "Broken dev-lc suite reference: $($file.FullName) -> $target"
                continue
            }

            Write-Verbose "Optional external reference not validated: $($file.FullName) -> $target"
            continue
        }

        Assert-Condition -Condition (Test-Path -LiteralPath $resolved) -Message "Broken package reference: $($file.FullName) -> $target"
    }
}

$iconLinks = [regex]::Matches($manifest, 'icon_(?:small|large):\s*"([^"]+)"')
foreach ($iconLink in $iconLinks) {
    $iconPath = Join-Path $skillRoot $iconLink.Groups[1].Value
    Assert-Condition -Condition (Test-Path -LiteralPath $iconPath -PathType Leaf) -Message "Missing icon: $($iconLink.Groups[1].Value)"
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { [Console]::Error.WriteLine("ERROR: $_") }
    exit 1
}

Write-Output "dev-req validation passed: $($markdownFiles.Count) Markdown files checked."
