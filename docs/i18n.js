// Localization for the Maggy landing page.
// Supports ?lang=<code>, localStorage persistence, and browser locale detection.
(() => {
  "use strict";

  const STORAGE_KEY = "maggy-lang";
  const DEFAULT_LOCALE = "en";

  const LOCALES = [
    { code: "en", label: "English", ogLocale: "en_US" },
    { code: "zh-CN", label: "简体中文", ogLocale: "zh_CN" },
    { code: "ja", label: "日本語", ogLocale: "ja_JP" },
    { code: "ko", label: "한국어", ogLocale: "ko_KR" },
    { code: "es", label: "Español", ogLocale: "es_ES" },
    { code: "fr", label: "Français", ogLocale: "fr_FR" },
    { code: "de", label: "Deutsch", ogLocale: "de_DE" },
    { code: "pt", label: "Português", ogLocale: "pt_BR" },
  ];

  const MESSAGES = {
    en: {
      "meta.title": "Maggy — Terminal Pet & Statusline for Antigravity CLI (agy)",
      "meta.description": "Animated terminal pet & custom statusline for Antigravity CLI (agy). Watch Maggy dance beside your live model, context & quota usage bars, and git branch.",
      "meta.ogDescription": "Animated terminal pet & custom statusline for Antigravity CLI (agy) — a dancing mascot with live model, context & quota usage bars, reasoning effort, and git branch.",
      "a11y.skip": "Skip to content",
      "a11y.home": "Maggy home",
      "a11y.nav": "Primary",
      "a11y.lang": "Language",
      "nav.try": "Try it",
      "nav.install": "Install",
      "nav.commands": "Commands",
      "nav.github": "GitHub",
      "hero.title": "Maggy lives in your <span class=\"nowrap\">agy statusline.</span>",
      "hero.lede": "An animated terminal pet and custom <strong>Antigravity CLI (<code>agy</code>)</strong> statusline. Maggy dances while <code>agy</code> works, stomps through tool calls, and dozes off when you step away — right beside your live model, context window, quota usage bars, reasoning effort, and git branch.",
      "hero.hint": "macOS or Linux, Python 3, a truecolor terminal. <a href=\"#install\">Other ways to install</a>",
      "hero.spriteAria": "Maggy, the Antigravity logo with eyes, dancing",
      "states.done": "idle · just done",
      "states.sleep": "idle · 2 min",
      "states.note": "agy redraws the statusline only when something changes, never on a timer. While idle Maggy holds one pose and only her sparkles twinkle (via the terminal's blink attribute). Click <b>idle</b> again to simulate the next redraw.",
      "try.title": "Customize your agy statusline",
      "try.desc": "This is the statusline <code>agy</code> draws under your prompt. Maggy sits to the left of your model, context usage, color-coded quota bars, workspace, and git branch — every frame is the same width, so nothing beside her ever shifts. Change a setting below to see the command that does it.",
      "try.terminalAria": "Preview of the agy statusline with Maggy",
      "try.petName": "Pet name",
      "try.theme": "Theme",
      "try.moodCaption": "Mood caption",
      "try.idleTwinkle": "Idle twinkle",
      "try.note": "<code>auto</code> switches to the Xmas look by itself on December 25: Santa hat, falling snow, lights on the arch and a little tree. Idle twinkle uses the terminal's blink attribute, so sparkles keep moving even when agy stops redrawing.",
      "install.title": "Install Maggy for Antigravity CLI",
      "install.desc": "<code>maggy setup</code> points <code>statusLine</code> in <code>~/.gemini/antigravity-cli/settings.json</code> at Maggy. Your other settings stay as they are, and the old file is saved as <code>settings.json.bak</code>.",
      "install.tabsAria": "Install method",
      "install.brew.step1": "Install the formula",
      "install.brew.step2": "Hook Maggy into agy",
      "install.restart": "Restart agy, or run <code>/statusline enable</code> inside it.",
      "install.brew.note": "Upgrade with <code>brew upgrade maggy</code>. Shell completions for bash, zsh and fish come with it.",
      "install.curl.step1": "Run the installer. It clones to <code>~/.maggy</code>, links <code>maggy</code> into <code>~/.local/bin</code> and runs <code>maggy setup</code>.",
      "install.curl.note": "Pass setup options with <code>| bash -s -- --theme xmas --no-mood</code>. Update later with <code>maggy update</code>.",
      "install.git.step1": "Clone the repo",
      "install.git.step2": "Hook Maggy into agy",
      "commands.title": "CLI commands",
      "commands.desc": "Everything goes through one command. Run <code>maggy help</code> for the full list.",
      "commands.status": "Shows whether Maggy is hooked up, your theme and settings, and a sample of her.",
      "commands.preview": "Plays any <code>agent_state</code> in your terminal without starting an agent turn.",
      "commands.disable": "Hides the statusline without removing it. <code>statusline on</code> brings it back.",
      "commands.pet": "Hides the logo and keeps the metrics. <code>motion off</code> holds a still pose instead, and <code>side right</code> moves her to the right. Each takes <code>toggle</code>.",
      "commands.hide": "Leaves segments out: <code>model</code>, <code>context</code>, <code>quota</code>, <code>workspace</code>, <code>git</code>, <code>effort</code>. <code>maggy statusline show</code> brings them back.",
      "commands.doctor": "Checks Python, truecolor support, the settings file, and how fast a frame renders.",
      "commands.config": "Shows <code>~/.config/maggy/config.json</code>. Use <code>get</code>, <code>set</code> or <code>reset</code> to change it.",
      "commands.uninstall": "Removes the statusLine entry, config and cache. Your other agy settings stay.",
      "footer.madeFor": "Made for <a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a> statuslines. Not affiliated with Google.",
      "footer.source": "Source on GitHub",
      "copy.idle": "Copy",
      "copy.copied": "Copied",
      "copy.fallback": "Select and copy",
    },

    "zh-CN": {
      "meta.title": "Maggy — Antigravity CLI (agy) 终端宠物与自定义状态栏",
      "meta.description": "专为 Antigravity CLI (agy) 打造的动态终端宠物与自定义状态栏。看 Maggy 在当前模型、上下文与配额进度条以及 Git 分支旁起舞。",
      "meta.ogDescription": "专为 Antigravity CLI (agy) 打造的动态终端宠物与自定义状态栏，在当前模型、上下文与配额进度条、推理强度和 Git 分支旁起舞。",
      "a11y.skip": "跳到主要内容",
      "a11y.home": "Maggy 首页",
      "a11y.nav": "主导航",
      "a11y.lang": "选择语言",
      "nav.try": "在线体验",
      "nav.install": "安装",
      "nav.commands": "命令",
      "nav.github": "GitHub",
      "hero.title": "让 Maggy 住进你的 <span class=\"nowrap\">agy 状态栏</span>",
      "hero.lede": "专为 <strong>Antigravity CLI（<code>agy</code>）</strong>打造的动态终端宠物与自定义状态栏。<code>agy</code> 干活时 Maggy 会跟着起舞，调用工具时欢快踏步，你离开一会儿她就打起瞌睡——紧挨着你的当前模型、上下文窗口、配额进度条、推理强度和 Git 分支。",
      "hero.hint": "需要 macOS 或 Linux、Python 3 和支持真彩色的终端。<a href=\"#install\">其他安装方式</a>",
      "hero.spriteAria": "正在跳舞的带眼睛 Antigravity 标志宠物 Maggy",
      "states.done": "idle · 刚完成",
      "states.sleep": "idle · 2 分钟",
      "states.note": "agy 只在状态变化时重绘状态栏，不会定时刷新。空闲时 Maggy 保持同一个姿势，只有星光通过终端闪烁属性闪动。再次点击 <b>idle</b> 可模拟下一次重绘。",
      "try.title": "定制你的 agy 状态栏",
      "try.desc": "这就是 <code>agy</code> 显示在提示符下方的状态栏。Maggy 待在模型、上下文用量、彩色配额条、工作区和 Git 分支左侧——每一帧都严格等宽，右侧信息纹丝不动。试试调整下面的选项，看看对应的命令。",
      "try.terminalAria": "带有 Maggy 的 agy 状态栏预览",
      "try.petName": "宠物名称",
      "try.theme": "主题",
      "try.moodCaption": "心情文案",
      "try.idleTwinkle": "待机微光",
      "try.note": "<code>auto</code> 会在 12 月 25 日自动换上圣诞装：圣诞帽、飘雪、拱门彩灯和一棵小圣诞树。待机微光借助终端自带的 blink 效果，哪怕 agy 暂停刷新，星光也会继续闪动。",
      "install.title": "为 Antigravity CLI 安装 Maggy",
      "install.desc": "<code>maggy setup</code> 会把 <code>~/.gemini/antigravity-cli/settings.json</code> 中的 <code>statusLine</code> 指向 Maggy。其他配置不受影响，原文件会自动备份为 <code>settings.json.bak</code>。",
      "install.tabsAria": "安装方式",
      "install.brew.step1": "通过 Homebrew 安装",
      "install.brew.step2": "配置到 agy",
      "install.restart": "重启 agy，或在里面执行 <code>/statusline enable</code>。",
      "install.brew.note": "升级只需运行 <code>brew upgrade maggy</code>，并自带 bash、zsh 和 fish 的命令补全。",
      "install.curl.step1": "运行一键安装脚本：自动克隆到 <code>~/.maggy</code>、把 <code>maggy</code> 链接进 <code>~/.local/bin</code>，并完成 <code>maggy setup</code>。",
      "install.curl.note": "可通过 <code>| bash -s -- --theme xmas --no-mood</code> 传入初始化参数，后续用 <code>maggy update</code> 更新。",
      "install.git.step1": "克隆仓库",
      "install.git.step2": "配置到 agy",
      "commands.title": "CLI 命令",
      "commands.desc": "所有操作都收在一个命令里。运行 <code>maggy help</code> 查看完整列表。",
      "commands.status": "查看 Maggy 是否已接入、当前主题与配置，并打印一条预览。",
      "commands.preview": "无需发起对话，直接在终端预览任意 <code>agent_state</code> 动画。",
      "commands.disable": "暂时隐藏状态栏但不删除配置，用 <code>statusline on</code> 即可恢复。",
      "commands.pet": "只保留指标、隐藏宠物图标。<code>motion off</code> 改为静态姿势，<code>side right</code> 移到右侧；以上均支持 <code>toggle</code>。",
      "commands.hide": "隐藏不需要的模块：<code>model</code>、<code>context</code>、<code>quota</code>、<code>workspace</code>、<code>git</code>、<code>effort</code>。用 <code>maggy statusline show</code> 恢复。",
      "commands.doctor": "检测 Python 环境、真彩色支持、配置文件以及单帧渲染耗时。",
      "commands.config": "查看 <code>~/.config/maggy/config.json</code>，支持通过 <code>get</code>、<code>set</code> 或 <code>reset</code> 修改。",
      "commands.uninstall": "移除 statusLine 配置项、配置文件与缓存，其余 agy 设置保持原样。",
      "footer.madeFor": "为 <a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a> 状态栏而生，与 Google 无官方关联。",
      "footer.source": "GitHub 源码",
      "copy.idle": "复制",
      "copy.copied": "已复制",
      "copy.fallback": "请手动复制",
    },

    ja: {
      "meta.title": "Maggy — Antigravity CLI (agy) 向けターミナルペット＆ステータスライン",
      "meta.description": "Antigravity CLI (agy) 向けのアニメーション付きターミナルペット＆カスタムステータスライン。使用中のモデル、コンテキストやクォータ残量バー、Git ブランチの横で Maggy が踊ります。",
      "meta.ogDescription": "Antigravity CLI (agy) 向けのアニメーション付きターミナルペット＆カスタムステータスライン。使用中のモデル、コンテキスト＆クォータ残量バー、推論レベル、Git ブランチのすぐ隣で踊るマスコット。",
      "a11y.skip": "コンテンツへスキップ",
      "a11y.home": "Maggy ホーム",
      "a11y.nav": "メインナビゲーション",
      "a11y.lang": "言語を選択",
      "nav.try": "試してみる",
      "nav.install": "インストール",
      "nav.commands": "コマンド",
      "nav.github": "GitHub",
      "hero.title": "<span class=\"nowrap\">agy ステータスライン</span>に暮らす Maggy。",
      "hero.lede": "<strong>Antigravity CLI（<code>agy</code>）</strong>向けのアニメーション付きターミナルペット＆カスタムステータスライン。<code>agy</code> が動いている間は楽しそうに踊り、ツール実行中は元気よく足踏みし、席を外すとうとうと居眠りします。使用中のモデル、コンテキスト使用率、クォータ残量バー、推論レベル、Git ブランチのすぐ隣でいつも一緒です。",
      "hero.hint": "macOS / Linux・Python 3・Truecolor 対応ターミナルが必要です。<a href=\"#install\">その他のインストール方法</a>",
      "hero.spriteAria": "踊っている目の付いた Antigravity ロゴのペット、Maggy",
      "states.done": "idle · 完了直後",
      "states.sleep": "idle · 2 分経過",
      "states.note": "agy はステータスラインを状態が変わったときだけ再描画し、タイマーでは更新しません。アイドル中の Maggy は同じポーズのままで、ターミナルの点滅属性によりきらめきだけが瞬きます。<b>idle</b> をもう一度クリックすると次の再描画を再現できます。",
      "try.title": "agy ステータスラインをカスタマイズ",
      "try.desc": "プロンプトの下に <code>agy</code> が表示するステータスラインです。モデル、コンテキスト使用率、色分けされたクォータバー、ワークスペース、Git ブランチの左側に Maggy が並びます。全フレーム同じ幅なので、横の表示がガタつくことはありません。下の設定を変えると、対応するコマンドがリアルタイムで確認できます。",
      "try.terminalAria": "Maggy 付き agy ステータスラインのプレビュー",
      "try.petName": "ペットの名前",
      "try.theme": "テーマ",
      "try.moodCaption": "ひとこと表示",
      "try.idleTwinkle": "待機時のきらめき",
      "try.note": "<code>auto</code> は 12 月 25 日になると自動でクリスマス仕様に衣替えします（サンタ帽、降る雪、アーチの電飾、小さなツリー）。待機時のきらめきはターミナルの点滅属性を使っているため、agy の再描画が止まっても星がきらめき続けます。",
      "install.title": "Antigravity CLI に Maggy をインストール",
      "install.desc": "<code>maggy setup</code> は <code>~/.gemini/antigravity-cli/settings.json</code> の <code>statusLine</code> に Maggy を設定します。他の設定には触れず、元のファイルは <code>settings.json.bak</code> としてバックアップされます。",
      "install.tabsAria": "インストール方法",
      "install.brew.step1": "Homebrew でインストール",
      "install.brew.step2": "agy に組み込む",
      "install.restart": "agy を再起動するか、セッション内で <code>/statusline enable</code> を実行してください。",
      "install.brew.note": "<code>brew upgrade maggy</code> でアップデートできます。bash・zsh・fish のシェル補完も同梱されています。",
      "install.curl.step1": "インストーラーを実行します。<code>~/.maggy</code> にクローンし、<code>~/.local/bin</code> に <code>maggy</code> をリンクして <code>maggy setup</code> まで自動で行います。",
      "install.curl.note": "<code>| bash -s -- --theme xmas --no-mood</code> のように初期オプションを渡せます。更新は <code>maggy update</code> で行えます。",
      "install.git.step1": "リポジトリをクローン",
      "install.git.step2": "agy に組み込む",
      "commands.title": "CLI コマンド",
      "commands.desc": "操作はすべて 1 つのコマンドで完結します。全一覧は <code>maggy help</code> を実行してください。",
      "commands.status": "Maggy の設定状況やテーマを確認し、プレビューサンプルを表示します。",
      "commands.preview": "エージェントを実行せずに、好きな <code>agent_state</code> の動きをターミナルで再生します。",
      "commands.disable": "設定を残したままステータスラインを一時非表示にします。<code>statusline on</code> で復帰できます。",
      "commands.pet": "ロゴを隠してメトリクスだけ表示します。<code>motion off</code> で静止ポーズに、<code>side right</code> で右側配置に切り替え可能。いずれも <code>toggle</code> に対応しています。",
      "commands.hide": "表示項目を絞り込みます（<code>model</code> / <code>context</code> / <code>quota</code> / <code>workspace</code> / <code>git</code> / <code>effort</code>）。<code>maggy statusline show</code> で戻せます。",
      "commands.doctor": "Python、Truecolor 対応、設定ファイル、および 1 フレームあたりの描画速度を診断します。",
      "commands.config": "<code>~/.config/maggy/config.json</code> を表示します。<code>get</code>・<code>set</code>・<code>reset</code> で編集できます。",
      "commands.uninstall": "statusLine の設定・コンフィグ・キャッシュをきれいに削除します。他の agy 設定には触れません。",
      "footer.madeFor": "<a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a> ステータスラインのために作りました。Google とは無関係です。",
      "footer.source": "GitHub でソースを見る",
      "copy.idle": "コピー",
      "copy.copied": "コピー済み",
      "copy.fallback": "選択してコピー",
    },

    ko: {
      "meta.title": "Maggy — Antigravity CLI (agy)용 터미널 펫 & 상태바",
      "meta.description": "Antigravity CLI (agy)를 위한 애니메이션 터미널 펫과 커스텀 상태바. 현재 모델, 컨텍스트 및 할당량 바, Git 브랜치 옆에서 춤추는 Maggy를 만나보세요.",
      "meta.ogDescription": "Antigravity CLI (agy)용 애니메이션 터미널 펫 & 커스텀 상태바 — 현재 모델, 컨텍스트 및 할당량 바, 추론 강도, Git 브랜치 옆에서 함께하는 마스코트.",
      "a11y.skip": "본문으로 건너뛰기",
      "a11y.home": "Maggy 홈",
      "a11y.nav": "주요 메뉴",
      "a11y.lang": "언어 선택",
      "nav.try": "체험하기",
      "nav.install": "설치",
      "nav.commands": "명령어",
      "nav.github": "GitHub",
      "hero.title": "내 <span class=\"nowrap\">agy 상태바</span>에 사는 Maggy.",
      "hero.lede": "<strong>Antigravity CLI(<code>agy</code>)</strong>용 애니메이션 터미널 펫이자 커스텀 상태바입니다. <code>agy</code>가 일할 땐 신나게 춤추고, 도구를 호출할 땐 발을 동동 구르며, 자리를 비우면 꾸벅꾸벅 좁니다. 현재 모델, 컨텍스트 창, 할당량 바, 추론 강도, Git 브랜치 바로 옆에서 함께해요.",
      "hero.hint": "macOS 또는 Linux, Python 3, 트루컬러 터미널이 필요합니다. <a href=\"#install\">다른 설치 방법</a>",
      "hero.spriteAria": "눈이 달린 Antigravity 로고 펫 Maggy가 춤추는 모습",
      "states.done": "idle · 방금 완료",
      "states.sleep": "idle · 2분 경과",
      "states.note": "agy는 상태가 바뀔 때만 상태 표시줄을 다시 그리며 타이머로 갱신하지 않습니다. 유휴 중 Maggy는 한 자세를 유지하고, 터미널 깜박임 속성으로 반짝이만 깜박입니다. <b>idle</b>을 다시 클릭하면 다음 다시 그리기를 시뮬레이션합니다.",
      "try.title": "agy 상태바 커스터마이즈",
      "try.desc": "프롬프트 아래에 <code>agy</code>가 띄워 주는 상태바입니다. 모델, 컨텍스트 사용량, 색상별 할당량 바, 워크스페이스, Git 브랜치 왼쪽에 Maggy가 자리하며 모든 프레임의 너비가 같아 옆 글자가 흔들리지 않습니다. 아래 옵션을 바꿔 보며 해당하는 명령어를 바로 확인해 보세요.",
      "try.terminalAria": "Maggy가 포함된 agy 상태바 미리보기",
      "try.petName": "펫 이름",
      "try.theme": "테마",
      "try.moodCaption": "상태 문구",
      "try.idleTwinkle": "대기 중 반짝임",
      "try.note": "<code>auto</code>는 12월 25일이 되면 알아서 크리스마스 옷으로 갈아입습니다. 산타 모자, 내리는 눈, 아치 전구, 작은 트리까지 함께해요. 대기 중 반짝임은 터미널의 blink 속성을 쓰기 때문에 agy가 화면을 다시 그리지 않아도 별빛이 계속 반짝입니다.",
      "install.title": "Antigravity CLI에 Maggy 설치하기",
      "install.desc": "<code>maggy setup</code>은 <code>~/.gemini/antigravity-cli/settings.json</code>의 <code>statusLine</code>을 Maggy로 연결합니다. 다른 설정은 건드리지 않으며 기존 파일은 <code>settings.json.bak</code>으로 백업됩니다.",
      "install.tabsAria": "설치 방법",
      "install.brew.step1": "Homebrew로 설치",
      "install.brew.step2": "agy에 연결",
      "install.restart": "agy를 다시 시작하거나 안에서 <code>/statusline enable</code>을 실행하세요.",
      "install.brew.note": "<code>brew upgrade maggy</code>로 간편하게 업그레이드할 수 있습니다. bash, zsh, fish 셸 자동 완성도 함께 설치됩니다.",
      "install.curl.step1": "설치 스크립트를 실행하면 <code>~/.maggy</code>에 클론하고 <code>~/.local/bin</code>에 <code>maggy</code>를 연결한 뒤 <code>maggy setup</code>까지 자동으로 마칩니다.",
      "install.curl.note": "<code>| bash -s -- --theme xmas --no-mood</code>처럼 초기 옵션을 넘길 수 있고, 업데이트는 <code>maggy update</code>로 하면 됩니다.",
      "install.git.step1": "저장소 클론",
      "install.git.step2": "agy에 연결",
      "commands.title": "CLI 명령어",
      "commands.desc": "모든 기능을 하나의 명령어로 제어합니다. 전체 목록은 <code>maggy help</code>로 확인하세요.",
      "commands.status": "Maggy 연결 상태와 현재 테마, 설정값 그리고 미리보기 샘플을 보여줍니다.",
      "commands.preview": "에이전트를 돌리지 않고도 원하는 <code>agent_state</code> 애니메이션을 터미널에서 바로 재생합니다.",
      "commands.disable": "설정을 지우지 않고 상태바만 잠시 숨깁니다. <code>statusline on</code>로 다시 켤 수 있어요.",
      "commands.pet": "로고는 숨기고 지표만 남깁니다. <code>motion off</code>로 움직임을 멈추고, <code>side right</code>로 오른쪽으로 옮길 수 있어요. 모두 <code>toggle</code>을 지원합니다.",
      "commands.hide": "원하는 항목만 골라 숨깁니다: <code>model</code>, <code>context</code>, <code>quota</code>, <code>workspace</code>, <code>git</code>, <code>effort</code>. <code>maggy statusline show</code>로 다시 띄울 수 있어요.",
      "commands.doctor": "Python, 트루컬러 지원, 설정 파일 상태 및 프레임 렌더링 속도를 점검합니다.",
      "commands.config": "<code>~/.config/maggy/config.json</code>을 보여줍니다. <code>get</code>, <code>set</code>, <code>reset</code>으로 바꿀 수 있어요.",
      "commands.uninstall": "statusLine 항목과 설정 파일, 캐시를 깔끔하게 지웁니다. 다른 agy 설정은 그대로 유지됩니다.",
      "footer.madeFor": "<a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a> 상태바를 위해 만들었습니다. Google과는 무관합니다.",
      "footer.source": "GitHub 소스 코드",
      "copy.idle": "복사",
      "copy.copied": "복사됨",
      "copy.fallback": "선택 후 복사",
    },

    es: {
      "meta.title": "Maggy — Mascota de terminal y barra de estado para Antigravity CLI (agy)",
      "meta.description": "Mascota animada de terminal y barra de estado a medida para Antigravity CLI (agy). Mira a Maggy bailar junto a tu modelo activo, barras de contexto y cuota, y rama de git.",
      "meta.ogDescription": "Mascota animada de terminal y barra de estado a medida para Antigravity CLI (agy): una mascota bailarina junto a tu modelo activo, barras de contexto y cuota, nivel de razonamiento y rama de git.",
      "a11y.skip": "Saltar al contenido",
      "a11y.home": "Inicio de Maggy",
      "a11y.nav": "Navegación principal",
      "a11y.lang": "Idioma",
      "nav.try": "Pruébalo",
      "nav.install": "Instalar",
      "nav.commands": "Comandos",
      "nav.github": "GitHub",
      "hero.title": "Maggy vive en tu <span class=\"nowrap\">statusline de agy.</span>",
      "hero.lede": "Una mascota animada para tu terminal y barra de estado a medida para <strong>Antigravity CLI (<code>agy</code>)</strong>. Maggy baila mientras <code>agy</code> trabaja, zapatea con cada llamada a herramientas y se echa una siesta cuando te alejas, justo al lado de tu modelo activo, ventana de contexto, barras de cuota, nivel de razonamiento y rama de git.",
      "hero.hint": "macOS o Linux, Python 3 y una terminal truecolor. <a href=\"#install\">Otras formas de instalar</a>",
      "hero.spriteAria": "Maggy, el logotipo de Antigravity con ojos, bailando",
      "states.done": "idle · recién listo",
      "states.sleep": "idle · 2 min",
      "states.note": "agy solo redibuja la statusline cuando algo cambia, nunca con un temporizador. En reposo Maggy mantiene una pose y solo sus destellos parpadean (con el atributo de parpadeo de la terminal). Pulsa <b>idle</b> otra vez para simular el siguiente redibujado.",
      "try.title": "Personaliza tu statusline de agy",
      "try.desc": "Así se ve la barra de estado que <code>agy</code> dibuja bajo tu prompt. Maggy va a la izquierda del modelo, el uso de contexto, las barras de cuota con colores, el workspace y la rama de git: todos los fotogramas miden exactamente lo mismo, así que nada a su lado salta ni se mueve. Prueba los controles de abajo para ver el comando exacto.",
      "try.terminalAria": "Vista previa de la barra de estado de agy con Maggy",
      "try.petName": "Nombre de la mascota",
      "try.theme": "Tema",
      "try.moodCaption": "Frase de estado",
      "try.idleTwinkle": "Destellos en reposo",
      "try.note": "<code>auto</code> se viste de Navidad por su cuenta el 25 de diciembre: gorro de Papá Noel, nieve cayendo, luces en el arco y un arbolito. Los destellos en reposo usan el atributo de parpadeo de la terminal, así que las chispas siguen brillando aunque agy deje de redibujar.",
      "install.title": "Instala Maggy para Antigravity CLI",
      "install.desc": "<code>maggy setup</code> apunta <code>statusLine</code> en <code>~/.gemini/antigravity-cli/settings.json</code> hacia Maggy. El resto de tus ajustes queda intacto y el archivo anterior se guarda como <code>settings.json.bak</code>.",
      "install.tabsAria": "Método de instalación",
      "install.brew.step1": "Instala el paquete con Homebrew",
      "install.brew.step2": "Conecta Maggy con agy",
      "install.restart": "Reinicia agy o ejecuta <code>/statusline enable</code> dentro de él.",
      "install.brew.note": "Actualiza con <code>brew upgrade maggy</code>. Incluye autocompletado para bash, zsh y fish.",
      "install.curl.step1": "Ejecuta el instalador: clona el repositorio en <code>~/.maggy</code>, enlaza <code>maggy</code> en <code>~/.local/bin</code> y ejecuta <code>maggy setup</code>.",
      "install.curl.note": "Puedes pasar opciones con <code>| bash -s -- --theme xmas --no-mood</code> y actualizar más adelante con <code>maggy update</code>.",
      "install.git.step1": "Clona el repositorio",
      "install.git.step2": "Conecta Maggy con agy",
      "commands.title": "Comandos CLI",
      "commands.desc": "Todo pasa por un único comando. Ejecuta <code>maggy help</code> para ver la lista completa.",
      "commands.status": "Comprueba si Maggy está conectada, muestra tu tema y ajustes, y enseña una vista previa.",
      "commands.preview": "Reproduce cualquier <code>agent_state</code> en tu terminal sin lanzar ninguna consulta al agente.",
      "commands.disable": "Oculta la barra de estado sin borrar la configuración. <code>statusline on</code> la devuelve.",
      "commands.pet": "Oculta el logotipo y deja solo las métricas. <code>motion off</code> la mantiene quieta y <code>side right</code> la pasa a la derecha. Todos admiten <code>toggle</code>.",
      "commands.hide": "Oculta los bloques que quieras: <code>model</code>, <code>context</code>, <code>quota</code>, <code>workspace</code>, <code>git</code>, <code>effort</code>. Con <code>maggy statusline show</code> vuelven a aparecer.",
      "commands.doctor": "Comprueba Python, el soporte truecolor, el archivo de configuración y la velocidad de renderizado.",
      "commands.config": "Muestra <code>~/.config/maggy/config.json</code>. Usa <code>get</code>, <code>set</code> o <code>reset</code> para editarlo.",
      "commands.uninstall": "Elimina la entrada statusLine, la configuración y la caché sin tocar tus demás ajustes de agy.",
      "footer.madeFor": "Hecho para las barras de estado de <a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a>. Sin afiliación con Google.",
      "footer.source": "Código en GitHub",
      "copy.idle": "Copiar",
      "copy.copied": "Copiado",
      "copy.fallback": "Selecciona y copia",
    },

    fr: {
      "meta.title": "Maggy — Mascotte de terminal & barre d'état pour Antigravity CLI (agy)",
      "meta.description": "Mascotte animée de terminal et barre d'état sur mesure pour Antigravity CLI (agy). Regardez Maggy danser à côté du modèle actif, des barres de contexte et de quota, et de votre branche git.",
      "meta.ogDescription": "Mascotte animée de terminal et barre d'état sur mesure pour Antigravity CLI (agy) — une mascotte dansante à côté du modèle actif, des barres de contexte et de quota, du niveau de raisonnement et de votre branche git.",
      "a11y.skip": "Aller au contenu",
      "a11y.home": "Accueil Maggy",
      "a11y.nav": "Navigation principale",
      "a11y.lang": "Langue",
      "nav.try": "Essayer",
      "nav.install": "Installer",
      "nav.commands": "Commandes",
      "nav.github": "GitHub",
      "hero.title": "Maggy s'installe dans votre <span class=\"nowrap\">statusline agy.</span>",
      "hero.lede": "Une mascotte animée de terminal et barre d'état sur mesure pour <strong>Antigravity CLI (<code>agy</code>)</strong>. Maggy danse pendant qu'<code>agy</code> réfléchit, trépigne lors des appels d'outils et pique du nez quand vous vous absentez — juste à côté du modèle actif, de la fenêtre de contexte, des barres de quota, du niveau de raisonnement et de votre branche git.",
      "hero.hint": "macOS ou Linux, Python 3, un terminal truecolor. <a href=\"#install\">Autres méthodes d'installation</a>",
      "hero.spriteAria": "Maggy, le logo Antigravity doté d'yeux, en train de danser",
      "states.done": "idle · terminé",
      "states.sleep": "idle · 2 min",
      "states.note": "agy ne redessine la statusline que lorsque quelque chose change, jamais sur minuterie. Au repos, Maggy garde une seule pose et seules ses étincelles scintillent (via l'attribut de clignotement du terminal). Cliquez à nouveau sur <b>idle</b> pour simuler le prochain rafraîchissement.",
      "try.title": "Personnalisez votre statusline agy",
      "try.desc": "Voici la barre d'état qu'<code>agy</code> affiche sous votre invite. Maggy se tient à gauche du modèle, de l'usage du contexte, des barres de quota colorées, de l'espace de travail et de la branche git : chaque image fait exactement la même largeur, rien ne bouge autour d'elle. Modifiez une option ci-dessous pour voir la commande correspondante.",
      "try.terminalAria": "Aperçu de la barre d'état agy avec Maggy",
      "try.petName": "Nom de la mascotte",
      "try.theme": "Thème",
      "try.moodCaption": "Message d'humeur",
      "try.idleTwinkle": "Scintillement au repos",
      "try.note": "<code>auto</code> enfile tout seul sa tenue de Noël le 25 décembre : bonnet de Père Noël, flocons qui tombent, guirlande sur l'arche et petit sapin. Le scintillement au repos s'appuie sur l'attribut blink du terminal : les étincelles continuent même quand agy ne rafraîchit plus l'écran.",
      "install.title": "Installer Maggy pour Antigravity CLI",
      "install.desc": "<code>maggy setup</code> fait pointer <code>statusLine</code> dans <code>~/.gemini/antigravity-cli/settings.json</code> vers Maggy. Vos autres réglages restent intacts et l'ancien fichier est sauvegardé sous <code>settings.json.bak</code>.",
      "install.tabsAria": "Méthode d'installation",
      "install.brew.step1": "Installer via Homebrew",
      "install.brew.step2": "Connecter Maggy à agy",
      "install.restart": "Redémarrez agy, ou lancez <code>/statusline enable</code> directement dedans.",
      "install.brew.note": "Mettez à jour avec <code>brew upgrade maggy</code>. Les complétions pour bash, zsh et fish sont incluses.",
      "install.curl.step1": "Lancez l'installeur : il clone le dépôt dans <code>~/.maggy</code>, crée le lien <code>maggy</code> dans <code>~/.local/bin</code> et exécute <code>maggy setup</code>.",
      "install.curl.note": "Passez des options via <code>| bash -s -- --theme xmas --no-mood</code>, puis mettez à jour avec <code>maggy update</code>.",
      "install.git.step1": "Cloner le dépôt",
      "install.git.step2": "Connecter Maggy à agy",
      "commands.title": "Commandes CLI",
      "commands.desc": "Tout passe par une seule commande. Lancez <code>maggy help</code> pour la liste complète.",
      "commands.status": "Affiche si Maggy est bien branchée, votre thème, vos réglages et un aperçu en direct.",
      "commands.preview": "Joue n'importe quel <code>agent_state</code> dans votre terminal sans lancer de requête agent.",
      "commands.disable": "Masque la barre d'état sans la supprimer. <code>statusline on</code> la réactive.",
      "commands.pet": "Masque le logo tout en gardant les métriques. <code>motion off</code> fige la pose et <code>side right</code> la place à droite. Chaque option accepte <code>toggle</code>.",
      "commands.hide": "Masque les segments de votre choix : <code>model</code>, <code>context</code>, <code>quota</code>, <code>workspace</code>, <code>git</code>, <code>effort</code>. <code>maggy statusline show</code> les réaffiche.",
      "commands.doctor": "Vérifie Python, le support truecolor, le fichier de réglages et le temps de rendu d'une image.",
      "commands.config": "Affiche <code>~/.config/maggy/config.json</code>. Utilisez <code>get</code>, <code>set</code> ou <code>reset</code> pour le modifier.",
      "commands.uninstall": "Supprime l'entrée statusLine, la configuration et le cache sans toucher à vos autres réglages agy.",
      "footer.madeFor": "Conçu pour les barres d'état d'<a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a>. Non affilié à Google.",
      "footer.source": "Code source sur GitHub",
      "copy.idle": "Copier",
      "copy.copied": "Copié",
      "copy.fallback": "Sélectionner et copier",
    },

    de: {
      "meta.title": "Maggy — Terminal-Maskottchen & Statuszeile für Antigravity CLI (agy)",
      "meta.description": "Animiertes Terminal-Maskottchen und eigene Statuszeile für Antigravity CLI (agy). Sieh Maggy neben aktivem Modell, Kontext- und Kontingentbalken sowie Git-Branch tanzen.",
      "meta.ogDescription": "Animiertes Terminal-Maskottchen und eigene Statuszeile für Antigravity CLI (agy) – ein tanzendes Maskottchen neben aktivem Modell, Kontext- und Kontingentbalken, Reasoning-Stufe und Git-Branch.",
      "a11y.skip": "Zum Inhalt springen",
      "a11y.home": "Maggy Startseite",
      "a11y.nav": "Hauptnavigation",
      "a11y.lang": "Sprache",
      "nav.try": "Ausprobieren",
      "nav.install": "Installieren",
      "nav.commands": "Befehle",
      "nav.github": "GitHub",
      "hero.title": "Maggy zieht in deine <span class=\"nowrap\">agy-Statuszeile</span> ein.",
      "hero.lede": "Ein animiertes Terminal-Maskottchen und eine eigene Statuszeile für <strong>Antigravity CLI (<code>agy</code>)</strong>. Maggy tanzt, während <code>agy</code> arbeitet, stampft bei Tool-Aufrufen und nickt ein, wenn du kurz weg bist – direkt neben aktivem Modell, Kontextfenster, Kontingentbalken, Reasoning-Stufe und Git-Branch.",
      "hero.hint": "macOS oder Linux, Python 3, ein Truecolor-Terminal. <a href=\"#install\">Weitere Installationswege</a>",
      "hero.spriteAria": "Maggy, das tanzende Antigravity-Logo mit Augen",
      "states.done": "idle · gerade fertig",
      "states.sleep": "idle · 2 Min.",
      "states.note": "agy zeichnet die Statuszeile nur neu, wenn sich etwas ändert, nie per Timer. Im Leerlauf hält Maggy eine Pose und nur ihre Funkel blinken (über das Blink-Attribut des Terminals). Klicke erneut auf <b>idle</b>, um das nächste Neuzeichnen zu simulieren.",
      "try.title": "Passe deine agy-Statuszeile an",
      "try.desc": "So sieht die Statuszeile aus, die <code>agy</code> unter deinem Prompt anzeigt. Maggy sitzt links neben Modell, Kontextverbrauch, farbigen Kontingentbalken, Workspace und Git-Branch – jedes Frame ist exakt gleich breit, sodass nichts daneben verrutscht. Probier unten eine Einstellung aus, um direkt den passenden Befehl zu sehen.",
      "try.terminalAria": "Vorschau der agy-Statuszeile mit Maggy",
      "try.petName": "Name des Maskottchens",
      "try.theme": "Theme",
      "try.moodCaption": "Stimmungszeile",
      "try.idleTwinkle": "Ruhe-Funkeln",
      "try.note": "<code>auto</code> schaltet am 25. Dezember ganz von allein auf den Weihnachts-Look um: Weihnachtsmütze, Schneefall, Lichterkette am Bogen und ein kleiner Baum. Das Ruhe-Funkeln nutzt das Blink-Attribut des Terminals, sodass die Funken weiterleuchten, selbst wenn agy nicht mehr neu zeichnet.",
      "install.title": "Maggy für Antigravity CLI installieren",
      "install.desc": "<code>maggy setup</code> verweist <code>statusLine</code> in <code>~/.gemini/antigravity-cli/settings.json</code> auf Maggy. Alle anderen Einstellungen bleiben unverändert, und die alte Datei wird als <code>settings.json.bak</code> gesichert.",
      "install.tabsAria": "Installationsmethode",
      "install.brew.step1": "Mit Homebrew installieren",
      "install.brew.step2": "Maggy mit agy verbinden",
      "install.restart": "Starte agy neu oder führe darin <code>/statusline enable</code> aus.",
      "install.brew.note": "Aktualisieren mit <code>brew upgrade maggy</code>. Shell-Vervollständigungen für bash, zsh und fish sind enthalten.",
      "install.curl.step1": "Starte das Installationsskript: Es klont nach <code>~/.maggy</code>, verlinkt <code>maggy</code> nach <code>~/.local/bin</code> und führt <code>maggy setup</code> aus.",
      "install.curl.note": "Optionen übergibst du per <code>| bash -s -- --theme xmas --no-mood</code>; spätere Updates laufen über <code>maggy update</code>.",
      "install.git.step1": "Repository klonen",
      "install.git.step2": "Maggy mit agy verbinden",
      "commands.title": "CLI-Befehle",
      "commands.desc": "Alles läuft über einen einzigen Befehl. Führe <code>maggy help</code> für die vollständige Liste aus.",
      "commands.status": "Zeigt, ob Maggy eingebunden ist, dein Theme, deine Einstellungen und eine Vorschau.",
      "commands.preview": "Spielt beliebige <code>agent_state</code>-Zustände direkt im Terminal ab, ohne einen Agenten-Lauf zu starten.",
      "commands.disable": "Blendet die Statuszeile aus, ohne sie zu entfernen. <code>statusline on</code> holt sie zurück.",
      "commands.pet": "Blendet das Logo aus und behält die Metriken. <code>motion off</code> hält stattdessen eine feste Pose und <code>side right</code> schiebt sie nach rechts. Alles unterstützt <code>toggle</code>.",
      "commands.hide": "Blendet einzelne Segmente aus: <code>model</code>, <code>context</code>, <code>quota</code>, <code>workspace</code>, <code>git</code>, <code>effort</code>. <code>maggy statusline show</code> blendet sie wieder ein.",
      "commands.doctor": "Prüft Python, Truecolor-Unterstützung, die Einstellungsdatei und die Renderzeit pro Frame.",
      "commands.config": "Zeigt <code>~/.config/maggy/config.json</code>. Mit <code>get</code>, <code>set</code> oder <code>reset</code> anpassen.",
      "commands.uninstall": "Entfernt den statusLine-Eintrag samt Konfiguration und Cache. Alle anderen agy-Einstellungen bleiben unberührt.",
      "footer.madeFor": "Gemacht für <a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a>-Statuszeilen. Nicht mit Google verbunden.",
      "footer.source": "Quellcode auf GitHub",
      "copy.idle": "Kopieren",
      "copy.copied": "Kopiert",
      "copy.fallback": "Markieren & kopieren",
    },

    pt: {
      "meta.title": "Maggy — Mascote de terminal e barra de status para Antigravity CLI (agy)",
      "meta.description": "Mascote animado de terminal e barra de status sob medida para a Antigravity CLI (agy). Veja Maggy dançar ao lado do modelo atual, barras de contexto e cota, e branch do git.",
      "meta.ogDescription": "Mascote animado de terminal e barra de status sob medida para a Antigravity CLI (agy) — um mascote dançante ao lado do modelo atual, barras de contexto e cota, nível de raciocínio e branch do git.",
      "a11y.skip": "Ir para o conteúdo",
      "a11y.home": "Início do Maggy",
      "a11y.nav": "Navegação principal",
      "a11y.lang": "Idioma",
      "nav.try": "Experimentar",
      "nav.install": "Instalar",
      "nav.commands": "Comandos",
      "nav.github": "GitHub",
      "hero.title": "Maggy mora na sua <span class=\"nowrap\">statusline do agy.</span>",
      "hero.lede": "Um mascote animado de terminal e barra de status sob medida para a <strong>Antigravity CLI (<code>agy</code>)</strong>. Maggy dança enquanto o <code>agy</code> trabalha, sapateia nas chamadas de ferramentas e tira um cochilo quando você se afasta — bem ao lado do modelo atual, janela de contexto, barras de cota, nível de raciocínio e branch do git.",
      "hero.hint": "macOS ou Linux, Python 3 e um terminal truecolor. <a href=\"#install\">Outras formas de instalar</a>",
      "hero.spriteAria": "Maggy, o logotipo da Antigravity com olhos, dançando",
      "states.done": "idle · recém-concluído",
      "states.sleep": "idle · 2 min",
      "states.note": "O agy só redesenha a statusline quando algo muda, nunca por temporizador. Em repouso a Maggy mantém uma pose e só os brilhos piscam (pelo atributo de piscar do terminal). Clique em <b>idle</b> de novo para simular o próximo redesenho.",
      "try.title": "Personalize sua statusline do agy",
      "try.desc": "Esta é a barra de status que o <code>agy</code> desenha abaixo do seu prompt. Maggy fica à esquerda do modelo, uso de contexto, barras de cota coloridas, workspace e branch do git — todos os quadros têm exatamente a mesma largura, então nada ao lado dela sai do lugar. Teste uma opção abaixo para ver o comando correspondente.",
      "try.terminalAria": "Prévia da barra de status do agy com Maggy",
      "try.petName": "Nome do mascote",
      "try.theme": "Tema",
      "try.moodCaption": "Legenda de humor",
      "try.idleTwinkle": "Brilho ocioso",
      "try.note": "<code>auto</code> entra sozinho no clima de Natal em 25 de dezembro: gorro de Papai Noel, neve caindo, pisca-pisca no arco e uma árvore pequenininha. O brilho ocioso usa o atributo blink do terminal, mantendo as faíscas acesas mesmo quando o agy para de redesenhar.",
      "install.title": "Instale o Maggy para Antigravity CLI",
      "install.desc": "<code>maggy setup</code> aponta <code>statusLine</code> em <code>~/.gemini/antigravity-cli/settings.json</code> para o Maggy. Suas outras configurações permanecem intactas e o arquivo antigo é salvo como <code>settings.json.bak</code>.",
      "install.tabsAria": "Método de instalação",
      "install.brew.step1": "Instale via Homebrew",
      "install.brew.step2": "Conecte o Maggy ao agy",
      "install.restart": "Reinicie o agy ou execute <code>/statusline enable</code> dentro dele.",
      "install.brew.note": "Atualize com <code>brew upgrade maggy</code>. Inclui autocompletar para bash, zsh e fish.",
      "install.curl.step1": "Execute o instalador: ele clona para <code>~/.maggy</code>, cria o link de <code>maggy</code> em <code>~/.local/bin</code> e roda o <code>maggy setup</code>.",
      "install.curl.note": "Passe opções com <code>| bash -s -- --theme xmas --no-mood</code> e atualize depois com <code>maggy update</code>.",
      "install.git.step1": "Clone o repositório",
      "install.git.step2": "Conecte o Maggy ao agy",
      "commands.title": "Comandos CLI",
      "commands.desc": "Tudo passa por um único comando. Execute <code>maggy help</code> para ver a lista completa.",
      "commands.status": "Mostra se o Maggy está conectado, seu tema, suas configurações e uma prévia ao vivo.",
      "commands.preview": "Reproduz qualquer <code>agent_state</code> no terminal sem precisar iniciar uma rodada do agente.",
      "commands.disable": "Oculta a barra de status sem removê-la. <code>statusline on</code> a traz de volta.",
      "commands.pet": "Oculta o logotipo mantendo as métricas. <code>motion off</code> mantém uma pose estática e <code>side right</code> a move para a direita. Cada um aceita <code>toggle</code>.",
      "commands.hide": "Oculta os segmentos que quiser: <code>model</code>, <code>context</code>, <code>quota</code>, <code>workspace</code>, <code>git</code>, <code>effort</code>. <code>maggy statusline show</code> restaura.",
      "commands.doctor": "Verifica Python, suporte a truecolor, o arquivo de configuração e o tempo de renderização de um quadro.",
      "commands.config": "Mostra <code>~/.config/maggy/config.json</code>. Use <code>get</code>, <code>set</code> ou <code>reset</code> para alterar.",
      "commands.uninstall": "Remove a entrada statusLine, a configuração e o cache. Suas outras configurações do agy ficam intactas.",
      "footer.madeFor": "Feito para barras de status da <a href=\"https://antigravity.google/docs/cli/statusline\">Antigravity CLI</a>. Sem afiliação com o Google.",
      "footer.source": "Código-fonte no GitHub",
      "copy.idle": "Copiar",
      "copy.copied": "Copiado",
      "copy.fallback": "Selecionar e copiar",
    },
  };

  function resolveLocale(raw) {
    if (!raw) return null;
    const norm = String(raw).trim().toLowerCase().replace(/_/g, "-");
    for (const loc of LOCALES) {
      if (loc.code.toLowerCase() === norm) return loc.code;
    }
    const base = norm.split("-")[0];
    if (base === "zh") return "zh-CN";
    for (const loc of LOCALES) {
      if (loc.code.toLowerCase().split("-")[0] === base) return loc.code;
    }
    return null;
  }

  function detectLocale() {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = resolveLocale(params.get("lang"));
    if (fromUrl) return fromUrl;

    try {
      const stored = resolveLocale(localStorage.getItem(STORAGE_KEY));
      if (stored) return stored;
    } catch {
      // Ignore storage access errors (e.g. private browsing restrictions).
    }

    const browserLangs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language];
    for (const lang of browserLangs) {
      const matched = resolveLocale(lang);
      if (matched) return matched;
    }
    return DEFAULT_LOCALE;
  }

  let currentLocale = DEFAULT_LOCALE;

  function t(key) {
    const dict = MESSAGES[currentLocale] || MESSAGES[DEFAULT_LOCALE];
    if (Object.prototype.hasOwnProperty.call(dict, key)) return dict[key];
    return MESSAGES[DEFAULT_LOCALE][key] || key;
  }

  function setMeta(selector, value) {
    const el = document.querySelector(selector);
    if (el && value) el.setAttribute("content", value);
  }

  function applyLocale(locale, opts = {}) {
    currentLocale = resolveLocale(locale) || DEFAULT_LOCALE;
    const meta = LOCALES.find((l) => l.code === currentLocale) || LOCALES[0];

    document.documentElement.lang = currentLocale;
    document.title = t("meta.title");
    setMeta('meta[name="description"]', t("meta.description"));
    setMeta('meta[property="og:title"]', t("meta.title"));
    setMeta('meta[property="og:description"]', t("meta.ogDescription"));
    setMeta('meta[property="og:locale"]', meta.ogLocale);
    setMeta('meta[name="twitter:title"]', t("meta.title"));
    setMeta('meta[name="twitter:description"]', t("meta.description"));

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      el.innerHTML = t(el.dataset.i18nHtml);
    });
    document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      el.dataset.i18nAttr.split(",").forEach((pair) => {
        const idx = pair.indexOf(":");
        if (idx === -1) return;
        const attr = pair.slice(0, idx).trim();
        const key = pair.slice(idx + 1).trim();
        if (attr && key) el.setAttribute(attr, t(key));
      });
    });

    const picker = document.getElementById("lang-select");
    if (picker && picker.value !== currentLocale) {
      picker.value = currentLocale;
    }

    if (opts.persist) {
      try {
        localStorage.setItem(STORAGE_KEY, currentLocale);
      } catch {
        // Ignore storage errors.
      }
    }

    if (opts.syncUrl && window.history && window.history.replaceState) {
      const url = new URL(window.location.href);
      if (currentLocale === DEFAULT_LOCALE) {
        url.searchParams.delete("lang");
      } else {
        url.searchParams.set("lang", currentLocale);
      }
      window.history.replaceState(null, "", url.toString());
    }
  }

  function init() {
    const picker = document.getElementById("lang-select");
    if (picker) {
      picker.innerHTML = LOCALES.map(
        (loc) => `<option value="${loc.code}">${loc.label}</option>`
      ).join("");
      picker.addEventListener("change", () => {
        applyLocale(picker.value, { persist: true, syncUrl: true });
      });
    }
    applyLocale(detectLocale());
  }

  window.MaggyI18n = {
    LOCALES,
    MESSAGES,
    t,
    getLocale: () => currentLocale,
    setLocale: (code) => applyLocale(code, { persist: true, syncUrl: true }),
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
