#ifndef MyAppVersion
  #define MyAppVersion "2.7.4"
#endif
#define MyAppName "MKV Muxing Batch GUI (Qt5 Compatibility)"
#define MyAppExeName "MKV Muxing Batch GUI Qt5.exe"
#define MyAppPublisher "MKV Muxing Batch GUI contributors"
#define MyAppURL "https://github.com/orphick/mkv-muxing-batch"
#define BuildRoot "..\.."

[Setup]
AppId={{098DFA9B-FF73-49A5-9D14-D984D1C85CA8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases/latest
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#BuildRoot}\LICENSE
OutputDir={#BuildRoot}\release-qt5
OutputBaseFilename=MKV.Muxing.Batch.GUI.x64.v{#MyAppVersion}.Qt5.Windows.Installer
SetupIconFile={#BuildRoot}\Resources\Icons\App.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#BuildRoot}\dist-qt5\MKV Muxing Batch GUI Qt5\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
