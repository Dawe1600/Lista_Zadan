#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif

#define AppName "ToDoList"
#define AppExeName "ToDoList.exe"
#define AppPublisher "Dawe1600"
#define AppURL "https://github.com/Dawe1600/Lista_Zadan"
#define AppRegKey "Software\ToDoList\ToDoWidgetApp"

[Setup]
AppId={{8D6B4A2E-5C3F-4F9A-9D1B-7E2F0A3C8B14}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}/releases
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
PrivilegesRequired=lowest
OutputDir=..\Output
OutputBaseFilename=ToDoList-Setup-v{#AppVersion}
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=auto
LanguageDetectionMethod=uilanguage
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
polish.AiPageTitle=Konfiguracja Asystenta AI (Google Gemini)
polish.AiPageSubTitle=Opcjonalnie włącz asystenta AI i podaj swój klucz Gemini API.
polish.AiEnableCheck=Włącz funkcje AI (Google Gemini)
polish.AiKeyLabel=Klucz Gemini API (wymagany dla AI; możesz zostawić puste, jeśli AI jest wyłączone):
polish.AiHintLabel=Bezpłatny klucz API wygenerujesz w Google AI Studio (aistudio.google.com). Przy aktualizacji istniejący klucz zostanie automatycznie zachowany.

english.AiPageTitle=AI Assistant Setup (Google Gemini)
english.AiPageSubTitle=Optionally enable the AI assistant and enter your Gemini API key.
english.AiEnableCheck=Enable AI features (Google Gemini)
english.AiKeyLabel=Gemini API Key (required for AI; leave empty if AI is disabled):
english.AiHintLabel=You can generate a free API key in Google AI Studio (aistudio.google.com). When updating, your existing key is preserved automatically.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\ToDoList\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  AiPage: TWizardPage;
  AiEnableCheckBox: TNewCheckBox;
  AiKeyLabel: TNewStaticText;
  AiKeyEdit: TNewEdit;
  AiHintLabel: TNewStaticText;

procedure UpdateAiInputState(Sender: TObject);
begin
  if Assigned(AiKeyEdit) then
    AiKeyEdit.Enabled := AiEnableCheckBox.Checked;
end;

procedure InitializeWizard;
var
  ExistingEnableAI: Cardinal;
  ExistingApiKey: string;
begin
  AiPage := CreateCustomPage(
    wpSelectTasks,
    CustomMessage('AiPageTitle'),
    CustomMessage('AiPageSubTitle')
  );

  AiEnableCheckBox := TNewCheckBox.Create(WizardForm);
  AiEnableCheckBox.Parent := AiPage.Surface;
  AiEnableCheckBox.Left := 0;
  AiEnableCheckBox.Top := ScaleY(8);
  AiEnableCheckBox.Width := AiPage.SurfaceWidth;
  AiEnableCheckBox.Caption := CustomMessage('AiEnableCheck');

  if RegQueryDWordValue(HKEY_CURRENT_USER, '{#AppRegKey}', 'EnableAI', ExistingEnableAI) then
    AiEnableCheckBox.Checked := (ExistingEnableAI <> 0)
  else
    AiEnableCheckBox.Checked := True;

  AiKeyLabel := TNewStaticText.Create(WizardForm);
  AiKeyLabel.Parent := AiPage.Surface;
  AiKeyLabel.Left := 0;
  AiKeyLabel.Top := AiEnableCheckBox.Top + AiEnableCheckBox.Height + ScaleY(16);
  AiKeyLabel.Width := AiPage.SurfaceWidth;
  AiKeyLabel.WordWrap := True;
  AiKeyLabel.AutoSize := True;
  AiKeyLabel.Caption := CustomMessage('AiKeyLabel');

  AiKeyEdit := TNewEdit.Create(WizardForm);
  AiKeyEdit.Parent := AiPage.Surface;
  AiKeyEdit.Left := 0;
  AiKeyEdit.Top := AiKeyLabel.Top + AiKeyLabel.Height + ScaleY(8);
  AiKeyEdit.Width := AiPage.SurfaceWidth;
  if RegQueryStringValue(HKEY_CURRENT_USER, '{#AppRegKey}', 'GeminiApiKey', ExistingApiKey) then
    AiKeyEdit.Text := ExistingApiKey;

  AiHintLabel := TNewStaticText.Create(WizardForm);
  AiHintLabel.Parent := AiPage.Surface;
  AiHintLabel.Left := 0;
  AiHintLabel.Top := AiKeyEdit.Top + AiKeyEdit.Height + ScaleY(12);
  AiHintLabel.Width := AiPage.SurfaceWidth;
  AiHintLabel.WordWrap := True;
  AiHintLabel.AutoSize := True;
  AiHintLabel.Caption := CustomMessage('AiHintLabel');

  AiEnableCheckBox.OnClick := @UpdateAiInputState;
  AiKeyEdit.Enabled := AiEnableCheckBox.Checked;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnableVal: Cardinal;
begin
  if CurStep = ssPostInstall then
  begin
    if AiEnableCheckBox.Checked then
      EnableVal := 1
    else
      EnableVal := 0;

    RegWriteDWordValue(HKEY_CURRENT_USER, '{#AppRegKey}', 'EnableAI', EnableVal);
    RegWriteStringValue(HKEY_CURRENT_USER, '{#AppRegKey}', 'GeminiApiKey', Trim(AiKeyEdit.Text));
  end;
end;
