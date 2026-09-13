@echo off
REM ---------------------------------------------------------------------------
REM  Start the JATS RAG retrieval service (Windows launcher)
REM  Serves the store at G:\My Drive\JATS_RAG on http://127.0.0.1:8088
REM ---------------------------------------------------------------------------
setlocal

set "HERE=%~dp0"
if not defined JATS_STORE_DIR set "JATS_STORE_DIR=G:\My Drive\JATS_RAG"
if not defined RAG_PORT set "RAG_PORT=8088"

REM Optional shared secret: set JATS_RAG_TOKEN before running to require auth.
REM set "JATS_RAG_TOKEN=change-me"

echo Store : %JATS_STORE_DIR%
echo Port  : %RAG_PORT%
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%HERE%rag_service.py"
) else (
    python "%HERE%rag_service.py"
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Service exited with code %ERRORLEVEL%.
    echo Check that Ollama is running ^(ollama serve^) and that numpy is installed:
    echo     py -3 -m pip install -r "%HERE%requirements.txt"
    pause
)

endlocal
