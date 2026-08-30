Get-ChildItem "C:\Scripts\python\Claude_DB\to_restore" -Recurse -File |
    Where-Object { $_.LastWriteTime.Date -eq (Get-Date).Date } |
    Sort-Object LastWriteTime -Descending |
    Select-Object LastWriteTime, FullName

