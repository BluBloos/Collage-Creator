/* TODO(Noah):

Below are the things that will make the platform layer usable for Daniel

- Fix the Alt key because it's not working right now
- Can resize the window
- Can make the window go fullscreen
- Dynamic framerate

Below are the things that would be nice

- Change the icon of the window

*/

/* DEPENDENCIES */
#include "Python.h"
#include <windows.h>
#include <stdio.h>
#include "strings.cpp"
#include "collage_python.cpp"

/* DEFINES */

#if 1
#define DEBUG
#else
#define RELEASE
#endif

#define DESIRED_WINDOW_WIDTH 1280
#define DESIRED_WINDOW_HEIGHT 720
#define DESIRED_FRAMES_PER_SECOND 30
#define OVERRIDE_MONITOR_REFRESH true
#define PLATFORM_KEY_COUNT (26 + 10 + 3 + 4 + 2)

static HANDLE consoleStdOut = NULL;
static DWORD __charactersWrittenDump = 0;

#ifdef DEBUG
#define Log(string) WriteConsole(consoleStdOut, string, StrLen(string), &__charactersWrittenDump, NULL)
#define LogError(string) (printf("[Error]:"), printf(string), Log("[Error]:"), Log(string))
#else
#define Log(string)
#endif

/* ENUMS AND STRUCTS */

/* APP */
enum app_command
{
	COMMAND_IMPORT,
	COMMAND_EXPORT,
	COMMAND_LOAD
};

struct app_button
{
	bool isDown;
	bool wasDown;
};

struct app_input
{
	app_button buttons[PLATFORM_KEY_COUNT];
	float deltaTime;
};

/* WIN32 */

struct win32_bitmap_header
{
	DWORD biSize;
	LONG  biWidth;
	LONG  biHeight;
	WORD  biPlanes;
	WORD  biBitCount;
	DWORD biCompression;
	DWORD biSizeImage;
	LONG  biXPelsPerMeter;
	LONG  biYPelsPerMeter;
	DWORD biClrUsed;
	DWORD biClrImportant;
	DWORD redMask;
	DWORD greenMask;
	DWORD blueMask;
};

struct win32_offscreen_buffer
{
	win32_bitmap_header info;
	void *memory;
	int width;
	int height;
	int pitch;
	int bytesPerPixel;
	int totalSize;
};

/* PLATFORM */

enum platform_key
{
	PLATFORM_KEY_A,
	PLATFORM_KEY_B,
	PLATFORM_KEY_C,
	PLATFORM_KEY_D,
	PLATFORM_KEY_E,
	PLATFORM_KEY_F,
	PLATFORM_KEY_G,
	PLATFORM_KEY_H,
	PLATFORM_KEY_I,
	PLATFORM_KEY_J,
	PLATFORM_KEY_K,
	PLATFORM_KEY_L,
	PLATFORM_KEY_M,
	PLATFORM_KEY_N,
	PLATFORM_KEY_O,
	PLATFORM_KEY_P,
	PLATFORM_KEY_Q,
	PLATFORM_KEY_R,
	PLATFORM_KEY_S,
	PLATFORM_KEY_T,
	PLATFORM_KEY_U,
	PLATFORM_KEY_V,
	PLATFORM_KEY_W,
	PLATFORM_KEY_X,
	PLATFORM_KEY_Y,
	PLATFORM_KEY_Z,
	PLATFORM_KEY_0,
	PLATFORM_KEY_1,
	PLATFORM_KEY_2,
	PLATFORM_KEY_3,
	PLATFORM_KEY_4,
	PLATFORM_KEY_5,
	PLATFORM_KEY_6,
	PLATFORM_KEY_7,
	PLATFORM_KEY_8,
	PLATFORM_KEY_9,
	PLATFORM_KEY_SHIFT,
	PLATFORM_KEY_CTRL,
	PLATFORM_KEY_ALT,
	PLATFORM_KEY_LEFT_ARROW,
	PLATFORM_KEY_RIGHT_ARROW,
	PLATFORM_KEY_UP_ARROW,
	PLATFORM_KEY_DOWN_ARROW,
	PLATFORM_KEY_MOUSE_LEFT,
	PLATFORM_KEY_MOUSE_RIGHT
};

/* GLOBALS */

static bool globalRunning = true;
static win32_offscreen_buffer globalBackBuffer;
static app_input globalInput = {};
static LONGLONG globalPerfFreq;
static char windowName[MAX_PATH] = {};

/* PY OBJECTS FOR PROGRAM SCOPE */

static PyObject *pPlatform = NULL;
static PyObject *pStorage = NULL;
static PyObject *pBackBufferBytes = NULL;
static PyObject *pBackBuffer = NULL;
static PyObject *pModule = NULL;

// Registered python app callbacks
static PyObject *pUpdateAndRender = NULL;
static PyObject *pInit = NULL;
static PyObject *pImport = NULL;
static PyObject *pExport = NULL;
static PyObject *pClose = NULL;
static PyObject *pPreInit = NULL;

// Array of the python objects, where each object stores information about a given input key. platform.keys() is a wrapper around this list.
static PyObject *platformKeys[PLATFORM_KEY_COUNT] = {};

/* WIN32 FUNCTIONS */

