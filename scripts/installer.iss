; TimeTrack — Inno Setup installer script
; Produces:  dist\TimeTrack_Setup.exe
; Run with:  ISCC.exe scripts\installer.iss

#define AppName      "TimeTrack"
#define AppVersion   "1.0.0"
#define AppPublisher "TimeTrack"
#define AppURL       "https://github.com/your-username/timetrack"
#define AppExeName   "TimeTrack.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=TimeTrack_Setup
SetupIconFile=TimeTrack.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Require Windows 10 or later (matches PySide6 support)
MinVersion=10.0
; Allow installing without admin rights (per-user install)
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon";  Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; The entire PyInstaller one-file exe
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#AppName}";            Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";  Filename: "{uninstallexe}"
; Desktop (optional — user chooses during install)
Name: "{autodesktop}\{#AppName}";      Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up the data file only if the user explicitly uninstalls
; (commented out by default — user data is precious)
; Type: files; Name: "{userappdata}\.timetrack_data.json"
