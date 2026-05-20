@echo off
@findstr /v "^@f" "%~f0" | powershell -NoProfile -ExecutionPolicy Bypass - & goto :EOF

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@

$keywords = @('save as', 'lưu', 'save', 'export', 'machine', 'xuất', 'confirm', 'xác nhận', 'already exists', 'replace')

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Closing dialog windows (Save As, Export)..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

$closedCount = 0
[Win32]::EnumWindows({
    param($hwnd, $lparam)
    if ([Win32]::IsWindowVisible($hwnd)) {
        $sb = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity) | Out-Null
        $title = $sb.ToString()
        if ($title -and ($title -notmatch "TX Embroider") -and ($title -notmatch "TX EMBROIDER")) {
            foreach ($kw in $keywords) {
                if ($title.ToLower().Contains($kw)) {
                    Write-Host "Closing dialog: $title" -ForegroundColor Yellow
                    [Win32]::PostMessage($hwnd, 0x0112, 0xF060, 0) | Out-Null
                    [Win32]::PostMessage($hwnd, 0x0111, 2, 0) | Out-Null
                    [Win32]::PostMessage($hwnd, 0x0010, 0, 0) | Out-Null
                    $script:closedCount++
                    break
                }
            }
        }
    }
    return $true
}, [IntPtr]::Zero)

if ($closedCount -eq 0) {
    Write-Host "No open dialog windows found matching the keywords." -ForegroundColor Gray
} else {
    Write-Host "Successfully closed $closedCount dialog(s)." -ForegroundColor Green
}
Start-Sleep -Seconds 1
