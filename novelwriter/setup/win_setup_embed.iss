; Script for building setup.exe installer with Inno Setup

#define nwAppDir "%%dist%%"
#define nwAppName "novelWriter"
#define nwAppVersion "%%version%%"
#define nwAppPublisher "novelWriter"
#define nwAppURL "https://novelWriter.io"

[Setup]
AppId={{459A75D0-951F-4932-9809-6002EC8E733E}
AppName={#nwAppName}
AppVersion={#nwAppVersion}
AppVerName={#nwAppName} {#nwAppVersion}
AppPublisher={#nwAppPublisher}
AppPublisherURL={#nwAppURL}
AppSupportURL={#nwAppURL}
AppUpdatesURL={#nwAppURL}
SetupIconFile=setup\icons\novelwriter.ico
UninstallDisplayIcon={app}\novelwriter.ico
DefaultDirName={autopf}\{#nwAppName}
LicenseFile=setup\iss_license.txt
DisableProgramGroupPage=yes
UsedUserAreasWarning=no
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#nwAppDir}
OutputBaseFilename=novelwriter-{#nwAppVersion}-amd64-setup
Compression=zip
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; Check: not IsAdminInstallMode

[InstallDelete]
Type: filesandordirs; Name: "{app}\lib\*"
Type: filesandordirs; Name: "{app}\novelwriter\*"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\lib\*"
Type: filesandordirs; Name: "{app}\novelwriter\*"

[Files]
Source: "{#nwAppDir}\novelWriter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#nwAppName}"; Filename: "{app}\novelWriter.exe"; IconFilename: "{app}\novelWriter.ico"
Name: "{autodesktop}\{#nwAppName}"; Filename: "{app}\novelWriter.exe"; IconFilename: "{app}\novelWriter.ico"; Tasks: desktopicon;

[Run]
Filename: "{app}\novelWriter.exe"; Description: "{cm:LaunchProgram,{#StringChange(nwAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKA; Subkey: "Software\Classes\.nwx\OpenWithProgids"; ValueType: string; ValueName: "novelWriterProject.nwx"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\novelWriterProject.nwx"; ValueType: string; ValueName: ""; ValueData: "novelWriter Project File"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\novelWriterProject.nwx\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\novelwriter\assets\icons\x-novelwriter-project.ico"
Root: HKA; Subkey: "Software\Classes\novelWriterProject.nwx\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\novelWriter.exe"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\novelWriter.exe\SupportedTypes"; ValueType: string; ValueName: ".nwx"; ValueData: ""; Flags: uninsdeletekey
