$uri = "http://localhost:8000/query_stream?query=What+did+the+Supreme+Court+rule+about+Ram+Mandir+ownership%3F&user_id=default_user"

try {
    $response = Invoke-WebRequest -Uri $uri -Method Get -ErrorAction Stop
    Write-Output $response.Content
} catch {
    $response = $_.Exception.Response
    if ($response -ne $null) {
        $stream = $response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $body = $reader.ReadToEnd()
        $reader.Close()
        Write-Output $body
    } else {
        Write-Output "No response object"
    }
}