# -*- coding: utf-8 -*-
"""Web assets (HTML, CSS, JavaScript, PWA Manifest, Service Worker) for the JuiceVault Web Remote.

Inspired by Kinetics (kinetics.colorion.co) and OriginKit (originkit.dev):
- Zero emojis: pure custom SVG iconography throughout.
- Kinetic spring physics micro-interactions and tactile feedback.
- Dark zinc/obsidian surfaces with refined neon-violet highlights.
- Dual responsive layout: desktop multi-column dashboard and mobile thumb-optimized PWA.
- Full HTTP and HTTPS / WSS auto-negotiation.
"""

HTML_INDEX = """<!DOCTYPE html>
<html lang="en" style="background-color: #09090d; color-scheme: dark;">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>JuiceVault — Web Remote</title>
  <meta name="color-scheme" content="dark">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="JuiceVault">
  <meta name="theme-color" content="#09090d">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" href="https://api.juicevault.xyz/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #09090d;
      --surface: #111116;
      --surface-elevated: #16161d;
      --surface-card: rgba(18, 18, 24, 0.78);
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(168, 85, 247, 0.35);
      --border-focus: #a855f7;
      --accent: #a855f7;
      --accent-glow: rgba(168, 85, 247, 0.4);
      --accent-muted: rgba(168, 85, 247, 0.15);
      --text: #f4f4f5;
      --text-muted: #a1a1aa;
      --text-sub: #71717a;
      --success: #10b981;
      --danger: #ef4444;
      --safe-top: env(safe-area-inset-top, 0px);
      --safe-bottom: env(safe-area-inset-bottom, 0px);
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 18px;
      --radius-xl: 24px;
      --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
      --ease: cubic-bezier(0.16, 1, 0.3, 1);
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }
    html, body {
      background-color: var(--bg) !important;
      color: var(--text) !important;
      color-scheme: dark !important;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100%;
      min-height: 100dvh;
      overflow-x: hidden;
    }
    body {
      display: flex;
      flex-direction: column;
      padding-top: var(--safe-top);
      padding-bottom: calc(72px + var(--safe-bottom));
      position: relative;
    }
    /* Ambient radial glow backdrop (OriginKit / Kinetics style) */
    .backdrop-glow {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: radial-gradient(circle at 50% 8%, rgba(147, 51, 234, 0.18) 0%, rgba(9, 9, 13, 0.98) 70%);
      z-index: -1;
      pointer-events: none;
    }
    /* Icons styling */
    .icon-svg {
      width: 18px;
      height: 18px;
      stroke: currentColor;
      fill: none;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      flex-shrink: 0;
    }
    .icon-svg.fill-current {
      fill: currentColor;
    }
    /* Kinetics Kinetic Buttons */
    .btn-kinetic {
      transition: transform 0.22s var(--spring), background 0.15s ease, border-color 0.15s ease, box-shadow 0.2s ease;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font-family: inherit;
    }
    .btn-kinetic:active {
      transform: scale(0.92);
    }
    /* Header */
    header.app-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 20px;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(9, 9, 13, 0.85);
    }
    .header-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo-disc {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background: linear-gradient(135deg, #a855f7, #6b21a8);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 12px var(--accent-glow);
      color: #fff;
    }
    .brand-title {
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
    }
    .brand-tag {
      font-size: 0.68rem;
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
    }
    .header-meta {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 20px;
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text-muted);
    }
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
    }
    .status-dot.offline {
      background: var(--danger);
      box-shadow: 0 0 8px var(--danger);
    }
    /* Layout Container: Responsive Mobile -> Desktop */
    .app-container {
      max-width: 1040px;
      width: 100%;
      margin: 0 auto;
      padding: 20px;
      flex: 1;
    }
    @media (min-width: 860px) {
      body {
        padding-bottom: 24px;
      }
      .app-grid {
        display: grid;
        grid-template-columns: 360px 1fr;
        gap: 24px;
        align-items: start;
      }
      .desktop-segment {
        display: flex !important;
      }
      .mobile-nav {
        display: none !important;
      }
      .card-player-wrap {
        display: block !important;
        position: sticky;
        top: 80px;
      }
      .card-content-wrap {
        display: block !important;
      }
    }
    @media (max-width: 859px) {
      .desktop-segment {
        display: none !important;
      }
      .card-content-wrap {
        display: none;
      }
    }
    /* Tab Content Switcher */
    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
      animation: fadeIn 0.16s ease;
    }
    /* Cards */
    .ui-card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    /* Now Playing Display */
    .player-visual {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      max-width: 280px;
      margin: 0 auto 18px;
      border-radius: var(--radius-md);
      overflow: hidden;
      background: #14141a;
      border: 1px solid var(--border);
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.65), 0 0 28px rgba(168, 85, 247, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .player-cover {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.6s ease;
    }
    .player-cover.playing {
      transform: scale(1.02);
    }
    /* Kinetic Soundwave Indicator */
    .soundwave-box {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 14px;
    }
    .wave-bar {
      width: 3px;
      height: 4px;
      background: var(--accent);
      border-radius: 2px;
      transition: height 0.2s ease;
    }
    .playing .wave-bar:nth-child(1) { animation: soundwave 1.1s infinite ease-in-out; }
    .playing .wave-bar:nth-child(2) { animation: soundwave 0.8s infinite ease-in-out 0.2s; }
    .playing .wave-bar:nth-child(3) { animation: soundwave 1.3s infinite ease-in-out 0.4s; }
    .playing .wave-bar:nth-child(4) { animation: soundwave 0.9s infinite ease-in-out 0.1s; }
    @keyframes soundwave {
      0%, 100% { height: 4px; }
      50% { height: 14px; }
    }
    /* Track Info */
    .track-meta {
      text-align: center;
      margin-bottom: 16px;
    }
    .track-title-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-bottom: 4px;
    }
    .track-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      letter-spacing: -0.01em;
    }
    .track-artist {
      font-size: 0.88rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .pill-row {
      display: flex;
      justify-content: center;
      gap: 6px;
      margin-top: 10px;
      flex-wrap: wrap;
    }
    .pill-tag {
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 4px 8px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .pill-tag.accent {
      color: var(--accent);
      border-color: var(--border-accent);
      background: var(--accent-muted);
    }
    /* Scrubber */
    .scrubber-wrap {
      margin: 14px 0 20px;
    }
    .scrubber-track {
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 4px;
      position: relative;
      cursor: pointer;
      touch-action: none;
      transition: height 0.15s ease;
    }
    .scrubber-track:hover {
      height: 8px;
    }
    .scrubber-fill {
      height: 100%;
      background: linear-gradient(90deg, #9333ea, #c084fc);
      border-radius: 4px;
      width: 0%;
      box-shadow: 0 0 10px var(--accent);
      position: relative;
    }
    .scrubber-thumb {
      width: 12px;
      height: 12px;
      background: #fff;
      border-radius: 50%;
      position: absolute;
      right: -6px;
      top: 50%;
      transform: translateY(-50%);
      box-shadow: 0 0 8px rgba(0, 0, 0, 0.8);
      opacity: 0;
      transition: opacity 0.15s ease;
    }
    .scrubber-track:hover .scrubber-thumb {
      opacity: 1;
    }
    .scrubber-times {
      display: flex;
      justify-content: space-between;
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--text-sub);
      margin-top: 6px;
    }
    /* Main Control Row */
    .controls-main {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    .btn-circle {
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .btn-circle:hover {
      background: var(--surface-elevated);
      border-color: rgba(255, 255, 255, 0.15);
      color: #fff;
    }
    .btn-circle.active {
      color: var(--accent);
      border-color: var(--accent);
      background: var(--accent-muted);
    }
    .btn-play-pause {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #a855f7, #7e22ce);
      border: none;
      color: #fff;
      box-shadow: 0 6px 20px var(--accent-glow);
    }
    .btn-play-pause:hover {
      background: linear-gradient(135deg, #b56bfa, #8b28e0);
      box-shadow: 0 8px 24px var(--accent-glow);
    }
    .btn-action-md {
      width: 44px;
      height: 44px;
    }
    .btn-action-sm {
      width: 36px;
      height: 36px;
      color: var(--text-muted);
    }
    /* Secondary Bar */
    .controls-sub {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      border-top: 1px solid var(--border);
      padding-top: 14px;
    }
    .btn-flat {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 500;
      padding: 8px;
    }
    .btn-flat:hover {
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
    }
    /* Section Headers */
    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }
    .section-title {
      font-size: 0.92rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    /* Tab Segment Control (OriginKit Component) */
    .segment-bar {
      display: flex;
      background: #0d0d12;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 3px;
      gap: 4px;
      margin-bottom: 16px;
    }
    .segment-btn {
      flex: 1;
      padding: 7px 12px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 7px;
      cursor: pointer;
      transition: all 0.18s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .segment-btn.active {
      background: var(--surface-elevated);
      color: #fff;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border);
    }
    /* Track List */
    .track-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 480px;
      overflow-y: auto;
    }
    .track-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      transition: background 0.15s ease, border-color 0.15s ease;
      gap: 12px;
    }
    .track-card:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.12);
    }
    .track-meta-col {
      flex: 1;
      min-width: 0;
    }
    .track-name {
      font-size: 0.86rem;
      font-weight: 600;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .track-desc {
      font-size: 0.72rem;
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
      margin-top: 2px;
    }
    .btn-badge {
      background: var(--accent-muted);
      border: 1px solid var(--border-accent);
      color: var(--accent);
      font-size: 0.74rem;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 6px;
    }
    .btn-badge:hover {
      background: var(--accent);
      color: #fff;
    }
    /* Search Bar */
    .search-input-group {
      display: flex;
      align-items: center;
      background: #0d0d12;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 8px 14px;
      gap: 10px;
      margin-bottom: 12px;
      transition: border-color 0.2s;
    }
    .search-input-group:focus-within {
      border-color: var(--border-focus);
    }
    .search-field {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 0.9rem;
      font-family: inherit;
    }
    .search-field::placeholder {
      color: var(--text-sub);
    }
    /* Category Grid */
    .grid-categories {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 10px;
    }
    .cat-item {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 14px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .cat-item:hover {
      background: var(--surface-elevated);
      border-color: rgba(255, 255, 255, 0.15);
    }
    .cat-item.active {
      border-color: var(--accent);
      background: var(--accent-muted);
      box-shadow: 0 0 16px var(--accent-glow);
    }
    .cat-item-title {
      font-size: 0.85rem;
      font-weight: 700;
      color: #fff;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .cat-item-count {
      font-size: 0.72rem;
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
    }
    /* Bottom Navigation Bar for Mobile */
    nav.mobile-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      width: 100%;
      height: calc(64px + var(--safe-bottom));
      padding-bottom: var(--safe-bottom);
      background: rgba(9, 9, 13, 0.94);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-around;
      align-items: center;
      z-index: 100;
    }
    .nav-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      font-size: 0.68rem;
      color: var(--text-sub);
      background: none;
      border: none;
      cursor: pointer;
      padding: 6px 12px;
      transition: color 0.15s ease;
      font-weight: 500;
    }
    .nav-btn.active {
      color: var(--accent);
      font-weight: 700;
    }
    /* Modal / Bottom Sheet */
    .sheet-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.72);
      backdrop-filter: blur(6px);
      z-index: 200;
      display: none;
      align-items: flex-end;
      animation: fadeIn 0.18s ease;
    }
    .sheet-backdrop.active {
      display: flex;
    }
    .sheet-panel {
      width: 100%;
      max-width: 520px;
      margin: 0 auto;
      background: #121218;
      border-top-left-radius: var(--radius-xl);
      border-top-right-radius: var(--radius-xl);
      border-top: 1px solid var(--border);
      border-left: 1px solid var(--border);
      border-right: 1px solid var(--border);
      padding: 20px;
      padding-bottom: calc(24px + var(--safe-bottom));
      max-height: 80vh;
      overflow-y: auto;
      animation: slideUp 0.24s var(--ease);
    }
    @keyframes slideUp {
      from { transform: translateY(100%); }
      to { transform: translateY(0); }
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    /* Toast */
    .toast-pill {
      position: fixed;
      top: calc(14px + var(--safe-top));
      left: 50%;
      transform: translateX(-50%) translateY(-100px);
      background: #171720;
      border: 1px solid var(--border-accent);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
      padding: 10px 18px;
      border-radius: 30px;
      font-size: 0.82rem;
      font-weight: 600;
      color: #fff;
      z-index: 300;
      transition: transform 0.28s var(--spring);
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .toast-pill.show {
      transform: translateX(-50%) translateY(0);
    }
    /* Lockscreen Banner */
    .banner-box {
      background: rgba(168, 85, 247, 0.08);
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 14px;
    }
    .banner-text {
      font-size: 0.76rem;
      color: #e9d5ff;
      line-height: 1.4;
    }
    /* Auth Modal / Token Prompt */
    .auth-box {
      background: #14141d;
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-md);
      padding: 16px;
      margin-bottom: 16px;
      display: none;
      flex-direction: column;
      gap: 10px;
    }
    .auth-box.active {
      display: flex;
    }
  </style>
</head>
<body>
  <div class="backdrop-glow"></div>

  <!-- Header -->
  <header class="app-header">
    <div class="header-brand">
      <div class="brand-logo-disc">
        <svg class="icon-svg fill-current" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="#09090d"/></svg>
      </div>
      <div>
        <div class="brand-title">JuiceVault</div>
      </div>
      <span class="brand-tag">REMOTE</span>
    </div>
    <div class="header-meta">
      <div class="status-badge" id="voiceBadge">
        <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span id="vcLabel">Not Connected</span>
      </div>
      <div class="status-badge">
        <span class="status-dot" id="connDot"></span>
        <span id="connLabel" style="font-family:'JetBrains Mono',monospace;">Live</span>
      </div>
    </div>
  </header>

  <div class="toast-pill" id="toast">
    <svg class="icon-svg" style="width:15px;height:15px;color:var(--accent);" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
    <span id="toastMsg">Action applied</span>
  </div>

  <div class="app-container">
    <!-- Auth Token Box (if token missing or unauthorized) -->
    <div class="auth-box" id="authBox">
      <div style="font-weight: 700; font-size: 0.9rem; color: #fff; display:flex; align-items:center; gap:8px;">
        <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        Authentication Required
      </div>
      <div style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.4;">
        Enter your secret auth passcode from Discord (run <code>4jv remote</code> in Discord):
      </div>
      <div style="display: flex; gap: 8px;">
        <input type="text" id="manualTokenInput" class="search-field" placeholder="Enter token…" style="background: rgba(0,0,0,0.5); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; color: #fff; font-family:'JetBrains Mono',monospace;">
        <button class="btn-kinetic btn-badge" onclick="saveManualToken()">Connect</button>
      </div>
    </div>

    <!-- Responsive Grid -->
    <div class="app-grid">
      <!-- LEFT COLUMN: NOW PLAYING CARD -->
      <div class="card-player-wrap">
        <div class="ui-card">
          <div class="player-visual" id="artContainer">
            <img src="https://api.juicevault.xyz/favicon.ico" class="player-cover" id="coverImg" alt="Album Cover">
          </div>

          <div class="track-meta" id="trackMetaContainer">
            <div class="track-title-row">
              <div class="soundwave-box" id="soundwaveBox">
                <span class="wave-bar"></span>
                <span class="wave-bar"></span>
                <span class="wave-bar"></span>
                <span class="wave-bar"></span>
              </div>
              <div class="track-title" id="trackTitle">Connecting…</div>
            </div>
            <div class="track-artist" id="trackArtist">Please wait</div>
            <div class="pill-row">
              <span class="pill-tag accent" id="categoryBadge">All Music</span>
              <span class="pill-tag" id="sourceBadge">Archive</span>
              <span class="pill-tag" id="eqBadge">Flat</span>
            </div>
          </div>

          <!-- Interactive Scrubber Bar -->
          <div class="scrubber-wrap">
            <div class="scrubber-track" id="progressBar">
              <div class="scrubber-fill" id="progressFill">
                <span class="scrubber-thumb"></span>
              </div>
            </div>
            <div class="scrubber-times">
              <span id="timeElapsed">0:00</span>
              <span id="timeDuration">0:00</span>
            </div>
          </div>

          <!-- Main Controls -->
          <div class="controls-main">
            <button class="btn-kinetic btn-circle btn-action-sm" id="btnRepeat" title="Repeat" onclick="action('repeat')">
              <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
            </button>
            <button class="btn-kinetic btn-circle btn-action-md" id="btnPrev" title="Previous Track" onclick="action('previous')">
              <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="5" x2="5" y2="19"/></svg>
            </button>
            <button class="btn-kinetic btn-circle btn-action-sm" title="Rewind 10s" onclick="action('seek', {delta: -10})">
              <svg class="icon-svg" viewBox="0 0 24 24"><path d="M11 3a9 9 0 1 0 9 9"/><polyline points="11 1 11 5 7 5"/><text x="10" y="14" font-size="7" font-weight="bold" fill="currentColor">10</text></svg>
            </button>
            <button class="btn-kinetic btn-play-pause" id="btnPlayPause" title="Play / Pause" onclick="action('toggle')">
              <svg class="icon-svg fill-current" id="playIconSvg" style="width:24px;height:24px;" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></svg>
            </button>
            <button class="btn-kinetic btn-circle btn-action-sm" title="Forward 10s" onclick="action('seek', {delta: 10})">
              <svg class="icon-svg" viewBox="0 0 24 24"><path d="M13 3a9 9 0 1 1-9 9"/><polyline points="13 1 13 5 17 5"/><text x="8" y="14" font-size="7" font-weight="bold" fill="currentColor">10</text></svg>
            </button>
            <button class="btn-kinetic btn-circle btn-action-md" id="btnNext" title="Next Track" onclick="action('skip')">
              <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
            </button>
            <button class="btn-kinetic btn-circle btn-action-sm" id="btnShuffle" title="Shuffle Queue" onclick="action('shuffle')">
              <svg class="icon-svg" viewBox="0 0 24 24"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
            </button>
          </div>

          <!-- Secondary Toolbar -->
          <div class="controls-sub">
            <button class="btn-kinetic btn-flat" onclick="openEqModal()">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>
              <span>EQ Presets</span>
            </button>
            <button class="btn-kinetic btn-flat" onclick="action('stop')">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>
              <span>Stop</span>
            </button>
            <button class="btn-kinetic btn-flat" id="lyricsBtn" onclick="openLyrics()">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              <span>Lyrics</span>
            </button>
          </div>

          <!-- Live Browser Audio & Lock Screen Banner -->
          <div class="banner-box" id="liveAudioBanner" style="flex-direction:column; align-items:stretch; gap:10px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <svg class="icon-svg" style="color:var(--accent); width:18px; height:18px;" viewBox="0 0 24 24"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
                <div>
                  <div style="font-weight:700; font-size:0.84rem; color:#fff;" id="liveStatusTitle">Listen on Phone / Browser</div>
                  <div style="font-size:0.72rem; color:var(--text-sub);">Stream live audio & enable lock screen media</div>
                </div>
              </div>
              <button class="btn-kinetic btn-badge" id="btnListenLive" onclick="toggleLiveAudio()">
                <span id="liveBtnLabel">Listen Live</span>
              </button>
            </div>
            <div id="liveAudioControls" style="display:none; align-items:center; gap:10px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.06);">
              <svg class="icon-svg" style="width:14px; height:14px; color:var(--text-sub);" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
              <input type="range" min="0" max="1" step="0.05" value="1" id="liveVolumeSlider" style="flex:1; accent-color:var(--accent); cursor:pointer;" oninput="updateLiveVolume(this.value)">
              <span id="liveVolPercent" style="font-size:0.72rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub);">100%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: TABS (Queue, Search, Collections, Shortcuts) -->
      <div class="card-content-wrap">
        <!-- Segment Bar Switcher for Desktop Only -->
        <div class="segment-bar desktop-segment">
          <button class="segment-btn active" onclick="switchTab('queue')">
            <svg class="icon-svg" style="width:15px;height:15px;" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
            <span>Queue</span>
          </button>
          <button class="segment-btn" onclick="switchTab('search')">
            <svg class="icon-svg" style="width:15px;height:15px;" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <span>Search</span>
          </button>
          <button class="segment-btn" onclick="switchTab('categories')">
            <svg class="icon-svg" style="width:15px;height:15px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
            <span>Library</span>
          </button>
          <button class="segment-btn" onclick="switchTab('shortcuts')">
            <svg class="icon-svg" style="width:15px;height:15px;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <span>Shortcuts</span>
          </button>
        </div>

        <!-- TAB: QUEUE -->
        <div class="tab-content active" id="tab-queue">
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                Requested (<span id="reqCount">0</span>)
              </span>
            </div>
            <div class="track-list" id="reqList">
              <div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No requested tracks. Use Search to queue songs.</div>
            </div>
          </div>

          <div class="ui-card">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg>
                Upcoming Archive (<span id="queueCount">0</span>)
              </span>
              <button class="btn-kinetic btn-flat" style="padding:4px 10px;" onclick="action('shuffle')">
                <svg class="icon-svg" style="width:13px;height:13px;" viewBox="0 0 24 24"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/></svg>
                <span>Shuffle</span>
              </button>
            </div>
            <div class="track-list" id="upcomingList">
              <div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Loading queue…</div>
            </div>
          </div>
        </div>

        <!-- TAB: SEARCH -->
        <div class="tab-content" id="tab-search">
          <div class="ui-card">
            <div class="search-input-group">
              <svg class="icon-svg" style="color:var(--text-sub);" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="search-field" id="searchInput" placeholder="Search song title or artist…" onkeydown="if(event.key==='Enter') executeSearch()">
              <button class="btn-kinetic btn-badge" onclick="executeSearch()">Search</button>
            </div>

            <!-- Mode Selector Switch -->
            <div class="segment-bar" style="margin-bottom:14px;">
              <button class="segment-btn active" id="modeVault" onclick="setSearchMode('vault')">
                <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
                <span>JuiceVault Archive</span>
              </button>
              <button class="segment-btn" id="modeExternal" onclick="setSearchMode('external')">
                <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                <span>Online (YT / SC)</span>
              </button>
            </div>

            <div class="section-title" style="margin-bottom:10px;">Results</div>
            <div class="track-list" id="searchResults">
              <div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Type a query and press Search.</div>
            </div>
          </div>
        </div>

        <!-- TAB: CATEGORIES -->
        <div class="tab-content" id="tab-categories">
          <div class="ui-card">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
                Collections & Library
              </span>
            </div>
            <div class="grid-categories" id="catGrid">
              <div class="cat-item" onclick="changeCategory('all')">
                <div class="cat-item-title">All Music</div>
                <div class="cat-item-count">Loading…</div>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB: SHORTCUTS & API -->
        <div class="tab-content" id="tab-shortcuts">
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                Apple Shortcuts & Siri Automation
              </span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 12px;">
              Trigger controls via Siri, back-tap, or iOS widgets. In Apple Shortcuts, create a shortcut with the action <strong>"Get Contents of URL"</strong> and paste one of these endpoints:
            </p>
            <div class="track-list" id="shortcutUrls"></div>
          </div>

          <div class="ui-card">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                Host Connection
              </span>
            </div>
            <div style="font-size: 0.78rem; font-family:'JetBrains Mono',monospace; color: var(--text-muted); display:flex; flex-direction:column; gap:6px;">
              <div>Guild: <span id="guildName" style="color:#fff;">--</span></div>
              <div>Voice: <span id="vcName" style="color:#fff;">--</span></div>
              <div>Protocol: <span id="protocolName" style="color:var(--accent);">--</span></div>
              <div>Auth Token: <code id="tokenDisplay" style="color:var(--accent);">--</code></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Bottom Navigation Bar -->
  <nav class="mobile-nav">
    <button class="nav-btn active" onclick="switchMobileNav('player')">
      <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      <span>Player</span>
    </button>
    <button class="nav-btn" onclick="switchMobileNav('queue')">
      <svg class="icon-svg" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg>
      <span>Queue</span>
    </button>
    <button class="nav-btn" onclick="switchMobileNav('search')">
      <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <span>Search</span>
    </button>
    <button class="nav-btn" onclick="switchMobileNav('categories')">
      <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
      <span>Library</span>
    </button>
    <button class="nav-btn" onclick="switchMobileNav('shortcuts')">
      <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
      <span>Shortcuts</span>
    </button>
  </nav>

  <!-- EQ Preset Bottom Sheet -->
  <div class="sheet-backdrop" id="eqSheet" onclick="if(event.target===this) closeEqModal()">
    <div class="sheet-panel">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <span class="section-title">
          <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/></svg>
          Audio EQ Profiles
        </span>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeEqModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div style="display:flex; flex-direction:column; gap:8px;" id="eqOptions"></div>
    </div>
  </div>

  <!-- Track Action Popup Sheet (Play Now / Move Next / Remove) -->
  <div class="sheet-backdrop" id="trackActionSheet" onclick="if(event.target===this) closeTrackModal()">
    <div class="sheet-panel">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:12px; min-width:0;">
          <div class="brand-logo-disc" style="width:40px; height:40px; border-radius:10px;">
            <svg class="icon-svg fill-current" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </div>
          <div style="min-width:0;">
            <div id="modalTrackTitle" style="font-weight:700; font-size:0.95rem; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">Track Title</div>
            <div id="modalTrackDesc" style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">Artist • 3:20</div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeTrackModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div style="display:flex; flex-direction:column; gap:10px;">
        <!-- Option 1: Play Right Now -->
        <div class="btn-kinetic track-card" style="border:1px solid var(--accent); background:var(--accent-muted); cursor:pointer;" onclick="modalAction('play_now')">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:36px; height:36px; border-radius:50%; background:var(--accent); display:flex; align-items:center; justify-content:center; color:#fff;">
              <svg class="icon-svg fill-current" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></svg>
            </div>
            <div>
              <div style="font-weight:700; font-size:0.9rem; color:#fff;">Play Right Now</div>
              <div style="font-size:0.74rem; color:var(--text-sub);">Interrupt current track and play this song immediately</div>
            </div>
          </div>
        </div>

        <!-- Option 2: Move to Next -->
        <div class="btn-kinetic track-card" style="cursor:pointer;" onclick="modalAction('move_next')">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:36px; height:36px; border-radius:50%; background:rgba(255,255,255,0.08); display:flex; align-items:center; justify-content:center; color:#fff;">
              <svg class="icon-svg" viewBox="0 0 24 24"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
            </div>
            <div>
              <div style="font-weight:700; font-size:0.9rem; color:#fff;">Play Next</div>
              <div style="font-size:0.74rem; color:var(--text-sub);">Place at the front of queue to play after current song</div>
            </div>
          </div>
        </div>

        <!-- Option 3: Remove from Queue -->
        <div class="btn-kinetic track-card" style="cursor:pointer;" onclick="modalAction('remove')">
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:36px; height:36px; border-radius:50%; background:rgba(239,68,68,0.15); display:flex; align-items:center; justify-content:center; color:var(--danger);">
              <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </div>
            <div>
              <div style="font-weight:700; font-size:0.9rem; color:var(--danger);">Remove From Queue</div>
              <div style="font-size:0.74rem; color:var(--text-sub);">Delete track from queue</div>
            </div>
          </div>
        </div>

        <button class="btn-kinetic btn-flat" style="padding:12px; margin-top:4px;" onclick="closeTrackModal()">
          Cancel
        </button>
      </div>
    </div>
  </div>

  <audio id="liveAudio" preload="auto" playsinline style="display:none;"></audio>

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

    // Protocol check
    const isHttps = window.location.protocol === 'https:';
    document.getElementById('protocolName').innerText = isHttps ? 'HTTPS / WSS (Secure)' : 'HTTP / WS';

    function saveManualToken() {
      const val = document.getElementById('manualTokenInput').value.trim();
      if (!val) return;
      token = val;
      localStorage.setItem('jv_token', token);
      document.getElementById('authBox').classList.remove('active');
      fetchStatus();
      connectWS();
      showToast('Authenticated');
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      document.getElementById('toastMsg').innerText = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2200);
      if (navigator.vibrate) navigator.vibrate(10);
    }

    // Tab switcher
    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.segment-btn').forEach(el => el.classList.remove('active'));
      const target = document.getElementById('tab-' + tabId);
      if (target) target.classList.add('active');
      const idx = ['queue', 'search', 'categories', 'shortcuts'].indexOf(tabId);
      if (idx !== -1) {
        const btns = document.querySelectorAll('.segment-btn');
        if (btns[idx]) btns[idx].classList.add('active');
      }
      if (tabId === 'queue') loadQueue();
      if (tabId === 'categories') loadCategories();
      if (tabId === 'shortcuts') renderShortcuts();
      if (navigator.vibrate) navigator.vibrate(8);
    }

    function switchMobileNav(tabId) {
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      const idx = ['player', 'queue', 'search', 'categories', 'shortcuts'].indexOf(tabId);
      if (idx !== -1) document.querySelectorAll('.nav-btn')[idx].classList.add('active');

      const playerWrap = document.querySelector('.card-player-wrap');
      const contentWrap = document.querySelector('.card-content-wrap');

      if (window.innerWidth < 860) {
        if (tabId === 'player') {
          playerWrap.style.display = 'block';
          contentWrap.style.display = 'none';
        } else {
          playerWrap.style.display = 'none';
          contentWrap.style.display = 'block';
          switchTab(tabId);
        }
      } else {
        switchTab(tabId);
      }
      if (navigator.vibrate) navigator.vibrate(8);
    }

    // Format time
    function formatTime(sec) {
      if (isNaN(sec) || sec < 0) return '0:00';
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // Scrubber
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

    async function action(name, payload = {}) {
      if (navigator.vibrate) navigator.vibrate(10);
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

    let liveStreamActive = false;
    let currentLiveTrackId = null;

    function toggleLiveAudio() {
      const audio = document.getElementById('liveAudio');
      liveStreamActive = !liveStreamActive;
      const btn = document.getElementById('btnListenLive');
      const controls = document.getElementById('liveAudioControls');
      const title = document.getElementById('liveStatusTitle');

      if (liveStreamActive) {
        btn.classList.add('active');
        btn.innerHTML = '<span>Stop Listening</span>';
        controls.style.display = 'flex';
        title.innerText = 'Live Audio: Streaming';
        syncLiveAudio(true);
        setupMediaSession();
        showToast('Live audio connected');
      } else {
        audio.pause();
        audio.removeAttribute('src');
        btn.classList.remove('active');
        btn.innerHTML = '<span>Listen Live</span>';
        controls.style.display = 'none';
        title.innerText = 'Listen on Phone / Browser';
        currentLiveTrackId = null;
        showToast('Live audio disconnected');
      }
    }

    function updateLiveVolume(val) {
      const audio = document.getElementById('liveAudio');
      audio.volume = parseFloat(val);
      const pctEl = document.getElementById('liveVolPercent');
      if (pctEl) pctEl.innerText = `${Math.round(val * 100)}%`;
    }

    function syncLiveAudio(force = false) {
      if (!liveStreamActive || !currentState) return;
      const audio = document.getElementById('liveAudio');
      const t = currentState.track;

      if (!t || !currentState.is_running) {
        if (!audio.paused) audio.pause();
        return;
      }

      const trackKey = (t.id || t.title || 'track') + '_' + (t.duration_seconds || 0);

      if (force || currentLiveTrackId !== trackKey) {
        currentLiveTrackId = trackKey;
        const streamUrl = `/api/stream?token=${encodeURIComponent(token)}&t=${encodeURIComponent(trackKey)}`;
        audio.src = streamUrl;
        audio.currentTime = Math.max(0, currentElapsed);
        if (currentState.is_playing) {
          audio.play().catch(e => console.log('Live playback interaction required:', e));
        }
      } else {
        if (Math.abs(audio.currentTime - currentElapsed) > 2.5) {
          audio.currentTime = currentElapsed;
        }
        if (currentState.is_playing && audio.paused) {
          audio.play().catch(() => {});
        } else if (!currentState.is_playing && !audio.paused) {
          audio.pause();
        }
      }
    }

    function setupMediaSession() {
      if (!('mediaSession' in navigator)) return;
      navigator.mediaSession.setActionHandler('play', () => { action('play'); });
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

    function applyState(state) {
      currentState = state;
      document.getElementById('connDot').classList.remove('offline');
      document.getElementById('connLabel').innerText = 'Live';

      if (state.guild) {
        document.getElementById('guildName').innerText = state.guild.name || state.guild.id;
      }
      if (state.voice_channel) {
        document.getElementById('vcLabel').innerText = state.voice_channel;
        document.getElementById('vcName').innerText = state.voice_channel;
      } else {
        document.getElementById('vcLabel').innerText = 'Offline';
      }

      document.getElementById('tokenDisplay').innerText = token || '(none)';

      const t = state.track;
      const metaBox = document.getElementById('trackMetaContainer');
      const soundwave = document.getElementById('soundwaveBox');

      if (t) {
        document.getElementById('trackTitle').innerText = t.title || 'Untitled';
        document.getElementById('trackArtist').innerText = t.artist || 'Juice WRLD';
        document.getElementById('coverImg').src = t.cover_url || 'https://api.juicevault.xyz/favicon.ico';
        document.getElementById('categoryBadge').innerText = (state.category_label || state.category || 'All').toUpperCase();
        document.getElementById('sourceBadge').innerText = t.is_external ? (t.source || 'External') : 'JuiceVault';
        document.getElementById('eqBadge').innerText = (state.effect || 'Flat').toUpperCase();

        durationSeconds = t.duration_seconds || 0;
        currentElapsed = t.position_seconds || 0;
        document.getElementById('timeDuration').innerText = t.length || formatTime(durationSeconds);
        updateScrubberUI();
      } else {
        document.getElementById('trackTitle').innerText = state.is_running ? 'Buffering archive…' : 'Player Inactive';
        document.getElementById('trackArtist').innerText = state.is_running ? 'Loading track' : 'Use Play to begin';
      }

      // Play/Pause button and soundwave state
      const playIcon = document.getElementById('playIconSvg');
      if (state.is_playing) {
        playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
        document.getElementById('coverImg').classList.add('playing');
        soundwave.classList.add('playing');
      } else {
        playIcon.innerHTML = '<polygon points="6 3 20 12 6 21 6 3"/>';
        document.getElementById('coverImg').classList.remove('playing');
        soundwave.classList.remove('playing');
      }

      const repeatBtn = document.getElementById('btnRepeat');
      if (state.repeat) repeatBtn.classList.add('active');
      else repeatBtn.classList.remove('active');

      document.getElementById('reqCount').innerText = state.requested_size || 0;
      document.getElementById('queueCount').innerText = state.queue_size || 0;

      updateMediaSession();
      syncLiveAudio();
      const qTab = document.getElementById('tab-queue');
      if (qTab && qTab.classList.contains('active')) {
        loadQueue();
      }
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

    // Local tick
    clearInterval(progressTimer);
    progressTimer = setInterval(() => {
      if (currentState && currentState.is_playing && durationSeconds > 0) {
        currentElapsed += 1;
        if (currentElapsed > durationSeconds) currentElapsed = durationSeconds;
        updateScrubberUI();
      }
    }, 1000);

    // WebSocket auto-detect protocol
    function connectWS() {
      if (!token) return;
      const wsProto = isHttps ? 'wss:' : 'ws:';
      const wsUrl = `${wsProto}//${window.location.host}/ws?token=${encodeURIComponent(token)}`;
      try {
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
          document.getElementById('connLabel').innerText = 'Offline';
          setTimeout(connectWS, 3000);
        };

        ws.onerror = () => ws.close();
      } catch (err) {
        console.error('WS init error:', err);
      }
    }

    // Fetch Status
    async function fetchStatus() {
      try {
        const res = await fetch(`/api/status?token=${encodeURIComponent(token)}`);
        if (res.status === 401) {
          document.getElementById('authBox').classList.add('active');
          document.getElementById('trackTitle').innerText = 'Unauthorized';
          document.getElementById('trackArtist').innerText = 'Provide token to connect';
          return;
        }
        if (res.ok) {
          const data = await res.json();
          if (data.state) applyState(data.state);
        }
      } catch (e) {
        console.error('Fetch status error:', e);
      }
    }

    let selectedQueueItem = null;

    function openTrackModal(source, index, title, artist, length) {
      selectedQueueItem = { source, index, title, artist, length };
      const titleEl = document.getElementById('modalTrackTitle');
      const descEl = document.getElementById('modalTrackDesc');
      if (titleEl) titleEl.innerText = title || 'Untitled Track';
      if (descEl) descEl.innerText = `${artist || 'Juice WRLD'} • ${length || '—'}`;
      const sheet = document.getElementById('trackActionSheet');
      if (sheet) sheet.classList.add('active');
      if (navigator.vibrate) navigator.vibrate(10);
    }

    function closeTrackModal() {
      const sheet = document.getElementById('trackActionSheet');
      if (sheet) sheet.classList.remove('active');
      selectedQueueItem = null;
    }

    async function modalAction(actionType) {
      if (!selectedQueueItem) return;
      const { source, index, title } = selectedQueueItem;
      closeTrackModal();

      try {
        if (actionType === 'remove') {
          const res = await fetch(`/api/queue/remove?token=${encodeURIComponent(token)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: source, index })
          });
          const d = await res.json();
          showToast(d.success ? 'Track removed from queue' : 'Remove failed');
          loadQueue();
        } else if (actionType === 'play_now') {
          const res = await fetch(`/api/queue/play_now?token=${encodeURIComponent(token)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: source, index })
          });
          const d = await res.json();
          showToast(d.message || `Playing now: ${title}`);
          loadQueue();
        } else if (actionType === 'move_next') {
          const res = await fetch(`/api/queue/move_next?token=${encodeURIComponent(token)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: source, index })
          });
          const d = await res.json();
          showToast(d.message || `Moved to play next: ${title}`);
          loadQueue();
        }
      } catch (err) {
        showToast('Action failed: ' + err.message);
      }
    }

    // Load Queue
    async function loadQueue() {
      try {
        const res = await fetch(`/api/queue?token=${encodeURIComponent(token)}`);
        const data = await res.json();
        const reqList = document.getElementById('reqList');
        if (data.requested && data.requested.length > 0) {
          reqList.innerHTML = data.requested.map((t, idx) => {
            const title = (t.title || 'Untitled Track').replace(/'/g, "&#39;");
            const artist = (t.artist || 'Juice WRLD').replace(/'/g, "&#39;");
            const len = (t.length || '—').replace(/'/g, "&#39;");
            return `
            <div class="track-card" style="cursor:pointer;" onclick="openTrackModal('requested', ${idx}, '${title}', '${artist}', '${len}')">
              <div class="track-meta-col">
                <div class="track-name">${t.title || 'Untitled'}</div>
                <div class="track-desc">${t.artist || 'Juice WRLD'} • ${t.length || '—'}</div>
              </div>
              <span class="btn-badge" style="font-size:0.68rem; padding:3px 7px;">Manage</span>
            </div>
          `;
          }).join('');
        } else {
          reqList.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No requested tracks. Use Search to queue songs.</div>';
        }

        const upList = document.getElementById('upcomingList');
        if (data.upcoming && data.upcoming.length > 0) {
          upList.innerHTML = data.upcoming.slice(0, 30).map((t, idx) => {
            const title = (t.title || 'Untitled Track').replace(/'/g, "&#39;");
            const artist = (t.artist || 'Juice WRLD').replace(/'/g, "&#39;");
            const len = (t.length || '—').replace(/'/g, "&#39;");
            return `
            <div class="track-card" style="cursor:pointer;" onclick="openTrackModal('upcoming', ${idx}, '${title}', '${artist}', '${len}')">
              <div class="track-meta-col">
                <div class="track-name">${idx + 1}. ${t.title || 'Untitled'}</div>
                <div class="track-desc">${t.artist || 'Juice WRLD'} • ${t.length || '—'}</div>
              </div>
              <span class="btn-badge" style="font-size:0.68rem; padding:3px 7px;">Manage</span>
            </div>
          `;
          }).join('');
        } else {
          upList.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Archive queue empty.</div>';
        }
      } catch (e) {
        console.error('Queue load error:', e);
      }
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
      resContainer.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Searching archive…</div>';
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&source=${searchMode}&token=${encodeURIComponent(token)}`);
        const data = await res.json();
        if (data.results && data.results.length > 0) {
          resContainer.innerHTML = data.results.map((item) => `
            <div class="track-card">
              <div class="track-meta-col">
                <div class="track-name">${item.title || 'Untitled'}</div>
                <div class="track-desc">${item.artist || 'Juice WRLD'} • ${item.length || '—'}</div>
              </div>
              <button class="btn-kinetic btn-badge" onclick='addToQueue(${JSON.stringify(item).replace(/'/g, "&#39;")})'>+ Add</button>
            </div>
          `).join('');
        } else {
          resContainer.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No results found.</div>';
        }
      } catch (e) {
        resContainer.innerHTML = `<div class="track-card" style="color: var(--danger); font-size: 0.8rem;">Search failed: ${e.message}</div>`;
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
        showToast(d.message || 'Added to Requested');
      } catch (e) {
        showToast('Error: ' + e.message);
      }
    }

    // Categories
    async function loadCategories() {
      if (!currentState || !currentState.categories) {
        await fetchStatus();
      }
      const grid = document.getElementById('catGrid');
      if (!grid) return;
      if (!currentState || !currentState.categories) {
        grid.innerHTML = '<div class="track-card" style="color:var(--text-sub); font-size:0.8rem;">Loading collections…</div>';
        return;
      }
      const cats = currentState.categories;
      const active = (currentState.category || 'all').toLowerCase();
      grid.innerHTML = Object.entries(cats).map(([name, count]) => `
        <div class="cat-item ${name.toLowerCase() === active ? 'active' : ''}" onclick="changeCategory('${name}')">
          <div class="cat-item-title">${name}</div>
          <div class="cat-item-count">${count} tracks</div>
        </div>
      `).join('');
    }

    async function changeCategory(category) {
      if (currentState) {
        currentState.category = category;
        const b = document.getElementById('categoryBadge');
        if (b) b.innerText = category.toUpperCase();
      }
      loadCategories();
      showToast(`Category: ${category}`);
      try {
        await fetch(`/api/category?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category })
        });
      } catch (e) {
        console.error('Category change error:', e);
      }
    }

    // EQ Sheet
    function openEqModal() {
      if (!currentState || !currentState.effects) return;
      const container = document.getElementById('eqOptions');
      container.innerHTML = currentState.effects.map(eq => `
        <div class="track-card ${currentState.effect === eq.id ? 'active' : ''}" style="cursor:pointer; ${currentState.effect === eq.id ? 'border-color:var(--accent); background:var(--accent-muted);' : ''}" onclick="setEq('${eq.id}')">
          <div>
            <div style="font-weight:600; font-size:0.88rem; color:#fff;">${eq.label}</div>
            <div style="font-size:0.72rem; color:var(--text-sub); margin-top:2px;">${eq.desc}</div>
          </div>
          ${currentState.effect === eq.id ? '<svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
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
      showToast(`EQ: ${effect}`);
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
        { name: 'Toggle Play / Pause', url: `${base}/toggle${tParam}` },
        { name: 'Next Track (Skip)', url: `${base}/skip${tParam}` },
        { name: 'Previous Track', url: `${base}/previous${tParam}` },
        { name: 'Skip 10s Forward', url: `${base}/seek${tParam}${tParam ? '&' : '?'}delta=10` },
        { name: 'Rewind 10s Backward', url: `${base}/seek${tParam}${tParam ? '&' : '?'}delta=-10` },
        { name: 'Stop Playback', url: `${base}/stop${tParam}` },
        { name: 'Shuffle Archive Queue', url: `${base}/shuffle${tParam}` },
      ];
      const container = document.getElementById('shortcutUrls');
      container.innerHTML = shortcuts.map(s => `
        <div class="track-card" style="flex-direction:column; align-items:flex-start; gap:6px;">
          <div style="font-size:0.84rem; font-weight:600; color:#fff;">${s.name}</div>
          <code style="font-size:0.72rem; color:var(--accent); word-break:break-all; font-family:'JetBrains Mono',monospace;">${s.url}</code>
          <button class="btn-kinetic btn-badge" style="align-self:flex-end; font-size:0.7rem; padding:4px 8px;" onclick="copyShortcut('${s.url}')">Copy URL</button>
        </div>
      `).join('');
    }

    function copyShortcut(url) {
      navigator.clipboard.writeText(url).then(() => showToast('Shortcut URL copied'));
    }

    // Startup
    if (!token) {
      document.getElementById('authBox').classList.add('active');
    } else {
      connectWS();
      fetchStatus();
    }
  </script>
</body>
</html>
"""

MANIFEST_JSON = """{
  "name": "JuiceVault Remote",
  "short_name": "JuiceVault",
  "start_url": "/?pwa=1",
  "display": "standalone",
  "background_color": "#09090d",
  "theme_color": "#a855f7",
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
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
"""
