; Instalador de PokéFollower Desktop.
; Build: ver tools/build.ps1 (encadena PyInstaller + ISCC).
; Requiere que dist\PokeFollower\ ya exista (salida de PyInstaller, Fase 2).

#define MyAppName "PokéFollower"
; Versión semántica: única fuente en version.py (raíz del repo). tools/build.ps1 la lee
; de ahí y avisa si este valor no coincide. El tag git es "v" + este string.
#define MyAppVersion "0.1.0-beta.1"
; Equivalente numérico x.x.x.x que exige Windows para los recursos de versión del .exe
; del instalador (coincide con version.__version_tuple__).
#define MyAppVersionNumeric "0.1.0.1"
#define MyAppPublisher "PokéFollower Desktop (unofficial, non-commercial fan project)"
#define MyAppExeName "PokeFollower.exe"

[Setup]
; AppId fijo — NUNCA cambiar entre versiones: es la identidad para upgrades y
; desinstalación. Cambiarlo produce una entrada duplicada en Programas y características.
AppId={{9D6B59FE-F850-4412-923B-A03E4D593945}
; Mismo nombre de mutex que crea la app en single_instance.py (MUTEX_NAME). Permite que
; el instalador/desinstalador detecte una instancia en marcha y pida cerrarla. NO depende
; de la versión: idéntico entre releases.
AppMutex=PokeFollowerDesktop
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PokeFollower
; lowest = sin prompt de UAC, instala en %LOCALAPPDATA%\Programs para el usuario actual.
; Menos fricción para un usuario no técnico y elimina de raíz los bugs de permisos en
; Program Files (aunque la migración de config.json a %APPDATA% ya es obligatoria
; independientemente de esto — ver paths.py).
PrivilegesRequired=lowest
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
OutputDir=Output
OutputBaseFilename=PokeFollower-Setup-{#MyAppVersion}
VersionInfoVersion={#MyAppVersionNumeric}
VersionInfoProductVersion={#MyAppVersionNumeric}
VersionInfoProductTextVersion={#MyAppVersion}
SetupIconFile=..\assets\icons\pokeball.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
; English first = default. Spanish still available in the language picker.
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
english.AutoStartTask=Start PokéFollower automatically when Windows starts
spanish.AutoStartTask=Iniciar PokéFollower automáticamente con Windows

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "{cm:AutoStartTask}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\PokeFollower\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CREDITS.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Autostart implementado a nivel de instalador (acceso directo en Startup), no en Python —
; ver decision.log del ciclo de empaquetado.
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; NO se borra %APPDATA%\PokeFollower por defecto: config.json es 208 B y reinstalar debe
; conservar las preferencias del usuario (Pokémon elegido, escala, velocidad, etc.).
