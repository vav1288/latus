// launch.cpp : Defines the entry point for the application.
//

#include "stdafx.h"
#include <fstream>
using namespace std;

#include "launch.h"

#define MAX_LOADSTRING 100

// Global Variables:
HINSTANCE hInst;                                // current instance
WCHAR szTitle[MAX_LOADSTRING];                  // The title bar text
WCHAR szWindowClass[MAX_LOADSTRING];            // the main window class name

// Forward declarations of functions included in this code module:
ATOM                MyRegisterClass(HINSTANCE hInstance);
HWND                InitInstance(HINSTANCE, int);
LRESULT CALLBACK    WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK    About(HWND, UINT, WPARAM, LPARAM);

// this code is mainly based on the template created from MSDEV and this web site:
// http://www.codeproject.com/Tips/333559/CreateProcess-and-wait-for-result

#define BIG_MAX_PATH (10 * MAX_PATH)  // much larger than the current windows max file path len for future compatibility
#define MAX_DISPLAY_STRING 1024
#define MAX_LINES 16
bool g_show_display = FALSE;
wchar_t g_log_file_path[BIG_MAX_PATH] = L"";  // if we can't determine a suitable path this will be length 0
int g_line_index = 0;
wchar_t g_lp_display_string[MAX_LINES][MAX_DISPLAY_STRING];
void output_display_string(HWND hwnd);
void clear_log(void);

int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow)
{
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);

	memset(g_lp_display_string, 0, sizeof(g_lp_display_string));

	wchar_t *app_data_string;
	size_t app_data_size = BIG_MAX_PATH;
	errno_t env_err = _wdupenv_s(&app_data_string, &app_data_size, L"APPDATA");
	if (!env_err)
	{
		swprintf(g_log_file_path, BIG_MAX_PATH, L"%s\\latus\\latus_launch.log", app_data_string);
	}

	clear_log();

	DWORD exitCode = 0;

	g_show_display = wcslen(lpCmdLine) > 0; // show the window on any command line option
	if (g_show_display)
	{
		nCmdShow = TRUE;
	}

    // Initialize global strings
    LoadStringW(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
    LoadStringW(hInstance, IDC_LAUNCH, szWindowClass, MAX_LOADSTRING);
    MyRegisterClass(hInstance);

    // Perform application initialization:
	HWND hwnd = InitInstance(hInstance, nCmdShow);
    if (!hwnd)
    {
        return FALSE;
    }

	swprintf(g_lp_display_string[g_line_index], MAX_DISPLAY_STRING, L"Starting");
	output_display_string(hwnd);

    HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_LAUNCH));

    MSG msg;

	// Create the process
	PROCESS_INFORMATION processInformation = { 0 };
	STARTUPINFO startupInfo = { 0 };
	wchar_t latus_cmd_line[] = L"python\\python.exe latus_main.py";
	BOOL result = CreateProcess(NULL, latus_cmd_line,
		NULL, NULL, FALSE,
		NORMAL_PRIORITY_CLASS | CREATE_NO_WINDOW,
		NULL, NULL, &startupInfo, &processInformation);

	if (!result)
	{
		// CreateProcess() failed
		// Get the error from the system
		LPVOID lpMsgBuf;
		DWORD dw = GetLastError();
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
			NULL, dw, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&lpMsgBuf, 0, NULL);

		// Display the error
		swprintf(g_lp_display_string[g_line_index], MAX_DISPLAY_STRING, L"Failed at CreateProcess() Command=%s Message=%s", latus_cmd_line, (LPTSTR) lpMsgBuf);
		output_display_string(hwnd);
		g_show_display = TRUE; // we have an error, so display it
	}
	else
	{
		swprintf(g_lp_display_string[g_line_index], MAX_DISPLAY_STRING, L"CreateProcess success. Command=%s", latus_cmd_line);
		output_display_string(hwnd);
	}

	// todo: keep this app alive until latus finishes
	if (g_show_display)
	{
		if (FALSE)
		{
			// Successfully created the process.  Wait for it to finish.
			WaitForSingleObject(processInformation.hProcess, INFINITE);

			// Get the exit code.
			result = GetExitCodeProcess(processInformation.hProcess, &exitCode);

			// Close the handles.
			CloseHandle(processInformation.hProcess);
			CloseHandle(processInformation.hThread);

			if (!result)
			{
				// Could not get exit code.
				swprintf(g_lp_display_string[g_line_index], MAX_DISPLAY_STRING, L"Executed command but couldn't get exit code. Command=%s", latus_cmd_line);
				output_display_string(hwnd);
			}
			else
			{
				swprintf(g_lp_display_string[g_line_index], MAX_DISPLAY_STRING, L"Finished. Exit code=%d", exitCode);
				output_display_string(hwnd);
			}
		}

		// Main message loop:
		while (GetMessage(&msg, nullptr, 0, 0))
		{
			if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
			{
				TranslateMessage(&msg);
				DispatchMessage(&msg);
			}
		}
	}

	swprintf(g_lp_display_string[g_line_index], MAX_DISPLAY_STRING, L"Exiting");
	output_display_string(hwnd);

    return (int) msg.wParam;
}


