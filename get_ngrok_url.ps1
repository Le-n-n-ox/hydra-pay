# Reads the public HTTPS URL from the local ngrok API
try {
    $t = (Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels").tunnels
    ($t | Where-Object { $_.public_url -like "https*" } | Select-Object -First 1).public_url
} catch { "" }
