# -*- coding: utf-8 -*-
"""Web assets (HTML, CSS, JavaScript, PWA Manifest, Service Worker) for the JuiceVault Mobile Remote."""

HTML_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>JuiceVault Remote</title>
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="JuiceVault">
  <meta name="theme-color" content="#0d0b14">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" href="https://api.juicevault.xyz/favicon.ico">
  <style>
    :root {
      --bg: #0a0910;
      --card-bg: rgba(22, 18, 35, 0.75);
      --card-border: rgba(168, 85, 247, 0.18);
      --accent: #a855f7;
      --accent-glow: rgba(168, 85, 247, 0.4);
      --accent-hover: #c084fc;
      --text: #f3e8ff;
      --text-muted: #a89bb8;
      --danger: #ef4444;
      --success: #22c55e;
      --safe-top: env(safe-area-inset-top, 0px);
      --safe-bottom: env(safe-area-inset-bottom, 0px);
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      min-height: 100vh;
      min-height: -webkit-fill-available;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      padding-top: var(--safe-top);
      padding-bottom: calc(65px + var(--safe-bottom));
      position: relative;
    }
    /* Dynamic ambient glow behind cover */
    .ambient-bg {
      position: fixed;
      top: -20%;
      left: -20%;
      width: 140%;
      height: 140%;
      background: radial-gradient(circle at 50% 30%, rgba(147, 51, 234, 0.22) 0%, rgba(10, 9, 16, 0.95) 70%);
      filter: blur(60px);
      z-index: -1;
      pointer-events: none;
      transition: background 0.8s ease;
    }
    /* Top Bar */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 20px;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(10, 9, 16, 0.85);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-badge {
      font-size: 20px;
      line-height: 1;
      filter: drop-shadow(0 0 8px var(--accent));
    }
    .brand-title {
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      background: linear-gradient(135deg, #f3e8ff, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .header-status {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .badge {
      font-size: 0.72rem;
      padding: 4px 10px;
      border-radius: 20px;
      font-weight: 600;
      letter-spacing: 0.3px;
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid var(--card-border);
      color: #e9d5ff;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .badge-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
    }
    .badge-dot.offline {
      background: var(--danger);
      box-shadow: 0 0 8px var(--danger);
    }
    /* Main Content */
    main {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 16px 20px;
      max-width: 540px;
      width: 100%;
      margin: 0 auto;
    }
    .tab-content {
      display: none;
      flex-direction: column;
      gap: 18px;
      animation: fadeIn 0.25s ease-out;
    }
    .tab-content.active {
      display: flex;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    /* Player Card */
    .artwork-container {
      position: relative;
      width: 100%;
      max-width: 320px;
      aspect-ratio: 1;
      margin: 10px auto 16px;
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6), 0 0 24px var(--accent-glow);
      border: 1px solid rgba(168, 85, 247, 0.25);
      background: #14121d;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .artwork-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.5s ease;
    }
    .artwork-img.playing {
      transform: scale(1.02);
    }
    .artwork-placeholder {
      font-size: 5rem;
      opacity: 0.6;
    }
    .track-meta {
      text-align: center;
      margin-bottom: 8px;
    }
    .track-title {
      font-size: 1.35rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 4px;
      line-height: 1.25;
      text-overflow: ellipsis;
      overflow: hidden;
      white-space: nowrap;
    }
    .track-artist {
      font-size: 0.95rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .track-pills {
      display: flex;
      justify-content: center;
      gap: 8px;
      margin-top: 10px;
      flex-wrap: wrap;
    }
    /* Scrubber */
    .scrubber-container {
      margin: 8px 0 16px;
    }
    .progress-bar-wrap {
      height: 8px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      overflow: hidden;
      position: relative;
      cursor: pointer;
      touch-action: none;
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, #9333ea, #c084fc);
      width: 0%;
      border-radius: 6px;
      transition: width 0.2s linear;
      box-shadow: 0 0 10px var(--accent);
    }
    .time-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 6px;
      font-variant-numeric: tabular-nums;
    }
    /* Controls */
    .controls-primary {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin-bottom: 12px;
    }
    .btn-circle {
      border: none;
      outline: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: #fff;
      border-radius: 50%;
    }
    .btn-circle:active {
      transform: scale(0.92);
    }
    .btn-large {
      width: 68px;
      height: 68px;
      font-size: 1.8rem;
      background: linear-gradient(135deg, #a855f7, #7e22ce);
      box-shadow: 0 8px 24px var(--accent-glow);
      border: none;
    }
    .btn-medium {
      width: 48px;
      height: 48px;
      font-size: 1.25rem;
    }
    .btn-small {
      width: 38px;
      height: 38px;
      font-size: 0.95rem;
      color: var(--text-muted);
    }
    .btn-small.active {
      color: var(--accent-hover);
      border-color: var(--accent);
      background: rgba(168, 85, 247, 0.2);
    }
    .controls-secondary {
      display: flex;
      align-items: center;
      justify-content: space-around;
      padding: 10px 14px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }
    .btn-ghost {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.8rem;
      font-weight: 600;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      cursor: pointer;
      padding: 6px 12px;
      border-radius: 10px;
      transition: all 0.15s ease;
    }
    .btn-ghost span.icon {
      font-size: 1.2rem;
    }
    .btn-ghost.active {
      color: var(--accent-hover);
    }
    .btn-ghost:active {
      transform: scale(0.92);
    }
    /* Bottom Navigation */
    nav.bottom-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      width: 100%;
      height: calc(60px + var(--safe-bottom));
      padding-bottom: var(--safe-bottom);
      background: rgba(10, 9, 16, 0.92);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-top: 1px solid var(--card-border);
      display: flex;
      justify-content: space-around;
      align-items: center;
      z-index: 100;
    }
    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      font-size: 0.7rem;
      color: var(--text-muted);
      background: none;
      border: none;
      cursor: pointer;
      padding: 8px 14px;
      transition: color 0.15s ease;
      font-weight: 500;
    }
    .nav-item .icon {
      font-size: 1.3rem;
    }
    .nav-item.active {
      color: var(--accent-hover);
      font-weight: 700;
    }
    /* Cards & Lists */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 16px;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }
    .card-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .track-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 480px;
      overflow-y: auto;
    }
    .track-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      gap: 10px;
    }
    .track-info {
      flex: 1;
      min-width: 0;
    }
    .track-info-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .track-info-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .btn-action-small {
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid var(--accent);
      color: var(--text);
      font-size: 0.75rem;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: background 0.15s;
    }
    .btn-action-small:active {
      transform: scale(0.95);
    }
    /* Search Bar */
    .search-box {
      display: flex;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 8px 14px;
      gap: 8px;
    }
    .search-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 0.95rem;
    }
    .search-input::placeholder {
      color: var(--text-muted);
    }
    .search-modes {
      display: flex;
      gap: 8px;
      margin-top: 10px;
    }
    .mode-pill {
      flex: 1;
      text-align: center;
      padding: 8px 12px;
      border-radius: 12px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
    }
    .mode-pill.active {
      background: rgba(168, 85, 247, 0.25);
      color: #fff;
      border-color: var(--accent);
    }
    /* Category Grid */
    .cat-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }
    .cat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 14px;
      cursor: pointer;
      transition: transform 0.15s, border-color 0.15s;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .cat-card:active {
      transform: scale(0.96);
    }
    .cat-card.active {
      border-color: var(--accent);
      background: rgba(168, 85, 247, 0.18);
      box-shadow: 0 0 14px var(--accent-glow);
    }
    .cat-card-title {
      font-size: 0.9rem;
      font-weight: 700;
      color: #fff;
    }
    .cat-card-count {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    /* Modal / Bottom Sheet */
    .sheet-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(6px);
      z-index: 200;
      display: none;
      align-items: flex-end;
      animation: fadeIn 0.2s;
    }
    .sheet-overlay.active {
      display: flex;
    }
    .sheet {
      width: 100%;
      background: #141122;
      border-top-left-radius: 24px;
      border-top-right-radius: 24px;
      border-top: 1px solid var(--card-border);
      padding: 20px;
      padding-bottom: calc(24px + var(--safe-bottom));
      max-height: 80vh;
      overflow-y: auto;
      animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes slideUp {
      from { transform: translateY(100%); }
      to { transform: translateY(0); }
    }
    .sheet-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .sheet-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: #fff;
    }
    .sheet-close {
      background: none;
      border: none;
      font-size: 1.4rem;
      color: var(--text-muted);
      cursor: pointer;
    }
    .sheet-options {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .sheet-option-item {
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.04);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .sheet-option-item.active {
      border-color: var(--accent);
      background: rgba(168, 85, 247, 0.2);
    }
    /* Toast */
    .toast {
      position: fixed;
      top: calc(14px + var(--safe-top));
      left: 50%;
      transform: translateX(-50%) translateY(-100px);
      background: rgba(30, 24, 48, 0.95);
      border: 1px solid var(--accent);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
      padding: 10px 18px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      color: #fff;
      z-index: 300;
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .toast.show {
      transform: translateX(-50%) translateY(0);
    }
    /* Lockscreen helper banner */
    .lockscreen-banner {
      background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(126, 34, 206, 0.15));
      border: 1px dashed var(--accent);
      border-radius: 14px;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 4px;
    }
    .lockscreen-text {
      font-size: 0.78rem;
      color: #e9d5ff;
      line-height: 1.35;
    }
    .btn-pill {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 6px 12px;
      border-radius: 14px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
    }
  </style>
</head>
<body>
  <div class="ambient-bg" id="ambientBg"></div>

  <!-- Header -->
  <header>
    <div class="brand">
      <div class="logo-badge">🧃</div>
      <div class="brand-title">JuiceVault Remote</div>
    </div>
    <div class="header-status">
      <div class="badge" id="voiceBadge">🔊 VC: --</div>
      <div class="badge"><span class="badge-dot" id="connDot"></span> <span id="connLabel">Live</span></div>
    </div>
  </header>

  <div class="toast" id="toast">✅ Action applied</div>

  <main>
    <!-- TAB 1: NOW PLAYING -->
    <div class="tab-content active" id="tab-player">
      <div class="artwork-container" id="artContainer">
        <img src="https://api.juicevault.xyz/favicon.ico" class="artwork-img" id="coverImg" alt="Album Cover">
      </div>

      <div class="track-meta">
        <div class="track-title" id="trackTitle">Connecting to JuiceVault…</div>
        <div class="track-artist" id="trackArtist">Please wait</div>
        <div class="track-pills">
          <span class="badge" id="categoryBadge">🎚️ Category: All</span>
          <span class="badge" id="sourceBadge">🎵 Archive</span>
          <span class="badge" id="eqBadge">🎚️ Flat</span>
        </div>
      </div>

      <div class="scrubber-container">
        <div class="progress-bar-wrap" id="progressBar">
          <div class="progress-bar-fill" id="progressFill"></div>
        </div>
        <div class="time-labels">
          <span id="timeElapsed">0:00</span>
          <span id="timeDuration">0:00</span>
        </div>
      </div>

      <div class="controls-primary">
        <button class="btn-circle btn-small" id="btnRepeat" title="Repeat" onclick="action('repeat')">🔁</button>
        <button class="btn-circle btn-medium" id="btnPrev" title="Previous" onclick="action('previous')">⏮</button>
        <button class="btn-circle btn-small" title="Rewind 10s" onclick="action('seek', {delta: -10})">⏪10</button>
        <button class="btn-circle btn-large" id="btnPlayPause" title="Play/Pause" onclick="action('toggle')">▶</button>
        <button class="btn-circle btn-small" title="Forward 10s" onclick="action('seek', {delta: 10})">10⏩</button>
        <button class="btn-circle btn-medium" id="btnNext" title="Next" onclick="action('skip')">⏭</button>
        <button class="btn-circle btn-small" id="btnShuffle" title="Shuffle" onclick="action('shuffle')">🔀</button>
      </div>

      <div class="controls-secondary">
        <button class="btn-ghost" onclick="openEqModal()"><span class="icon">🎚️</span>EQ Preset</button>
        <button class="btn-ghost" onclick="action('stop')"><span class="icon">⏹️</span>Stop</button>
        <button class="btn-ghost" id="lyricsBtn" onclick="openLyrics()"><span class="icon">🎶</span>Lyrics</button>
      </div>

      <div class="lockscreen-banner" id="lockscreenBanner">
        <div class="lockscreen-text">
          <strong>📱 Lock Screen Controls:</strong> Enable background audio so your phone's lock screen & control center can control playback.
        </div>
        <button class="btn-pill" onclick="enableLockScreen()">Enable</button>
      </div>
    </div>

    <!-- TAB 2: QUEUE -->
    <div class="tab-content" id="tab-queue">
      <div class="card">
        <div class="card-title">
          <span>📥 Requested (<span id="reqCount">0</span>)</span>
        </div>
        <div class="track-list" id="reqList">
          <div class="track-item" style="color: var(--text-muted); font-size: 0.8rem;">No requested tracks. Use Search to queue some!</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <span>🎶 Upcoming Archive (<span id="queueCount">0</span>)</span>
          <button class="btn-action-small" onclick="action('shuffle')">🔀 Shuffle</button>
        </div>
        <div class="track-list" id="upcomingList">
          <div class="track-item" style="color: var(--text-muted); font-size: 0.8rem;">Loading queue…</div>
        </div>
      </div>
    </div>

    <!-- TAB 3: SEARCH -->
    <div class="tab-content" id="tab-search">
      <div class="search-box">
        <span style="font-size: 1.1rem;">🔎</span>
        <input type="text" class="search-input" id="searchInput" placeholder="Search track or artist…" onkeydown="if(event.key==='Enter') executeSearch()">
        <button class="btn-action-small" onclick="executeSearch()">Search</button>
      </div>

      <div class="search-modes">
        <div class="mode-pill active" id="modeVault" onclick="setSearchMode('vault')">🎵 JuiceVault Archive</div>
        <div class="mode-pill" id="modeExternal" onclick="setSearchMode('external')">🌐 Online (YouTube/SoundCloud)</div>
      </div>

      <div class="card" style="margin-top: 10px;">
        <div class="card-title">Search Results</div>
        <div class="track-list" id="searchResults">
          <div class="track-item" style="color: var(--text-muted); font-size: 0.8rem;">Type a query and press Search.</div>
        </div>
      </div>
    </div>

    <!-- TAB 4: CATEGORIES -->
    <div class="tab-content" id="tab-categories">
      <div class="card">
        <div class="card-title">🎚️ Collections & Categories</div>
        <div class="cat-grid" id="catGrid">
          <div class="cat-card" onclick="changeCategory('all')"><div class="cat-card-title">All Music</div><div class="cat-card-count">Loading…</div></div>
        </div>
      </div>
    </div>

    <!-- TAB 5: SHORTCUTS & API -->
    <div class="tab-content" id="tab-shortcuts">
      <div class="card">
        <div class="card-title">📱 iOS Shortcuts & Siri Integration</div>
        <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 12px;">
          You can control JuiceVault with Siri, phone back-tap, or home screen widgets using Apple Shortcuts! Create a shortcut with the action <strong>"Get Contents of URL"</strong> using any of these URLs:
        </p>
        <div class="track-list" id="shortcutUrls"></div>
      </div>

      <div class="card">
        <div class="card-title">⚙️ Connection Details</div>
        <div style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.6;">
          <div><strong>Bot Guild:</strong> <span id="guildName">--</span></div>
          <div><strong>Voice Channel:</strong> <span id="vcName">--</span></div>
          <div><strong>Auth Token:</strong> <code id="tokenDisplay" style="color: var(--accent-hover);">--</code></div>
        </div>
      </div>
    </div>
  </main>

  <!-- Bottom Navigation Bar -->
  <nav class="bottom-nav">
    <button class="nav-item active" onclick="switchTab('player')"><span class="icon">🎵</span><span>Player</span></button>
    <button class="nav-item" onclick="switchTab('queue')"><span class="icon">📑</span><span>Queue</span></button>
    <button class="nav-item" onclick="switchTab('search')"><span class="icon">🔍</span><span>Search</span></button>
    <button class="nav-item" onclick="switchTab('categories')"><span class="icon">🎚️</span><span>Library</span></button>
    <button class="nav-item" onclick="switchTab('shortcuts')"><span class="icon">⚡</span><span>Shortcuts</span></button>
  </nav>

  <!-- EQ Preset Bottom Sheet -->
  <div class="sheet-overlay" id="eqSheet" onclick="if(event.target===this) closeEqModal()">
    <div class="sheet">
      <div class="sheet-header">
        <div class="sheet-title">🎚️ Audio EQ & Effects</div>
        <button class="sheet-close" onclick="closeEqModal()">✕</button>
      </div>
      <div class="sheet-options" id="eqOptions"></div>
    </div>
  </div>

  <audio id="silentAudio" loop playsinline preload="auto" style="display:none;"></audio>

  <script>
    // State management
    const urlParams = new URLSearchParams(window.location.search);
    let token = urlParams.get('token') || localStorage.getItem('jv_token') || '';
    if (token) localStorage.setItem('jv_token', token);

    let currentState = null;
    let ws = null;
    let progressTimer = null;
    let currentElapsed = 0;
    let durationSeconds = 0;
    let searchMode = 'vault';
    let lockScreenActive = false;

    // Toast helper
    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2400);
      if (navigator.vibrate) navigator.vibrate(15);
    }

    // Tab switcher
    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
      const target = document.getElementById('tab-' + tabId);
      if (target) target.classList.add('active');
      const idx = ['player', 'queue', 'search', 'categories', 'shortcuts'].indexOf(tabId);
      if (idx !== -1) document.querySelectorAll('.nav-item')[idx].classList.add('active');
      if (tabId === 'queue') loadQueue();
      if (tabId === 'categories') loadCategories();
      if (tabId === 'shortcuts') renderShortcuts();
      if (navigator.vibrate) navigator.vibrate(10);
    }

    // Time format
    function formatTime(sec) {
      if (isNaN(sec) || sec < 0) return '0:00';
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // Scrubber click/touch
    const progressBar = document.getElementById('progressBar');
    progressBar.addEventListener('click', (e) => {
      if (!durationSeconds || durationSeconds <= 0) return;
      const rect = progressBar.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const ratio = Math.max(0, Math.min(1, clickX / rect.width));
      const target = ratio * durationSeconds;
      action('seek_to', { position: target });
      currentElapsed = target;
      updateScrubberUI();
    });

    // Send action to API or WebSocket
    async function action(name, payload = {}) {
      if (navigator.vibrate) navigator.vibrate(12);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: name, ...payload }));
        return;
      }
      try {
        const res = await fetch(`/api/playback/${name}?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.message) showToast(data.message);
      } catch (e) {
        console.error('Action failed:', e);
      }
    }

    // Setup silent audio for Lock Screen MediaSession
    function enableLockScreen() {
      const audio = document.getElementById('silentAudio');
      // 1-second silent WAV base64
      audio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
      audio.play().then(() => {
        lockScreenActive = true;
        document.getElementById('lockscreenBanner').style.display = 'none';
        showToast('📱 Lock screen controls activated!');
        setupMediaSession();
        updateMediaSession();
      }).catch(err => {
        console.log('Audio playback error:', err);
      });
    }

    function setupMediaSession() {
      if (!('mediaSession' in navigator)) return;
      navigator.mediaSession.setActionHandler('play', () => { action('play'); if (silentAudio) silentAudio.play(); });
      navigator.mediaSession.setActionHandler('pause', () => { action('pause'); });
      navigator.mediaSession.setActionHandler('previoustrack', () => { action('previous'); });
      navigator.mediaSession.setActionHandler('nexttrack', () => { action('skip'); });
      navigator.mediaSession.setActionHandler('seekbackward', () => { action('seek', { delta: -10 }); });
      navigator.mediaSession.setActionHandler('seekforward', () => { action('seek', { delta: 10 }); });
    }

    function updateMediaSession() {
      if (!('mediaSession' in navigator) || !currentState || !currentState.track) return;
      const t = currentState.track;
      navigator.mediaSession.metadata = new MediaMetadata({
        title: t.title || 'Juice WRLD Track',
        artist: t.artist || 'Juice WRLD',
        album: 'JuiceVault • ' + (t.category || 'Archive'),
        artwork: [{ src: t.cover_url || 'https://api.juicevault.xyz/favicon.ico', sizes: '512x512', type: 'image/png' }]
      });
      navigator.mediaSession.playbackState = currentState.is_playing ? 'playing' : 'paused';
    }

    // Apply UI state update
    function applyState(state) {
      currentState = state;
      document.getElementById('connDot').classList.remove('offline');
      document.getElementById('connLabel').innerText = 'Live';

      if (state.guild) {
        document.getElementById('guildName').innerText = state.guild.name || state.guild.id;
      }
      if (state.voice_channel) {
        document.getElementById('voiceBadge').innerText = '🔊 ' + state.voice_channel;
        document.getElementById('vcName').innerText = state.voice_channel;
      } else {
        document.getElementById('voiceBadge').innerText = '🔊 Disconnected';
      }

      document.getElementById('tokenDisplay').innerText = token || '(none)';

      const t = state.track;
      if (t) {
        document.getElementById('trackTitle').innerText = t.title || 'Untitled Track';
        document.getElementById('trackArtist').innerText = t.artist || 'Juice WRLD';
        document.getElementById('coverImg').src = t.cover_url || 'https://api.juicevault.xyz/favicon.ico';
        document.getElementById('categoryBadge').innerText = '🎚️ ' + (state.category_label || state.category || 'All');
        document.getElementById('sourceBadge').innerText = t.is_external ? '🌐 ' + (t.source || 'External') : '🎵 JuiceVault';
        document.getElementById('eqBadge').innerText = '🎚️ ' + (state.effect || 'Flat').toUpperCase();

        durationSeconds = t.duration_seconds || 0;
        currentElapsed = t.position_seconds || 0;
        document.getElementById('timeDuration').innerText = t.length || formatTime(durationSeconds);
        updateScrubberUI();
      } else {
        document.getElementById('trackTitle').innerText = state.is_running ? 'Loading next track…' : 'Player Offline';
        document.getElementById('trackArtist').innerText = state.is_running ? 'Buffering archive' : 'Tap Play to start';
      }

      // Buttons
      const playBtn = document.getElementById('btnPlayPause');
      if (state.is_playing) {
        playBtn.innerText = '⏸';
        document.getElementById('coverImg').classList.add('playing');
      } else {
        playBtn.innerText = '▶';
        document.getElementById('coverImg').classList.remove('playing');
      }

      const repeatBtn = document.getElementById('btnRepeat');
      if (state.repeat) repeatBtn.classList.add('active');
      else repeatBtn.classList.remove('active');

      document.getElementById('reqCount').innerText = state.requested_size || 0;
      document.getElementById('queueCount').innerText = state.queue_size || 0;

      updateMediaSession();
    }

    function updateScrubberUI() {
      document.getElementById('timeElapsed').innerText = formatTime(currentElapsed);
      if (durationSeconds > 0) {
        const pct = Math.min(100, Math.max(0, (currentElapsed / durationSeconds) * 100));
        document.getElementById('progressFill').style.width = pct + '%';
      } else {
        document.getElementById('progressFill').style.width = '0%';
      }
    }

    // Local tick for smooth scrubber
    clearInterval(progressTimer);
    progressTimer = setInterval(() => {
      if (currentState && currentState.is_playing && durationSeconds > 0) {
        currentElapsed += 1;
        if (currentElapsed > durationSeconds) currentElapsed = durationSeconds;
        updateScrubberUI();
      }
    }, 1000);

    // WebSocket connection
    function connectWS() {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${proto}//${window.location.host}/ws?token=${encodeURIComponent(token)}`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        document.getElementById('connDot').classList.remove('offline');
        document.getElementById('connLabel').innerText = 'Live';
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'state_update') {
            applyState(msg.data);
          } else if (msg.type === 'toast') {
            showToast(msg.message);
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        document.getElementById('connDot').classList.add('offline');
        document.getElementById('connLabel').innerText = 'Reconnecting…';
        setTimeout(connectWS, 2500);
      };

      ws.onerror = () => ws.close();
    }

    // Fallback polling for status
    async function fetchStatus() {
      try {
        const res = await fetch(`/api/status?token=${encodeURIComponent(token)}`);
        if (res.ok) {
          const data = await res.json();
          if (data.state) applyState(data.state);
        }
      } catch (e) {
        console.error('Fetch status error:', e);
      }
    }

    // Load queue list
    async function loadQueue() {
      try {
        const res = await fetch(`/api/queue?token=${encodeURIComponent(token)}`);
        const data = await res.json();
        const reqList = document.getElementById('reqList');
        if (data.requested && data.requested.length > 0) {
          reqList.innerHTML = data.requested.map((t, idx) => `
            <div class="track-item">
              <div class="track-info">
                <div class="track-info-title">${t.title || 'Untitled'}</div>
                <div class="track-info-sub">${t.artist || 'Juice WRLD'} • ${t.length || '—'}</div>
              </div>
              <button class="btn-action-small" onclick="removeQueueItem(${idx})">✕</button>
            </div>
          `).join('');
        } else {
          reqList.innerHTML = '<div class="track-item" style="color: var(--text-muted); font-size: 0.8rem;">No requested tracks.</div>';
        }

        const upList = document.getElementById('upcomingList');
        if (data.upcoming && data.upcoming.length > 0) {
          upList.innerHTML = data.upcoming.slice(0, 30).map((t, idx) => `
            <div class="track-item">
              <div class="track-info">
                <div class="track-info-title">${idx + 1}. ${t.title || 'Untitled'}</div>
                <div class="track-info-sub">${t.artist || 'Juice WRLD'} • ${t.length || '—'}</div>
              </div>
            </div>
          `).join('');
        }
      } catch (e) {
        console.error('Queue load error:', e);
      }
    }

    async function removeQueueItem(index) {
      await fetch(`/api/queue/remove?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index })
      });
      showToast('Removed from Requested');
      loadQueue();
    }

    // Search
    function setSearchMode(mode) {
      searchMode = mode;
      document.getElementById('modeVault').classList.toggle('active', mode === 'vault');
      document.getElementById('modeExternal').classList.toggle('active', mode === 'external');
    }

    async function executeSearch() {
      const q = document.getElementById('searchInput').value.trim();
      if (!q) return;
      const resContainer = document.getElementById('searchResults');
      resContainer.innerHTML = '<div class="track-item" style="color: var(--text-muted); font-size: 0.8rem;">Searching…</div>';
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&source=${searchMode}&token=${encodeURIComponent(token)}`);
        const data = await res.json();
        if (data.results && data.results.length > 0) {
          resContainer.innerHTML = data.results.map((item) => `
            <div class="track-item">
              <div class="track-info">
                <div class="track-info-title">${item.title || 'Untitled'}</div>
                <div class="track-info-sub">${item.artist || 'Juice WRLD'} • ${item.length || '—'}</div>
              </div>
              <button class="btn-action-small" onclick='addToQueue(${JSON.stringify(item).replace(/'/g, "&#39;")})'>+ Add</button>
            </div>
          `).join('');
        } else {
          resContainer.innerHTML = '<div class="track-item" style="color: var(--text-muted); font-size: 0.8rem;">No results found.</div>';
        }
      } catch (e) {
        resContainer.innerHTML = `<div class="track-item" style="color: var(--danger); font-size: 0.8rem;">Search failed: ${e.message}</div>`;
      }
    }

    async function addToQueue(item) {
      try {
        const res = await fetch(`/api/queue/add?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ track: item })
        });
        const d = await res.json();
        showToast(d.message || 'Added to Requested queue!');
      } catch (e) {
        showToast('Failed to queue: ' + e.message);
      }
    }

    // Categories
    async function loadCategories() {
      if (!currentState || !currentState.categories) return;
      const grid = document.getElementById('catGrid');
      const cats = currentState.categories;
      const active = currentState.category || 'all';
      grid.innerHTML = Object.entries(cats).map(([name, count]) => `
        <div class="cat-card ${name.toLowerCase() === active.toLowerCase() ? 'active' : ''}" onclick="changeCategory('${name}')">
          <div class="cat-card-title">${name.toUpperCase()}</div>
          <div class="cat-card-count">${count} tracks</div>
        </div>
      `).join('');
    }

    async function changeCategory(category) {
      await fetch(`/api/category?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category })
      });
      showToast(`Category changed to ${category}`);
      setTimeout(loadCategories, 500);
    }

    // EQ Modal
    function openEqModal() {
      if (!currentState || !currentState.effects) return;
      const container = document.getElementById('eqOptions');
      container.innerHTML = currentState.effects.map(eq => `
        <div class="sheet-option-item ${currentState.effect === eq.id ? 'active' : ''}" onclick="setEq('${eq.id}')">
          <div>
            <strong>${eq.label}</strong>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 2px;">${eq.desc}</div>
          </div>
          ${currentState.effect === eq.id ? '<span>✓</span>' : ''}
        </div>
      `).join('');
      document.getElementById('eqSheet').classList.add('active');
    }

    function closeEqModal() {
      document.getElementById('eqSheet').classList.remove('active');
    }

    async function setEq(effect) {
      closeEqModal();
      await fetch(`/api/playback/eq?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ effect })
      });
      showToast(`EQ applied: ${effect}`);
    }

    function openLyrics() {
      if (!currentState || !currentState.track) return;
      const t = currentState.track;
      const q = encodeURIComponent(`${t.artist || ''} ${t.title || ''}`.trim());
      window.open(`https://genius.com/search?q=${q}`, '_blank');
    }

    // Shortcuts helper render
    function renderShortcuts() {
      const base = `${window.location.origin}/api/playback`;
      const tParam = token ? `?token=${encodeURIComponent(token)}` : '';
      const shortcuts = [
        { name: 'Toggle Play/Pause', url: `${base}/toggle${tParam}` },
        { name: 'Next Track (Skip)', url: `${base}/skip${tParam}` },
        { name: 'Previous Track', url: `${base}/previous${tParam}` },
        { name: 'Skip 10s Forward', url: `${base}/seek${tParam}${tParam ? '&' : '?'}delta=10` },
        { name: 'Stop Playback', url: `${base}/stop${tParam}` },
        { name: 'Shuffle Queue', url: `${base}/shuffle${tParam}` },
      ];
      const container = document.getElementById('shortcutUrls');
      container.innerHTML = shortcuts.map(s => `
        <div class="track-item" style="flex-direction: column; align-items: flex-start; gap: 4px;">
          <div style="font-size: 0.82rem; font-weight: 700; color: #fff;">${s.name}</div>
          <code style="font-size: 0.72rem; color: var(--accent-hover); word-break: break-all;">${s.url}</code>
          <button class="btn-action-small" style="align-self: flex-end; margin-top: 2px;" onclick="copyShortcut('${s.url}')">📋 Copy URL</button>
        </div>
      `).join('');
    }

    function copyShortcut(url) {
      navigator.clipboard.writeText(url).then(() => showToast('Copied shortcut URL to clipboard!'));
    }

    // Startup
    connectWS();
    fetchStatus();
  </script>
</body>
</html>
"""

MANIFEST_JSON = """{
  "name": "JuiceVault Remote",
  "short_name": "JuiceVault",
  "start_url": "/?pwa=1",
  "display": "standalone",
  "background_color": "#0a0910",
  "theme_color": "#9b59b6",
  "icons": [
    {
      "src": "https://api.juicevault.xyz/favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ]
}
"""

SERVICE_WORKER_JS = """// Service Worker for JuiceVault Remote PWA
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Let network handle dynamic API & WS requests
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
"""
