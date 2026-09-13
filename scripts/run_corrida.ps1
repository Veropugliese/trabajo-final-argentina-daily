<#
.SYNOPSIS
  Ejecuta de verdad el contrato (prompts/system_prompt.md + user_prompt.md) contra la API de
  Gemini con Google Search real, y guarda la corrida en corridas/.

  Existe como alternativa a scripts/daily_briefing.py porque esta máquina no tiene Python
  instalado; hace exactamente el mismo llamado (mismo modelo, mismo payload, misma herramienta
  googleSearch) a mano en PowerShell. Nunca imprime la API key.

.PARAMETER Modelo
  Modelo de Gemini a usar (default: gemini-3.1-flash-lite, el que usa el contrato).

.PARAMETER Fecha
  Fecha del briefing en formato DD/MM/YYYY (default: hoy).

.PARAMETER VentanaHoras
  Ventana temporal en horas (default: 36).

.PARAMETER Etiqueta
  Sufijo para el nombre del archivo de salida en corridas/ (ej: "1", "2", "pro").
#>

param(
    [string]$Modelo = "gemini-3.1-flash-lite",
    [string]$Fecha = (Get-Date -Format "dd/MM/yyyy"),
    [int]$VentanaHoras = 36,
    [Parameter(Mandatory = $true)][string]$Etiqueta,
    [string]$MaterialFile = $null
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $Root ".env"
$CorridasDir = Join-Path $Root "corridas"

if (-not (Test-Path $EnvFile)) {
    throw "No existe .env en $Root. Creá el archivo con GEMINI_API_KEY=... antes de correr esto."
}

$ApiKey = $null
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*GEMINI_API_KEY\s*=\s*(.+)\s*$') {
        $ApiKey = $Matches[1].Trim()
    }
}
if (-not $ApiKey) {
    throw "GEMINI_API_KEY no encontrada dentro de .env"
}
if ($ApiKey.Length -ge 10) {
    $Masked = $ApiKey.Substring(0, 4) + ("*" * ($ApiKey.Length - 8)) + $ApiKey.Substring($ApiKey.Length - 4)
}
else {
    $Masked = "*" * $ApiKey.Length
}
Write-Host "API key leida (enmascarada): $Masked (longitud: $($ApiKey.Length))"
if ($ApiKey -match '["'']') {
    Write-Host "OJO: la key contiene comillas - probablemente se guardo mal."
}

$SystemPrompt = Get-Content (Join-Path $Root "prompts/system_prompt.md") -Raw -Encoding UTF8
$UserPromptTemplate = Get-Content (Join-Path $Root "prompts/user_prompt.md") -Raw -Encoding UTF8

$UsaMaterialProvisto = [bool]$MaterialFile
if ($UsaMaterialProvisto) {
    $Material = Get-Content $MaterialFile -Raw -Encoding UTF8
}
else {
    $Material = 'No aplica: usa las herramientas de busqueda web disponibles.'
}

$MaterialParaReemplazo = $Material -replace '\$', '$$$$'

$UserPrompt = $UserPromptTemplate `
    -replace '\{\{FECHA\}\}', $Fecha `
    -replace '\{\{VENTANA_HORAS, default 36\}\}', $VentanaHoras `
    -replace '\{\{PEGAR_AQUI_LISTA_DE_ARTICULOS_RECOLECTADOS\}\}', $MaterialParaReemplazo

function ConvertTo-JsonStringLiteral([string]$Text) {
    # Windows PowerShell 5.1's ConvertTo-Json tira System.OutOfMemoryException con textos
    # largos (bug conocido de su escapado de strings) - se arma el JSON a mano para el
    # system prompt / user prompt, que son los campos grandes.
    $Escaped = $Text -replace '\\', '\\\\'
    $Escaped = $Escaped -replace '"', '\"'
    $Escaped = $Escaped -replace "`r`n", '\n'
    $Escaped = $Escaped -replace "`n", '\n'
    $Escaped = $Escaped -replace "`r", '\n'
    $Escaped = $Escaped -replace "`t", '\t'
    return $Escaped
}

$SystemPromptJson = ConvertTo-JsonStringLiteral $SystemPrompt
$UserPromptJson = ConvertTo-JsonStringLiteral $UserPrompt

if ($UsaMaterialProvisto) {
    $ToolsJson = ''
}
else {
    $ToolsJson = '"tools":[{"googleSearch":{}}],'
}

