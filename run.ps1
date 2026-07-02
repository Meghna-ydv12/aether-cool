Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Starting AETHER-COOL (Local Dev Mode)   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Start the Backend in a separate PowerShell window
Write-Host "`n[1/2] Starting FastAPI Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd backend; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000`""

# Start the Frontend in a separate PowerShell window
Write-Host "[2/2] Starting React Frontend...`n" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd frontend; npm run dev`""

Write-Host "🚀 Both servers are spinning up in new windows!" -ForegroundColor Cyan
Write-Host "-> Backend API Docs : http://localhost:8000/docs"
Write-Host "-> Frontend UI      : http://localhost:5173"
Write-Host "`nTo stop the servers, just close the two new windows that popped up." -ForegroundColor Gray
