#define AppInternalName "SimpleYTDLP"
#define AppDisplayName "Simple Video Downloader"
#define AppPublisher "SimpleYTDLP"

#ifndef AppVersion
  #define AppVersion "1.0.1"
#endif

#ifndef SourceDir
  #define SourceDir "..\dist\SimpleYTDLP"
#endif

[Setup]
AppId={{C27ADD14-4734-4EAC-BF2D-5AF02E35B874}
AppName={#AppDisplayName}
AppVersion={#AppVersion}
AppVerName={#AppDisplayName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={code:GetDefaultDir}
DefaultGroupName={#AppDisplayName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=SimpleYTDLP_Setup_{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app.ico
UninstallDisplayName={#AppDisplayName}
UninstallDisplayIcon={app}\SimpleYTDLP.exe
LicenseFile=..\LICENSE
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppDisplayName} installer
VersionInfoProductName={#AppDisplayName}
VersionInfoProductVersion={#AppVersion}
VersionInfoVersion={#AppVersion}
CloseApplications=yes
RestartApplications=no
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\assets"
Type: filesandordirs; Name: "{app}\vendor"
Type: filesandordirs; Name: "{userprograms}\{#AppInternalName}"
Type: filesandordirs; Name: "{commonprograms}\{#AppInternalName}"; Check: IsAdminInstallMode

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppDisplayName}"; Filename: "{app}\SimpleYTDLP.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\app.ico"
Name: "{autodesktop}\{#AppDisplayName}"; Filename: "{app}\SimpleYTDLP.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\SimpleYTDLP.exe"; Description: "Launch {#AppDisplayName}"; Flags: nowait postinstall skipifsilent

[Code]
function GetDefaultDir(Param: String): String;
begin
  if IsAdminInstallMode then
    Result := ExpandConstant('{commonpf}\{#AppInternalName}')
  else
    Result := ExpandConstant('{userappdata}\{#AppInternalName}');
end;