inline LARGE_INTEGER Win32GetWallClock()
{
	LARGE_INTEGER Result;
	QueryPerformanceCounter(&Result);
	return (Result);
}

inline float Win32GetSecondsElapsed(LARGE_INTEGER Start, LARGE_INTEGER End, LONGLONG PerfCountFrequency64)
{
	float Result = (float)(End.QuadPart - Start.QuadPart) / (float)PerfCountFrequency64;
	return (Result);
}

void Win32ResizeDIBSection(win32_offscreen_buffer *buffer,int width, int height)
{
	//NOTE(Noah): we can do this since we know that bitmapMemory is initialized to zero since it's static.
	if(buffer->memory)
	{
		VirtualFree(buffer->memory, 0, MEM_RELEASE);
	}

	//NOTE(Noah): set bitmap heights and widths for global struct
	buffer->width = width;
	buffer->height = height;

	//NOTE(Noah): set values in the bitmapinfo
	buffer->info = {};
	buffer->info.biSize = sizeof(BITMAPINFOHEADER);
	buffer->info.biWidth = width;
	buffer->info.biHeight = -height;
	buffer->info.biPlanes = 1;
	buffer->info.biBitCount = 32;
	buffer->info.biCompression = BI_RGB;
	buffer->info.redMask = 0x000000FF;
	buffer->info.greenMask = 0x0000FF00;
	buffer->info.blueMask = 0x00FF0000;

	//NOTE(Noah): Here we are allocating memory to our bitmap since we resized it
	buffer->bytesPerPixel = 4;
	int bitmapMemorySize = width * height * buffer->bytesPerPixel;
	buffer->memory = VirtualAlloc(0, bitmapMemorySize, MEM_COMMIT,PAGE_READWRITE);

	//NOTE(Noah): setting pitch shit, ahah.
	buffer->pitch = width * buffer->bytesPerPixel;

	buffer->totalSize = bitmapMemorySize;
	// TODO(Noah): Probrably want to clear to black each time we resize the window. Also need to recreate the backBuffer object. Dang.
}

void Win32GetWindowDimension(HWND window, int *width, int *height)
{
	RECT clientRect;
	GetClientRect(window, &clientRect);
	*width = clientRect.right - clientRect.left;
	*height = clientRect.bottom - clientRect.top;
}

void Win32DisplayBufferWindow(HDC deviceContext,win32_offscreen_buffer *buffer,int windowWidth,int windowHeight)
{
	int offsetX = (windowWidth - buffer->width) / 2;
	int offsetY = (windowHeight - buffer->height) / 2;

	PatBlt(deviceContext, 0, 0, windowWidth, offsetY, BLACKNESS);
	PatBlt(deviceContext, 0, offsetY + buffer->height, windowWidth, offsetY, BLACKNESS);
	PatBlt(deviceContext, 0, 0, offsetX, windowHeight, BLACKNESS);
	PatBlt(deviceContext, offsetX + buffer->width, 0, offsetX, windowHeight, BLACKNESS);

	//TODO(Noah): Correct aspect ratio.
	StretchDIBits(deviceContext,
				  offsetX, offsetY, buffer->width, buffer->height,
				  0, 0, buffer->width, buffer->height,
				  buffer->memory,
				  (BITMAPINFO *)&buffer->info,
				  DIB_RGB_COLORS,
				  SRCCOPY);
}

OPENFILENAME Win32FileNameDialog(HWND window, char *filePath, int filePathLen, char *initialDir, char*title, int flags, char *filters)
{
	OPENFILENAME fileNameResult = {};
	fileNameResult.lStructSize = sizeof(OPENFILENAME);
	fileNameResult.hwndOwner = window;
	fileNameResult.hInstance = NULL;
	fileNameResult.lpstrFilter = filters;
	if (filters != NULL) {
		fileNameResult.nFilterIndex = 1;
	}
	fileNameResult.lpstrCustomFilter = NULL;
	fileNameResult.lpstrFile = filePath;
	fileNameResult.nMaxFile = filePathLen;
	fileNameResult.lpstrInitialDir = initialDir;
	fileNameResult.lpstrTitle = title;
	fileNameResult.Flags = flags;
	return fileNameResult;
}

/* PYTHON FUNCTIONS */

PyObject *PyPlatformWallClock(PyObject *self, PyObject *args)
{
	LARGE_INTEGER clockTime = Win32GetWallClock();
	float fClockTime = (float)clockTime.QuadPart / (float)globalPerfFreq;

	PyObject *pClockTime = Py_BuildValue("d", fClockTime);

	return pClockTime;
}

PyObject *PyPlatformPrintError(PyObject *self, PyObject *args)
{
	char *message;
	if(!PyArg_ParseTuple(args, "s", &message))
		return NULL;
	LogError(message);
	Log("\n");
	Py_RETURN_NONE;
}

PyObject *PyPlatformPrint(PyObject *self, PyObject *args)
{
	char *message;
	if(!PyArg_ParseTuple(args, "s", &message))
		return NULL;
	Log(message);
	Log("\n");
	Py_RETURN_NONE;
}