$Payload = '{"systemInstruction":{"parts":[{"text":"' + $SystemPromptJson + '"}]},' + `
    '"contents":[{"role":"user","parts":[{"text":"' + $UserPromptJson + '"}]}],' + `
    $ToolsJson + `
    '"generationConfig":{"temperature":0.2}}'

try {
    $null = $Payload | ConvertFrom-Json
}
catch {
    Write-Host "El JSON armado a mano no es valido antes de mandarlo (largo: $($Payload.Length) caracteres):"
    Write-Host $_.Exception.Message
    throw
}

$Uri = "https://generativelanguage.googleapis.com/v1beta/models/$($Modelo):generateContent"

Write-Host "Llamando a Gemini ($Modelo) para el $Fecha..."

$BodyBytes = [System.Text.Encoding]::UTF8.GetBytes($Payload)

try {
    $Response = Invoke-RestMethod -Uri $Uri -Method Post -Headers @{ "x-goog-api-key" = $ApiKey; "Content-Type" = "application/json; charset=utf-8" } -Body $BodyBytes
}
catch {
    Write-Host "ERROR HTTP al llamar a Gemini:"
    $ErrResponse = $_.Exception.Response
    if ($ErrResponse) {
        $Stream = $ErrResponse.GetResponseStream()
        $Reader = New-Object System.IO.StreamReader($Stream)
        $Body = $Reader.ReadToEnd()
        Write-Host $Body
    }
    else {
        Write-Host $_.Exception.Message
    }
    throw
}

$UsedSearch = $false
foreach ($c in $Response.candidates) {
    if ($c.groundingMetadata.webSearchQueries) { $UsedSearch = $true }
}
if ($UsaMaterialProvisto) {
    Write-Host "Modo Opcion B (material provisto) - no se exige googleSearch de Gemini."
}
elseif (-not $UsedSearch) {
    throw "Gemini no utilizo Google Search; se descarta el briefing (mismo criterio que scripts/daily_briefing.py)"
}

$TextChunks = @()
foreach ($c in $Response.candidates) {
    foreach ($p in $c.content.parts) {
        if ($p.text -and -not $p.thought) { $TextChunks += $p.text }
    }
}
$OutputText = ($TextChunks -join "`n").Trim()
$OutputText = $OutputText -replace '^```json\s*', '' -replace '^```\s*', '' -replace '\s*```$', ''

try {
    $Parsed = $OutputText | ConvertFrom-Json
    $RequiredKeys = @("agente", "fecha_briefing", "version_contrato", "metadata_corrida", "resumen_ejecutivo", "noticias")
    $Missing = $RequiredKeys | Where-Object { -not ($Parsed.PSObject.Properties.Name -contains $_) }
    if ($Missing) {
        throw "Faltan claves obligatorias: $($Missing -join ', ')"
    }
    $ValidationError = $null
}
catch {
    $ValidationError = $_.Exception.Message
    Write-Host "ERROR DE VALIDACION (se guarda igual, tal cual salio, para documentar la falla):"
    Write-Host $ValidationError
}

$PromptTokens = $Response.usageMetadata.promptTokenCount
$OutputTokens = $Response.usageMetadata.candidatesTokenCount
$TotalTokens  = $Response.usageMetadata.totalTokenCount

$Timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"
$FileDate = Get-Date -Format "yyyy-MM-dd"
$OutPath = Join-Path $CorridasDir "$FileDate`_$Etiqueta.md"

$MdContent = @"
# Corrida real - $FileDate ($Etiqueta)

## Entrada

Modelo: ``$Modelo``

``````
$UserPrompt
``````

(Enviado junto con el system prompt vigente en ``prompts/system_prompt.md``.)

## Salida

``````json
$OutputText
``````

## Fecha

- Ejecutada: $Timestamp
- Modelo: $Modelo
- Uso de Google Search confirmado: $UsedSearch
- Tokens de entrada (prompt): $PromptTokens
- Tokens de salida (respuesta): $OutputTokens
- Tokens totales: $TotalTokens
- Validacion de schema: $(if ($ValidationError) { "FALLO -> $ValidationError" } else { "OK" })
"@

New-Item -ItemType Directory -Force -Path $CorridasDir | Out-Null
Set-Content -Path $OutPath -Value $MdContent -Encoding UTF8

Write-Host "Guardado en $OutPath"
Write-Host "Tokens entrada=$PromptTokens salida=$OutputTokens total=$TotalTokens"
Write-Host "Busqueda real usada: $UsedSearch"
if ($ValidationError) {
    Write-Host "OJO: la corrida no paso la validacion de schema (ver arriba) - queda documentada igual."
}
