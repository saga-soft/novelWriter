/*
** novelWriter - Windows Launcher
** ==============================
**
** This file is a part of novelWriter
** Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors
**
** This program is free software: you can redistribute it and/or modify
** it under the terms of the GNU General Public License as published by
** the Free Software Foundation, either version 3 of the License, or
** (at your option) any later version.
**
** This program is distributed in the hope that it will be useful, but
** WITHOUT ANY WARRANTY; without even the implied warranty of
** MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
** General Public License for more details.
**
** You should have received a copy of the GNU General Public License
** along with this program. If not, see <https://www.gnu.org/licenses/>.
*/

#ifndef UNICODE
#define UNICODE
#endif

#include <windows.h>
#include <wchar.h>
#include <stdio.h>

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow)
{

    STARTUPINFO si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    wchar_t path[MAX_PATH];
    GetModuleFileNameW(NULL, path, MAX_PATH);
    wchar_t *lastSlash = wcsrchr(path, L'\\');
    if (lastSlash != NULL)
    {
        *lastSlash = 0;
    }
    SetCurrentDirectory(path);

    // 32767 chars is the maximum length of a Windows command line
    wchar_t cmd[32768] = L"pythonw.exe novelWriter.pyw";
    if (__argc > 1)
    {
        wcsncat_s(cmd, L" \"", 2);
        wcsncat_s(cmd, __wargv[1], _TRUNCATE);
        wcsncat_s(cmd, L"\"", 1);
    }

    DWORD exitCode = 0;
    if (CreateProcess(NULL, cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi))
    {
        // Explicitly grant the child the right to bring its own window to
        // the foreground. Without this, the implicit grace period Windows
        // gives a newly launched process expires by the time the splash
        // screen finishes and the main window is ready to show, so it
        // opens behind other windows instead of in the foreground.
        AllowSetForegroundWindow(pi.dwProcessId);

        // Keep the launcher process alive until the app exits so that
        // Windows treats them as one continuously-running process for
        // taskbar/shell purposes, and so the app's exit code propagates.
        WaitForSingleObject(pi.hProcess, INFINITE);
        GetExitCodeProcess(pi.hProcess, &exitCode);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    return static_cast<int>(exitCode);
}