PyObject *PyPlatformSetCursor(PyObject *self, PyObject *args)
{
	int cursorEnum;
	if(!PyArg_ParseTuple(args, "i", &cursorEnum))
		return NULL;

	switch(cursorEnum)
	{
		case 0: // arrow
		SetCursor(LoadCursor(0, IDC_ARROW));
		break;
		case 1: // hand
		SetCursor(LoadCursor(0, IDC_HAND));
		break;
		case 2: // up scale
		SetCursor(LoadCursor(0, IDC_SIZENS));
		break;
		case 3: // side scale
		SetCursor(LoadCursor(0, IDC_SIZEWE));
		break;
		case 4: // diagonal up
		SetCursor(LoadCursor(0, IDC_SIZENESW));
		break;
		case 5: // diagonal downs
		SetCursor(LoadCursor(0, IDC_SIZENWSE));
		break;
	}

	Py_RETURN_NONE;
}

PyObject *PyPlatformWindowName(PyObject *self, PyObject *args)
{
	char *message;
	if(!PyArg_ParseTuple(args, "s", &message))
		return NULL;
	StrCpy(windowName, MAX_PATH, message, StrLen(message));
	Py_RETURN_NONE;
}

static PyMethodDef pyPlatformMethods[] =
{
	{"Log", PyPlatformPrint, METH_VARARGS, "Print to the console. Does nothing unless compiled with DEBUG switch."},
	{"SetCursor", PyPlatformSetCursor, METH_VARARGS, "Set the cursor."},
	{"WallClock", PyPlatformWallClock, METH_VARARGS, "Get the current time in seconds"},
	{"SetWindowName", PyPlatformWindowName, METH_VARARGS, "Set the name of the window. Only works if called in AppInit."},
	{"LogError", PyPlatformPrintError, METH_VARARGS, "Print to the error stream."},
	{NULL, NULL, 0, NULL} // Sentinel
};

static struct PyModuleDef pyPlatformModule =
{
	PyModuleDef_HEAD_INIT,
	"platform", // Name of the module
	NULL, // module documentation
	-1, // our module keeps state in global variables
	pyPlatformMethods
};

static struct PyModuleDef pyStorageModule =
{
	PyModuleDef_HEAD_INIT,
	"storage", // Name of the module
	NULL, // module documentation
	-1, // our module keeps state in global variables
	NULL
};

char *PyToString(PyObject *pObj)
{
	PyObject *pString = PyObject_Str(pObj);

	if (pString && PyUnicode_Check(pString))
	{
		if (PyUnicode_READY(pString))
		{
			goto PyToStringFail;
		}

		return (char *)PyUnicode_DATA(pString);
	}
	else
	{
		goto PyToStringFail;
	}

	PyToStringFail:

	Py_XDECREF(pString);
	return NULL;
}

void PyHandleExceptionDumb()
{
	PyObject * err = PyErr_Occurred();

	if (err)
	{
		PyObject *pExcType;
		PyObject *pValue;
		PyObject *pTraceback;

		PyErr_Fetch(&pExcType, &pValue, &pTraceback);

		char *message = PyToString(pValue);

		if (message)
		{
			Log("[Exception]:\n");
			LogError(message);
			Log("\n");
		}
		else
		{
			LogError("Exception printing failed!");
			Log("\n");
		}

		Py_XDECREF(pExcType);
		Py_XDECREF(pValue);
		Py_XDECREF(pTraceback);
	}
}

void PyHandleException()
{
	PyHandleExceptionDumb();
}

