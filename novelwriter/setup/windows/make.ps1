if (Test-Path .\build) {
    Remove-Item .\build -Recurse
}
New-Item -Path . -Name build -ItemType Directory
Set-Location .\build

cmake -S .. -B .
cmake --build . --config Release

Set-Location ..
Copy-Item .\build\Release\novelWriter.exe . -Force
