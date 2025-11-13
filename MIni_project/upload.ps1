$uri = "http://localhost:8000/ingest"

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$filePath = ".\data\upload_Ram_Mandir_Judgment.pdf"
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileEnc = [System.Text.Encoding]::GetEncoding("ISO-8859-1").GetString($fileBytes)

$bodyLines = (
    "--$boundary",
    'Content-Disposition: form-data; name="file"; filename="upload_Ram_Mandir_Judgment.pdf"',
    "Content-Type: application/pdf$LF",
    $fileEnc,
    "--$boundary--"
) -join $LF

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
    Write-Output $response
} catch {
    Write-Output $_.Exception.Message
}