LRESULT CALLBACK Win32WindowProc(HWND window,
								 UINT message,
								 WPARAM wParam,
								 LPARAM lParam)
{
	LRESULT result = 0;

	switch(message)
	{
		case WM_DESTROY:
		{
			LogError("The window was destroyed!\n");
			globalRunning = false;
		}
		break;
		case WM_CLOSE:
		{
			Log("The window is closing.\n");
			globalRunning = false;
		}
		break;

		// NOTE(Noah): WM_PAINT happens when the system sends a request to paint a portion of the window.
		case WM_PAINT:
		{
			PAINTSTRUCT paintStruct = {};
			HDC deviceContext = BeginPaint(window, &paintStruct);

			int width;
			int height;
			Win32GetWindowDimension(window, &width, &height);
			Win32DisplayBufferWindow(deviceContext,&globalBackBuffer, width, height);

			EndPaint(window, &paintStruct);
		}
		break;

		case WM_LBUTTONDOWN:
		globalInput.buttons[PLATFORM_KEY_MOUSE_LEFT].isDown = true;
		break;
		case WM_LBUTTONUP:
		globalInput.buttons[PLATFORM_KEY_MOUSE_LEFT].isDown = false;
		break;
		case WM_RBUTTONDOWN:
		globalInput.buttons[PLATFORM_KEY_MOUSE_RIGHT].isDown = true;
		break;
		case WM_RBUTTONUP:
		globalInput.buttons[PLATFORM_KEY_MOUSE_RIGHT].isDown = false;
		break;

		case WM_KEYUP:
		case WM_KEYDOWN:
		{
			bool IsDown = ((lParam & (1 << 31)) == 0);

			switch(wParam)
			{
				case VK_CONTROL:
				globalInput.buttons[PLATFORM_KEY_CTRL].isDown = IsDown;
				break;
				case VK_SHIFT:
				globalInput.buttons[PLATFORM_KEY_SHIFT].isDown = IsDown;
				break;
				case VK_MENU:
				globalInput.buttons[PLATFORM_KEY_ALT].isDown = IsDown;
				break;
				case VK_LEFT:
				globalInput.buttons[PLATFORM_KEY_LEFT_ARROW].isDown = IsDown;
				break;
				case VK_RIGHT:
				globalInput.buttons[PLATFORM_KEY_RIGHT_ARROW].isDown = IsDown;
				break;
				case VK_UP:
				globalInput.buttons[PLATFORM_KEY_UP_ARROW].isDown = IsDown;
				break;
				case VK_DOWN:
				globalInput.buttons[PLATFORM_KEY_DOWN_ARROW].isDown = IsDown;
				break;
				default:
				{
					if (wParam >= '0' && wParam <= '9')
					{
						unsigned int index = (wParam - '0') + PLATFORM_KEY_0;
						globalInput.buttons[index].isDown = IsDown;
					}
					else if (wParam >= 'A' && wParam <= 'Z')
					{
						globalInput.buttons[wParam - 'A'].isDown = IsDown;
					}
				}
			}
		}
		break;
		case WM_COMMAND:
		{
			switch(LOWORD(wParam))
			{
				case COMMAND_IMPORT:
				{
					char filePath[256] = {};

					// TODO: Make more general, i.e. no hard coding of filter and title for dialog
					OPENFILENAME fileNameResult = Win32FileNameDialog(window, filePath, 256, "C:\\", "Open image", OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR, NULL);

					if(!GetOpenFileName(&fileNameResult))
					{
						LogError("Could not open file.\n");
					}
					else
					{
						if (pImport && PyCallable_Check(pImport))
						{
							PyObject *pString = Py_BuildValue("s", filePath);

							PyObject *pValue = PyObject_CallFunctionObjArgs(pImport, pPlatform, pStorage, pString, NULL);

							Py_DECREF(pString);
							Py_XDECREF(pValue);
						}
						else
						{
							// TODO(Noah): Fatal error!
						}
					}
				}
				break;
				case COMMAND_EXPORT:
				{
					char filePath[256] = {};
					char filter[6] = {};
					filter[0] = '.'; filter[1] = 'P'; filter[2] = 'N'; filter[3] = 'G';
					filter[4] = 0; filter[5] = 0;
					//".PNG"
					OPENFILENAME fileNameResult = Win32FileNameDialog(window, filePath, 256, "C:\\", "Save image", OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR, filter);

					if(!GetSaveFileName(&fileNameResult))
					{
						LogError("Could not save file.\n");
					}
					else
					{
						if (pExport && PyCallable_Check(pExport))
						{
							PyObject *pString = Py_BuildValue("s", filePath);

							PyObject *pValue = PyObject_CallFunctionObjArgs(pExport, pPlatform, pStorage,pBackBuffer, pString, NULL);

							Py_DECREF(pString);
							Py_XDECREF(pValue);
						}
						else
						{
							// TODO(Noah): Fatal error!
						}
					}
				}
				break;

				/*
case COMMAND_LOAD:
{
Log("[COMMAND]: Load\n");
}
break;
*/
			}
		}
		break;
		default:
		{
			result = DefWindowProc(window, message, wParam,lParam);
		}
	}
	return result;
}