// output string in g_lp_display_string
void output_display_string(HWND hwnd)
{
	// write to the log file
	if (wcslen(g_log_file_path) > 0)
	{
		wofstream out(g_log_file_path, ios::app);
		out << g_lp_display_string[g_line_index];
		out << "\n";
		out.close();
	}

	g_line_index++;

	if (g_show_display)
	{
		ShowWindow(hwnd, TRUE);
		RedrawWindow(hwnd, NULL, 0, RDW_INVALIDATE);
	}

}

void clear_log(void)
{
	wofstream out(g_log_file_path);
	out.close();
}

//
//  FUNCTION: MyRegisterClass()
//
//  PURPOSE: Registers the window class.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
    WNDCLASSEXW wcex;

    wcex.cbSize = sizeof(WNDCLASSEX);

    wcex.style          = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc    = WndProc;
    wcex.cbClsExtra     = 0;
    wcex.cbWndExtra     = 0;
    wcex.hInstance      = hInstance;
    wcex.hIcon          = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_LAUNCH));
    wcex.hCursor        = LoadCursor(nullptr, IDC_ARROW);
    wcex.hbrBackground  = (HBRUSH)(COLOR_WINDOW+1);
    wcex.lpszMenuName   = MAKEINTRESOURCEW(IDC_LAUNCH);
    wcex.lpszClassName  = szWindowClass;
    wcex.hIconSm        = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

    return RegisterClassExW(&wcex);
}

//
//   FUNCTION: InitInstance(HINSTANCE, int)
//
//   PURPOSE: Saves instance handle and creates main window
//
//   COMMENTS:
//
//        In this function, we save the instance handle in a global variable and
//        create and display the main program window.
//
HWND InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   hInst = hInstance; // Store instance handle in our global variable

   HWND hWnd = CreateWindowW(szWindowClass, szTitle, WS_OVERLAPPEDWINDOW,
      CW_USEDEFAULT, 0, CW_USEDEFAULT, 0, nullptr, nullptr, hInstance, nullptr);

   if (!hWnd)
   {
      return hWnd;
   }

   return hWnd;
}

//
//  FUNCTION: WndProc(HWND, UINT, WPARAM, LPARAM)
//
//  PURPOSE:  Processes messages for the main window.
//
//  WM_COMMAND  - process the application menu
//  WM_PAINT    - Paint the main window
//  WM_DESTROY  - post a quit message and return
//
//
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_COMMAND:
        {
            int wmId = LOWORD(wParam);
            // Parse the menu selections:
            switch (wmId)
            {
            case IDM_ABOUT:
                DialogBox(hInst, MAKEINTRESOURCE(IDD_ABOUTBOX), hWnd, About);
                break;
            case IDM_EXIT:
                DestroyWindow(hWnd);
                break;
            default:
                return DefWindowProc(hWnd, message, wParam, lParam);
            }
        }
        break;
    case WM_PAINT:
        {
			PAINTSTRUCT ps;
			HDC hdc = BeginPaint(hWnd, &ps);
			int y = 10;
			for (int i = 0; i < g_line_index; i++)
			{
				TextOut(hdc, 10, y, g_lp_display_string[i], wcslen(g_lp_display_string[i]));
				y += 20; // to do: calculate based on font, not this SWAG ...
			}
			EndPaint(hWnd, &ps);
        }
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

// Message handler for about box.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    UNREFERENCED_PARAMETER(lParam);
    switch (message)
    {
    case WM_INITDIALOG:
        return (INT_PTR)TRUE;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, LOWORD(wParam));
            return (INT_PTR)TRUE;
        }
        break;
    }
    return (INT_PTR)FALSE;
}
