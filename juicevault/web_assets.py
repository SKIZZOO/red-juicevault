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
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2064%2064%22%3E%3Cdefs%3E%3ClinearGradient%20id%3D%22discGrad%22%20x1%3D%220%25%22%20y1%3D%220%25%22%20x2%3D%22100%25%22%20y2%3D%22100%25%22%3E%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%23c084fc%22%2F%3E%3Cstop%20offset%3D%2250%25%22%20stop-color%3D%22%23a855f7%22%2F%3E%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%236b21a8%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Ccircle%20cx%3D%2232%22%20cy%3D%2232%22%20r%3D%2230%22%20fill%3D%22url(%23discGrad)%22%2F%3E%3Ccircle%20cx%3D%2232%22%20cy%3D%2232%22%20r%3D%2222%22%20fill%3D%22none%22%20stroke%3D%22rgba(255%2C255%2C255%2C0.3)%22%20stroke-width%3D%221.6%22%2F%3E%3Ccircle%20cx%3D%2232%22%20cy%3D%2232%22%20r%3D%2216%22%20fill%3D%22none%22%20stroke%3D%22rgba(255%2C255%2C255%2C0.22)%22%20stroke-width%3D%221.2%22%2F%3E%3Ccircle%20cx%3D%2232%22%20cy%3D%2232%22%20r%3D%2210%22%20fill%3D%22%2309090d%22%20stroke%3D%22%23a855f7%22%20stroke-width%3D%221.8%22%2F%3E%3Ccircle%20cx%3D%2232%22%20cy%3D%2232%22%20r%3D%223.5%22%20fill%3D%22%23c084fc%22%2F%3E%3C%2Fsvg%3E">
  <link rel="alternate icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" sizes="192x192" href="/icon-192.png">
  <link rel="manifest" href="/manifest.json">
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
      header.app-header {
        padding: 10px 12px !important;
        gap: 6px;
      }
      .header-meta {
        gap: 5px !important;
      }
      #vcLabel {
        max-width: 68px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .stats-badge {
        padding: 4px 7px !important;
        font-size: 0.7rem !important;
        gap: 4px !important;
      }
      .desktop-segment {
        display: none !important;
      }
      .card-content-wrap {
        display: none;
      }
      .app-container {
        padding: 10px 12px calc(72px + var(--safe-bottom)) !important;
      }
      .ui-card {
        padding: 14px 14px 12px !important;
      }
      .player-visual {
        max-width: 140px !important;
        margin: 0 auto 8px !important;
      }
      .track-meta {
        margin-bottom: 8px !important;
      }
      .track-title {
        font-size: 1.05rem !important;
      }
      .track-artist {
        font-size: 0.8rem !important;
      }
      .pill-row {
        margin-top: 6px !important;
        gap: 4px !important;
      }
      .pill-tag {
        font-size: 0.68rem !important;
        padding: 2px 6px !important;
      }
      .scrubber-wrap {
        margin: 8px 0 10px !important;
      }
      .controls-main {
        gap: 8px !important;
        margin-bottom: 10px !important;
      }
      .btn-play-pause {
        width: 48px !important;
        height: 48px !important;
      }
      .btn-action-md {
        width: 36px !important;
        height: 36px !important;
      }
      .btn-action-sm {
        width: 30px !important;
        height: 30px !important;
      }
      .controls-sub {
        margin-bottom: 8px !important;
        gap: 6px !important;
      }
      .controls-sub .btn-flat {
        padding: 4px 8px !important;
        font-size: 0.72rem !important;
      }
      .banner-box {
        padding: 8px 10px !important;
        margin-top: 8px !important;
        gap: 8px !important;
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
      padding: 18px;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    /* Now Playing Display */
    .player-visual {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      max-width: 200px;
      margin: 0 auto 12px;
      border-radius: var(--radius-md);
      overflow: hidden;
      background: #14141a;
      border: 1px solid var(--border);
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.65), 0 0 24px rgba(168, 85, 247, 0.12);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .player-cover {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.4s var(--spring), filter 0.3s ease;
    }
    .player-cover.playing {
      transform: scale(1.035);
      filter: drop-shadow(0 0 16px var(--accent-glow));
    }
    /* Kinetic Soundwave Indicator */
    .soundwave-box {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 16px;
    }
    .wave-bar {
      width: 3px;
      height: 4px;
      background: var(--accent);
      border-radius: 2px;
      transition: height 0.15s ease, background-color 0.2s ease;
    }
    .playing .wave-bar {
      box-shadow: 0 0 8px var(--accent-glow);
    }
    .playing .wave-bar:nth-child(1) { animation: soundwave 0.85s infinite ease-in-out; }
    .playing .wave-bar:nth-child(2) { animation: soundwave 0.62s infinite ease-in-out 0.15s; }
    .playing .wave-bar:nth-child(3) { animation: soundwave 1.05s infinite ease-in-out 0.35s; }
    .playing .wave-bar:nth-child(4) { animation: soundwave 0.72s infinite ease-in-out 0.1s; }
    .playing .wave-bar:nth-child(5) { animation: soundwave 0.9s infinite ease-in-out 0.25s; }
    @keyframes soundwave {
      0%, 100% { height: 4px; }
      50% { height: 16px; }
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
    .scrubber-track:hover, .scrubber-track:active {
      height: 8px;
    }
    .scrubber-fill {
      height: 100%;
      background: linear-gradient(90deg, #9333ea, #c084fc);
      border-radius: 4px;
      width: 0%;
      box-shadow: 0 0 12px var(--accent-glow);
      position: relative;
      will-change: width;
    }
    .scrubber-thumb {
      width: 14px;
      height: 14px;
      background: #ffffff;
      border: 2px solid var(--accent);
      border-radius: 50%;
      position: absolute;
      right: -7px;
      top: 50%;
      transform: translateY(-50%) scale(1);
      box-shadow: 0 0 10px var(--accent-glow), 0 2px 5px rgba(0, 0, 0, 0.8);
      opacity: 0.9;
      transition: transform 0.15s var(--spring), opacity 0.15s ease;
    }
    .scrubber-track:hover .scrubber-thumb,
    .scrubber-track:active .scrubber-thumb {
      transform: translateY(-50%) scale(1.3);
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
      transition: transform 0.2s var(--spring), background 0.15s ease, border-color 0.15s ease, box-shadow 0.2s ease, color 0.15s ease;
    }
    .btn-circle:hover {
      background: var(--surface-elevated);
      border-color: rgba(255, 255, 255, 0.2);
      color: #fff;
      transform: scale(1.06);
    }
    .btn-circle:active {
      transform: scale(0.92);
    }
    .btn-circle.active {
      color: var(--accent);
      border-color: var(--accent);
      background: var(--accent-muted);
      box-shadow: 0 0 12px var(--accent-muted);
    }
    .btn-play-pause {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #a855f7, #7e22ce);
      border: none;
      color: #fff;
      box-shadow: 0 6px 20px var(--accent-glow);
      transition: transform 0.2s var(--spring), box-shadow 0.25s ease, background 0.2s ease;
    }
    .btn-play-pause:hover {
      background: linear-gradient(135deg, #b56bfa, #8b28e0);
      box-shadow: 0 8px 28px var(--accent-glow);
      transform: scale(1.08);
    }
    .btn-play-pause:active {
      transform: scale(0.92);
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
      transition: transform 0.18s var(--spring), background 0.15s ease, border-color 0.15s ease, box-shadow 0.18s ease;
      gap: 12px;
    }
    .track-card:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.16);
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
    }
    .track-card:active {
      transform: scale(0.98);
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
      transition: transform 0.15s var(--spring), background 0.15s ease, color 0.15s ease;
    }
    .btn-badge:hover {
      background: var(--accent);
      color: #fff;
      transform: scale(1.05);
    }
    .btn-badge:active {
      transform: scale(0.94);
    }
    .btn-badge.active {
      background: var(--accent);
      color: #fff;
      box-shadow: 0 0 12px var(--accent-glow);
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
    /* Category Grid & Library Collections */
    .active-col-banner {
      padding: 4px;
    }
    .active-col-icon-wrap {
      width: 44px;
      height: 44px;
      border-radius: var(--radius-md);
      background: var(--accent-muted);
      border: 1px solid var(--border-accent);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .grid-categories {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      gap: 12px;
    }
    @media (max-width: 560px) {
      .grid-categories {
        grid-template-columns: 1fr;
      }
    }
    .cat-item {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      cursor: pointer;
      transition: transform 0.2s var(--spring), background 0.15s ease, border-color 0.15s ease, box-shadow 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 8px;
      position: relative;
    }
    .cat-item.featured {
      grid-column: 1 / -1;
      background: linear-gradient(135deg, rgba(255, 45, 85, 0.08) 0%, rgba(18, 18, 24, 0.95) 100%);
      border-color: rgba(255, 45, 85, 0.35);
      box-shadow: 0 4px 20px rgba(255, 45, 85, 0.06);
    }
    .cat-item:hover {
      background: var(--surface-elevated);
      border-color: rgba(255, 255, 255, 0.22);
      transform: translateY(-2px);
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.45);
    }
    .cat-item:active {
      transform: scale(0.98);
    }
    .cat-item.active {
      border-color: var(--accent);
      background: linear-gradient(135deg, rgba(255, 45, 85, 0.16) 0%, rgba(18, 18, 24, 0.92) 100%);
      box-shadow: 0 0 20px var(--accent-glow);
    }
    .cat-item.browsing:not(.active) {
      border-color: rgba(255, 255, 255, 0.35);
      background: var(--surface-elevated);
    }
    .cat-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .cat-icon-badge {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.09);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      flex-shrink: 0;
    }
    .cat-item.active .cat-icon-badge {
      background: var(--accent-muted);
      border-color: var(--border-accent);
      color: var(--accent);
    }
    .cat-active-pill {
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      font-family: 'JetBrains Mono', monospace;
      color: var(--accent);
      background: var(--accent-muted);
      border: 1px solid var(--border-accent);
      padding: 2px 7px;
      border-radius: 999px;
    }
    .cat-item-count {
      font-size: 0.72rem;
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
    }
    .cat-meta-wrap {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .cat-item-title {
      font-size: 0.92rem;
      font-weight: 700;
      color: #fff;
      letter-spacing: -0.01em;
    }
    .cat-item-subtitle {
      font-size: 0.7rem;
      color: var(--accent);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .cat-item-desc {
      font-size: 0.74rem;
      color: var(--text-muted);
      line-height: 1.35;
      margin-top: 2px;
    }
    .cat-actions-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-top: 4px;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .track-thumb {
      width: 36px;
      height: 36px;
      border-radius: 6px;
      object-fit: cover;
      background: #1a1a24;
      flex-shrink: 0;
      border: 1px solid rgba(255, 255, 255, 0.08);
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
    /* Telemetry, Views & Daily Usage System */
    .stats-badge {
      cursor: pointer;
      user-select: none;
      transition: all 0.2s var(--spring);
      position: relative;
    }
    .stats-badge:hover {
      background: var(--surface-elevated);
      border-color: rgba(235, 47, 150, 0.4);
      box-shadow: 0 0 14px rgba(235, 47, 150, 0.25);
      transform: translateY(-1px);
    }
    .stats-badge:active {
      transform: scale(0.96);
    }
    .telemetry-live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 8px var(--accent-glow);
      animation: pulseNeon 1.8s infinite ease-in-out;
      flex-shrink: 0;
    }
    @keyframes pulseNeon {
      0%, 100% { opacity: 0.5; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.3); }
    }
    .header-pill-sub {
      font-size: 0.65rem;
      font-weight: 700;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.25);
      padding: 1px 6px;
      border-radius: 10px;
      margin-left: 2px;
      letter-spacing: 0.02em;
    }

    /* Left Column Compact Telemetry Ribbon */
    .telemetry-quick-bar {
      margin-top: 10px;
      background: rgba(18, 18, 24, 0.85);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 8px 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      cursor: pointer;
      transition: all 0.2s var(--spring);
    }
    .telemetry-quick-bar:hover {
      background: var(--surface-elevated);
      border-color: rgba(255, 255, 255, 0.18);
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
      transform: translateY(-1px);
    }
    .telemetry-q-item {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }
    .telemetry-q-col {
      display: flex;
      flex-direction: column;
      line-height: 1.1;
    }
    .telemetry-q-sub {
      font-size: 0.6rem;
      text-transform: uppercase;
      color: var(--text-sub);
      font-weight: 600;
      letter-spacing: 0.03em;
    }
    .telemetry-q-num {
      font-size: 0.8rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      color: #fff;
    }
    .telemetry-q-num.highlight {
      color: #f43f5e;
    }
    .telemetry-q-sep {
      width: 1px;
      height: 20px;
      background: rgba(255, 255, 255, 0.07);
    }
    .telemetry-q-more {
      font-size: 0.75rem;
      color: var(--text-sub);
      font-weight: 700;
      margin-left: 2px;
      transition: color 0.15s ease, transform 0.15s ease;
    }
    .telemetry-quick-bar:hover .telemetry-q-more {
      color: var(--accent);
      transform: translate(2px, -2px);
    }

    /* Telemetry Grid & Hero Cards */
    .telemetry-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin-bottom: 14px;
    }
    @media (max-width: 480px) {
      .telemetry-grid {
        grid-template-columns: 1fr;
      }
    }
    .telemetry-card {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(18, 18, 24, 0.95) 100%);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .telemetry-card:hover {
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateY(-2px);
    }
    .telemetry-card.highlight-card {
      background: linear-gradient(135deg, rgba(235, 47, 150, 0.1) 0%, rgba(18, 18, 24, 0.95) 100%);
      border-color: rgba(235, 47, 150, 0.35);
      box-shadow: 0 4px 20px rgba(235, 47, 150, 0.08);
    }
    .t-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .t-card-title {
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
    }
    .t-card-icon {
      width: 26px;
      height: 26px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .t-card-icon svg {
      width: 14px;
      height: 14px;
    }
    .t-card-icon.purple {
      background: rgba(168, 85, 247, 0.15);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.3);
    }
    .t-card-icon.pink {
      background: rgba(244, 63, 94, 0.15);
      color: #fb7185;
      border: 1px solid rgba(244, 63, 94, 0.3);
    }
    .t-card-icon.blue {
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .t-card-icon.green {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .t-card-val {
      font-size: 1.45rem;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #fff;
      letter-spacing: -0.02em;
    }
    .t-card-val.accent-val {
      color: #f43f5e;
      text-shadow: 0 0 16px rgba(244, 63, 94, 0.4);
    }
    .t-card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      font-size: 0.7rem;
    }
    .t-tag {
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.62rem;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }
    .t-tag.purple { background: rgba(168, 85, 247, 0.15); color: #d8b4fe; }
    .t-tag.pink { background: rgba(244, 63, 94, 0.15); color: #fda4af; }
    .t-tag.blue { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }
    .t-tag.green { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }
    .t-sub {
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
    }

    /* 24-Hour Activity Pulse Section */
    .telemetry-activity-section {
      background: rgba(13, 13, 18, 0.7);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      margin-bottom: 14px;
    }
    .t-act-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .t-act-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .t-act-status {
      font-size: 0.68rem;
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
    }
    .activity-bars-grid {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 48px;
      padding: 4px 0;
    }
    .activity-bar-slot {
      flex: 1;
      height: 100%;
      display: flex;
      align-items: flex-end;
      position: relative;
    }
    .activity-bar {
      width: 100%;
      border-radius: 3px;
      min-height: 4px;
      background: rgba(255, 255, 255, 0.08);
      transition: height 0.4s var(--ease), background 0.3s ease;
    }
    .activity-bar.active {
      background: linear-gradient(180deg, #c084fc 0%, #6b21a8 100%);
    }
    .activity-bar.high {
      background: linear-gradient(180deg, #f43f5e 0%, #a855f7 100%);
      box-shadow: 0 0 8px rgba(244, 63, 94, 0.35);
    }
    .activity-bar.current {
      background: linear-gradient(180deg, #38bdf8 0%, var(--accent) 100%);
      box-shadow: 0 0 10px var(--accent-glow);
      animation: pulseNeon 1.5s infinite;
    }
    .activity-bars-legend {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 6px;
      font-size: 0.65rem;
      color: var(--text-sub);
      font-family: 'JetBrains Mono', monospace;
    }

    /* Telemetry Breakdown Details Card */
    .telemetry-breakdown-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .t-detail-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.76rem;
    }
    .t-detail-label {
      color: var(--text-muted);
    }
    .t-detail-value {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      color: #fff;
    }
    .telemetry-live-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.62rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: var(--accent);
      background: rgba(235, 47, 150, 0.12);
      border: 1px solid rgba(235, 47, 150, 0.3);
      padding: 2px 7px;
      border-radius: 12px;
    }
    .pulse-ring {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 6px var(--accent-glow);
      animation: pulseNeon 1.2s infinite;
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
    /* Soundboard Grid & Pads */
    .soundboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 10px;
    }
    .sound-pad {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 12px 10px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 8px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: transform 0.16s var(--ease), border-color 0.16s ease, box-shadow 0.16s ease;
      user-select: none;
      -webkit-tap-highlight-color: transparent;
    }
    .sound-pad:hover {
      transform: translateY(-2px);
      border-color: var(--pad-color, var(--accent));
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4), 0 0 10px var(--pad-glow, rgba(235, 47, 150, 0.25));
    }
    .sound-pad:active {
      transform: scale(0.96);
    }
    .sound-pad.is-playing {
      border-color: var(--pad-color, var(--accent)) !important;
      box-shadow: 0 0 16px var(--pad-glow, rgba(235, 47, 150, 0.5)) !important;
      animation: padPulse 1.1s infinite alternate ease-in-out;
    }
    @keyframes padPulse {
      0% { transform: scale(1); filter: brightness(1); }
      100% { transform: scale(1.03); filter: brightness(1.2); }
    }
    .sound-pad-icon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--pad-bg, rgba(235, 47, 150, 0.12));
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--pad-color, var(--accent));
      transition: transform 0.2s ease, background 0.2s ease;
      flex-shrink: 0;
    }
    .sound-pad:hover .sound-pad-icon {
      transform: scale(1.08);
      background: var(--pad-color, var(--accent));
      color: #fff;
    }
    .sound-pad-title {
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--text-main);
      line-height: 1.25;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 1.9em;
    }
    .credit-author {
      color: var(--accent);
      font-weight: 600;
      text-decoration: none;
      transition: color 0.15s ease;
    }
    .credit-author:hover {
      color: #c084fc;
      text-decoration: underline;
    }
    .credit-partner {
      color: #38bdf8;
      font-weight: 600;
      text-decoration: none;
      transition: color 0.15s ease;
    }
    .credit-partner:hover {
      color: #7dd3fc;
      text-decoration: underline;
    }
    .app-footer {
      margin-top: 24px;
      padding: 16px 8px 12px;
      text-align: center;
      font-size: 0.74rem;
      color: var(--text-sub);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    .footer-credit {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .footer-sep {
      color: var(--border);
    }
    .footer-sub {
      font-size: 0.67rem;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
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
      <div class="status-badge stats-badge" id="headerViewsBadge" onclick="openStatsModal()" title="View Live Traffic & Daily Usage">
        <span class="telemetry-live-dot"></span>
        <svg class="icon-svg" style="width:13px;height:13px;color:var(--accent);" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        <span id="headerViewsCount" style="font-family:'JetBrains Mono',monospace;">--</span>
        <span class="header-pill-sub" id="headerDailyCount">-- today</span>
      </div>
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
            <button class="btn-kinetic btn-flat" onclick="switchMobileNav('soundboard')">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>
              <span>Soundboard</span>
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

          <!-- Listen Together & Lock Screen Banner -->
          <div class="banner-box" id="liveAudioBanner" style="flex-direction:column; align-items:stretch; gap:8px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">
              <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:28px; height:28px; border-radius:50%; background:var(--accent-muted); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                  <svg class="icon-svg" style="color:var(--accent); width:15px; height:15px;" viewBox="0 0 24 24"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
                </div>
                <div>
                  <div style="display:flex; align-items:center; gap:6px;">
                    <div style="font-weight:700; font-size:0.82rem; color:#fff;" id="liveStatusTitle">Listen Together</div>
                    <span class="pill-tag accent" style="font-size:0.62rem; padding:1px 5px; text-transform:uppercase;" id="liveSyncBadge">1:1 Sync</span>
                  </div>
                  <div style="font-size:0.7rem; color:var(--text-sub);" id="liveStatusSub">1:1 Real-time synced audio with Discord voice channel</div>
                </div>
              </div>
              <div style="display:flex; gap:6px; align-items:center;">
                <button class="btn-kinetic btn-badge" id="btnListenLive" onclick="toggleLiveAudio()" title="Stream synchronized audio directly on this phone">
                  <span id="liveBtnLabel">Listen Together</span>
                </button>
              </div>
            </div>
            <div id="liveAudioControls" style="display:none; align-items:center; gap:8px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.06);">
              <svg class="icon-svg" style="width:13px; height:13px; color:var(--text-sub);" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
              <input type="range" min="0" max="1" step="0.05" value="1" id="liveVolumeSlider" style="flex:1; accent-color:var(--accent); cursor:pointer;" oninput="updateLiveVolume(this.value)">
              <span id="liveVolPercent" style="font-size:0.7rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub);">100%</span>
              <span style="font-size:0.65rem; color:var(--accent); font-family:'JetBrains Mono',monospace;" id="syncDriftLabel">±0ms</span>
            </div>
          </div>

          <!-- Telemetry & Daily Usage Quick Bar -->
          <div class="telemetry-quick-bar" onclick="openStatsModal()" title="Click to view full Live Telemetry &amp; Daily Usage">
            <div class="telemetry-q-item">
              <svg class="icon-svg" style="width:13px;height:13px;color:var(--accent);" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <div class="telemetry-q-col">
                <span class="telemetry-q-sub">Views</span>
                <span class="telemetry-q-num" id="quickTotalViews">--</span>
              </div>
            </div>
            <div class="telemetry-q-sep"></div>
            <div class="telemetry-q-item">
              <svg class="icon-svg" style="width:13px;height:13px;color:#f43f5e;" viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
              <div class="telemetry-q-col">
                <span class="telemetry-q-sub">Today</span>
                <span class="telemetry-q-num highlight" id="quickDailyViews">--</span>
              </div>
            </div>
            <div class="telemetry-q-sep"></div>
            <div class="telemetry-q-item">
              <svg class="icon-svg" style="width:13px;height:13px;color:#38bdf8;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              <div class="telemetry-q-col">
                <span class="telemetry-q-sub">Streamed</span>
                <span class="telemetry-q-num" id="quickDailyTime">--</span>
              </div>
            </div>
            <div class="telemetry-q-sep"></div>
            <div class="telemetry-q-item">
              <svg class="icon-svg" style="width:13px;height:13px;color:#10b981;" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
              <div class="telemetry-q-col">
                <span class="telemetry-q-sub">Played</span>
                <span class="telemetry-q-num" id="quickDailyTracks">--</span>
              </div>
            </div>
            <span class="telemetry-q-more">↗</span>
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
          <button class="segment-btn" onclick="switchTab('soundboard')">
            <svg class="icon-svg" style="width:15px;height:15px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>
            <span>Sounds</span>
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
          <!-- Active Library Banner -->
          <div class="ui-card" style="margin-bottom:14px; position:relative; overflow:hidden;">
            <div class="active-col-banner" id="activeColBanner">
              <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                <div style="display:flex; align-items:center; gap:12px;">
                  <div class="active-col-icon-wrap" id="activeColIcon">
                    <svg class="icon-svg" style="width:20px;height:20px;color:var(--accent);" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
                  </div>
                  <div>
                    <div style="display:flex; align-items:center; gap:8px;">
                      <span style="font-size:0.7rem; font-weight:700; letter-spacing:0.06em; color:var(--accent); text-transform:uppercase;">Active Collection</span>
                      <span class="btn-badge" id="activeColTrackCount" style="font-size:0.68rem; padding:2px 7px;">3,881 tracks</span>
                    </div>
                    <div id="activeColName" style="font-size:1.05rem; font-weight:700; color:#fff; margin-top:2px;">All Music (Full Archive)</div>
                  </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                  <button class="btn-kinetic btn-primary" onclick="playSelectedCollection(true)" title="Shuffle & play active collection on Discord">
                    <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
                    <span>Shuffle & Play</span>
                  </button>
                  <button class="btn-kinetic" onclick="loadCategories()" title="Refresh collections">
                    <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Collections Grid Card -->
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
                Juice WRLD Vault Collections
              </span>
              <span style="font-size:0.74rem; color:var(--text-sub);">8 Archives Available</span>
            </div>
            <div class="grid-categories" id="catGrid">
              <!-- Populated dynamically by loadCategories() -->
            </div>
          </div>

          <!-- Collection Track Browser Card -->
          <div class="ui-card" id="colBrowserCard">
            <div class="section-header" style="flex-wrap:wrap; gap:10px;">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                Browse Collection: <span id="colBrowserLabel" style="color:var(--accent);">All Music</span>
              </span>
              <div style="display:flex; align-items:center; gap:8px;">
                <span id="colBrowserCountBadge" style="font-size:0.72rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub);">Loading tracks…</span>
              </div>
            </div>
            <div class="search-input-group" style="margin-bottom:12px;">
              <svg class="icon-svg" style="color:var(--text-sub); width:15px; height:15px;" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="search-field" id="colSearchInput" placeholder="Filter songs in this collection…" oninput="filterCollectionTracks()">
            </div>
            <div class="track-list" id="colTracksList">
              <div class="track-card" style="color:var(--text-sub); font-size:0.8rem;">Select a collection above to browse tracks.</div>
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

          <!-- Telemetry & Daily Usage Full Card -->
          <div class="ui-card" style="margin-bottom:14px; position:relative; overflow:hidden;">
            <div style="position:absolute; top:-40px; right:-40px; width:120px; height:120px; background:radial-gradient(circle, var(--accent-glow) 0%, transparent 70%); pointer-events:none; border-radius:50%; filter:blur(24px);"></div>
            <div class="section-header" style="margin-bottom:12px;">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                Website Traffic &amp; Daily Usage
              </span>
              <span class="telemetry-live-pill"><span class="pulse-ring"></span>LIVE SYNC</span>
            </div>
            <p style="font-size: 0.78rem; color: var(--text-sub); margin-bottom: 14px; line-height: 1.45;">
              Real-time telemetry showing remote visits, unique daily visitors, and 24/7 Discord audio streaming duration.
            </p>

            <div class="telemetry-grid">
              <div class="telemetry-card">
                <div class="t-card-header">
                  <span class="t-card-title">Total Views</span>
                  <span class="t-card-icon purple"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></span>
                </div>
                <div class="t-card-val" id="cardTotalViews">--</div>
                <div class="t-card-footer">
                  <span class="t-tag purple">All-Time</span>
                  <span class="t-sub" id="cardSessionsNow">-- active</span>
                </div>
              </div>

              <div class="telemetry-card highlight-card">
                <div class="t-card-header">
                  <span class="t-card-title">Today's Visits</span>
                  <span class="t-card-icon pink"><svg viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg></span>
                </div>
                <div class="t-card-val accent-val" id="cardDailyViews">--</div>
                <div class="t-card-footer">
                  <span class="t-tag pink">Daily Traffic</span>
                  <span class="t-sub"><span id="cardUniqueViews">--</span> unique</span>
                </div>
              </div>

              <div class="telemetry-card">
                <div class="t-card-header">
                  <span class="t-card-title">Stream Time Today</span>
                  <span class="t-card-icon blue"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></span>
                </div>
                <div class="t-card-val" id="cardDailyTime">--</div>
                <div class="t-card-footer">
                  <span class="t-tag blue">Discord Audio</span>
                  <span class="t-sub" id="cardAllTimeTime">-- total</span>
                </div>
              </div>

              <div class="telemetry-card">
                <div class="t-card-header">
                  <span class="t-card-title">Songs Played Today</span>
                  <span class="t-card-icon green"><svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></span>
                </div>
                <div class="t-card-val" id="cardDailyTracks">--</div>
                <div class="t-card-footer">
                  <span class="t-tag green"><span id="cardDailyReqs">--</span> queued</span>
                  <span class="t-sub" id="cardAllTimeTracks">-- total</span>
                </div>
              </div>
            </div>

            <!-- Activity Pulse Bar -->
            <div class="telemetry-activity-section" style="margin-top:14px;">
              <div class="t-act-header">
                <span class="t-act-title">24h System Activity &amp; Hourly Distribution</span>
                <span class="t-act-status" id="cardLastUpdated">Updated live</span>
              </div>
              <div class="activity-bars-grid" id="cardActivityBars"></div>
              <div class="activity-bars-legend">
                <span>00:00 UTC</span>
                <span>Peak Streaming</span>
                <span>Current Hour</span>
              </div>
            </div>
          </div>

          <div class="ui-card">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                Host Connection & Credits
              </span>
            </div>
            <div style="font-size: 0.78rem; font-family:'JetBrains Mono',monospace; color: var(--text-muted); display:flex; flex-direction:column; gap:6px;">
              <div>Guild: <span id="guildName" style="color:#fff;">--</span></div>
              <div>Voice: <span id="vcName" style="color:#fff;">--</span></div>
              <div>Protocol: <span id="protocolName" style="color:var(--accent);">--</span></div>
              <div>Auth Token: <code id="tokenDisplay" style="color:var(--accent);">--</code></div>
            </div>
            <div style="margin-top:10px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); font-size:0.75rem; color:var(--text-sub); display:flex; flex-direction:column; gap:6px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>Bot Developer:</span>
                <a href="https://sosocial.lol/ski" target="_blank" rel="noopener" class="credit-author">SKIZZOO ↗</a>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>Domain Provider:</span>
                <a href="https://sosocial.lol/spinti" target="_blank" rel="noopener" class="credit-partner">Spinti ↗</a>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB: SOUNDBOARD -->
        <div class="tab-content" id="tab-soundboard">
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="section-header" style="flex-wrap:wrap; gap:10px;">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>
                Meme Soundboard
                <span style="font-size:0.7rem; font-weight:600; padding:2px 8px; border-radius:10px; background:rgba(235,47,150,0.15); color:var(--accent); margin-left:6px;">50 Sounds</span>
              </span>
              <div style="display:flex; gap:8px; align-items:center;">
                <button class="btn-kinetic btn-badge" id="sbStopBtn" style="display:none; background:var(--danger); color:#fff; font-weight:600;" onclick="stopSoundboard()">
                  <svg class="icon-svg" style="width:12px; height:12px; margin-right:4px;" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
                  Stop Sound
                </button>
              </div>
            </div>

            <p style="font-size:0.78rem; color:var(--text-sub); margin-bottom:12px; line-height:1.45;">
              Tap any sound to pause current music and broadcast on Discord voice. The song resumes automatically right where it left off when the sound ends.
            </p>

            <!-- Search and Controls Filter -->
            <div style="display:flex; flex-direction:column; gap:10px; margin-bottom:14px;">
              <div class="search-input-group">
                <svg class="icon-svg" style="color:var(--text-sub);" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" class="search-field" id="soundboardSearch" placeholder="Filter 50 meme sounds (e.g. Vine Boom, Bruh, Sad Violin)…" oninput="filterSoundboard()">
                <button class="btn-kinetic btn-badge" onclick="clearSoundboardFilter()">Clear</button>
              </div>

              <!-- Options Bar -->
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-size:0.75rem; color:var(--text-sub);">
                <label style="display:flex; align-items:center; gap:6px; cursor:pointer; user-select:none;">
                  <input type="checkbox" id="sbPreviewToggle" checked style="accent-color:var(--accent);">
                  <span>Play audio preview locally in browser too</span>
                </label>
                <span id="sbFilteredCount" style="font-family:'JetBrains Mono',monospace;">50 sounds</span>
              </div>
            </div>

            <!-- Active Sound Playing Banner -->
            <div id="sbActiveBanner" style="display:none; background:linear-gradient(135deg, rgba(235,47,150,0.14), rgba(114,46,209,0.12)); border:1px solid rgba(235,47,150,0.35); border-radius:10px; padding:10px 14px; margin-bottom:14px; align-items:center; justify-content:space-between;">
              <div style="display:flex; align-items:center; gap:10px;">
                <div class="equalizer-bars" style="height:14px; gap:2px;">
                  <span class="bar" style="background:var(--accent); animation-duration:0.6s;"></span>
                  <span class="bar" style="background:var(--accent); animation-duration:0.9s;"></span>
                  <span class="bar" style="background:var(--accent); animation-duration:0.7s;"></span>
                </div>
                <div>
                  <div style="font-size:0.68rem; text-transform:uppercase; color:var(--accent); font-weight:700;">Live Soundboard</div>
                  <div id="sbActiveName" style="font-size:0.85rem; font-weight:700; color:var(--text-main);">Sound Name</div>
                </div>
              </div>
              <button class="btn-kinetic btn-flat" style="padding:4px 8px; font-size:0.72rem; color:var(--danger);" onclick="stopSoundboard()">Resume Song</button>
            </div>

            <!-- Soundboard Grid -->
            <div id="soundboardGrid" class="soundboard-grid">
              <div style="color:var(--text-sub); font-size:0.8rem; padding:12px;">Loading soundboard…</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Credits -->
    <footer class="app-footer">
      <div class="footer-credit">
        <span>Bot crafted by <a href="https://sosocial.lol/ski" target="_blank" rel="noopener" class="credit-author">SKIZZOO</a></span>
        <span class="footer-sep">•</span>
        <span>Domain provided by <a href="https://sosocial.lol/spinti" target="_blank" rel="noopener" class="credit-partner">Spinti</a></span>
      </div>
      <div class="footer-sub">
        JuiceVault 24/7 Music Player &amp; Mobile Web Remote
      </div>
    </footer>
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
    <button class="nav-btn" onclick="switchMobileNav('soundboard')">
      <svg class="icon-svg" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>
      <span>Sounds</span>
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

  <!-- Lyrics Options Sheet (Send in Channel / Give Me Link) -->
  <div class="sheet-backdrop" id="lyricsSheet" onclick="if(event.target===this) closeLyricsModal()">
    <div class="sheet-panel">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:12px; min-width:0;">
          <div class="cat-icon-badge" style="width:38px; height:38px; border-radius:10px; background:var(--accent-muted); border-color:var(--border-accent); color:var(--accent);">
            <svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
          </div>
          <div style="min-width:0;">
            <div id="lyricsModalTitle" style="font-weight:700; font-size:0.95rem; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">Lyrics Options</div>
            <div id="lyricsModalDesc" style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">Choose an option for the lyrics</div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeLyricsModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div style="display:flex; flex-direction:column; gap:12px;">
        <!-- Option 1: Send in a Discord Channel -->
        <div class="ui-card" style="padding:14px; background:var(--surface); border:1px solid var(--border);">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <svg class="icon-svg" style="width:16px;height:16px;color:var(--accent);" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
            <span style="font-weight:700; font-size:0.88rem; color:#fff;">Option 1: Send in a Channel</span>
          </div>
          <p style="font-size:0.74rem; color:var(--text-sub); margin-bottom:10px;">Select which Discord text channel to post the lyrics into:</p>
          <div style="display:flex; gap:8px; align-items:center;">
            <select id="lyricsChannelSelect" style="flex:1; background:#0d0d12; color:#fff; border:1px solid var(--border); border-radius:var(--radius-md); padding:8px 12px; font-size:0.82rem; font-family:inherit; outline:none;">
              <option value="">Loading channels…</option>
            </select>
            <button class="btn-kinetic btn-primary" onclick="sendLyricsToSelectedChannel()" style="padding:8px 14px; white-space:nowrap;">
              <span>Send Lyrics</span>
            </button>
          </div>
        </div>

        <!-- Option 2: Give Me the Link -->
        <div class="ui-card" style="padding:14px; background:var(--surface); border:1px solid var(--border);">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <svg class="icon-svg" style="width:16px;height:16px;color:var(--accent);" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <span style="font-weight:700; font-size:0.88rem; color:#fff;">Option 2: Give Me the Link</span>
          </div>
          <p style="font-size:0.74rem; color:var(--text-sub); margin-bottom:10px;">Open the official Genius lyrics page for this track:</p>
          <div style="display:flex; gap:8px;">
            <button class="btn-kinetic btn-badge" id="btnGeniusLink" onclick="openGeniusDirectLink()" style="flex:1; justify-content:center; padding:10px 14px; font-size:0.82rem;">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              <span>Open on Genius</span>
            </button>
            <button class="btn-kinetic btn-badge" onclick="copyGeniusLink()" style="padding:10px 12px;" title="Copy link to clipboard">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            </button>
          </div>
        </div>

        <!-- Lyrics In-Player Preview Box -->
        <div class="ui-card" id="lyricsPreviewBox" style="padding:14px; background:#0a0a0f; border:1px solid rgba(255,255,255,0.06); max-height:220px; overflow-y:auto; display:none;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:0.72rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:0.04em;">Lyrics Preview</span>
            <span id="lyricsSourceBadge" style="font-size:0.65rem; color:var(--text-sub); font-family:'JetBrains Mono',monospace;">Genius</span>
          </div>
          <pre id="lyricsPreviewText" style="font-family:inherit; font-size:0.8rem; color:var(--text-muted); line-height:1.5; white-space:pre-wrap; margin:0;"></pre>
        </div>
      </div>
    </div>
  </div>

  <!-- Live Telemetry & Daily Usage Full Modal Sheet -->
  <div class="sheet-backdrop" id="statsSheet" onclick="if(event.target===this) closeStatsModal()">
    <div class="sheet-panel" style="max-width:560px;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:12px;">
          <div class="brand-logo-disc" style="width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg, var(--accent), #7928ca); box-shadow:0 0 18px var(--accent-glow);">
            <svg class="icon-svg fill-current" viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          </div>
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="font-weight:800; font-size:1.02rem; color:#fff;">Live Telemetry &amp; Daily Usage</div>
              <span class="telemetry-live-pill"><span class="pulse-ring"></span>LIVE</span>
            </div>
            <div style="font-size:0.74rem; color:var(--text-sub); margin-top:2px;">
              Real-time web traffic, unique visitors &amp; 24/7 stream statistics
            </div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeStatsModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div class="telemetry-grid">
        <div class="telemetry-card">
          <div class="t-card-header">
            <span class="t-card-title">Total Views</span>
            <span class="t-card-icon purple"><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></span>
          </div>
          <div class="t-card-val" id="statsTotalViews">--</div>
          <div class="t-card-footer">
            <span class="t-tag purple">All-Time</span>
            <span class="t-sub" id="statsSessionsNow">-- active</span>
          </div>
        </div>

        <div class="telemetry-card highlight-card">
          <div class="t-card-header">
            <span class="t-card-title">Today's Visits</span>
            <span class="t-card-icon pink"><svg viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg></span>
          </div>
          <div class="t-card-val accent-val" id="statsDailyViews">--</div>
          <div class="t-card-footer">
            <span class="t-tag pink">Daily Traffic</span>
            <span class="t-sub"><span id="statsUniqueViews">--</span> unique</span>
          </div>
        </div>

        <div class="telemetry-card">
          <div class="t-card-header">
            <span class="t-card-title">Stream Time Today</span>
            <span class="t-card-icon blue"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></span>
          </div>
          <div class="t-card-val" id="statsDailyTime">--</div>
          <div class="t-card-footer">
            <span class="t-tag blue">Discord Audio</span>
            <span class="t-sub" id="statsAllTimeTime">-- total</span>
          </div>
        </div>

        <div class="telemetry-card">
          <div class="t-card-header">
            <span class="t-card-title">Songs Played Today</span>
            <span class="t-card-icon green"><svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></span>
          </div>
          <div class="t-card-val" id="statsDailyTracks">--</div>
          <div class="t-card-footer">
            <span class="t-tag green"><span id="statsDailyReqs">--</span> queued</span>
            <span class="t-sub" id="statsAllTimeTracks">-- total</span>
          </div>
        </div>
      </div>

      <!-- Activity Pulse Section -->
      <div class="telemetry-activity-section">
        <div class="t-act-header">
          <span class="t-act-title">24h System Activity &amp; Hourly Heat</span>
          <span class="t-act-status" id="statsLastUpdated">Updated live</span>
        </div>
        <div class="activity-bars-grid" id="statsActivityBars"></div>
        <div class="activity-bars-legend">
          <span>00:00 UTC</span>
          <span>Peak Usage</span>
          <span>Current Hour</span>
        </div>
      </div>

      <!-- Breakdown Details Card -->
      <div class="telemetry-breakdown-card">
        <div class="t-detail-row">
          <span class="t-detail-label">Active Remote Listeners / Sessions:</span>
          <span class="t-detail-value"><span class="status-dot"></span> <span id="statsWsCount">1</span> active now</span>
        </div>
        <div class="t-detail-row">
          <span class="t-detail-label">Remote Commands Executed Today:</span>
          <span class="t-detail-value" id="statsDailyActions">--</span>
        </div>
        <div class="t-detail-row">
          <span class="t-detail-label">All-Time Remote Actions:</span>
          <span class="t-detail-value" id="statsAllTimeActions">--</span>
        </div>
        <div class="t-detail-row">
          <span class="t-detail-label">Live Domain:</span>
          <span class="t-detail-value" style="color:var(--accent);">remote.juicevault.space</span>
        </div>
      </div>

      <button class="btn-kinetic btn-flat" style="padding:12px; margin-top:14px; width:100%; justify-content:center;" onclick="closeStatsModal()">
        Close
      </button>
    </div>
  </div>

  <audio id="liveAudio" preload="auto" playsinline style="display:none;"></audio>
  <audio id="silentAudio" preload="auto" playsinline loop style="display:none;"></audio>

  <script>
    // Silent carrier audio for mobile lock screen background playback controls
    const SILENT_AUDIO_URI = 'data:audio/wav;base64,UklGRiwAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQgAAACAgICAgICAgA==';
    let lockScreenControlsEnabled = true;
    let mediaSessionConfigured = false;
    let wsReconnectTimer = null;

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
    let lastQueueChecksum = '';
    let currentQueueData = { requested: [], upcoming: [] };
    let currentSearchResults = [];
    let isScrubbing = false;
    let currentTrackKey = '';
    let lastTickTime = performance.now();
    let isAudioLoading = false;
    let audioRetryTimer = null;

    function getTrackKey(t) {
      if (!t) return '';
      return String(t.id || t.title || 'track');
    }

    function escapeHtml(str) {
      return String(str || '').replace(/[&<>"']/g, function(m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
      });
    }

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
      const idx = ['queue', 'search', 'categories', 'soundboard', 'shortcuts'].indexOf(tabId);
      if (idx !== -1) {
        const btns = document.querySelectorAll('.segment-bar.desktop-segment .segment-btn');
        if (btns[idx]) btns[idx].classList.add('active');
      }
      if (tabId === 'queue') loadQueue();
      if (tabId === 'categories') loadCategories();
      if (tabId === 'soundboard') loadSoundboard();
      if (tabId === 'shortcuts') renderShortcuts();
      if (navigator.vibrate) navigator.vibrate(8);
    }

    function switchMobileNav(tabId) {
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      const idx = ['player', 'queue', 'search', 'categories', 'soundboard', 'shortcuts'].indexOf(tabId);
      if (idx !== -1) {
        const btns = document.querySelectorAll('.nav-btn');
        if (btns[idx]) btns[idx].classList.add('active');
      }

      const playerWrap = document.querySelector('.card-player-wrap');
      const contentWrap = document.querySelector('.card-content-wrap');

      if (window.innerWidth < 860) {
        if (tabId === 'player') {
          if (playerWrap) playerWrap.style.display = 'block';
          if (contentWrap) contentWrap.style.display = 'none';
        } else {
          if (playerWrap) playerWrap.style.display = 'none';
          if (contentWrap) contentWrap.style.display = 'block';
          if (tabId === 'queue') lastQueueChecksum = '';
          switchTab(tabId);
        }
      } else {
        if (tabId === 'queue') lastQueueChecksum = '';
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

    // Scrubber interaction with full pointer tracking (touch & mouse)
    const progressBar = document.getElementById('progressBar');

    function getScrubTarget(e) {
      if (!durationSeconds || durationSeconds <= 0) return 0;
      const rect = progressBar.getBoundingClientRect();
      const clientX = e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      return ratio * durationSeconds;
    }

    progressBar.addEventListener('pointerdown', (e) => {
      if (!durationSeconds || durationSeconds <= 0) return;
      isScrubbing = true;
      try { progressBar.setPointerCapture(e.pointerId); } catch (_) {}
      currentElapsed = getScrubTarget(e);
      updateScrubberUI();
    });

    progressBar.addEventListener('pointermove', (e) => {
      if (isScrubbing) {
        currentElapsed = getScrubTarget(e);
        updateScrubberUI();
      }
    });

    const endScrub = (e) => {
      if (isScrubbing) {
        isScrubbing = false;
        try { progressBar.releasePointerCapture(e.pointerId); } catch (_) {}
        const target = getScrubTarget(e);
        currentElapsed = target;
        updateScrubberUI();
        action('seek_to', { position: target });
      }
    };

    progressBar.addEventListener('pointerup', endScrub);
    progressBar.addEventListener('pointercancel', () => { isScrubbing = false; });

    async function action(name, payload = {}) {
      if (navigator.vibrate) navigator.vibrate(10);
      armBackgroundMediaSession();

      // Instant optimistic UI updates for sub-millisecond perceived responsiveness
      if (name === 'toggle') {
        if (currentState) {
          currentState.is_playing = !currentState.is_playing;
          const playIcon = document.getElementById('playIconSvg');
          const coverImg = document.getElementById('coverImg');
          const soundwave = document.getElementById('soundwaveBox');
          if (currentState.is_playing) {
            if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
            if (coverImg) coverImg.classList.add('playing');
            if (soundwave) soundwave.classList.add('playing');
          } else {
            if (playIcon) playIcon.innerHTML = '<polygon points="6 3 20 12 6 21 6 3"/>';
            if (coverImg) coverImg.classList.remove('playing');
            if (soundwave) soundwave.classList.remove('playing');
          }
          syncLiveAudio();
          updateMediaSession();
        }
      } else if (name === 'play') {
        if (currentState) {
          currentState.is_playing = true;
          const playIcon = document.getElementById('playIconSvg');
          const coverImg = document.getElementById('coverImg');
          const soundwave = document.getElementById('soundwaveBox');
          if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
          if (coverImg) coverImg.classList.add('playing');
          if (soundwave) soundwave.classList.add('playing');
          syncLiveAudio();
          updateMediaSession();
        }
      } else if (name === 'pause') {
        if (currentState) {
          currentState.is_playing = false;
          const playIcon = document.getElementById('playIconSvg');
          const coverImg = document.getElementById('coverImg');
          const soundwave = document.getElementById('soundwaveBox');
          if (playIcon) playIcon.innerHTML = '<polygon points="6 3 20 12 6 21 6 3"/>';
          if (coverImg) coverImg.classList.remove('playing');
          if (soundwave) soundwave.classList.remove('playing');
          syncLiveAudio();
          updateMediaSession();
        }
      } else if (name === 'seek') {
        const delta = payload.delta || 0;
        currentElapsed = Math.max(0, Math.min(durationSeconds, currentElapsed + delta));
        updateScrubberUI();
        updateMediaSession();
        if (liveStreamActive) {
          const a = document.getElementById('liveAudio');
          if (a) {
            try { a.currentTime = currentElapsed; } catch (e) {}
          }
        }
      } else if (name === 'seek_to') {
        currentElapsed = Math.max(0, Math.min(durationSeconds, payload.position || 0));
        updateScrubberUI();
        updateMediaSession();
        if (liveStreamActive) {
          const a = document.getElementById('liveAudio');
          if (a) {
            try { a.currentTime = currentElapsed; } catch (e) {}
          }
        }
      } else if (name === 'set_eq') {
        const effectName = payload.effect || 'none';
        if (currentState) {
          currentState.effect = effectName;
        }
        const eqBadge = document.getElementById('eqBadge');
        if (eqBadge) eqBadge.innerText = effectName.toUpperCase();
        applyLiveEQ(effectName);
      } else if (name === 'skip') {
        showToast('Skipping track…');
        if (liveStreamActive) {
          const a = document.getElementById('liveAudio');
          if (a && !a.paused) a.pause();
        }
        const nextTrack = (currentQueueData.requested && currentQueueData.requested.length > 0)
          ? currentQueueData.requested[0]
          : (currentQueueData.upcoming && currentQueueData.upcoming.length > 0 ? currentQueueData.upcoming[0] : null);
        if (nextTrack) {
          document.getElementById('trackTitle').innerText = nextTrack.title || 'Buffering archive…';
          document.getElementById('trackArtist').innerText = nextTrack.artist || 'Juice WRLD';
        } else {
          document.getElementById('trackTitle').innerText = 'Buffering next track…';
        }
        currentElapsed = 0;
        updateScrubberUI();
      } else if (name === 'previous') {
        showToast('Playing previous track…');
        if (liveStreamActive) {
          const a = document.getElementById('liveAudio');
          if (a && !a.paused) a.pause();
        }
        document.getElementById('trackTitle').innerText = 'Loading previous track…';
        currentElapsed = 0;
        updateScrubberUI();
      } else if (name === 'shuffle') {
        showToast('Queue shuffled');
      } else if (name === 'repeat') {
        const repeatBtn = document.getElementById('btnRepeat');
        if (repeatBtn) repeatBtn.classList.toggle('active');
      }

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: name, ...payload }));
        return;
      }
      try {
        const endpoint = (name === 'set_eq') ? 'eq' : name;
        const res = await fetch(`/api/playback/${endpoint}?token=${encodeURIComponent(token)}`, {
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
    let audioCtx = null;
    let audioSourceNode = null;
    let bassFilterNode = null;
    let subFilterNode = null;
    let stereoPannerNode = null;
    let delayNode = null;
    let delayFeedbackNode = null;
    let delayGainNode = null;
    let masterGainNode = null;
    let pannerAnimFrame = null;
    let pannerAngle = 0;

    function initWebAudio() {
      if (audioCtx) {
        if (audioCtx.state === 'suspended') {
          audioCtx.resume().catch(() => {});
        }
        return;
      }
      try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return;
        audioCtx = new AudioContextClass();
        const audio = document.getElementById('liveAudio');
        if (!audio) return;
        audioSourceNode = audioCtx.createMediaElementSource(audio);

        // 1. Bass filter (lowshelf at 110Hz)
        bassFilterNode = audioCtx.createBiquadFilter();
        bassFilterNode.type = 'lowshelf';
        bassFilterNode.frequency.value = 110;
        bassFilterNode.gain.value = 0;

        // 2. Sub-bass filter (peaking at 55Hz)
        subFilterNode = audioCtx.createBiquadFilter();
        subFilterNode.type = 'peaking';
        subFilterNode.frequency.value = 55;
        subFilterNode.Q.value = 1.0;
        subFilterNode.gain.value = 0;

        // 3. Stereo Panner Node (for 8D spatial audio)
        if (audioCtx.createStereoPanner) {
          stereoPannerNode = audioCtx.createStereoPanner();
        }

        // 4. Delay / Echo Node
        delayNode = audioCtx.createDelay(1.0);
        delayNode.delayTime.value = 0.25;
        delayFeedbackNode = audioCtx.createGain();
        delayFeedbackNode.gain.value = 0.35;
        delayGainNode = audioCtx.createGain();
        delayGainNode.gain.value = 0;

        // Feedback loop
        delayNode.connect(delayFeedbackNode);
        delayFeedbackNode.connect(delayNode);
        delayNode.connect(delayGainNode);

        // 5. Master Gain Node (for accurate hardware volume control)
        masterGainNode = audioCtx.createGain();
        const curVol = parseFloat(document.getElementById('liveVolumeSlider')?.value || 1);
        masterGainNode.gain.value = curVol;

        // Audio graph routing:
        // audioSourceNode -> bassFilterNode -> subFilterNode -> (stereoPanner or direct) -> masterGainNode -> destination
        let lastNode = audioSourceNode;
        lastNode.connect(bassFilterNode);
        lastNode = bassFilterNode;
        lastNode.connect(subFilterNode);
        lastNode = subFilterNode;

        if (stereoPannerNode) {
          lastNode.connect(stereoPannerNode);
          lastNode = stereoPannerNode;
        }

        lastNode.connect(masterGainNode);
        lastNode.connect(delayNode);
        delayGainNode.connect(masterGainNode);

        masterGainNode.connect(audioCtx.destination);
      } catch (err) {
        console.warn('Web Audio API initialization failed:', err);
      }
    }

    function applyLiveEQ(effect) {
      const eff = String(effect || (currentState && currentState.effect) || 'none').toLowerCase().replace(/[-_]/g, ' ').trim();
      const audio = document.getElementById('liveAudio');
      if (!audio) return;

      initWebAudio();

      // Reset speed & pitch
      audio.playbackRate = 1.0;
      if ('preservesPitch' in audio) audio.preservesPitch = true;
      if ('mozPreservesPitch' in audio) audio.mozPreservesPitch = true;
      if ('webkitPreservesPitch' in audio) audio.webkitPreservesPitch = true;

      if (pannerAnimFrame) {
        cancelAnimationFrame(pannerAnimFrame);
        pannerAnimFrame = null;
      }
      if (stereoPannerNode) {
        stereoPannerNode.pan.value = 0;
      }

      if (bassFilterNode) bassFilterNode.gain.value = 0;
      if (subFilterNode) subFilterNode.gain.value = 0;
      if (delayGainNode) delayGainNode.gain.value = 0;

      if (eff.includes('night')) {
        audio.preservesPitch = false;
        audio.mozPreservesPitch = false;
        audio.webkitPreservesPitch = false;
        audio.playbackRate = 1.22;
      } else if (eff.includes('slow')) {
        audio.preservesPitch = false;
        audio.mozPreservesPitch = false;
        audio.webkitPreservesPitch = false;
        audio.playbackRate = 0.86;
      } else if (eff.includes('virtual') || eff.includes('sub')) {
        if (bassFilterNode) bassFilterNode.gain.value = 16;
        if (subFilterNode) subFilterNode.gain.value = 10;
      } else if (eff.includes('8d')) {
        if (bassFilterNode) bassFilterNode.gain.value = 4;
        if (stereoPannerNode) {
          const run8D = () => {
            if (!liveStreamActive) return;
            pannerAngle += 0.025;
            stereoPannerNode.pan.value = Math.sin(pannerAngle) * 0.95;
            pannerAnimFrame = requestAnimationFrame(run8D);
          };
          run8D();
        }
      } else if (eff.includes('echo') || eff.includes('reverb')) {
        if (delayGainNode) delayGainNode.gain.value = 0.45;
      } else if (eff.includes('wide') || eff.includes('stereo')) {
        if (bassFilterNode) bassFilterNode.gain.value = 3;
        if (delayGainNode) delayGainNode.gain.value = 0.18;
      } else if (eff.includes('bass')) {
        if (bassFilterNode) bassFilterNode.gain.value = 11;
        if (subFilterNode) subFilterNode.gain.value = 4;
      }
    }

    function armBackgroundMediaSession() {
      setupMediaSession();
      if (!lockScreenControlsEnabled || liveStreamActive) return;
      const silent = document.getElementById('silentAudio');
      if (silent) {
        if (!silent.src || !silent.src.startsWith('data:audio')) {
          silent.src = SILENT_AUDIO_URI;
        }
        if (currentState && currentState.is_playing && silent.paused) {
          silent.play().catch(() => {});
        }
      }
    }

    function toggleLockScreenControls() {
      lockScreenControlsEnabled = !lockScreenControlsEnabled;
      const btn = document.getElementById('btnLockScreen');
      const label = document.getElementById('lockScreenBtnLabel');
      if (lockScreenControlsEnabled) {
        if (btn) btn.classList.add('active');
        if (label) label.innerText = 'Lock Controls: ON';
        armBackgroundMediaSession();
        showToast('Lock screen media controls enabled');
      } else {
        if (btn) btn.classList.remove('active');
        if (label) label.innerText = 'Lock Controls: OFF';
        const silent = document.getElementById('silentAudio');
        if (silent) silent.pause();
        showToast('Lock screen controls disabled');
      }
    }

    let liveSyncInterval = null;

    function toggleLiveAudio() {
      const audio = document.getElementById('liveAudio');
      liveStreamActive = !liveStreamActive;
      const btn = document.getElementById('btnListenLive');
      const controls = document.getElementById('liveAudioControls');
      const title = document.getElementById('liveStatusTitle');
      const badge = document.getElementById('liveSyncBadge');

      if (liveStreamActive) {
        initWebAudio();
        const silent = document.getElementById('silentAudio');
        if (silent) silent.pause();
        btn.classList.add('active');
        btn.innerHTML = '<span>Stop Listening</span>';
        controls.style.display = 'flex';
        title.innerText = 'Listen Together: Active';
        if (badge) badge.innerText = '1:1 Sync';
        syncLiveAudio(true);
        setupMediaSession();
        if (liveSyncInterval) clearInterval(liveSyncInterval);
        liveSyncInterval = setInterval(() => {
          if (liveStreamActive) syncLiveAudio(false);
        }, 250);
        showToast('Listen Together: 1:1 sync connected');
      } else {
        if (liveSyncInterval) {
          clearInterval(liveSyncInterval);
          liveSyncInterval = null;
        }
        if (pannerAnimFrame) {
          cancelAnimationFrame(pannerAnimFrame);
          pannerAnimFrame = null;
        }
        audio.pause();
        audio.removeAttribute('src');
        btn.classList.remove('active');
        btn.innerHTML = '<span>Listen Together</span>';
        controls.style.display = 'none';
        title.innerText = 'Listen Together';
        if (badge) badge.innerText = '1:1 Sync';
        currentLiveTrackId = null;
        isAudioLoading = false;
        if (audioRetryTimer) {
          clearTimeout(audioRetryTimer);
          audioRetryTimer = null;
        }
        if (lockScreenControlsEnabled) {
          armBackgroundMediaSession();
        }
        showToast('Listen Together disconnected');
      }
    }

    function updateLiveVolume(val) {
      const v = parseFloat(val);
      const audio = document.getElementById('liveAudio');
      if (audio) audio.volume = v;
      if (masterGainNode) masterGainNode.gain.value = v;
      const pctEl = document.getElementById('liveVolPercent');
      if (pctEl) pctEl.innerText = `${Math.round(v * 100)}%`;
    }

    function syncLiveAudio(force = false) {
      if (!liveStreamActive || !currentState) return;
      const audio = document.getElementById('liveAudio');
      if (!audio) return;
      const t = currentState.track;

      if (!t || !currentState.is_running) {
        if (!audio.paused) audio.pause();
        return;
      }

      const eff = String(currentState.effect || '').toLowerCase();
      const speed = (t && t.effect_speed) || (eff.includes('night') ? 1.22 : (eff.includes('slow') ? 0.86 : 1.0));
      const trackKey = getTrackKey(t);

      if (force || currentLiveTrackId !== trackKey) {
        currentLiveTrackId = trackKey;
        isAudioLoading = true;
        if (audioRetryTimer) {
          clearTimeout(audioRetryTimer);
          audioRetryTimer = null;
        }

        const gid = (currentState && currentState.guild && currentState.guild.id) ? currentState.guild.id : '';
        const streamUrl = `/api/stream?token=${encodeURIComponent(token)}&guild_id=${encodeURIComponent(gid)}&t=${encodeURIComponent(trackKey)}`;
        
        audio.src = streamUrl;
        audio.load();

        audio.onerror = () => {
          if (!liveStreamActive || !currentState || !currentState.is_playing) return;
          console.warn('Live audio stream error, auto-retrying in 1s...');
          if (audioRetryTimer) clearTimeout(audioRetryTimer);
          audioRetryTimer = setTimeout(() => {
            if (liveStreamActive && currentState && currentState.is_playing) {
              syncLiveAudio(true);
            }
          }, 1000);
        };

        const onCanPlay = () => {
          isAudioLoading = false;
          try {
            if (currentElapsed > 0.05) {
              audio.currentTime = currentElapsed;
            }
          } catch (e) {}
          applyLiveEQ(currentState.effect);
          if (currentState && currentState.is_playing) {
            audio.play().catch(e => console.log('Live playback play error:', e));
          }
        };
        audio.addEventListener('canplay', onCanPlay, { once: true });
        return;
      }

      if (isAudioLoading) return;

      applyLiveEQ(currentState.effect);

      if (!currentState.is_playing) {
        if (!audio.paused) audio.pause();
        return;
      }

      if (audio.paused && currentState.is_playing) {
        try {
          if (Math.abs(audio.currentTime - currentElapsed) > 0.3) {
            audio.currentTime = Math.max(0, currentElapsed);
          }
        } catch (e) {}
        audio.play().catch(() => {});
      }

      // High-precision 1:1 Phase-Locked Loop (PLL) clock sync with Discord
      if (!audio.paused && audio.duration > 0) {
        const drift = audio.currentTime - currentElapsed;
        const driftMs = Math.round(drift * 1000);
        const driftLabel = document.getElementById('syncDriftLabel');
        if (driftLabel) {
          driftLabel.innerText = (driftMs >= 0 ? `+${driftMs}ms` : `${driftMs}ms`);
        }

        if (Math.abs(drift) > 0.35) {
          // Large drift (>350ms) -> Hard seek directly to Discord master position
          try { audio.currentTime = Math.max(0, currentElapsed); } catch (e) {}
          audio.playbackRate = speed;
        } else if (Math.abs(drift) > 0.02) {
          // Micro-drift (20ms - 350ms): Proportional rate steering for ultra-smooth, click-free sync
          const steer = Math.min(0.08, Math.max(0.015, Math.abs(drift) * 0.25));
          if (drift < 0) {
            // Audio lagging behind Discord -> accelerate proportionally
            audio.playbackRate = speed * (1 + steer);
          } else {
            // Audio ahead of Discord -> decelerate proportionally
            audio.playbackRate = speed * (1 - steer);
          }
        } else {
          // Locked in exact 1:1 sync (within ±20ms)
          audio.playbackRate = speed;
        }
      }
    }

    function setupMediaSession() {
      if (!('mediaSession' in navigator) || mediaSessionConfigured) return;
      mediaSessionConfigured = true;

      const handlers = [
        ['play', () => action('play')],
        ['pause', () => action('pause')],
        ['previoustrack', () => action('previous')],
        ['nexttrack', () => action('skip')],
        ['seekbackward', (details) => action('seek', { delta: -(details.seekOffset || 10) })],
        ['seekforward', (details) => action('seek', { delta: (details.seekOffset || 10) })],
        ['seekto', (details) => {
          if (details.seekTime != null) {
            action('seek_to', { position: details.seekTime });
          }
        }],
        ['stop', () => action('pause')]
      ];

      for (const [actionName, handler] of handlers) {
        try {
          navigator.mediaSession.setActionHandler(actionName, handler);
        } catch (e) {}
      }
    }

    function updateMediaSession() {
      if (!('mediaSession' in navigator) || !currentState || !currentState.track) return;
      const t = currentState.track;
      navigator.mediaSession.metadata = new MediaMetadata({
        title: t.title || 'Juice WRLD Track',
        artist: t.artist || 'Juice WRLD',
        album: 'JuiceVault • ' + (currentState.category_label || currentState.category || 'Archive'),
        artwork: [
          { src: t.cover_url || 'https://api.juicevault.xyz/favicon.ico', sizes: '512x512', type: 'image/png' },
          { src: t.cover_url || 'https://api.juicevault.xyz/favicon.ico', sizes: '192x192', type: 'image/png' }
        ]
      });
      navigator.mediaSession.playbackState = currentState.is_playing ? 'playing' : 'paused';

      // Keep silent audio loop in sync with playback state for Discord remote lock screen
      if (lockScreenControlsEnabled && !liveStreamActive) {
        const silent = document.getElementById('silentAudio');
        if (silent) {
          if (!silent.src || !silent.src.startsWith('data:audio')) {
            silent.src = SILENT_AUDIO_URI;
          }
          if (currentState.is_playing && silent.paused) {
            silent.play().catch(() => {});
          } else if (!currentState.is_playing && !silent.paused) {
            silent.pause();
          }
        }
      }

      // Update lock screen scrubber position
      if ('setPositionState' in navigator.mediaSession && durationSeconds > 0) {
        try {
          const pos = Math.max(0, Math.min(durationSeconds, currentElapsed));
          navigator.mediaSession.setPositionState({
            duration: durationSeconds,
            playbackRate: currentState.is_playing ? 1.0 : 0.0,
            position: pos
          });
        } catch (e) {}
      }
    }

    function applyState(state) {
      if (!state) return;
      currentState = state;
      try {
        localStorage.setItem('jv_state_cache', JSON.stringify(state));
      } catch (e) {}
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

      if (state.stats) {
        updateTelemetryUI(state.stats);
      }

      const t = state.track;
      const metaBox = document.getElementById('trackMetaContainer');
      const soundwave = document.getElementById('soundwaveBox');

      if (t) {
        document.getElementById('trackTitle').innerText = t.title || 'Untitled';
        document.getElementById('trackArtist').innerText = t.artist || 'Juice WRLD';
        document.getElementById('coverImg').src = t.cover_url || 'https://api.juicevault.xyz/favicon.ico';
        document.getElementById('categoryBadge').innerText = t.is_soundboard ? 'SOUNDBOARD' : ((state.category_label || state.category || 'All').toUpperCase());
        document.getElementById('sourceBadge').innerText = t.is_soundboard ? 'MEME SOUND' : (t.is_external ? (t.source || 'External') : 'JuiceVault');
        document.getElementById('eqBadge').innerText = (state.effect || 'Flat').toUpperCase();

        if (t.is_soundboard) {
          const banner = document.getElementById('sbActiveBanner');
          if (banner) banner.style.display = 'flex';
          const nameEl = document.getElementById('sbActiveName');
          if (nameEl) nameEl.textContent = t.title || 'Meme Sound';
          const stopBtn = document.getElementById('sbStopBtn');
          if (stopBtn) stopBtn.style.display = 'inline-flex';
        } else if (currentSbPlayingId) {
          currentSbPlayingId = null;
          document.querySelectorAll('.sound-pad').forEach(el => el.classList.remove('is-playing'));
          const banner = document.getElementById('sbActiveBanner');
          if (banner) banner.style.display = 'none';
          const stopBtn = document.getElementById('sbStopBtn');
          if (stopBtn) stopBtn.style.display = 'none';
        }

        const trackKey = getTrackKey(t);
        durationSeconds = t.duration_seconds || 0;
        const serverPos = typeof t.position_seconds === 'number' ? t.position_seconds : 0;
        const nowSec = Date.now() / 1000;
        const rttOffset = state.server_timestamp ? Math.max(0, Math.min(1.5, nowSec - state.server_timestamp)) : 0;
        const speed = (t && t.effect_speed) || 1.0;
        const liveDiscordPos = serverPos + (state.is_playing ? rttOffset * speed : 0);

        if (trackKey !== currentTrackKey) {
          currentTrackKey = trackKey;
          currentElapsed = liveDiscordPos;
        } else if (!isScrubbing) {
          if (Math.abs(currentElapsed - liveDiscordPos) > 0.35) {
            currentElapsed = liveDiscordPos;
          }
        }
        document.getElementById('timeDuration').innerText = t.length || formatTime(durationSeconds);
        updateScrubberUI();
      } else {
        currentTrackKey = '';
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
      applyLiveEQ(state.effect);
      const qTab = document.getElementById('tab-queue');
      const actionSheet = document.getElementById('trackActionSheet');
      const isModalOpen = actionSheet && actionSheet.classList.contains('active');
      const queueKey = `${state.requested_size || 0}_${state.queue_size || 0}_${state.track ? (state.track.id || state.track.title) : ''}`;
      if (qTab && qTab.classList.contains('active') && !isModalOpen && queueKey !== lastQueueChecksum) {
        lastQueueChecksum = queueKey;
        loadQueue();
      }
      const catTab = document.getElementById('tab-categories');
      if (catTab && catTab.classList.contains('active')) {
        updateActiveCategoryBanner();
      }
    }

    function updateScrubberUI() {
      document.getElementById('timeElapsed').innerText = formatTime(Math.floor(currentElapsed));
      if (durationSeconds > 0) {
        const pct = Math.min(100, Math.max(0, (currentElapsed / durationSeconds) * 100));
        document.getElementById('progressFill').style.width = pct + '%';
      } else {
        document.getElementById('progressFill').style.width = '0%';
      }
    }

    // High-precision 60fps liquid smooth progress ticker matching live playback
    function progressLoop() {
      const now = performance.now();
      const dt = (now - lastTickTime) / 1000;
      lastTickTime = now;

      if (!isScrubbing && currentState && currentState.is_playing && durationSeconds > 0) {
        const eff = String(currentState.effect || '').toLowerCase();
        const speed = (currentState.track && currentState.track.effect_speed) || (eff.includes('night') ? 1.22 : (eff.includes('slow') ? 0.86 : 1.0));
        currentElapsed = Math.min(durationSeconds, currentElapsed + dt * speed);
        updateScrubberUI();
      }
      requestAnimationFrame(progressLoop);
    }
    requestAnimationFrame(progressLoop);

    // WebSocket auto-detect protocol & resilient reconnection
    function connectWS() {
      if (wsReconnectTimer) {
        clearTimeout(wsReconnectTimer);
        wsReconnectTimer = null;
      }
      if (!token) return;
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        return;
      }
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
          if (!wsReconnectTimer) {
            wsReconnectTimer = setTimeout(() => {
              wsReconnectTimer = null;
              connectWS();
            }, 1800);
          }
        };

        ws.onerror = () => {
          try { ws.close(); } catch (e) {}
        };
      } catch (err) {
        console.error('WS init error:', err);
      }
    }

    // Keep WebSocket connection active and prevent mobile timeouts
    setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        try { ws.send(JSON.stringify({ action: 'ping' })); } catch (e) {}
      }
    }, 12000);

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

    function openTrackModalByIndex(source, index) {
      const list = source === 'requested' ? currentQueueData.requested : currentQueueData.upcoming;
      const t = list[index];
      if (!t) return;
      selectedQueueItem = {
        source,
        index,
        title: t.title || 'Untitled Track',
        artist: t.artist || 'Juice WRLD',
        length: t.length || '—'
      };
      const titleEl = document.getElementById('modalTrackTitle');
      const descEl = document.getElementById('modalTrackDesc');
      if (titleEl) titleEl.innerText = selectedQueueItem.title;
      if (descEl) descEl.innerText = `${selectedQueueItem.artist} • ${selectedQueueItem.length}`;
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
      lastQueueChecksum = '';

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
        currentQueueData = {
          requested: data.requested || [],
          upcoming: data.upcoming || []
        };
        const reqList = document.getElementById('reqList');
        if (currentQueueData.requested.length > 0) {
          reqList.innerHTML = currentQueueData.requested.map((t, idx) => `
            <div class="track-card" style="cursor:pointer;" onclick="openTrackModalByIndex('requested', ${idx})">
              <div class="track-meta-col">
                <div class="track-name">${escapeHtml(t.title || 'Untitled')}</div>
                <div class="track-desc">${escapeHtml(t.artist || 'Juice WRLD')} • ${escapeHtml(t.length || '—')}</div>
              </div>
              <span class="btn-badge" style="font-size:0.68rem; padding:3px 7px;">Manage</span>
            </div>
          `).join('');
        } else {
          reqList.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No requested tracks. Use Search to queue songs.</div>';
        }

        const upList = document.getElementById('upcomingList');
        if (currentQueueData.upcoming.length > 0) {
          upList.innerHTML = currentQueueData.upcoming.slice(0, 30).map((t, idx) => `
            <div class="track-card" style="cursor:pointer;" onclick="openTrackModalByIndex('upcoming', ${idx})">
              <div class="track-meta-col">
                <div class="track-name">${idx + 1}. ${escapeHtml(t.title || 'Untitled')}</div>
                <div class="track-desc">${escapeHtml(t.artist || 'Juice WRLD')} • ${escapeHtml(t.length || '—')}</div>
              </div>
              <span class="btn-badge" style="font-size:0.68rem; padding:3px 7px;">Manage</span>
            </div>
          `).join('');
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
      const input = document.getElementById('searchInput');
      if (input) {
        input.placeholder = mode === 'external'
          ? 'Song title, artist, or YouTube/SoundCloud playlist URL…'
          : 'Search song title or artist…';
      }
    }

    async function executeSearch() {
      const q = document.getElementById('searchInput').value.trim();
      if (!q) return;
      const isUrl = q.startsWith('http://') || q.startsWith('https://') || q.startsWith('www.') || q.includes('youtube.com') || q.includes('youtu.be') || q.includes('soundcloud.com') || q.includes('bandcamp.com');
      if (isUrl && searchMode === 'vault') {
        setSearchMode('external');
      }
      const resContainer = document.getElementById('searchResults');
      resContainer.innerHTML = `<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Searching ${searchMode === 'external' ? 'online (YouTube / SoundCloud)…' : 'archive…'}</div>`;
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&source=${searchMode}&token=${encodeURIComponent(token)}`);
        const data = await res.json();
        currentSearchResults = data.results || [];

        if (data.error) {
          resContainer.innerHTML = `<div class="track-card" style="color: var(--danger); font-size: 0.8rem;">Search error: ${escapeHtml(data.error)}</div>`;
          return;
        }

        if (currentSearchResults.length > 0) {
          let html = '';
          if (data.is_playlist) {
            html += `
              <div class="playlist-header-card" style="background: linear-gradient(135deg, rgba(235, 47, 150, 0.12), rgba(114, 46, 209, 0.08)); border: 1px solid rgba(235, 47, 150, 0.28); border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 10px;">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
                  <div style="min-width: 0;">
                    <div style="font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); font-weight: 700; margin-bottom: 2px;">
                      Online Playlist • ${escapeHtml(data.playlist_uploader || 'Online')}
                    </div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                      ${escapeHtml(data.playlist_title || 'Playlist')}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-sub); margin-top: 2px;">
                      ${currentSearchResults.length} track${currentSearchResults.length === 1 ? '' : 's'} found
                    </div>
                  </div>
                  <div style="display: flex; gap: 8px; flex-shrink: 0;">
                    <button class="btn-kinetic btn-badge" style="background: var(--accent); color: #fff; font-weight: 600;" onclick="addAllPlaylistTracks(true)">
                      <svg class="icon-svg" style="width: 12px; height: 12px; margin-right: 4px;" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                      Play All
                    </button>
                    <button class="btn-kinetic btn-badge" onclick="addAllPlaylistTracks(false)">
                      <svg class="icon-svg" style="width: 12px; height: 12px; margin-right: 4px;" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                      Queue All
                    </button>
                  </div>
                </div>
              </div>
            `;
          }

          html += currentSearchResults.map((item, idx) => `
            <div class="track-card">
              <div class="track-meta-col">
                <div class="track-name">${escapeHtml(item.title || 'Untitled')}</div>
                <div class="track-desc">${escapeHtml(item.artist || 'Juice WRLD')} • ${escapeHtml(item.length || '—')}${item._source ? ' • ' + escapeHtml(item._source) : ''}</div>
              </div>
              <div style="display: flex; gap: 6px;">
                <button class="btn-kinetic btn-badge" onclick="addSearchResultByIndex(${idx}, true)" title="Play Now">Play</button>
                <button class="btn-kinetic btn-badge" onclick="addSearchResultByIndex(${idx}, false)" title="Add to Queue">+ Add</button>
              </div>
            </div>
          `).join('');

          resContainer.innerHTML = html;
        } else {
          resContainer.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No results found.</div>';
        }
      } catch (e) {
        resContainer.innerHTML = `<div class="track-card" style="color: var(--danger); font-size: 0.8rem;">Search failed: ${escapeHtml(e.message)}</div>`;
      }
    }

    function addSearchResultByIndex(idx, playNow = false) {
      const item = currentSearchResults[idx];
      if (item) addToQueue(item, playNow);
    }

    async function addToQueue(item, playNow = false) {
      try {
        const res = await fetch(`/api/queue/add?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ track: item, play_now: playNow })
        });
        const d = await res.json();
        showToast(d.message || (playNow ? 'Playing now' : 'Added to Requested'));
      } catch (e) {
        showToast('Error: ' + e.message);
      }
    }

    async function addAllPlaylistTracks(playNow = false) {
      if (!currentSearchResults || !currentSearchResults.length) return;
      try {
        showToast(playNow ? 'Starting playlist playback…' : 'Adding playlist to queue…');
        const res = await fetch(`/api/queue/add?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tracks: currentSearchResults, play_now: playNow })
        });
        const d = await res.json();
        showToast(d.message || (playNow ? 'Playing playlist now' : 'Added playlist to queue'));
      } catch (e) {
        showToast('Error: ' + e.message);
      }
    }

    // Collections & Library Data
    const KNOWN_COLLECTIONS = [
      {
        id: 'all',
        title: 'All Music',
        tag: 'Complete Vault Archive',
        desc: 'The complete archive of 3,881+ tracks across all eras, studio leaks, session cuts, stems & remasters.',
        iconSvg: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/>',
        featured: true
      },
      {
        id: 'main',
        title: 'Main Vault',
        tag: 'Unreleased Vault',
        desc: 'Core leaked grails, studio unreleased singles, and mastered catalog.',
        iconSvg: '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        featured: false
      },
      {
        id: 'session edits',
        title: 'Studio Sessions',
        tag: 'Raw Studio Takes',
        desc: 'Unedited studio session takes, alternate verses, and freestyle sessions.',
        iconSvg: '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>',
        featured: false
      },
      {
        id: 'instrumental',
        title: 'Instrumentals',
        tag: 'Beats & Productions',
        desc: 'Original studio instrumentals, melodic trap beats, guitar and synth backings.',
        iconSvg: '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
        featured: false
      },
      {
        id: 'stems',
        title: 'Stems & Multitracks',
        tag: 'Isolated Layers',
        desc: 'Raw isolated vocal layers, studio acapellas, melodies, and drum stems.',
        iconSvg: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
        featured: false
      },
      {
        id: 'released',
        title: 'Officially Released',
        tag: 'Label Discography',
        desc: 'Commercial studio albums (GBGR, DRFL, LND, FD), official singles & features.',
        iconSvg: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
        featured: false
      },
      {
        id: 'cut',
        title: 'Cuts & Snippets',
        tag: 'Previews & Snippets',
        desc: 'Rare preview cuts, IG live snippets, concert performances, and short leaks.',
        iconSvg: '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/>',
        featured: false
      },
      {
        id: 'remaster',
        title: 'Remasters',
        tag: 'Audio Engineered',
        desc: 'Cleaned, remastered, and sound-engineered high-definition restorations.',
        iconSvg: '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>',
        featured: false
      }
    ];

    let currentSelectedCategory = 'all';
    let currentCategoryTracks = [];
    let filteredCategoryTracks = [];

    function getCollectionCount(colId, cats = null) {
      if (!cats && currentState && currentState.categories) cats = currentState.categories;
      if (!cats) return '—';
      const idLower = colId.toLowerCase();
      if (cats[colId] !== undefined) return cats[colId];
      if (cats[idLower] !== undefined) return cats[idLower];
      if (idLower === 'stems' && cats['stem'] !== undefined) return cats['stem'];
      if (idLower === 'cut' && cats['cuts'] !== undefined) return cats['cuts'];
      if (idLower === 'instrumental' && cats['instrumentals'] !== undefined) return cats['instrumentals'];
      if (idLower === 'remaster' && cats['remasters'] !== undefined) return cats['remasters'];
      if (idLower === 'all') {
        if (cats['all'] !== undefined) return cats['all'];
        const sum = Object.values(cats).reduce((a, b) => (typeof b === 'number' ? a + b : a), 0);
        return sum || 3881;
      }
      return '—';
    }

    function updateActiveCategoryBanner() {
      const active = (currentState && (currentState.category || 'all')).toLowerCase();
      const activeColObj = KNOWN_COLLECTIONS.find(c => c.id === active || (c.id === 'session edits' && (active === 'session' || active === 'session edits'))) || KNOWN_COLLECTIONS[0];
      const bannerName = document.getElementById('activeColName');
      const bannerCount = document.getElementById('activeColTrackCount');
      const bannerIcon = document.getElementById('activeColIcon');
      if (bannerName) bannerName.innerText = `${activeColObj.title} (${activeColObj.tag})`;
      if (bannerCount) {
        const cnt = getCollectionCount(activeColObj.id);
        bannerCount.innerText = typeof cnt === 'number' ? `${cnt.toLocaleString()} tracks` : `${cnt} tracks`;
      }
      if (bannerIcon) {
        bannerIcon.innerHTML = `<svg class="icon-svg" style="width:20px;height:20px;color:var(--accent);" viewBox="0 0 24 24">${activeColObj.iconSvg}</svg>`;
      }
    }

    // Categories
    async function loadCategories() {
      if (!currentState || !currentState.categories) {
        await fetchStatus();
      }
      const grid = document.getElementById('catGrid');
      if (!grid) return;

      const cats = (currentState && currentState.categories) ? currentState.categories : {};
      const active = (currentState && (currentState.category || 'all')).toLowerCase();
      if (!currentSelectedCategory) currentSelectedCategory = active;

      updateActiveCategoryBanner();

      grid.innerHTML = KNOWN_COLLECTIONS.map(col => {
        const cnt = getCollectionCount(col.id, cats);
        const countStr = typeof cnt === 'number' ? `${cnt.toLocaleString()} tracks` : `${cnt} tracks`;
        const isActive = (col.id === active || (col.id === 'session edits' && (active === 'session' || active === 'session edits')));
        const isBrowsing = (col.id === currentSelectedCategory || (col.id === 'session edits' && (currentSelectedCategory === 'session' || currentSelectedCategory === 'session edits')));

        return `
          <div class="cat-item ${col.featured ? 'featured' : ''} ${isActive ? 'active' : ''} ${isBrowsing ? 'browsing' : ''}" onclick="selectCategory('${col.id}')">
            <div class="cat-header-row">
              <div class="cat-icon-badge">
                <svg class="icon-svg" viewBox="0 0 24 24">${col.iconSvg}</svg>
              </div>
              <div style="display:flex; align-items:center; gap:6px;">
                ${isActive ? '<span class="cat-active-pill">PLAYING</span>' : ''}
                <span class="cat-item-count">${countStr}</span>
              </div>
            </div>
            <div class="cat-meta-wrap">
              <div class="cat-item-title">${escapeHtml(col.title)}</div>
              <div class="cat-item-subtitle">${escapeHtml(col.tag)}</div>
              <div class="cat-item-desc">${escapeHtml(col.desc)}</div>
            </div>
            <div class="cat-actions-row">
              <button class="btn-kinetic btn-badge" onclick="event.stopPropagation(); changeCategory('${col.id}');" style="padding:4px 9px;">
                ${isActive ? 'Active' : 'Set as Current'}
              </button>
              <button class="btn-kinetic btn-badge" onclick="event.stopPropagation(); playSpecificCategory('${col.id}', true);" title="Shuffle & play on Discord" style="padding:4px 8px;">
                <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
                <span>Shuffle</span>
              </button>
            </div>
          </div>
        `;
      }).join('');

      loadCollectionTracks(currentSelectedCategory || active || 'all');
    }

    function selectCategory(catId) {
      currentSelectedCategory = catId;
      document.querySelectorAll('.cat-item').forEach(el => el.classList.remove('browsing'));
      loadCategories();
    }

    async function changeCategory(category) {
      if (currentState) {
        currentState.category = category;
        const b = document.getElementById('categoryBadge');
        if (b) b.innerText = category.toUpperCase();
      }
      currentSelectedCategory = category;
      showToast(`Active Collection: ${category}`);
      loadCategories();
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

    async function playSpecificCategory(category, shuffle = true) {
      if (currentState) {
        currentState.category = category;
        const b = document.getElementById('categoryBadge');
        if (b) b.innerText = category.toUpperCase();
      }
      currentSelectedCategory = category;
      loadCategories();
      showToast(`${shuffle ? 'Shuffling' : 'Playing'} ${category} collection…`);
      action('play_category', { category, shuffle });
    }

    function playSelectedCollection(shuffle = true) {
      const activeCat = (currentState && currentState.category) || currentSelectedCategory || 'all';
      playSpecificCategory(activeCat, shuffle);
    }

    async function loadCollectionTracks(category) {
      const listEl = document.getElementById('colTracksList');
      const labelEl = document.getElementById('colBrowserLabel');
      const countEl = document.getElementById('colBrowserCountBadge');
      const colObj = KNOWN_COLLECTIONS.find(c => c.id === category || (c.id === 'session edits' && category === 'session')) || { title: category };

      if (labelEl) labelEl.innerText = colObj.title;
      if (countEl) countEl.innerText = 'Loading tracks…';
      if (listEl) listEl.innerHTML = '<div class="track-card" style="color:var(--text-sub); font-size:0.8rem;">Loading tracks from vault…</div>';

      try {
        const res = await fetch(`/api/category/tracks?category=${encodeURIComponent(category)}&limit=100&token=${encodeURIComponent(token)}`);
        if (!res.ok) {
          if (listEl) listEl.innerHTML = '<div class="track-card" style="color:var(--danger); font-size:0.8rem;">Failed to load collection tracks.</div>';
          return;
        }
        const data = await res.json();
        currentCategoryTracks = data.tracks || [];
        filteredCategoryTracks = currentCategoryTracks;
        if (countEl) countEl.innerText = `${(data.total || currentCategoryTracks.length).toLocaleString()} tracks`;
        renderCollectionTracksList();
      } catch (e) {
        if (listEl) listEl.innerHTML = `<div class="track-card" style="color:var(--danger); font-size:0.8rem;">Error loading tracks: ${escapeHtml(e.message)}</div>`;
      }
    }

    function renderCollectionTracksList() {
      const listEl = document.getElementById('colTracksList');
      if (!listEl) return;
      if (!filteredCategoryTracks || filteredCategoryTracks.length === 0) {
        listEl.innerHTML = '<div class="track-card" style="color:var(--text-sub); font-size:0.8rem;">No tracks found matching filter.</div>';
        return;
      }

      listEl.innerHTML = filteredCategoryTracks.map((t, idx) => `
        <div class="track-card">
          <img src="${escapeHtml(t.cover_url)}" class="track-thumb" onerror="this.src='https://api.juicevault.xyz/favicon.ico'" alt="">
          <div class="track-meta-col" style="flex:1; min-width:0;">
            <div class="track-name" title="${escapeHtml(t.title)}">${escapeHtml(t.title)}</div>
            <div class="track-desc">${escapeHtml(t.artist || 'Juice WRLD')} • ${escapeHtml(t.length || '—')}</div>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <button class="btn-kinetic btn-primary btn-badge" onclick="playCollectionTrackByIndex(${idx})" style="padding:4px 9px;" title="Play now on Discord">
              <svg class="icon-svg" style="width:11px;height:11px;" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></svg>
              <span>Play</span>
            </button>
            <button class="btn-kinetic btn-badge" onclick="queueCollectionTrackByIndex(${idx})" style="padding:4px 9px;" title="Add to queue">
              <span>+ Queue</span>
            </button>
          </div>
        </div>
      `).join('');
    }

    function filterCollectionTracks() {
      const query = (document.getElementById('colSearchInput')?.value || '').trim().toLowerCase();
      if (!query) {
        filteredCategoryTracks = currentCategoryTracks;
      } else {
        filteredCategoryTracks = currentCategoryTracks.filter(t => 
          (t.title && t.title.toLowerCase().includes(query)) ||
          (t.artist && t.artist.toLowerCase().includes(query))
        );
      }
      renderCollectionTracksList();
    }

    async function playCollectionTrackByIndex(idx) {
      const track = filteredCategoryTracks[idx];
      if (!track) return;
      try {
        const res = await fetch(`/api/queue/add?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ track, play_now: true })
        });
        const d = await res.json();
        showToast(d.message || `Playing now: ${track.title}`);
      } catch (e) {
        showToast('Play failed: ' + e.message);
      }
    }

    async function queueCollectionTrackByIndex(idx) {
      const track = filteredCategoryTracks[idx];
      if (!track) return;
      try {
        const res = await fetch(`/api/queue/add?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ track, play_now: false })
        });
        const d = await res.json();
        showToast(d.message || `Queued: ${track.title}`);
      } catch (e) {
        showToast('Queue failed: ' + e.message);
      }
    }

    // EQ Profiles (No emojis, modern SVG icons)
    const DEFAULT_EQ_LIST = [
      { id: "none", label: "Flat", desc: "Original unprocessed studio sound", icon: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/>' },
      { id: "bass", label: "Bass Boost", desc: "Deep punchy bass boost (+11dB)", icon: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>' },
      { id: "8d", label: "8D Audio", desc: "360° rotating spatial surround sound", icon: '<circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>' },
      { id: "nightcore", label: "Nightcore", desc: "High pitch and accelerated tempo (+22%)", icon: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>' },
      { id: "slowed", label: "Slowed & Reverb", desc: "Deep pitched chopped & slowed lo-fi", icon: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/>' },
      { id: "echo", label: "Echo & Reverb", desc: "Spacious delay and echo ambiance", icon: '<path d="M2 12h2a8 8 0 0 1 8 8v2"/><path d="M2 4h2a16 16 0 0 1 16 16v2"/>' },
      { id: "wide", label: "Stereo Wide", desc: "Immersive 3D stereo stage expansion", icon: '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>' },
      { id: "virtual bass", label: "Sub-Bass Boost", desc: "Massive low-end rumble (+16dB)", icon: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>' },
    ];

    function openEqModal() {
      const container = document.getElementById('eqOptions');
      if (!container) return;
      const effects = (currentState && currentState.effects && currentState.effects.length) ? currentState.effects : DEFAULT_EQ_LIST;
      const activeEffect = (currentState && currentState.effect) ? currentState.effect : 'none';
      container.innerHTML = effects.map(eq => `
        <div class="track-card ${activeEffect === eq.id ? 'active' : ''}" style="cursor:pointer; ${activeEffect === eq.id ? 'border-color:var(--accent); background:var(--accent-muted);' : ''}" onclick="setEq('${eq.id}')">
          <div style="display:flex; align-items:center; gap:12px;">
            ${eq.icon ? `<div class="cat-icon-badge" style="width:28px;height:28px;"><svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24">${eq.icon}</svg></div>` : ''}
            <div>
              <div style="font-weight:600; font-size:0.88rem; color:#fff;">${escapeHtml(eq.label)}</div>
              <div style="font-size:0.72rem; color:var(--text-sub); margin-top:2px;">${escapeHtml(eq.desc)}</div>
            </div>
          </div>
          ${activeEffect === eq.id ? '<svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
        </div>
      `).join('');
      document.getElementById('eqSheet').classList.add('active');
    }

    function closeEqModal() {
      document.getElementById('eqSheet').classList.remove('active');
    }

    async function setEq(effect) {
      if (currentState) {
        currentState.effect = effect;
        const b = document.getElementById('eqBadge');
        if (b) b.innerText = effect.toUpperCase();
      }
      closeEqModal();
      showToast(`EQ Profile: ${effect}`);
      action('set_eq', { effect });
    }

    let cachedLyricsUrl = null;
    let cachedServerChannels = [];

    async function openLyrics() {
      if (!currentState || !currentState.track) {
        showToast('No track is currently playing');
        return;
      }
      const t = currentState.track;
      const title = t.title || 'Untitled Track';
      const artist = t.artist || 'Juice WRLD';

      document.getElementById('lyricsModalTitle').innerText = title;
      document.getElementById('lyricsModalDesc').innerText = `${artist} • Lyrics Options`;

      const q = encodeURIComponent(`${artist} ${title}`.trim());
      cachedLyricsUrl = `https://genius.com/search?q=${q}`;

      const previewBox = document.getElementById('lyricsPreviewBox');
      const previewText = document.getElementById('lyricsPreviewText');
      if (previewBox) previewBox.style.display = 'none';
      if (previewText) previewText.innerText = 'Loading lyrics…';

      document.getElementById('lyricsSheet').classList.add('active');

      loadServerChannels();

      try {
        const res = await fetch(`/api/lyrics?token=${encodeURIComponent(token)}`);
        if (res.ok) {
          const d = await res.json();
          if (d.url) cachedLyricsUrl = d.url;
          if (d.lyrics) {
            if (previewText) previewText.innerText = d.lyrics;
            if (previewBox) previewBox.style.display = 'block';
            const srcBadge = document.getElementById('lyricsSourceBadge');
            if (srcBadge) srcBadge.innerText = d.source || 'Genius';
          }
        }
      } catch (_) {}
    }

    function closeLyricsModal() {
      const sheet = document.getElementById('lyricsSheet');
      if (sheet) sheet.classList.remove('active');
    }

    async function loadServerChannels() {
      const select = document.getElementById('lyricsChannelSelect');
      if (!select) return;
      try {
        const res = await fetch(`/api/channels?token=${encodeURIComponent(token)}`);
        if (res.ok) {
          const d = await res.json();
          cachedServerChannels = d.channels || [];
          if (cachedServerChannels.length > 0) {
            select.innerHTML = cachedServerChannels.map(c => `
              <option value="${escapeHtml(c.id)}">#${escapeHtml(c.name)}</option>
            `).join('');
          } else {
            select.innerHTML = '<option value="">No text channels found</option>';
          }
        }
      } catch (e) {
        select.innerHTML = '<option value="">Error loading channels</option>';
      }
    }

    async function sendLyricsToSelectedChannel() {
      const select = document.getElementById('lyricsChannelSelect');
      const channelId = select ? select.value : null;
      if (!channelId) {
        showToast('Please select a channel first');
        return;
      }
      showToast('Sending lyrics to Discord…');
      try {
        const res = await fetch(`/api/lyrics/send?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel_id: channelId })
        });
        const d = await res.json();
        if (d.success) {
          showToast(d.message || 'Lyrics sent to Discord!');
          closeLyricsModal();
        } else {
          showToast(d.error || 'Failed to send lyrics');
        }
      } catch (e) {
        showToast('Error: ' + e.message);
      }
    }

    function openGeniusDirectLink() {
      if (cachedLyricsUrl) {
        window.open(cachedLyricsUrl, '_blank');
      }
    }

    function copyGeniusLink() {
      if (cachedLyricsUrl) {
        navigator.clipboard.writeText(cachedLyricsUrl).then(() => {
          showToast('Genius link copied to clipboard!');
        }).catch(() => {
          showToast(cachedLyricsUrl);
        });
      }
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

    // Live Telemetry & Daily Usage Engine
    function openStatsModal() {
      const s = document.getElementById('statsSheet');
      if (s) s.classList.add('active');
      fetchTelemetry();
    }

    function closeStatsModal() {
      const s = document.getElementById('statsSheet');
      if (s) s.classList.remove('active');
    }

    async function fetchTelemetry() {
      try {
        const res = await fetch('/api/stats');
        if (res.ok) {
          const data = await res.json();
          if (data && data.stats) {
            updateTelemetryUI(data.stats);
          }
        }
      } catch (e) {
        // Fallback or offline
      }
    }

    function updateTelemetryUI(stats) {
      if (!stats) return;
      const views = stats.views || {};
      const daily = stats.daily_usage || {};
      const allTime = stats.all_time || {};

      const fmt = (n) => (n !== undefined && n !== null) ? Number(n).toLocaleString() : '--';

      // Header badge
      const hCount = document.getElementById('headerViewsCount');
      if (hCount) hCount.innerText = fmt(views.total) + ' views';
      const hDaily = document.getElementById('headerDailyCount');
      if (hDaily) hDaily.innerText = fmt(views.today) + ' today';

      // Compact quick bar
      const qTot = document.getElementById('quickTotalViews');
      if (qTot) qTot.innerText = fmt(views.total);
      const qDay = document.getElementById('quickDailyViews');
      if (qDay) qDay.innerText = fmt(views.today);
      const qTime = document.getElementById('quickDailyTime');
      if (qTime) qTime.innerText = daily.listening_formatted || '0m';
      const qTracks = document.getElementById('quickDailyTracks');
      if (qTracks) qTracks.innerText = fmt(daily.tracks_played);

      // Modal sheet values
      const sTot = document.getElementById('statsTotalViews');
      if (sTot) sTot.innerText = fmt(views.total);
      const sDay = document.getElementById('statsDailyViews');
      if (sDay) sDay.innerText = fmt(views.today);
      const sUniq = document.getElementById('statsUniqueViews');
      if (sUniq) sUniq.innerText = fmt(views.unique_today);
      const sSess = document.getElementById('statsSessionsNow');
      if (sSess) sSess.innerText = (views.active_sessions || 1) + ' active now';
      const sTime = document.getElementById('statsDailyTime');
      if (sTime) sTime.innerText = daily.listening_formatted || '0m';
      const sAllTime = document.getElementById('statsAllTimeTime');
      if (sAllTime) sAllTime.innerText = (allTime.listening_formatted || '0m') + ' total';
      const sTracks = document.getElementById('statsDailyTracks');
      if (sTracks) sTracks.innerText = fmt(daily.tracks_played);
      const sReqs = document.getElementById('statsDailyReqs');
      if (sReqs) sReqs.innerText = fmt(daily.requests_queued);
      const sAllTracks = document.getElementById('statsAllTimeTracks');
      if (sAllTracks) sAllTracks.innerText = fmt(allTime.tracks_played) + ' total';
      const sActions = document.getElementById('statsDailyActions');
      if (sActions) sActions.innerText = fmt(daily.remote_actions) + ' actions';
      const sAllActions = document.getElementById('statsAllTimeActions');
      if (sAllActions) sAllActions.innerText = fmt(allTime.remote_actions) + ' total';
      const sWs = document.getElementById('statsWsCount');
      if (sWs) sWs.innerText = views.active_sessions || 1;

      // Card in tab-shortcuts
      const cTot = document.getElementById('cardTotalViews');
      if (cTot) cTot.innerText = fmt(views.total);
      const cDay = document.getElementById('cardDailyViews');
      if (cDay) cDay.innerText = fmt(views.today);
      const cUniq = document.getElementById('cardUniqueViews');
      if (cUniq) cUniq.innerText = fmt(views.unique_today);
      const cSess = document.getElementById('cardSessionsNow');
      if (cSess) cSess.innerText = (views.active_sessions || 1) + ' active';
      const cTime = document.getElementById('cardDailyTime');
      if (cTime) cTime.innerText = daily.listening_formatted || '0m';
      const cAllTime = document.getElementById('cardAllTimeTime');
      if (cAllTime) cAllTime.innerText = (allTime.listening_formatted || '0m') + ' total';
      const cTracks = document.getElementById('cardDailyTracks');
      if (cTracks) cTracks.innerText = fmt(daily.tracks_played);
      const cReqs = document.getElementById('cardDailyReqs');
      if (cReqs) cReqs.innerText = fmt(daily.requests_queued);
      const cAllTracks = document.getElementById('cardAllTimeTracks');
      if (cAllTracks) cAllTracks.innerText = fmt(allTime.tracks_played) + ' total';

      renderActivityBars('statsActivityBars', daily.tracks_played || 1, views.today || 1);
      renderActivityBars('cardActivityBars', daily.tracks_played || 1, views.today || 1);
    }

    function renderActivityBars(containerId, tracksCount, viewsCount) {
      const container = document.getElementById(containerId);
      if (!container) return;
      const currentHour = new Date().getUTCHours();
      let html = '';
      for (let h = 0; h < 24; h++) {
        let cls = 'activity-bar';
        let pct = 8;
        if (h === currentHour) {
          cls += ' current';
          pct = Math.min(100, Math.max(35, (tracksCount * 3 + viewsCount * 2) % 65 + 35));
        } else if (h < currentHour) {
          cls += ' active';
          const wave = Math.sin((h + 2) / 3.2) * 35 + 45;
          pct = Math.max(15, Math.min(95, Math.round(wave + ((h * 7) % 20))));
          if (pct > 65) cls += ' high';
        } else {
          pct = 8;
        }
        const hourLabel = String(h).padStart(2, '0') + ':00 UTC';
        html += `<div class="activity-bar-slot" title="${hourLabel}"><div class="${cls}" style="height:${pct}%;"></div></div>`;
      }
      container.innerHTML = html;
    }

    // Soundboard Engine
    let soundboardSounds = [];
    let currentSbPlayingId = null;
    let localSbAudio = null;

    async function loadSoundboard() {
      const grid = document.getElementById('soundboardGrid');
      if (!grid) return;
      if (soundboardSounds.length > 0) {
        renderSoundboardGrid(soundboardSounds);
        return;
      }
      grid.innerHTML = '<div style="color:var(--text-sub); font-size:0.8rem; padding:12px; grid-column:1/-1;">Loading 50 meme sounds…</div>';
      try {
        const res = await fetch(`/api/soundboard?token=${encodeURIComponent(token)}`);
        const data = await res.json();
        soundboardSounds = data.sounds || [];
        renderSoundboardGrid(soundboardSounds);
      } catch (e) {
        grid.innerHTML = `<div style="color:var(--danger); font-size:0.8rem; padding:12px; grid-column:1/-1;">Failed to load soundboard: ${escapeHtml(e.message)}</div>`;
      }
    }

    function renderSoundboardGrid(list) {
      const grid = document.getElementById('soundboardGrid');
      if (!grid) return;
      const countEl = document.getElementById('sbFilteredCount');
      if (countEl) countEl.textContent = `${list.length} sound${list.length === 1 ? '' : 's'}`;

      if (!list || list.length === 0) {
        grid.innerHTML = '<div style="color:var(--text-sub); font-size:0.8rem; padding:14px; grid-column:1/-1;">No matching sounds found.</div>';
        return;
      }

      grid.innerHTML = list.map(s => {
        const isCurrent = (currentSbPlayingId === s.id);
        const color = s.color || '#eb2f96';
        return `
          <div class="sound-pad ${isCurrent ? 'is-playing' : ''}" id="sb_pad_${s.id}" style="--pad-color:${color}; --pad-glow:${color}55; --pad-bg:${color}1a;" onclick="triggerSoundboard('${s.id}')">
            <div class="sound-pad-icon">
              <svg class="icon-svg" style="width:14px; height:14px;" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
            </div>
            <div class="sound-pad-title">${escapeHtml(s.name)}</div>
          </div>
        `;
      }).join('');
    }

    function filterSoundboard() {
      const input = document.getElementById('soundboardSearch');
      const q = (input ? input.value : '').trim().toLowerCase();
      if (!q) {
        renderSoundboardGrid(soundboardSounds);
        return;
      }
      const filtered = soundboardSounds.filter(s => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q));
      renderSoundboardGrid(filtered);
    }

    function clearSoundboardFilter() {
      const input = document.getElementById('soundboardSearch');
      if (input) input.value = '';
      renderSoundboardGrid(soundboardSounds);
    }

    async function triggerSoundboard(soundId) {
      const sound = soundboardSounds.find(s => s.id === soundId);
      const name = sound ? sound.name : soundId;
      currentSbPlayingId = soundId;

      document.querySelectorAll('.sound-pad').forEach(el => el.classList.remove('is-playing'));
      const activePad = document.getElementById('sb_pad_' + soundId);
      if (activePad) activePad.classList.add('is-playing');

      const stopBtn = document.getElementById('sbStopBtn');
      if (stopBtn) stopBtn.style.display = 'inline-flex';
      const activeBanner = document.getElementById('sbActiveBanner');
      if (activeBanner) activeBanner.style.display = 'flex';
      const activeName = document.getElementById('sbActiveName');
      if (activeName) activeName.textContent = name;

      const previewCheckbox = document.getElementById('sbPreviewToggle');
      if (previewCheckbox && previewCheckbox.checked && sound && sound.url) {
        try {
          if (localSbAudio) {
            localSbAudio.pause();
            localSbAudio = null;
          }
          localSbAudio = new Audio(sound.url);
          localSbAudio.volume = 0.85;
          localSbAudio.play().catch(() => {});
        } catch (_) {}
      }

      showToast(`Soundboard: ${name} (music paused)`);

      try {
        const res = await fetch(`/api/soundboard/play?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sound_id: soundId })
        });
        const d = await res.json();
        if (d.error) showToast('Soundboard error: ' + d.error);
      } catch (e) {
        showToast('Error playing soundboard: ' + e.message);
      }
    }

    async function stopSoundboard() {
      if (localSbAudio) {
        localSbAudio.pause();
        localSbAudio = null;
      }
      currentSbPlayingId = null;
      document.querySelectorAll('.sound-pad').forEach(el => el.classList.remove('is-playing'));
      const stopBtn = document.getElementById('sbStopBtn');
      if (stopBtn) stopBtn.style.display = 'none';
      const activeBanner = document.getElementById('sbActiveBanner');
      if (activeBanner) activeBanner.style.display = 'none';

      showToast('Resuming music…');
      try {
        await fetch(`/api/soundboard/stop?token=${encodeURIComponent(token)}`, { method: 'POST' });
      } catch (e) {
        showToast('Error stopping: ' + e.message);
      }
    }

    // Lifecycle listeners for instant mobile reconnect on unlock / tab focus
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          connectWS();
        } else {
          try { ws.send(JSON.stringify({ action: 'ping' })); } catch (e) {}
        }
        fetchStatus();
        armBackgroundMediaSession();
      }
    });

    window.addEventListener('pageshow', () => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWS();
      }
      fetchStatus();
      armBackgroundMediaSession();
    });

    window.addEventListener('focus', () => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWS();
      }
      fetchStatus();
    });

    window.addEventListener('pointerdown', () => { armBackgroundMediaSession(); }, { passive: true });
    window.addEventListener('touchstart', () => { armBackgroundMediaSession(); }, { passive: true });

    // Instant paint from local cache (0ms perceived startup)
    try {
      const cachedState = localStorage.getItem('jv_state_cache');
      if (cachedState) {
        applyState(JSON.parse(cachedState));
      }
    } catch (e) {
      console.error('State cache load failed:', e);
    }

    // Startup
    fetchTelemetry();
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
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml"
    },
    {
      "src": "/favicon.ico",
      "sizes": "32x32",
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

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="discGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#c084fc"/>
      <stop offset="50%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#6b21a8"/>
    </linearGradient>
  </defs>
  <circle cx="32" cy="32" r="30" fill="url(#discGrad)"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="1.6"/>
  <circle cx="32" cy="32" r="16" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="1.2"/>
  <circle cx="32" cy="32" r="10" fill="#09090d" stroke="#a855f7" stroke-width="1.8"/>
  <circle cx="32" cy="32" r="3.5" fill="#c084fc"/>
</svg>"""

import os

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def _read_asset(filename: str) -> bytes:
    p = os.path.join(_ASSETS_DIR, filename)
    if os.path.isfile(p):
        try:
            with open(p, "rb") as f:
                return f.read()
        except Exception:
            pass
    return b""

FAVICON_ICO_BYTES = _read_asset("favicon.ico")
ICON_192_PNG_BYTES = _read_asset("icon-192.png")
ICON_512_PNG_BYTES = _read_asset("icon-512.png")