int CALLBACK WinMain(HINSTANCE instance,
					 HINSTANCE prevInstance,
					 LPSTR cmdLine,
					 int showCode)
{
	WNDCLASS windowClass = {};
	HWND windowHandle = NULL;
	bool pyInitialized = false;

	// Inialize default window name
	StrCpy(windowName, MAX_PATH, "App", 3);
	// reroute printf to log file for error handling
	freopen("log.txt", "w", stdout);

	/* Create a new console for printing (only in debug builds) */
#ifdef DEBUG
	{
		if(!AllocConsole())
		{
			LogError("Unable to create console!\n");
			goto COLLAGE_CLEANUP;
		}

		consoleStdOut = GetStdHandle(STD_OUTPUT_HANDLE);
		if (consoleStdOut == INVALID_HANDLE_VALUE)
		{
			LogError("Unable to retreive handle to console!\n");
			goto COLLAGE_CLEANUP;
		}

		Log("C/Python platform layer version 0.0.0!\n");
	}
#endif

	// Get the exectuable path.
	HMODULE hModule = GetModuleHandle(NULL);
	char exeAbsolutePath[MAX_PATH] = {};
	GetModuleFileName(hModule, exeAbsolutePath, MAX_PATH);

	// Initialize the python interpreter and load application
	Py_SetProgramName((const wchar_t *)exeAbsolutePath);
	Py_Initialize();
	pyInitialized = true;

	{
		PyObject *pName = Py_BuildValue("s", "app");
		pModule = PyImport_Import(pName);
		Py_DECREF(pName);

		if (!pModule)
		{
			LogError("Unable to import App!\n");
			PyHandleException();
			goto COLLAGE_CLEANUP;
		}

		pUpdateAndRender = PyObject_GetAttrString(pModule, "AppUpdateAndRender");

		pInit = PyObject_GetAttrString(pModule, "AppInit");

		pClose = PyObject_GetAttrString(pModule, "AppClose");

		pImport = PyObject_GetAttrString(pModule, "AppImport");

		pExport = PyObject_GetAttrString(pModule, "AppExport");

		pPreInit = PyObject_GetAttrString(pModule, "AppPreInit");

		pPlatform = PyModule_Create(&pyPlatformModule);

		if (!pPlatform)
		{
			LogError("Unable to create platform module!\n");
			PyHandleException();
			goto COLLAGE_CLEANUP;
		}

		pStorage = PyModule_Create(&pyStorageModule);

		if (!pStorage)
		{
			LogError("Unable to create storage module!\n");
			PyHandleException();
			goto COLLAGE_CLEANUP;
		}

		pName = Py_BuildValue("s", "recordclass");
		PyObject *pRecordclass = PyImport_Import(pName);
		Py_DECREF(pName);

		if (!pRecordclass)
		{
			LogError("Unable to import recordclass package!\n");
			PyHandleException();
			goto COLLAGE_CLEANUP;
		}

		PyObject *pKeyTuple = PyObject_CallMethod(pRecordclass, "recordclass", "ss", "key", "isDown wasDown");

		Py_DECREF(pRecordclass);

		if (!pKeyTuple || !PyCallable_Check(pKeyTuple))
		{
			LogError("Unable to generate named tuple for key storage!\n");
			PyHandleException();
			goto COLLAGE_CLEANUP;
		}

		PyObject *pKeys = PyList_New(0);

		if (!pKeys)
		{
			LogError("Unable to create platform.keys!\n");
			PyHandleException();
			goto COLLAGE_CLEANUP;
		}

		for (int i = 0; i < PLATFORM_KEY_COUNT; i++)
		{
			Py_INCREF(Py_False);
			Py_INCREF(Py_False);
			platformKeys[i] = PyObject_CallFunctionObjArgs(pKeyTuple, Py_False, Py_False, NULL);
			if (platformKeys[i] == NULL)
			{
				LogError("Unable to generate elements of platform.keys!\n");
				PyHandleException();
				goto COLLAGE_CLEANUP;
			}

			PyList_Append(pKeys, platformKeys[i]);
		}

		Py_DECREF(pKeyTuple);
		PyObject_SetAttrString(pPlatform, "keys", pKeys);

		// Setup the enums for the keys
		PyObject *pInt = NULL;
		pInt = Py_BuildValue("i", 0);
		PyObject_SetAttrString(pPlatform, "KEY_A", pInt);
		pInt = Py_BuildValue("i", 1);
		PyObject_SetAttrString(pPlatform, "KEY_B", pInt);
		pInt = Py_BuildValue("i", 2);
		PyObject_SetAttrString(pPlatform, "KEY_C", pInt);
		pInt = Py_BuildValue("i", 3);
		PyObject_SetAttrString(pPlatform, "KEY_D", pInt);
		pInt = Py_BuildValue("i", 4);
		PyObject_SetAttrString(pPlatform, "KEY_E", pInt);
		pInt = Py_BuildValue("i", 5);
		PyObject_SetAttrString(pPlatform, "KEY_F", pInt);
		pInt = Py_BuildValue("i", 6);
		PyObject_SetAttrString(pPlatform, "KEY_G", pInt);
		pInt = Py_BuildValue("i", 7);
		PyObject_SetAttrString(pPlatform, "KEY_H", pInt);
		pInt = Py_BuildValue("i", 8);
		PyObject_SetAttrString(pPlatform, "KEY_I", pInt);
		pInt = Py_BuildValue("i", 9);
		PyObject_SetAttrString(pPlatform, "KEY_J", pInt);
		pInt = Py_BuildValue("i", 10);
		PyObject_SetAttrString(pPlatform, "KEY_K", pInt);
		pInt = Py_BuildValue("i", 11);
		PyObject_SetAttrString(pPlatform, "KEY_L", pInt);
		pInt = Py_BuildValue("i", 12);
		PyObject_SetAttrString(pPlatform, "KEY_M", pInt);
		pInt = Py_BuildValue("i", 13);
		PyObject_SetAttrString(pPlatform, "KEY_N", pInt);
		pInt = Py_BuildValue("i", 14);
		PyObject_SetAttrString(pPlatform, "KEY_O", pInt);
		pInt = Py_BuildValue("i", 15);
		PyObject_SetAttrString(pPlatform, "KEY_P", pInt);
		pInt = Py_BuildValue("i", 16);
		PyObject_SetAttrString(pPlatform, "KEY_Q", pInt);
		pInt = Py_BuildValue("i", 17);
		PyObject_SetAttrString(pPlatform, "KEY_R", pInt);
		pInt = Py_BuildValue("i", 18);
		PyObject_SetAttrString(pPlatform, "KEY_S", pInt);
		pInt = Py_BuildValue("i", 19);
		PyObject_SetAttrString(pPlatform, "KEY_T", pInt);
		pInt = Py_BuildValue("i", 20);
		PyObject_SetAttrString(pPlatform, "KEY_U", pInt);
		pInt = Py_BuildValue("i", 21);
		PyObject_SetAttrString(pPlatform, "KEY_V", pInt);
		pInt = Py_BuildValue("i", 22);
		PyObject_SetAttrString(pPlatform, "KEY_W", pInt);
		pInt = Py_BuildValue("i", 23);
		PyObject_SetAttrString(pPlatform, "KEY_X", pInt);
		pInt = Py_BuildValue("i", 24);
		PyObject_SetAttrString(pPlatform, "KEY_Y", pInt);
		pInt = Py_BuildValue("i", 25);
		PyObject_SetAttrString(pPlatform, "KEY_Z", pInt);
		pInt = Py_BuildValue("i", 26);
		PyObject_SetAttrString(pPlatform, "KEY_0", pInt);
		pInt = Py_BuildValue("i", 27);
		PyObject_SetAttrString(pPlatform, "KEY_1", pInt);
		pInt = Py_BuildValue("i", 28);
		PyObject_SetAttrString(pPlatform, "KEY_2", pInt);
		pInt = Py_BuildValue("i", 29);
		PyObject_SetAttrString(pPlatform, "KEY_3", pInt);
		pInt = Py_BuildValue("i", 30);
		PyObject_SetAttrString(pPlatform, "KEY_4", pInt);
		pInt = Py_BuildValue("i", 31);
		PyObject_SetAttrString(pPlatform, "KEY_5", pInt);
		pInt = Py_BuildValue("i", 32);
		PyObject_SetAttrString(pPlatform, "KEY_6", pInt);
		pInt = Py_BuildValue("i", 33);
		PyObject_SetAttrString(pPlatform, "KEY_7", pInt);
		pInt = Py_BuildValue("i", 34);
		PyObject_SetAttrString(pPlatform, "KEY_8", pInt);
		pInt = Py_BuildValue("i", 35);
		PyObject_SetAttrString(pPlatform, "KEY_9", pInt);
		pInt = Py_BuildValue("i", 36);
		PyObject_SetAttrString(pPlatform, "KEY_SHIFT", pInt);
		pInt = Py_BuildValue("i", 37);
		PyObject_SetAttrString(pPlatform, "KEY_CTRL", pInt);
		pInt = Py_BuildValue("i", 38);
		PyObject_SetAttrString(pPlatform, "KEY_ALT", pInt);
		pInt = Py_BuildValue("i", 39);
		PyObject_SetAttrString(pPlatform, "KEY_LEFT_ARROW", pInt);
		pInt = Py_BuildValue("i", 40);
		PyObject_SetAttrString(pPlatform, "KEY_RIGHT_ARROW", pInt);
		pInt = Py_BuildValue("i", 41);
		PyObject_SetAttrString(pPlatform, "KEY_UP_ARROW", pInt);
		pInt = Py_BuildValue("i", 42);
		PyObject_SetAttrString(pPlatform, "KEY_DOWN_ARROW", pInt);
		pInt = Py_BuildValue("i", 43);
		PyObject_SetAttrString(pPlatform, "KEY_MOUSE_LEFT", pInt);
		pInt = Py_BuildValue("i", 44);
		PyObject_SetAttrString(pPlatform, "KEY_MOUSE_RIGHT", pInt);
	}

	// Call AppPreInit function
	if (pPreInit && PyCallable_Check(pPreInit))
	{
		PyObject *pValue = PyObject_CallFunctionObjArgs(pPreInit, pPlatform, pStorage, NULL);
		PyHandleException();
		Py_XDECREF(pValue);
	}

	/* Create the window class */
	windowClass.style = CS_VREDRAW | CS_HREDRAW;
	windowClass.lpfnWndProc = Win32WindowProc;
	windowClass.hInstance = instance;
	windowClass.lpszClassName = "CollageWindowClass";

	// NOTE(Noah): All window classes that an application registers are unregistered when it terminates.
	if(!RegisterClass(&windowClass))
	{
		LogError("Unable to register window class!\n");
		goto COLLAGE_CLEANUP;
	}

	/* Create the menu bar and friends */
	HMENU hMenubar = CreateMenu();
	HMENU hFile = CreateMenu();
	AppendMenu(hMenubar, MF_POPUP, (UINT_PTR)hFile, "File");
	AppendMenu(hFile, MF_STRING, COMMAND_IMPORT, "Import image");
	AppendMenu(hFile, MF_STRING, COMMAND_EXPORT, "Export");
	AppendMenu(hFile, MF_STRING, COMMAND_LOAD, "Open");

	/* Create the window */
	windowHandle = CreateWindowEx(0, windowClass.lpszClassName,windowName,WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX | WS_VISIBLE, CW_USEDEFAULT, CW_USEDEFAULT,DESIRED_WINDOW_WIDTH, DESIRED_WINDOW_HEIGHT, 0, hMenubar,instance, 0);

	if (!windowHandle)
	{
		LogError("Unable to create the window!\n");
		goto COLLAGE_CLEANUP;
	}

	// Set up timing things //
	LARGE_INTEGER lastCounter = Win32GetWallClock();
	float targetSecondsPerFrame = 1.0f / (float)DESIRED_FRAMES_PER_SECOND;
	LONGLONG perfCountFrequency64;

	{
		// TODO(Noah): Better refresh rate checking
		HDC refreshDC = GetDC(windowHandle);
		int monitorRefreshRateHz = (float)DESIRED_FRAMES_PER_SECOND;
		int win32RefreshRate = GetDeviceCaps(refreshDC, VREFRESH);

		if (win32RefreshRate > 1 && !OVERRIDE_MONITOR_REFRESH)
		{
			monitorRefreshRateHz = win32RefreshRate;
		}

		targetSecondsPerFrame = 1.0f / (float)monitorRefreshRateHz;
		ReleaseDC(windowHandle, refreshDC);

		LARGE_INTEGER perfCountFrequency;
		QueryPerformanceFrequency(&perfCountFrequency);
		perfCountFrequency64 = perfCountFrequency.QuadPart;
		globalPerfFreq = perfCountFrequency64;
	}

	int clientWidth;
	int clientHeight;
	Win32GetWindowDimension(windowHandle, &clientWidth, &clientHeight);

	// Create globalBackbuffer
	Win32ResizeDIBSection(&globalBackBuffer, clientWidth, clientHeight);

	// Final python initialization
	{
		PyObject *pName = Py_BuildValue("s", "PIL.Image");
		PyObject *pImage = PyImport_Import(pName);
		Py_DECREF(pName);

		if (!pImage)
		{
			LogError("Module PIL.Image not found!\n");
			goto COLLAGE_CLEANUP;
		}

		PyObject *pNewImage = PyObject_GetAttrString(pImage, "new");

		Py_DECREF(pImage);

		if (!pNewImage || !PyCallable_Check(pNewImage))
		{
			LogError("Unable to call Image.new()!\n");
			goto COLLAGE_CLEANUP;
		}

		PyObject *pMode = Py_BuildValue("s", "RGBA");
		PyObject *pSize = Py_BuildValue("ii", clientWidth, clientHeight);

		LARGE_INTEGER begin = Win32GetWallClock();

		pBackBuffer = PyObject_CallFunctionObjArgs(pNewImage, pMode, pSize, NULL);

		LARGE_INTEGER end = Win32GetWallClock();

		printf("Time to create pBackBuffer: %fms\n", Win32GetSecondsElapsed(begin, end, globalPerfFreq) * 1000.0f);

		Py_DECREF(pNewImage);
		Py_DECREF(pMode);
		Py_DECREF(pSize);

		if (!pBackBuffer)
		{
			LogError("Unable to create backBuffer!\n");
			goto COLLAGE_CLEANUP;
		}

		pBackBufferBytes = PyObject_GetAttrString(pBackBuffer, "tobytes");

		if (!pBackBufferBytes)
		{
			LogError("backBuffer has no method tobytes()!\n");
			goto COLLAGE_CLEANUP;
		}

		PyObject *pDeltaTime = Py_BuildValue("d", targetSecondsPerFrame);

		PyObject_SetAttrString(pPlatform, "deltaTime", pDeltaTime);
	}

	// Call python app init callback
	if (pInit && PyCallable_Check(pInit))
	{
		PyObject *pValue = PyObject_CallFunctionObjArgs(pInit, pPlatform, pStorage, pBackBuffer, NULL);
		PyHandleException();
		Py_XDECREF(pValue);
	}

	while (globalRunning)
	{
		// Update important input extravaganza
		for (int i = 0; i < PLATFORM_KEY_COUNT; i++)
		{
			globalInput.buttons[i].wasDown = globalInput.buttons[i].isDown;
		}

		// Handle windows messages //
		MSG message;
		while (PeekMessage(&message, 0, 0, 0, PM_REMOVE))
		{
			if (message.message == WM_QUIT)
			{
				globalRunning = false;
			}
			else
			{
				TranslateMessage(&message);
				DispatchMessage(&message);
			}
		}

		// Grab the position of the mouse
		// TODO(Noah): Will this code ever fail?
		// TODO(Noah): I have yet to do rigourous testing to verify the validity of this segment of code
		{
			POINT mouseP;
			GetCursorPos(&mouseP);
			ScreenToClient(windowHandle, &mouseP);

			PyObject *pMouseX = Py_BuildValue("i", mouseP.x);
			PyObject_SetAttrString(pPlatform, "mouseX", pMouseX);

			PyObject *pMouseY = Py_BuildValue("i", mouseP.y);
			PyObject_SetAttrString(pPlatform, "mouseY", pMouseY);
		}

		// Write the buttons list into the platform keys list!
		for (int i = 0; i < PLATFORM_KEY_COUNT; i++)
		{
			PyObject *pTuple = platformKeys[i];
			app_button appButton = globalInput.buttons[i];

			if (appButton.isDown)
			{
				Py_INCREF(Py_True);
				PyObject_SetAttrString(pTuple, "isDown", Py_True);
			}
			else
			{
				Py_INCREF(Py_False);
				PyObject_SetAttrString(pTuple, "isDown", Py_False);
			}

			if (appButton.wasDown)
			{
				Py_INCREF(Py_True);
				PyObject_SetAttrString(pTuple, "wasDown", Py_True);
			}
			else
			{
				Py_INCREF(Py_False);
				PyObject_SetAttrString(pTuple, "wasDown", Py_False);
			}
		}

		{
			if (pUpdateAndRender && PyCallable_Check(pUpdateAndRender))
			{
				PyObject *pValue = PyObject_CallFunctionObjArgs(pUpdateAndRender, pPlatform, pStorage, pBackBuffer, NULL);
				PyHandleException();
				Py_XDECREF(pValue);

				// Fix the bit formating. PIL images are ABGR and windows bitmap images are ARGB.
				// TODO(Noah): Look into string pBackBuffer as a PIL windows bitmap. This may speed up my program because I will no longer have to modify each pixel.

				LARGE_INTEGER begin = Win32GetWallClock();

				PyObject *pBytes = PyObject_CallFunctionObjArgs(pBackBufferBytes, NULL);

				LARGE_INTEGER end = Win32GetWallClock();
				printf("Time to retrieve bytes: %fms\n", Win32GetSecondsElapsed(begin, end, globalPerfFreq) * 1000.0f);

				if (pBytes)
				{

					LARGE_INTEGER begin = Win32GetWallClock();

					char *bytes = PyBytes_AsString(pBytes);
					unsigned int *destPointer = (unsigned int *)globalBackBuffer.memory;
					unsigned int *sourcePointer = (unsigned int *)bytes;

					for (unsigned int i = 0; i < globalBackBuffer.width * globalBackBuffer.height; i++)
					{
						*destPointer++ = (*sourcePointer & 0x000000FF) << 16 | (*sourcePointer & 0x00FF0000) >> 16 | *sourcePointer & 0xFF00FF00;
						sourcePointer++;
					}

					LARGE_INTEGER end = Win32GetWallClock();

					printf("Time to convert pixel from RGBA to ABGR: %fms\n", Win32GetSecondsElapsed(begin, end, globalPerfFreq) * 1000.0f);

					begin = Win32GetWallClock();

					Py_DECREF(pBytes);

					end = Win32GetWallClock();

					printf("Time to dealloc bytes: %fms\n", Win32GetSecondsElapsed(begin, end, globalPerfFreq) * 1000.0f);

				}

			}
		}

		LARGE_INTEGER begin = Win32GetWallClock();

		{
			HDC deviceContext = GetDC(windowHandle);
			int width;
			int height;
			Win32GetWindowDimension(windowHandle, &width, &height);
			Win32DisplayBufferWindow(deviceContext,&globalBackBuffer, width, height);
			ReleaseDC(windowHandle, deviceContext);
		}

		LARGE_INTEGER end = Win32GetWallClock();

		printf("Time to draw to window: %fms\n", Win32GetSecondsElapsed(begin, end, globalPerfFreq) * 1000.0f);

		// Sleep so that we don't burn the CPU
		float secondsElapsed = Win32GetSecondsElapsed(lastCounter, Win32GetWallClock(), perfCountFrequency64);

		if (secondsElapsed < targetSecondsPerFrame)
		{
			DWORD sleepMS = (DWORD)(1000.0f * (targetSecondsPerFrame - secondsElapsed));

			if (sleepMS > 0)
			{
				// NOTE(Noah): This function may not be accurate due to the granularity of the system clock. For more accuracy, see https://docs.microsoft.com/en-us/windows/desktop/api/synchapi/nf-synchapi-sleep
				Sleep(sleepMS);
			}

			while (secondsElapsed < targetSecondsPerFrame)
			{
				secondsElapsed = Win32GetSecondsElapsed(lastCounter, Win32GetWallClock(), perfCountFrequency64);
			}
		}
		else
		{
			//LogError("Missed the frame rate! Either something is wrong or you need to do some optimization. Or, Python sucks.\n");
		}

		LARGE_INTEGER endCounter = Win32GetWallClock();

		// Lol! What a cheese!!
		secondsElapsed = Win32GetSecondsElapsed(lastCounter, endCounter, perfCountFrequency64);

		PyObject *pDeltaTime = Py_BuildValue("d", secondsElapsed);

		PyObject_SetAttrString(pPlatform, "deltaTime", pDeltaTime);

		lastCounter = endCounter;
	}

	// Call AppClose function
	if (pClose && PyCallable_Check(pClose))
	{
		PyObject *pValue = PyObject_CallFunctionObjArgs(pClose, pPlatform, pStorage, pBackBuffer, NULL);
		PyHandleException();
		Py_XDECREF(pValue);
	}

	// Run cleanup routines
	{
		COLLAGE_CLEANUP:

		if (windowHandle)
		{
			DestroyWindow(windowHandle);
		}

		// Doesn't matter if this fails or whatever, it won't crash the program
		FreeConsole();

		if (pyInitialized)
		{
			// Since the the python interpreter may fail at deallocating things, I am going to dereference all of these things before finalization for good measure

			Py_XDECREF(pUpdateAndRender);
			Py_XDECREF(pInit);
			Py_XDECREF(pImport);
			Py_XDECREF(pExport);
			Py_XDECREF(pClose);
			Py_XDECREF(pPreInit);
			Py_XDECREF(pModule);
			Py_XDECREF(pBackBufferBytes);
			Py_XDECREF(pBackBuffer);
			Py_XDECREF(pPlatform);
			Py_XDECREF(pStorage);

			for (unsigned int i = 0; i < PLATFORM_KEY_COUNT; i++)
			{
				Py_XDECREF(platformKeys[i]);
			}

			Py_Finalize();
		}

		// Free the backBuffer
		if (globalBackBuffer.memory)
		{
			VirtualFree(globalBackBuffer.memory, 0, MEM_RELEASE);
		}
	}

	return 0;
}
