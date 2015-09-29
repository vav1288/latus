// launch.cpp : Launches the latus app.
//

#include "stdafx.h"
#include <fstream>
#include <time.h>
#include <string>
#include <sstream>
using namespace std;

#include "launch.h"

#define BIG_MAX_PATH (10 * MAX_PATH)  // much larger than the current windows max file path len for future compatibility

// These are bit fields so they can be OR'd together.  If writing to the log file fails, at least we potentially have this to inspect on error.
#define RETURN_SUCCESS 0
#define RETURN_PROCESS_FAILED 1
#define RETURN_LOG_FAILED 2
int g_return_code = RETURN_SUCCESS;

class Logger
{
public:
	Logger(void);
	~Logger(void);
	void out(wchar_t *message);
	void out(int value);

private:
	wchar_t log_file_path[BIG_MAX_PATH];
};

Logger::Logger(void)
{
	wchar_t *app_data_string;
	size_t app_data_size = BIG_MAX_PATH;
	errno_t env_err = _wdupenv_s(&app_data_string, &app_data_size, L"APPDATA");
	if (env_err)
	{
		const wchar_t *default_string = L"";
		wmemcpy(log_file_path, default_string, wcslen(default_string));
	}
	else
	{
		swprintf(log_file_path, BIG_MAX_PATH, L"%s\\latus\\latus_launch.log", app_data_string);
		// clear the log file
		wofstream log_file(log_file_path);
		log_file.close();
		out(L"Start.");
	}
}

Logger::~Logger()
{
	out(L"Exit.");
}

void Logger::out(wchar_t *message)
{
	if (wcslen(log_file_path) > 1)
	{
		// get timestamp
		time_t t = time(0); // obtain the current time_t value
		tm now;
		gmtime_s(&now, &t);
		wchar_t wts[26] = L"";
		_wasctime_s(wts, &now);
		wts[24] = 0; // get rid of newline

		// write to log file
		wofstream logfile(log_file_path, ios::app);
		logfile << wts;
		logfile << L" : ";
		logfile << message;
		logfile << "\n";
		logfile.close();
	}
	else
	{
		g_return_code |= RETURN_LOG_FAILED;
	}
}

void Logger::out(int value)
{
#define LOGGER_BUFFER_LEN 256
	wchar_t s[LOGGER_BUFFER_LEN];
	_itow_s(value, s, LOGGER_BUFFER_LEN, 10);
	out(s);
}

int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow)
{
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);

	Logger log;

	// Create the process
	PROCESS_INFORMATION processInformation = { 0 };
	STARTUPINFO startupInfo = { 0 };
	wchar_t latus_cmd_line[] = L"python\\python.exe main.py";
	BOOL result = CreateProcess(NULL, latus_cmd_line,
		NULL, NULL, FALSE,
		NORMAL_PRIORITY_CLASS | CREATE_NO_WINDOW,
		NULL, NULL, &startupInfo, &processInformation);

	// todo: output an error of the .py file isn't found by python.exe.
	// Currently it's silent.

	if (result)
	{
		log.out(L"CreateProcess success.");
		log.out(latus_cmd_line);
	}
	else
	{
		// CreateProcess() failed
		// Get the error from the system
		LPVOID lpMsgBuf;
		DWORD dw = GetLastError();
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
			NULL, dw, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPTSTR)&lpMsgBuf, 0, NULL);

		// Display the error
		log.out(L"Failed at CreateProcess():");
		log.out(latus_cmd_line);
		log.out((LPTSTR)lpMsgBuf);

		g_return_code |= RETURN_PROCESS_FAILED;
	}

	log.out(L"wWinMain return code:");
	log.out(g_return_code);

    return(g_return_code);
}



