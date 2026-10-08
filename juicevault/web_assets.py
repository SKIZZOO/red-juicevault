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
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
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
    ::-webkit-scrollbar {
      width: 5px;
      height: 5px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.12);
      border-radius: 999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: var(--accent);
    }
    html, body {
      background-color: var(--bg) !important;
      color: var(--text) !important;
      color-scheme: dark !important;
      font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      min-height: 100%;
      min-height: 100dvh;
      overflow-x: hidden;
    }
    body {
      display: flex;
      flex-direction: column;
      padding-top: var(--safe-top);
      padding-bottom: var(--safe-bottom);
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
    .header-nav-wrap {
      display: none;
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
    /* Header Animated Visualizer Wave */
    .header-visualizer-wave {
      display: inline-flex;
      align-items: center;
      gap: 2.5px;
      height: 18px;
      padding: 0 4px;
      margin-left: 2px;
    }
    .h-wave-bar {
      width: 2.5px;
      height: 4px;
      background: var(--accent);
      border-radius: 2px;
      transition: height 0.15s ease, background-color 0.2s ease;
    }
    .header-visualizer-wave.playing .h-wave-bar:nth-child(1) { animation: hWave 0.7s infinite alternate ease-in-out; }
    .header-visualizer-wave.playing .h-wave-bar:nth-child(2) { animation: hWave 1.1s infinite alternate ease-in-out 0.2s; }
    .header-visualizer-wave.playing .h-wave-bar:nth-child(3) { animation: hWave 0.85s infinite alternate ease-in-out 0.4s; }
    .header-visualizer-wave.playing .h-wave-bar:nth-child(4) { animation: hWave 1.05s infinite alternate ease-in-out 0.1s; }
    .header-visualizer-wave.playing .h-wave-bar:nth-child(5) { animation: hWave 0.75s infinite alternate ease-in-out 0.3s; }
    @keyframes hWave {
      0% { height: 3px; opacity: 0.5; }
      100% { height: 16px; opacity: 1; filter: drop-shadow(0 0 4px var(--accent)); }
    }
    /* Header JuiceVault User Badge */
    .header-user-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: border-color 0.18s, background 0.18s, transform 0.18s;
    }
    .header-user-badge:hover {
      border-color: var(--border-accent);
      background: rgba(168, 85, 247, 0.12);
    }
    .header-user-avatar {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      object-fit: cover;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
    /* Layout Container: Responsive Mobile -> Desktop */
    .app-container {
      max-width: 1140px;
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
        grid-template-columns: 420px minmax(0, 1fr);
        gap: 24px;
        align-items: start;
      }
      .header-nav-wrap {
        display: flex !important;
        align-items: center;
        justify-content: center;
        flex: 1;
        max-width: 580px;
        margin: 0 16px;
      }
      .header-nav-wrap .desktop-segment {
        display: flex !important;
        align-items: center;
        position: static !important;
        width: 100%;
        margin: 0 !important;
        background: rgba(18, 18, 24, 0.72);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 3px 4px;
        gap: 3px;
      }
      .header-nav-wrap .segment-btn {
        padding: 6px 12px;
        font-size: 0.76rem;
        border-radius: 16px;
        white-space: nowrap;
        color: var(--text-muted);
        border: 1px solid transparent;
        transition: all 0.18s ease;
      }
      .header-nav-wrap .segment-btn:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.05);
      }
      .header-nav-wrap .segment-btn.active {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.16);
        color: #fff;
        font-weight: 700;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.22);
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
        height: 50px;
        min-height: 50px;
        padding: 0 12px !important;
        gap: 6px;
      }
      .header-meta {
        gap: 5px !important;
      }
      #vcLabel {
        max-width: 85px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .btn-lt-action {
        padding: 5px 9px !important;
        font-size: 0.7rem !important;
      }
      .stats-badge {
        padding: 4px 7px !important;
        font-size: 0.7rem !important;
        gap: 4px !important;
      }
      .header-pill-sub {
        display: none !important;
      }
      .brand-tag {
        display: none !important;
      }
      #connLabel {
        display: none !important;
      }
      #guildBadge {
        display: none !important;
      }
      .controls-sub .btn-flat {
        padding: 5px 4px !important;
        font-size: 0.68rem !important;
        gap: 4px !important;
      }
      .controls-sub .btn-flat span {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .header-nav-wrap,
      .desktop-segment {
        display: none !important;
      }
      .card-content-wrap {
        display: none;
      }
      .app-container {
        padding: 10px 12px calc(80px + var(--safe-bottom)) !important;
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
      .banner-box, .listen-together-card, .telemetry-dock {
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
    .player-visual-wrap {
      position: relative;
      width: 100%;
      max-width: 200px;
      margin: 0 auto 14px;
    }
    .player-visual-ambient {
      position: absolute;
      inset: -6px;
      border-radius: var(--radius-lg);
      background: radial-gradient(circle at 50% 50%, var(--accent-glow) 0%, transparent 72%);
      filter: blur(24px);
      opacity: 0.3;
      transition: opacity 0.4s ease, transform 0.4s ease;
      z-index: 0;
      pointer-events: none;
    }
    .player-visual-ambient.playing {
      opacity: 0.85;
      animation: ambientBreathe 3.5s infinite alternate ease-in-out;
    }
    @keyframes ambientBreathe {
      0% { opacity: 0.55; transform: scale(0.98); }
      100% { opacity: 0.95; transform: scale(1.08); }
    }
    .player-visual {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      border-radius: var(--radius-md);
      overflow: hidden;
      background: #14141a;
      border: 1px solid var(--border);
      box-shadow: 0 14px 32px rgba(0, 0, 0, 0.65), 0 0 24px rgba(168, 85, 247, 0.12);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1;
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
    .btn-fav {
      background: transparent;
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      padding: 3px;
      border-radius: 50%;
      transition: transform 0.2s var(--spring), color 0.15s ease;
      flex-shrink: 0;
    }
    .btn-fav:hover {
      color: #fff;
      transform: scale(1.18);
    }
    .btn-fav:active {
      transform: scale(0.9);
    }
    .btn-fav.is-favorite {
      color: #f43f5e !important;
    }
    .btn-fav.is-favorite svg path {
      fill: #f43f5e !important;
      stroke: #f43f5e !important;
    }
    .jv-badge-pill {
      font-size: 0.6rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 1px 6px;
      border-radius: 4px;
      background: var(--accent-muted);
      color: var(--accent);
      border: 1px solid var(--border-accent);
      font-family: 'JetBrains Mono', monospace;
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
    .scrubber-tooltip {
      position: absolute;
      top: -24px;
      left: 0;
      transform: translateX(-50%);
      background: #171722;
      border: 1px solid var(--border-accent);
      color: #fff;
      font-size: 0.65rem;
      font-family: 'JetBrains Mono', monospace;
      padding: 2px 6px;
      border-radius: 4px;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.15s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
      white-space: nowrap;
      z-index: 10;
    }
    .scrubber-track:hover .scrubber-tooltip {
      opacity: 1;
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
      margin-bottom: 10px;
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
    .btn-clear-search {
      background: none;
      border: none;
      color: var(--text-sub);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 4px;
      border-radius: 50%;
      transition: color 0.15s ease;
    }
    .btn-clear-search:hover {
      color: #fff;
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
    /* Mobile Floating Mini-Player Bar */
    .mobile-mini-player {
      position: fixed;
      left: 12px;
      right: 12px;
      bottom: calc(12px + var(--safe-bottom));
      height: 56px;
      background: rgba(18, 18, 24, 0.94);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-md);
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.6), 0 0 16px rgba(168, 85, 247, 0.15);
      display: none;
      align-items: center;
      justify-content: space-between;
      padding: 0 12px;
      z-index: 95;
      cursor: pointer;
      animation: slideUpMini 0.25s var(--ease);
      overflow: hidden;
    }
    .mobile-mini-player.visible {
      display: flex;
    }
    @keyframes slideUpMini {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    .mini-progress-line {
      position: absolute;
      top: 0;
      left: 0;
      height: 2px;
      background: linear-gradient(90deg, #a855f7, #c084fc);
      width: 0%;
      box-shadow: 0 0 8px var(--accent-glow);
    }
    .mini-player-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex: 1;
    }
    .mini-player-thumb {
      width: 36px;
      height: 36px;
      border-radius: 6px;
      object-fit: cover;
      background: #14141a;
      flex-shrink: 0;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .mini-player-info {
      min-width: 0;
      flex: 1;
    }
    .mini-player-title {
      font-size: 0.82rem;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .mini-player-artist {
      font-size: 0.68rem;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-top: 1px;
    }
    .mini-player-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
      margin-left: 8px;
    }
    .btn-mini-action {
      width: 34px;
      height: 34px;
    }
    /* Top Navigation Bar for Mobile */
    nav.mobile-nav {
      position: sticky;
      top: 50px;
      left: 0;
      width: 100%;
      height: 46px;
      padding: 0 10px;
      background: rgba(10, 10, 15, 0.95);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 6px;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      z-index: 45;
    }
    nav.mobile-nav::-webkit-scrollbar {
      display: none;
    }
    .nav-btn {
      display: inline-flex;
      flex-direction: row;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.74rem;
      font-weight: 600;
      white-space: nowrap;
      flex-shrink: 0;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.07);
      color: var(--text-sub);
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
      user-select: none;
    }
    .nav-btn .icon-svg {
      width: 14px;
      height: 14px;
      flex-shrink: 0;
    }
    .nav-btn:hover {
      background: rgba(255, 255, 255, 0.07);
      color: var(--text-main);
    }
    .nav-btn.active {
      background: rgba(168, 85, 247, 0.18);
      border-color: rgba(168, 85, 247, 0.5);
      color: #fff;
      box-shadow: 0 0 14px rgba(168, 85, 247, 0.28);
      font-weight: 700;
    }
    .nav-btn.active .icon-svg {
      color: var(--accent);
    }
    .nav-btn:active {
      transform: scale(0.96);
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
    .sheet-backdrop.active,
    .sheet-backdrop.visible {
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
    /* Listen Together Studio Stream Card */
    .listen-together-card {
      margin-top: 12px;
      background: linear-gradient(135deg, rgba(20, 20, 28, 0.95), rgba(13, 13, 19, 0.98));
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-md);
      padding: 11px 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.04);
      transition: border-color 0.25s ease, box-shadow 0.25s ease;
      position: relative;
      overflow: hidden;
    }
    .listen-together-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 3px;
      height: 100%;
      background: var(--accent);
      opacity: 0.35;
      transition: opacity 0.25s ease, background 0.25s ease;
    }
    .listen-together-card.active {
      border-color: rgba(168, 85, 247, 0.4);
      box-shadow: 0 4px 24px rgba(168, 85, 247, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    .listen-together-card.active::before {
      opacity: 1;
      box-shadow: 0 0 10px var(--accent);
    }
    .lt-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .lt-info-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex: 1;
    }
    .lt-icon-capsule {
      width: 34px;
      height: 34px;
      border-radius: 9px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      position: relative;
      transition: all 0.2s ease;
    }
    .listen-together-card.active .lt-icon-capsule {
      background: var(--accent-muted);
      border-color: rgba(168, 85, 247, 0.3);
    }
    .lt-icon {
      width: 17px;
      height: 17px;
      color: #e2e8f0;
      transition: color 0.2s ease;
    }
    .listen-together-card.active .lt-icon {
      color: var(--accent);
    }
    .lt-live-indicator {
      display: none;
      position: absolute;
      top: -2px;
      right: -2px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      border: 1.5px solid #0d0d12;
    }
    .listen-together-card.active .lt-live-indicator {
      display: block;
      animation: pulseNeon 1.6s infinite ease-in-out;
    }
    .lt-text-meta {
      display: flex;
      flex-direction: column;
      gap: 3px;
      min-width: 0;
      flex: 1;
    }
    .lt-title-line {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .lt-title {
      font-weight: 700;
      font-size: 0.84rem;
      color: #fff;
      letter-spacing: -0.01em;
      white-space: nowrap;
    }
    .lt-meta-sub-row {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }
    .lt-sync-badge {
      font-size: 0.58rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      letter-spacing: 0.04em;
      padding: 1px 6px;
      border-radius: 4px;
      background: rgba(168, 85, 247, 0.15);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.3);
      text-transform: uppercase;
      white-space: nowrap;
      flex-shrink: 0;
      transition: all 0.2s ease;
    }
    .lt-sync-badge.connecting {
      background: rgba(234, 179, 8, 0.15);
      color: #facc15;
      border-color: rgba(234, 179, 8, 0.3);
    }
    .lt-sync-badge.live {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border-color: rgba(16, 185, 129, 0.3);
    }
    .lt-sync-badge.paused {
      background: rgba(148, 163, 184, 0.15);
      color: #94a3b8;
      border-color: rgba(148, 163, 184, 0.3);
    }
    .lt-subtitle {
      font-size: 0.68rem;
      color: var(--text-sub);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }
    .btn-lt-action {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #fff;
      font-size: 0.74rem;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 7px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
      transition: all 0.18s ease;
    }
    .btn-lt-action:hover {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      box-shadow: 0 0 14px var(--accent-glow);
      transform: translateY(-1px);
    }
    .btn-lt-action:active {
      transform: scale(0.96);
    }
    .btn-lt-action.active {
      background: rgba(244, 63, 94, 0.16);
      border-color: rgba(244, 63, 94, 0.4);
      color: #fb7185;
      box-shadow: 0 0 12px rgba(244, 63, 94, 0.2);
    }
    .btn-lt-action.active:hover {
      background: rgba(244, 63, 94, 0.3);
      border-color: rgba(244, 63, 94, 0.6);
      color: #fff;
    }
    .lt-action-icon {
      width: 12px;
      height: 12px;
      fill: currentColor;
    }
    .lt-controls-drawer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      animation: fadeIn 0.2s ease;
    }
    .lt-slider-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
      min-width: 0;
    }
    .lt-vol-icon {
      width: 13px;
      height: 13px;
      color: var(--text-sub);
      flex-shrink: 0;
    }
    .lt-volume-slider {
      flex: 1;
      height: 5px;
      background: linear-gradient(to right, var(--accent) 0%, var(--accent) var(--vol-fill, 100%), rgba(255, 255, 255, 0.12) var(--vol-fill, 100%), rgba(255, 255, 255, 0.12) 100%);
      border-radius: 3px;
      accent-color: var(--accent);
      cursor: pointer;
      outline: none;
      -webkit-appearance: none;
      appearance: none;
    }
    .lt-volume-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 0 8px var(--accent-glow);
      cursor: pointer;
      border: none;
      transition: transform 0.08s ease;
    }
    .lt-volume-slider::-webkit-slider-thumb:hover,
    .lt-volume-slider::-webkit-slider-thumb:active {
      transform: scale(1.2);
    }
    .lt-volume-slider::-moz-range-thumb {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fff;
      border: none;
      box-shadow: 0 0 8px var(--accent-glow);
      cursor: pointer;
      transition: transform 0.08s ease;
    }
    .lt-volume-slider::-moz-range-thumb:hover,
    .lt-volume-slider::-moz-range-thumb:active {
      transform: scale(1.2);
    }
    .lt-vol-val {
      font-size: 0.69rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      color: var(--text-sub);
      min-width: 34px;
      text-align: right;
    }
    .lt-drift-pill {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.07);
      font-size: 0.65rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      color: var(--accent);
      white-space: nowrap;
    }
    .lt-drift-dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 6px var(--accent-glow);
    }

    /* Fallback banner-box if ever used */
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

    /* Studio Telemetry Dock & Harmonious Neon Animations */
    .telemetry-dock {
      margin-top: 10px;
      background: linear-gradient(180deg, rgba(20, 20, 28, 0.92), rgba(14, 14, 20, 0.96));
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: var(--radius-md);
      padding: 10px 12px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 8px;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
      transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      position: relative;
      overflow: hidden;
    }
    .telemetry-dock:hover {
      background: linear-gradient(180deg, rgba(26, 26, 38, 0.96), rgba(18, 18, 26, 0.98));
      border-color: rgba(168, 85, 247, 0.35);
      box-shadow: 0 8px 28px rgba(0, 0, 0, 0.5), 0 0 20px rgba(168, 85, 247, 0.16);
      transform: translateY(-2px);
    }
    .telemetry-dock:active {
      transform: scale(0.99);
    }
    .telemetry-dock-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .telemetry-dock-tag {
      display: flex;
      align-items: center;
      gap: 7px;
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: var(--text-sub);
      text-transform: uppercase;
    }
    /* Animated Live Equalizer Bars in Dock Tag */
    .telemetry-live-bars {
      display: inline-flex;
      align-items: flex-end;
      gap: 2px;
      height: 12px;
      padding-bottom: 1px;
    }
    .tl-bar {
      width: 2.5px;
      background: linear-gradient(180deg, #c084fc, #a855f7);
      border-radius: 1px;
      animation: tlBarPulse 1s ease-in-out infinite alternate;
    }
    .tl-bar:nth-child(1) { height: 4px; animation-duration: 0.75s; }
    .tl-bar:nth-child(2) { height: 10px; animation-duration: 1.1s; animation-delay: 0.15s; }
    .tl-bar:nth-child(3) { height: 6px; animation-duration: 0.85s; animation-delay: 0.3s; }
    @keyframes tlBarPulse {
      0% { height: 3px; opacity: 0.5; }
      100% { height: 11px; opacity: 1; filter: drop-shadow(0 0 4px rgba(168, 85, 247, 0.8)); }
    }
    .telemetry-dock-link {
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--accent);
      letter-spacing: 0.02em;
      transition: transform 0.18s ease, color 0.18s ease;
    }
    .telemetry-dock:hover .telemetry-dock-link {
      color: #e9d5ff;
      transform: translateX(2px);
    }
    .telemetry-dock-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
    }
    .telemetry-dock-tile {
      background: rgba(255, 255, 255, 0.025);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: var(--radius-sm);
      padding: 7px 9px;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;
      min-width: 0;
      position: relative;
      overflow: hidden;
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .telemetry-dock-tile::after {
      content: '';
      position: absolute;
      top: 0;
      left: -120%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
      transition: left 0.55s ease;
      pointer-events: none;
    }
    .telemetry-dock:hover .telemetry-dock-tile::after {
      left: 120%;
    }
    .telemetry-dock-tile:hover {
      transform: translateY(-2px) scale(1.02);
    }
    .t-dock-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      margin-bottom: 2px;
    }
    .t-dock-lbl {
      font-size: 0.58rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-sub);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .t-dock-ico {
      width: 12px;
      height: 12px;
      stroke: currentColor;
      fill: none;
      flex-shrink: 0;
      opacity: 0.75;
      transition: transform 0.2s ease, opacity 0.2s ease;
    }
    .telemetry-dock-tile:hover .t-dock-ico {
      transform: scale(1.15);
      opacity: 1;
    }
    .t-dock-val {
      font-size: 0.88rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      color: #fff;
      line-height: 1.15;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      width: 100%;
      transition: color 0.18s ease;
    }
    /* Stat Number Pop Animation */
    @keyframes statNumPop {
      0% { transform: scale(1.14); filter: brightness(1.35); }
      100% { transform: scale(1); filter: brightness(1); }
    }
    .stat-pop {
      animation: statNumPop 0.32s cubic-bezier(0.16, 1, 0.3, 1);
    }
    /* Unified 2-Color Palette: Purple & White (matching the website) */
    .telemetry-dock-tile,
    .telemetry-dock-tile.tile-views,
    .telemetry-dock-tile.tile-today,
    .telemetry-dock-tile.tile-time,
    .telemetry-dock-tile.tile-tracks,
    .telemetry-dock-tile.highlight-rose,
    .telemetry-dock-tile.highlight-cyan,
    .telemetry-dock-tile.highlight-green {
      background: rgba(168, 85, 247, 0.04);
      border-color: rgba(168, 85, 247, 0.18);
    }
    .telemetry-dock-tile .t-dock-ico,
    .telemetry-dock-tile.tile-views .t-dock-ico,
    .telemetry-dock-tile.tile-today .t-dock-ico,
    .telemetry-dock-tile.tile-time .t-dock-ico,
    .telemetry-dock-tile.tile-tracks .t-dock-ico {
      color: var(--accent);
    }
    .telemetry-dock-tile .t-dock-val,
    .telemetry-dock-tile.tile-views .t-dock-val,
    .telemetry-dock-tile.tile-today .t-dock-val,
    .telemetry-dock-tile.tile-time .t-dock-val,
    .telemetry-dock-tile.tile-tracks .t-dock-val {
      color: #ffffff;
      text-shadow: 0 0 10px rgba(168, 85, 247, 0.25);
    }
    .telemetry-dock-tile:hover,
    .telemetry-dock-tile.tile-views:hover,
    .telemetry-dock-tile.tile-today:hover,
    .telemetry-dock-tile.tile-time:hover,
    .telemetry-dock-tile.tile-tracks:hover {
      background: rgba(168, 85, 247, 0.1);
      border-color: rgba(168, 85, 247, 0.45);
      box-shadow: 0 4px 16px rgba(168, 85, 247, 0.22);
    }
    @media (max-width: 440px) {
      .telemetry-dock-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 6px;
      }
      .t-dock-val {
        font-size: 0.84rem;
      }
    }

    /* Dynamic Song Cover Art Fullscreen Background */
    .dynamic-cover-bg {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      pointer-events: none;
      z-index: 0;
      overflow: hidden;
      opacity: 0;
      transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .dynamic-cover-bg.active {
      opacity: 1;
    }
    .dynamic-cover-img {
      position: absolute;
      top: -10%;
      left: -10%;
      width: 120%;
      height: 120%;
      object-fit: cover;
      filter: blur(36px) saturate(1.35);
      transform: scale(1.04);
      transition: filter 0.3s ease, transform 0.08s ease;
      will-change: transform, filter;
    }
    .dynamic-cover-overlay {
      position: absolute;
      inset: 0;
      background: rgba(9, 9, 13, 0.62);
      transition: background 0.3s ease;
    }

    /* Ambient Audio-Reactive Background Canvas */
    .ambient-visualizer-canvas {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      pointer-events: none;
      z-index: 0;
      opacity: 0;
      transition: opacity 0.4s ease;
    }
    .ambient-visualizer-canvas.active {
      opacity: 0.75;
    }

    /* Cover Art Audio Reactive Dynamic Aura */
    .cover-visualizer-aura {
      position: absolute;
      inset: -14px;
      border-radius: 20px;
      pointer-events: none;
      z-index: 0;
      filter: blur(18px);
      opacity: 0;
      transition: opacity 0.35s ease, transform 0.08s ease;
      background: radial-gradient(circle, var(--accent) 0%, rgba(121, 40, 202, 0.45) 55%, transparent 80%);
    }
    .cover-visualizer-aura.active {
      opacity: 0.85;
    }

    /* Visualizer Presets Modal Grid */
    .vis-preset-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      margin: 12px 0 16px;
    }
    @media (max-width: 480px) {
      .vis-preset-grid {
        grid-template-columns: 1fr;
      }
    }
    .vis-preset-card {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: var(--radius-sm);
      padding: 10px 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      transition: all 0.2s var(--spring);
      user-select: none;
    }
    .vis-preset-card:hover {
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(255, 255, 255, 0.16);
      transform: translateY(-1px);
    }
    .vis-preset-card.active {
      background: var(--accent-muted);
      border-color: var(--accent);
      box-shadow: 0 0 14px var(--accent-glow);
    }
    .vis-preset-card .p-left {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }
    .vis-preset-card .p-name {
      font-size: 0.78rem;
      font-weight: 700;
      color: #fff;
    }
    .vis-preset-card.active .p-name {
      color: var(--accent-light);
    }
    .vis-preset-card .p-desc {
      font-size: 0.65rem;
      color: var(--text-sub);
    }
    .vis-tag {
      font-size: 0.58rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      padding: 2px 5px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--text-muted);
      letter-spacing: 0.03em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .vis-tag.accent {
      background: rgba(168, 85, 247, 0.2);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.3);
    }
    .vis-tag.ambient {
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .vis-tag.cover {
      background: rgba(244, 63, 94, 0.15);
      color: #fb7185;
      border: 1px solid rgba(244, 63, 94, 0.3);
    }

    /* Global Network Telemetry Header Bar */
    .telemetry-global-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(168, 85, 247, 0.08);
      border: 1px solid rgba(168, 85, 247, 0.22);
      border-radius: var(--radius-sm);
      padding: 8px 12px;
      margin-bottom: 14px;
      font-size: 0.76rem;
      color: var(--text-sub);
    }
    .telemetry-global-banner .tag-lead {
      color: var(--accent);
      font-weight: 700;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      font-size: 0.7rem;
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
      transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .telemetry-card:hover {
      border-color: rgba(168, 85, 247, 0.35);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), 0 0 16px rgba(168, 85, 247, 0.14);
    }
    .telemetry-card.highlight-card {
      background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(18, 18, 24, 0.95) 100%);
      border-color: rgba(168, 85, 247, 0.4);
      box-shadow: 0 4px 20px rgba(168, 85, 247, 0.14);
    }
    .telemetry-card.highlight-card:hover {
      border-color: rgba(168, 85, 247, 0.65);
      box-shadow: 0 8px 26px rgba(0, 0, 0, 0.5), 0 0 20px rgba(168, 85, 247, 0.25);
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
      transition: transform 0.2s ease;
    }
    .telemetry-card:hover .t-card-icon {
      transform: scale(1.1);
    }
    .t-card-icon svg {
      width: 14px;
      height: 14px;
    }
    .t-card-icon,
    .t-card-icon.purple,
    .t-card-icon.pink,
    .t-card-icon.blue,
    .t-card-icon.green {
      background: rgba(168, 85, 247, 0.14);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.3);
    }
    .t-card-val {
      font-size: 1.45rem;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #fff;
      letter-spacing: -0.02em;
    }
    .t-card-val.accent-val {
      color: #fff;
      text-shadow: 0 0 16px rgba(168, 85, 247, 0.5);
    }
    .t-card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      font-size: 0.7rem;
    }
    .t-tag,
    .t-tag.purple,
    .t-tag.pink,
    .t-tag.blue,
    .t-tag.green {
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 700;
      font-size: 0.62rem;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      background: rgba(168, 85, 247, 0.14);
      color: #d8b4fe;
    }
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
      background: linear-gradient(180deg, #ffffff 0%, #a855f7 100%);
      box-shadow: 0 0 8px rgba(168, 85, 247, 0.45);
    }
    .activity-bar.current {
      background: linear-gradient(180deg, #ffffff 0%, var(--accent) 100%);
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
      background: rgba(168, 85, 247, 0.14);
      border: 1px solid rgba(168, 85, 247, 0.35);
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

    /* Dynamic Theme Palettes */
    body.theme-cyan {
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.4);
      --accent-muted: rgba(56, 189, 248, 0.15);
      --border-accent: rgba(56, 189, 248, 0.35);
      --border-focus: #38bdf8;
    }
    body.theme-rose {
      --accent: #f43f5e;
      --accent-glow: rgba(244, 63, 94, 0.4);
      --accent-muted: rgba(244, 63, 94, 0.15);
      --border-accent: rgba(244, 63, 94, 0.35);
      --border-focus: #f43f5e;
    }
    body.theme-green {
      --accent: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.4);
      --accent-muted: rgba(16, 185, 129, 0.15);
      --border-accent: rgba(16, 185, 129, 0.35);
      --border-focus: #10b981;
    }
    body.theme-gold {
      --accent: #f59e0b;
      --accent-glow: rgba(245, 158, 11, 0.4);
      --accent-muted: rgba(245, 158, 11, 0.15);
      --border-accent: rgba(245, 158, 11, 0.35);
      --border-focus: #f59e0b;
    }

    /* Album Art Geometry Shapes */
    body.cover-shape-squircle .player-cover {
      border-radius: 28px !important;
    }
    body.cover-shape-circle .player-cover {
      border-radius: 50% !important;
    }

    /* Glassmorphism Blur Levels */
    body.blur-none .ui-card, body.blur-none header.app-header, body.blur-none .desktop-segment {
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
      background: #111116 !important;
    }
    body.blur-frosted .ui-card, body.blur-frosted header.app-header, body.blur-frosted .desktop-segment {
      backdrop-filter: blur(28px) saturate(180%) !important;
      -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    }

    /* Listen Together Two-Row Studio Layout */
    .lt-vol-row {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
    }
    .lt-telemetry-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      width: 100%;
      padding-top: 6px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 0.68rem;
      color: var(--text-sub);
    }
    .lt-status-indicator {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-weight: 600;
      color: var(--text-muted);
    }
    .lt-status-indicator.locked {
      color: var(--success);
    }
    .lt-status-indicator.buffering {
      color: #eab308;
    }
    .lt-telemetry-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      padding: 2px 7px;
      border-radius: 5px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text-muted);
    }

    /* Settings Tab Styles */
    .settings-group {
      margin-bottom: 20px;
    }
    .settings-group:last-child {
      margin-bottom: 0;
    }
    .settings-group-title {
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .settings-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .setting-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .setting-row:last-child {
      padding-bottom: 0;
      border-bottom: none;
    }
    .setting-info {
      flex: 1;
      min-width: 0;
    }
    .setting-label {
      font-size: 0.84rem;
      font-weight: 600;
      color: #fff;
    }
    .setting-desc {
      font-size: 0.7rem;
      color: var(--text-muted);
      margin-top: 2px;
      line-height: 1.35;
    }
    .setting-action {
      flex-shrink: 0;
    }
    .color-swatch-row {
      display: flex;
      gap: 8px;
    }
    .color-swatch {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 2px solid transparent;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }
    .color-swatch:hover {
      transform: scale(1.15);
    }
    .color-swatch.active {
      border-color: #fff;
      box-shadow: 0 0 10px currentColor;
    }
    .pill-selector {
      display: inline-flex;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 2px;
      gap: 2px;
    }
    .pill-opt {
      padding: 4px 10px;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
      border-radius: 6px;
      background: transparent;
      border: none;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .pill-opt:hover {
      color: #fff;
    }
    .pill-opt.active {
      background: var(--accent);
      color: #fff;
      box-shadow: 0 0 10px var(--accent-glow);
    }
    .switch-toggle {
      position: relative;
      display: inline-block;
      width: 42px;
      height: 24px;
    }
    .switch-toggle input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    .switch-slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 24px;
      transition: 0.25s;
    }
    .switch-slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background: white;
      border-radius: 50%;
      transition: 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    input:checked + .switch-slider {
      background: var(--accent);
      box-shadow: 0 0 8px var(--accent-glow);
    }
    input:checked + .switch-slider:before {
      transform: translateX(18px);
    }

    /* JuiceVault Playlists Section in Library */
    .jv-playlists-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .jv-playlist-card {
      background: rgba(255, 255, 255, 0.025);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      transition: all 0.18s ease;
    }
    .jv-playlist-card:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--border-accent);
      transform: translateY(-1px);
    }
    .jv-playlist-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }
    .jv-playlist-disc {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(236, 72, 153, 0.3));
      border: 1px solid var(--border-accent);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      flex-shrink: 0;
    }
    .jv-playlist-meta {
      min-width: 0;
    }
    .jv-playlist-title {
      font-size: 0.86rem;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .jv-playlist-sub {
      font-size: 0.7rem;
      color: var(--text-sub);
    }
    .jv-playlist-actions {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }

    /* Tab Onboarding & User Guide Popup Modal */
    .tutorial-modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 2100;
      background: rgba(6, 6, 10, 0.78);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.24s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .tutorial-modal-backdrop.active {
      opacity: 1;
      pointer-events: auto;
    }
    .tutorial-popup-card {
      background: linear-gradient(135deg, rgba(22, 22, 32, 0.98), rgba(13, 13, 19, 0.96));
      border: 1px solid var(--border-accent);
      border-radius: 18px;
      padding: 22px 22px 20px;
      max-width: 480px;
      width: 100%;
      position: relative;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65), 0 0 35px var(--accent-glow), inset 0 1px 0 rgba(255, 255, 255, 0.08);
      transform: scale(0.92) translateY(14px);
      transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .tutorial-modal-backdrop.active .tutorial-popup-card {
      transform: scale(1) translateY(0);
    }
    .tutorial-popup-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 3px;
      background: linear-gradient(90deg, var(--accent) 0%, rgba(168, 85, 247, 0.6) 60%, transparent 100%);
    }
    .tutorial-popup-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
      gap: 12px;
    }
    .tutorial-popup-title-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .tutorial-popup-icon-box {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: var(--accent-muted);
      border: 1px solid var(--border-accent);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--accent);
      flex-shrink: 0;
      box-shadow: 0 0 12px var(--accent-glow);
    }
    .tutorial-popup-title {
      font-size: 0.96rem;
      font-weight: 800;
      color: #fff;
      letter-spacing: -0.01em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tutorial-popup-sub {
      font-size: 0.72rem;
      color: var(--text-sub);
      margin-top: 2px;
    }
    .tutorial-popup-close {
      flex-shrink: 0;
    }
    .tutorial-popup-steps {
      display: flex;
      flex-direction: column;
      gap: 9px;
      margin-bottom: 12px;
    }
    .tutorial-step-tile {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: border-color 0.15s ease, background 0.15s ease;
    }
    .tutorial-step-tile:hover {
      border-color: rgba(255, 255, 255, 0.18);
      background: rgba(255, 255, 255, 0.05);
    }
    .tutorial-step-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.67rem;
      font-weight: 800;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-family: 'JetBrains Mono', monospace;
    }
    .tutorial-step-text {
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.44;
    }
    .tutorial-step-text strong {
      color: #f4f4f5;
      font-weight: 600;
    }
    .tutorial-step-text em {
      color: var(--text-sub);
      font-style: normal;
    }
    .tutorial-popup-tip {
      font-size: 0.72rem;
      color: var(--text-sub);
      background: rgba(168, 85, 247, 0.08);
      border: 1px solid rgba(168, 85, 247, 0.22);
      border-radius: 8px;
      padding: 8px 12px;
      margin-bottom: 14px;
      line-height: 1.45;
    }
    .tutorial-popup-tip code {
      color: var(--accent);
      background: rgba(168, 85, 247, 0.18);
      padding: 1px 5px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
    }
    .tutorial-popup-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid rgba(255, 255, 255, 0.07);
      padding-top: 12px;
      gap: 10px;
    }
    .tutorial-popup-badge {
      font-size: 0.68rem;
      color: var(--text-sub);
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-family: 'JetBrains Mono', monospace;
    }
    .btn-tab-help {
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-sub);
      border-radius: 6px;
      padding: 3px 8px;
      font-size: 0.71rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
    }
    .btn-tab-help:hover {
      color: var(--accent);
      border-color: var(--border-accent);
      background: var(--accent-muted);
    }
  </style>
</head>
<body>
  <div id="dynamicCoverBg" class="dynamic-cover-bg">
    <img id="dynamicCoverImg" class="dynamic-cover-img" alt="" src="">
    <div id="dynamicCoverOverlay" class="dynamic-cover-overlay"></div>
  </div>
  <canvas id="ambientVisualizerCanvas" class="ambient-visualizer-canvas"></canvas>
  <div class="backdrop-glow"></div>

  <!-- Header -->
  <header class="app-header">
    <div class="header-brand">
      <div class="brand-logo-disc">
        <svg class="icon-svg fill-current" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="#09090d"/></svg>
      </div>
      <div>
        <div class="brand-title">JuiceVault</div>
        <div class="brand-sub" style="font-size:0.62rem; color:var(--text-muted); font-family:'JetBrains Mono',monospace; line-height:1; margin-top:1px;">by <span style="color:#c084fc;">SKIZZOO</span> • domain by <span style="color:#38bdf8;">Spinti</span></div>
      </div>
      <span class="brand-tag">REMOTE</span>
      <div class="header-visualizer-wave" id="headerVisualizerWave" title="Active audio wave indicator">
        <span class="h-wave-bar"></span>
        <span class="h-wave-bar"></span>
        <span class="h-wave-bar"></span>
        <span class="h-wave-bar"></span>
        <span class="h-wave-bar"></span>
      </div>
    </div>

    <!-- Desktop Navigation Pill Bar (Combined Pic 2 & Pic 3 in Header) -->
    <div class="header-nav-wrap">
      <div class="segment-bar desktop-segment">
        <button class="segment-btn active" onclick="switchTab('queue')">
          <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
          <span>Queue</span>
        </button>
        <button class="segment-btn" onclick="switchTab('search')">
          <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span>Search</span>
        </button>
        <button class="segment-btn" onclick="switchTab('categories')">
          <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
          <span>Library</span>
        </button>
        <button class="segment-btn" onclick="switchTab('soundboard')">
          <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>
          <span>Sounds</span>
        </button>
        <button class="segment-btn" onclick="switchTab('shortcuts')">
          <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span>Shortcuts</span>
        </button>
        <button class="segment-btn" onclick="switchTab('settings')">
          <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          <span>Settings</span>
        </button>
      </div>
    </div>

    <div class="header-meta">
      <div class="status-badge header-user-badge" id="headerUserBadge" onclick="openUserModal()" title="JuiceVault.xyz Account — Tap to Connect">
        <img id="headerUserAvatar" class="header-user-avatar" src="https://api.juicevault.xyz/favicon.ico" alt="Avatar">
        <span id="headerUserName" style="max-width:88px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#fff;">Sign In</span>
      </div>
      <div class="status-badge" id="guildBadge" onclick="openGuildModal()" title="Current Discord Server — Tap to Switch" style="cursor:pointer; transition:border-color 0.15s, background 0.15s;">
        <svg class="icon-svg" style="width:13px;height:13px;color:var(--accent);" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span id="guildBadgeName" style="max-width:96px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#fff;">Server</span>
        <svg class="icon-svg" style="width:10px;height:10px;opacity:0.6;margin-left:-2px;" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
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

  <!-- Mobile Top Navigation Bar (Phone view) -->
  <nav class="mobile-nav" id="mobileNav">
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
    <button class="nav-btn" onclick="switchMobileNav('settings')">
      <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      <span>Settings</span>
    </button>
  </nav>

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
          <div class="player-visual-wrap">
            <div class="player-visual-ambient" id="artAmbient"></div>
            <div class="cover-visualizer-aura" id="coverVisualizerAura"></div>
            <div class="player-visual" id="artContainer">
              <img src="https://api.juicevault.xyz/favicon.ico" class="player-cover" id="coverImg" alt="Album Cover">
            </div>
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
              <button class="btn-fav" id="btnFavoriteSong" onclick="toggleCurrentSongFavorite()" title="Favorite track on JuiceVault">
                <svg class="icon-svg fav-icon" style="width:16px;height:16px;" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              </button>
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
              <span class="scrubber-tooltip" id="scrubberTooltip">0:00</span>
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
            <button class="btn-kinetic btn-flat" id="visualizerBtn" onclick="openVisualizerModal()">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><path d="M12 2v20M17 5v14M7 9v6M22 10v4M2 10v4"/></svg>
              <span id="visualizerBtnText">Visualizer</span>
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
            <button class="btn-kinetic btn-flat" id="userBtn" onclick="openUserModal()">
              <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              <span id="userBtnLabel">Account</span>
            </button>
          </div>

          <!-- Listen Together Studio Stream Card -->
          <div class="listen-together-card" id="liveAudioBanner" onwheel="handleVolumeWheel(event)">
            <div class="lt-header-row">
              <div class="lt-info-left">
                <div class="lt-icon-capsule">
                  <svg class="icon-svg lt-icon" viewBox="0 0 24 24"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
                  <span class="lt-live-indicator"></span>
                </div>
                <div class="lt-text-meta">
                  <div class="lt-title-line">
                    <span class="lt-title" id="liveStatusTitle">Listen Together</span>
                  </div>
                  <div class="lt-meta-sub-row">
                    <span class="lt-sync-badge" id="liveSyncBadge">1:1 SYNC</span>
                    <span class="lt-subtitle" id="liveStatusSub">Discord Voice Sync</span>
                  </div>
                </div>
              </div>
              <div class="lt-actions-right">
                <button class="btn-kinetic btn-lt-action" id="btnListenLive" onclick="toggleLiveAudio()" title="Stream synchronized audio directly in your browser">
                  <svg class="icon-svg lt-action-icon" id="liveBtnIcon" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></svg>
                  <span id="liveBtnLabel">Listen Live</span>
                </button>
              </div>
            </div>
            <div class="lt-controls-drawer" id="liveAudioControls" style="display:none; flex-direction:column; gap:8px;">
              <div class="lt-vol-row">
                <svg class="icon-svg lt-vol-icon" viewBox="0 0 24 24"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
                <input type="range" min="0" max="1" step="any" value="1" id="liveVolumeSlider" class="lt-volume-slider" oninput="updateLiveVolume(this.value)" aria-label="Stream volume">
                <span id="liveVolPercent" class="lt-vol-val">100%</span>
              </div>
              <div class="lt-telemetry-row">
                <div class="lt-status-indicator locked" id="ltStatusInd" onclick="forceStreamRefresh(false)" title="Stream Status (Click to force refresh)" style="cursor:pointer;">
                  <span class="lt-drift-dot" style="width:6px; height:6px;"></span>
                  <span id="ltStatusText">Phase-Locked</span>
                </div>
                <div class="lt-telemetry-pill" id="ltDriftPill" onclick="forceStreamRefresh(false)" title="PLL Clock Drift vs Discord Bot Master (Click to force refresh)" style="cursor:pointer;">
                  <span id="syncDriftLabel">±0ms</span>
                </div>
                <div class="lt-telemetry-pill" title="Audio Stream Quality">
                  <span>320 kbps Studio</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Studio Telemetry Dock -->
          <div class="telemetry-dock" id="telemetryDock" onclick="openStatsModal()" title="Open detailed global telemetry and playback metrics">
            <div class="telemetry-dock-header">
              <div class="telemetry-dock-tag">
                <div class="telemetry-live-bars">
                  <span class="tl-bar"></span>
                  <span class="tl-bar"></span>
                  <span class="tl-bar"></span>
                </div>
                <span>GLOBAL TELEMETRY</span>
              </div>
              <span class="telemetry-dock-link">Live Metrics &rsaquo;</span>
            </div>
            <div class="telemetry-dock-grid">
              <div class="telemetry-dock-tile tile-views">
                <div class="t-dock-head">
                  <span class="t-dock-lbl">Views</span>
                  <svg class="t-dock-ico" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </div>
                <span class="t-dock-val" id="quickTotalViews">--</span>
              </div>
              <div class="telemetry-dock-tile tile-today">
                <div class="t-dock-head">
                  <span class="t-dock-lbl">Today</span>
                  <svg class="t-dock-ico" viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
                </div>
                <span class="t-dock-val" id="quickDailyViews">--</span>
              </div>
              <div class="telemetry-dock-tile tile-time">
                <div class="t-dock-head">
                  <span class="t-dock-lbl">Time</span>
                  <svg class="t-dock-ico" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </div>
                <span class="t-dock-val" id="quickDailyTime">--</span>
              </div>
              <div class="telemetry-dock-tile tile-tracks">
                <div class="t-dock-head">
                  <span class="t-dock-lbl">Tracks</span>
                  <svg class="t-dock-ico" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
                </div>
                <span class="t-dock-val" id="quickDailyTracks">--</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: TABS (Queue, Search, Collections, Shortcuts) -->
      <div class="card-content-wrap">
        <!-- TAB: QUEUE -->
        <div class="tab-content active" id="tab-queue">
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="search-input-group" style="margin-bottom:12px;">
              <svg class="icon-svg" style="color:var(--text-sub); width:15px; height:15px;" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="search-field" id="queueFilterInput" placeholder="Filter queued tracks…" oninput="filterQueueDisplay(this.value)">
            </div>
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

          <div class="ui-card" style="margin-top:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--text-sub);" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                Recently Played (Last 5 History) (<span id="historyCount">0</span>)
              </span>
            </div>
            <div class="track-list" id="historyList">
              <div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No recently played tracks yet.</div>
            </div>
          </div>
        </div>

        <!-- TAB: SEARCH -->
        <div class="tab-content" id="tab-search">
          <div class="ui-card">
            <div class="section-header" style="margin-bottom:12px;">
              <span class="section-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                Track Search
              </span>
              <button class="btn-tab-help" onclick="openTutorialPopup('search')" title="View Search Guide">
                <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <span>Guide</span>
              </button>
            </div>
            <div class="search-input-group">
              <svg class="icon-svg" style="color:var(--text-sub);" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="search-field" id="searchInput" placeholder="Search song title or artist…" oninput="handleSearchInput(event)" onkeydown="if(event.key==='Enter') executeSearch()">
              <button class="btn-clear-search" id="clearSearchBtn" onclick="clearSearchField()" title="Clear search" style="display:none;">
                <svg class="icon-svg" style="width:14px;height:14px;" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
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
                  <button class="btn-tab-help" onclick="openTutorialPopup('library')" title="View Library Guide">
                    <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                    <span>Guide</span>
                  </button>
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
          <!-- JuiceVault.xyz Account Playlists & Liked Songs -->
          <div class="ui-card" id="jvPlaylistsCard" style="margin-bottom:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" style="color:#ec4899;" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                My JuiceVault.xyz Playlists &amp; Likes
              </span>
              <button class="btn-kinetic btn-flat" style="font-size:0.72rem; padding:4px 8px;" onclick="loadJuiceVaultPlaylists(true)">
                <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                <span>Sync</span>
              </button>
            </div>
            <div id="jvPlaylistsContent">
              <div style="font-size:0.78rem; color:var(--text-sub); text-align:center; padding:16px 8px;">
                Connect your JuiceVault.xyz account to access your personal playlists and liked songs.
                <div style="margin-top:10px;">
                  <button class="btn-kinetic btn-primary" style="padding:6px 14px; font-size:0.75rem;" onclick="openUserModal()">Connect Account</button>
                </div>
              </div>
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
          <!-- Keyboard Hotkeys Card -->
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="6" y1="8" x2="6.01" y2="8"/><line x1="10" y1="8" x2="10.01" y2="8"/><line x1="14" y1="8" x2="14.01" y2="8"/><line x1="18" y1="8" x2="18.01" y2="8"/><line x1="8" y1="16" x2="16" y2="16"/></svg>
                Desktop Keyboard Hotkeys
              </span>
              <button class="btn-tab-help" onclick="openTutorialPopup('shortcuts')" title="View Shortcuts Guide">
                <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <span>Guide</span>
              </button>
            </div>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); gap:8px;">
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">Space</span>
                <span style="font-size:0.75rem; color:#fff;">Play / Pause</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">→ / ←</span>
                <span style="font-size:0.75rem; color:#fff;">Seek ±10s</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">Shift+→</span>
                <span style="font-size:0.75rem; color:#fff;">Skip Track</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">Shift+←</span>
                <span style="font-size:0.75rem; color:#fff;">Previous Track</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">S</span>
                <span style="font-size:0.75rem; color:#fff;">Shuffle Queue</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">R</span>
                <span style="font-size:0.75rem; color:#fff;">Repeat Track</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">L</span>
                <span style="font-size:0.75rem; color:#fff;">View Lyrics</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">/</span>
                <span style="font-size:0.75rem; color:#fff;">Focus Search</span>
              </div>
              <div class="track-card" style="padding:8px 12px; gap:8px;">
                <span class="btn-badge" style="font-family:'JetBrains Mono',monospace;">Esc</span>
                <span style="font-size:0.75rem; color:#fff;">Close Modals</span>
              </div>
            </div>
          </div>

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
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>Guild: <span id="guildName" style="color:#fff;">--</span></div>
                <button class="btn-kinetic btn-badge" style="font-size:0.68rem; padding:2px 7px;" onclick="openGuildModal()">Switch</button>
              </div>
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
                <button class="btn-tab-help" onclick="openTutorialPopup('soundboard')" title="View Soundboard Guide">
                  <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  <span>Guide</span>
                </button>
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
                  <input type="checkbox" id="sbPreviewToggle" checked style="accent-color:var(--accent);" onchange="try{localStorage.setItem('jv_sb_preview', this.checked ? 'true' : 'false')}catch(e){}">
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

        <!-- TAB: SETTINGS -->
        <div class="tab-content" id="tab-settings">
          <div class="ui-card" style="margin-bottom:14px;">
            <div class="section-header">
              <span class="section-title">
                <svg class="icon-svg" style="color:var(--accent);" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                Remote &amp; Studio Settings
              </span>
              <div style="display:flex; align-items:center; gap:8px;">
                <button class="btn-tab-help" onclick="openTutorialPopup('settings')" title="View Settings Guide">
                  <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  <span>Guide</span>
                </button>
                <span class="btn-badge" style="font-size:0.68rem; padding:2px 8px;">Auto-Saved</span>
              </div>
            </div>

            <!-- Group 1: Audio & Studio Streaming -->
            <div class="settings-group">
              <div class="settings-group-title">
                <svg class="icon-svg" style="width:13px;height:13px;" viewBox="0 0 24 24"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
                Audio &amp; Synchronization
              </div>
              <div class="settings-card">
                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Listen Together Buffer Latency</div>
                    <div class="setting-desc">Adaptive PLL clock buffer mode. Gecko/Zen and Firefox users should keep Stable to prevent audio clicks.</div>
                  </div>
                  <div class="setting-action">
                    <div class="pill-selector" id="settingLatencySelector">
                      <button class="pill-opt" data-val="low" onclick="setLatencyMode('low')">Ultra (250ms)</button>
                      <button class="pill-opt" data-val="balanced" onclick="setLatencyMode('balanced')">Balanced</button>
                      <button class="pill-opt active" data-val="stable" onclick="setLatencyMode('stable')">Stable (Gecko)</button>
                    </div>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Volume Wheel Velocity Curve</div>
                    <div class="setting-desc">1% per deliberate scroll notch. Flicking fast accelerates dynamically to 2%–5% with gradual smoothing.</div>
                  </div>
                  <div class="setting-action">
                    <div class="pill-selector" id="settingVolCurveSelector">
                      <button class="pill-opt active" data-val="adaptive" onclick="setVolWheelCurve('adaptive')">Adaptive (1%–5%)</button>
                      <button class="pill-opt" data-val="linear" onclick="setVolWheelCurve('linear')">Fixed 1%</button>
                    </div>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Soundboard Browser Preview</div>
                    <div class="setting-desc">Audition meme sound clips directly in your browser before triggering on Discord.</div>
                  </div>
                  <div class="setting-action">
                    <label class="switch-toggle">
                      <input type="checkbox" id="settingSbPreviewToggle" onchange="setSoundboardPreview(this.checked)">
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>

                <div class="setting-row" id="settingSbVolRow">
                  <div class="setting-info">
                    <div class="setting-label">Soundboard Preview Volume</div>
                    <div class="setting-desc">Volume gain applied to local in-browser soundboard previews.</div>
                  </div>
                  <div class="setting-action" style="display:flex; align-items:center; gap:8px;">
                    <input type="range" min="0" max="1" step="0.05" value="0.75" id="settingSbVolSlider" style="width:100px; accent-color:var(--accent);" oninput="setSoundboardPreviewVol(this.value)">
                    <span id="settingSbVolPct" style="font-size:0.75rem; color:var(--text-muted); font-family:'JetBrains Mono',monospace; min-width:32px;">75%</span>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Hardware Media Keys &amp; Lockscreen</div>
                    <div class="setting-desc">Allows keyboard media keys, headphone controls, and gaming mouse buttons to control playback.</div>
                  </div>
                  <div class="setting-action">
                    <label class="switch-toggle">
                      <input type="checkbox" id="settingMediaSessionToggle" checked onchange="setLockScreenControls(this.checked)">
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Group 2: Theme & Visual Appearance -->
            <div class="settings-group">
              <div class="settings-group-title">
                <svg class="icon-svg" style="width:13px;height:13px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>
                Theme &amp; Visual Appearance
              </div>
              <div class="settings-card">
                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Accent Theme Palette</div>
                    <div class="setting-desc">Custom neon highlight and glow color across cards, sliders, and buttons.</div>
                  </div>
                  <div class="setting-action">
                    <div class="color-swatch-row">
                      <div class="color-swatch active" style="background:#a855f7; color:#a855f7;" data-theme="purple" onclick="setThemeAccent('purple')" title="Neon Purple (Default)"></div>
                      <div class="color-swatch" style="background:#38bdf8; color:#38bdf8;" data-theme="cyan" onclick="setThemeAccent('cyan')" title="Electric Cyan"></div>
                      <div class="color-swatch" style="background:#f43f5e; color:#f43f5e;" data-theme="rose" onclick="setThemeAccent('rose')" title="Rose Pink"></div>
                      <div class="color-swatch" style="background:#10b981; color:#10b981;" data-theme="green" onclick="setThemeAccent('green')" title="Emerald Green"></div>
                      <div class="color-swatch" style="background:#f59e0b; color:#f59e0b;" data-theme="gold" onclick="setThemeAccent('gold')" title="Cyber Gold"></div>
                    </div>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Album Art Geometry</div>
                    <div class="setting-desc">Shape geometry for current song artwork on the main player card.</div>
                  </div>
                  <div class="setting-action">
                    <div class="pill-selector" id="settingCoverShapeSelector">
                      <button class="pill-opt active" data-val="modern" onclick="setCoverShape('modern')">Modern (16px)</button>
                      <button class="pill-opt" data-val="squircle" onclick="setCoverShape('squircle')">Squircle (28px)</button>
                      <button class="pill-opt" data-val="circle" onclick="setCoverShape('circle')">Vinyl Disc</button>
                    </div>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Glassmorphism Blur Filter</div>
                    <div class="setting-desc">Backdrop blur intensity for navigation headers and cards. Turn off for maximum FPS on low-power devices.</div>
                  </div>
                  <div class="setting-action">
                    <div class="pill-selector" id="settingGlassSelector">
                      <button class="pill-opt" data-val="none" onclick="setGlassBlur('none')">Flat (0px)</button>
                      <button class="pill-opt active" data-val="frosted" onclick="setGlassBlur('frosted')">Frosted (16px)</button>
                      <button class="pill-opt" data-val="deep" onclick="setGlassBlur('deep')">Deep (28px)</button>
                    </div>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Dynamic Ambient Aurora Waves</div>
                    <div class="setting-desc">Default backdrop effect initialized when remote opens. Seamless reactive audio pulse.</div>
                  </div>
                  <div class="setting-action">
                    <label class="switch-toggle">
                      <input type="checkbox" id="settingAuroraToggle" checked onchange="setAuroraDefaultToggle(this.checked)">
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Group 3: JuiceVault.xyz Account Integration -->
            <div class="settings-group">
              <div class="settings-group-title">
                <svg class="icon-svg" style="width:13px;height:13px;" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                JuiceVault.xyz Account Sync
              </div>
              <div class="settings-card">
                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label" id="settingUserStatusLabel">Account Status</div>
                    <div class="setting-desc" id="settingUserStatusDesc">Not signed in. Connect to sync your playlists and liked tracks.</div>
                  </div>
                  <div class="setting-action">
                    <button class="btn-kinetic btn-primary" id="settingUserActionBtn" style="padding:6px 12px; font-size:0.75rem;" onclick="openUserModal()">
                      Connect Account
                    </button>
                  </div>
                </div>

                <div class="setting-row" id="settingUserSyncRow" style="display:none;">
                  <div class="setting-info">
                    <div class="setting-label">Sync Playlists &amp; Likes</div>
                    <div class="setting-desc">Fetch and refresh your custom playlists and library from the official API.</div>
                  </div>
                  <div class="setting-action">
                    <button class="btn-kinetic btn-flat" style="padding:6px 12px; font-size:0.75rem;" onclick="loadJuiceVaultPlaylists(true)">
                      Sync Now
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Group 4: Storage & Maintenance -->
            <div class="settings-group">
              <div class="settings-group-title">
                <svg class="icon-svg" style="width:13px;height:13px;" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                Cache &amp; Reset
              </div>
              <div class="settings-card">
                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Clear Remote Web Cache</div>
                    <div class="setting-desc">Clears cached track queues, soundboard samples, and temporary browser storage.</div>
                  </div>
                  <div class="setting-action">
                    <button class="btn-kinetic btn-flat" style="padding:6px 12px; font-size:0.75rem;" onclick="clearAppCache()">
                      Clear Cache
                    </button>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Reset Tab Guides &amp; Walkthrough Popups</div>
                    <div class="setting-desc">Re-enables the 1-time animated walkthrough popups across Search, Library, Sounds, Shortcuts, and Settings.</div>
                  </div>
                  <div class="setting-action">
                    <button class="btn-kinetic btn-flat" style="padding:6px 12px; font-size:0.75rem;" onclick="resetAllTabTutorials()">
                      Reset Popups
                    </button>
                  </div>
                </div>

                <div class="setting-row">
                  <div class="setting-info">
                    <div class="setting-label">Factory Reset Remote Settings</div>
                    <div class="setting-desc">Restores all visual and audio settings back to original factory defaults.</div>
                  </div>
                  <div class="setting-action">
                    <button class="btn-kinetic btn-flat" style="padding:6px 12px; font-size:0.75rem; color:var(--danger);" onclick="resetAllSettings()">
                      Reset Defaults
                    </button>
                  </div>
                </div>
              </div>
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

  <!-- Mobile Floating Mini-Player Bar (Visible when browsing other tabs on phones) -->
  <div id="mobileMiniPlayer" class="mobile-mini-player" onclick="switchMobileNav('player')">
    <div class="mini-progress-line" id="miniProgressLine"></div>
    <div class="mini-player-left">
      <img src="https://api.juicevault.xyz/favicon.ico" class="mini-player-thumb" id="miniThumb" alt="Cover">
      <div class="mini-player-info">
        <div class="mini-player-title" id="miniTitle">Connecting…</div>
        <div class="mini-player-artist" id="miniArtist">Juice WRLD</div>
      </div>
    </div>
    <div class="mini-player-actions" onclick="event.stopPropagation()">
      <button class="btn-kinetic btn-circle btn-mini-action" onclick="action('toggle')" title="Play / Pause">
        <svg class="icon-svg fill-current" id="miniPlayIcon" style="width:14px;height:14px;" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></svg>
      </button>
      <button class="btn-kinetic btn-circle btn-mini-action" onclick="action('skip')" title="Skip Track">
        <svg class="icon-svg" style="width:13px;height:13px;" viewBox="0 0 24 24"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
      </button>
    </div>
  </div>

  <!-- Tab Tutorial / User Onboarding Popup Modal -->
  <div class="tutorial-modal-backdrop" id="tutorialModal" onclick="if(event.target===this) closeTutorialPopup()">
    <div class="tutorial-popup-card">
      <div class="tutorial-popup-header">
        <div class="tutorial-popup-title-wrap">
          <div class="tutorial-popup-icon-box" id="tutModalIcon">
            <svg class="icon-svg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </div>
          <div>
            <div class="tutorial-popup-title" id="tutModalTitle">Tab Guide &amp; Walkthrough</div>
            <div class="tutorial-popup-sub" id="tutModalSub">Feature tips and quick controls</div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm tutorial-popup-close" onclick="closeTutorialPopup()" title="Close guide (Esc)">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div class="tutorial-popup-steps" id="tutModalSteps"></div>

      <div class="tutorial-popup-tip" id="tutModalTip"></div>

      <div class="tutorial-popup-footer">
        <span class="tutorial-popup-badge">
          <svg class="icon-svg" style="width:11px;height:11px;" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <span id="tutModalFooterNote">First-Time Tab Tour • Shown 1 Time</span>
        </span>
        <button class="btn-kinetic btn-primary" onclick="closeTutorialPopup()" style="padding:8px 18px; font-weight:700; font-size:0.8rem;">
          <span>Got it, explore!</span>
        </button>
      </div>
    </div>
  </div>

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

  <!-- JuiceVault User Modal Sheet -->
  <div class="sheet-backdrop" id="userSheet" onclick="if(event.target===this) closeUserModal()">
    <div class="sheet-panel" style="max-width:440px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <div class="brand-logo-disc" style="width:34px; height:34px; border-radius:10px; background:linear-gradient(135deg, #ec4899, #a855f7); display:flex; align-items:center; justify-content:center;">
            <svg class="icon-svg" style="width:16px;height:16px;color:#fff;" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div>
            <div style="font-weight:700; font-size:0.92rem; color:#fff;">JuiceVault.xyz Account</div>
            <div style="font-size:0.72rem; color:var(--text-muted);">Sync profile &amp; save favorite tracks</div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeUserModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- Profile View (when logged in) -->
      <div id="userProfileView" style="display:none;">
        <div style="display:flex; align-items:center; gap:12px; padding:12px; background:rgba(255,255,255,0.03); border:1px solid var(--border); border-radius:var(--radius-md); margin-bottom:12px;">
          <img id="userCardAvatar" src="https://api.juicevault.xyz/favicon.ico" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:2px solid var(--border-accent);" alt="Avatar">
          <div style="min-width:0; flex:1;">
            <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
              <span id="userCardDisplayName" style="font-weight:700; font-size:0.95rem; color:#fff;">User</span>
              <span id="userCardBadges" style="display:inline-flex; gap:4px; flex-wrap:wrap;"></span>
            </div>
            <div id="userCardHandle" style="font-size:0.75rem; color:var(--text-sub); font-family:'JetBrains Mono',monospace;">@username</div>
            <div id="userCardBio" style="font-size:0.72rem; color:var(--text-muted); margin-top:2px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"></div>
          </div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:6px; margin-bottom:14px; text-align:center;">
          <div style="padding:8px 4px; background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:var(--radius-sm);">
            <div id="userLikedCount" style="font-weight:700; font-size:0.9rem; color:#f43f5e;">0</div>
            <div style="font-size:0.65rem; color:var(--text-sub); text-transform:uppercase;">Likes</div>
          </div>
          <div style="padding:8px 4px; background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:var(--radius-sm);">
            <div id="userListensCount" style="font-weight:700; font-size:0.9rem; color:var(--accent);">0</div>
            <div style="font-size:0.65rem; color:var(--text-sub); text-transform:uppercase;">Listens</div>
          </div>
          <div style="padding:8px 4px; background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:var(--radius-sm);">
            <div id="userUniqueCount" style="font-weight:700; font-size:0.9rem; color:#10b981;">0</div>
            <div style="font-size:0.65rem; color:var(--text-sub); text-transform:uppercase;">Songs</div>
          </div>
          <div style="padding:8px 4px; background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:var(--radius-sm);">
            <div id="userStreakCount" style="font-weight:700; font-size:0.9rem; color:#38bdf8;">0d</div>
            <div style="font-size:0.65rem; color:var(--text-sub); text-transform:uppercase;">Streak</div>
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn-kinetic btn-flat" style="flex:1; justify-content:center; color:#f43f5e;" onclick="viewUserFavorites()">
            Favorites (<span id="userFavsBtnCount">0</span>)
          </button>
          <button class="btn-kinetic btn-flat" style="flex:1; justify-content:center; color:var(--accent);" onclick="loadJuiceVaultPlaylists(true)">
            Sync Playlists
          </button>
          <button class="btn-kinetic btn-flat" style="justify-content:center; color:var(--text-muted); padding:6px 10px;" onclick="logoutUser()">
            Log Out
          </button>
        </div>
      </div>

      <!-- Login Form (when not logged in) -->
      <div id="userLoginForm">
        <!-- Auth Mode Toggle -->
        <div style="display:flex; background:rgba(0,0,0,0.4); border:1px solid var(--border); border-radius:8px; padding:3px; margin-bottom:14px; gap:4px;">
          <button id="authTabLogin" class="btn-kinetic" style="flex:1; padding:6px; font-size:0.75rem; border-radius:6px; background:var(--accent); color:#fff; border:none;" onclick="switchAuthMode('login')">Account Sign In</button>
          <button id="authTabPublic" class="btn-kinetic" style="flex:1; padding:6px; font-size:0.75rem; border-radius:6px; background:transparent; color:var(--text-muted); border:none;" onclick="switchAuthMode('public')">Public Username</button>
        </div>

        <!-- Full Login Panel -->
        <div id="authPanelLogin">
          <p style="font-size:0.78rem; color:var(--text-muted); line-height:1.45; margin-bottom:12px;">
            Sign in with your <strong>juicevault.xyz</strong> credentials to sync private playlists, likes, and full account stats.
          </p>
          <div style="display:flex; flex-direction:column; gap:8px; margin-bottom:10px;">
            <input type="text" id="jvAuthLoginInput" class="search-field" placeholder="Username or Email" style="background:rgba(0,0,0,0.5); border:1px solid var(--border); border-radius:var(--radius-sm); padding:9px 12px; color:#fff;" onkeydown="if(event.key==='Enter') loginJuiceVaultUserFull()">
            <input type="password" id="jvAuthPassInput" class="search-field" placeholder="Password" style="background:rgba(0,0,0,0.5); border:1px solid var(--border); border-radius:var(--radius-sm); padding:9px 12px; color:#fff;" onkeydown="if(event.key==='Enter') loginJuiceVaultUserFull()">
          </div>
          <button class="btn-kinetic btn-primary" id="jvAuthLoginBtn" style="width:100%; padding:10px; font-size:0.82rem; justify-content:center;" onclick="loginJuiceVaultUserFull()">
            Sign In to JuiceVault.xyz
          </button>
        </div>

        <!-- Public Connect Panel -->
        <div id="authPanelPublic" style="display:none;">
          <p style="font-size:0.78rem; color:var(--text-muted); line-height:1.45; margin-bottom:12px;">
            Enter any public <strong>juicevault.xyz</strong> username to display profile badges and stream their public likes.
          </p>
          <div style="display:flex; gap:8px; margin-bottom:8px;">
            <input type="text" id="jvUsernameInput" class="search-field" placeholder="Username (e.g. ajaxfnc)" style="background:rgba(0,0,0,0.5); border:1px solid var(--border); border-radius:var(--radius-sm); padding:9px 12px; color:#fff;" onkeydown="if(event.key==='Enter') loginJuiceVaultUser()">
            <button class="btn-kinetic btn-badge" style="padding:8px 14px;" onclick="loginJuiceVaultUser()">Connect</button>
          </div>
        </div>

        <div id="jvLoginError" style="font-size:0.74rem; color:var(--danger); display:none; margin-top:8px;"></div>
      </div>
    </div>
  </div>

  <!-- Server / Guild Switcher Modal Sheet -->
  <div class="sheet-backdrop" id="guildSheet" onclick="if(event.target===this) closeGuildModal()">
    <div class="sheet-panel" style="max-width:440px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <div style="display:flex; align-items:center; gap:10px; min-width:0;">
          <div class="cat-icon-badge" style="width:36px; height:36px; border-radius:10px; background:rgba(192, 132, 252, 0.15); border:1px solid rgba(192, 132, 252, 0.35); color:#c084fc;">
            <svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div style="min-width:0;">
            <div style="font-weight:700; font-size:0.95rem; color:#fff;">Switch Discord Server</div>
            <div style="font-size:0.73rem; color:var(--text-muted); margin-top:1px;">Select server to control via Web Remote</div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeGuildModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div id="guildListContainer" style="display:flex; flex-direction:column; gap:8px; max-height:300px; overflow-y:auto; padding-right:2px;">
        <div style="text-align:center; padding:18px; color:var(--text-sub); font-size:0.8rem;">Loading servers...</div>
      </div>

      <button class="btn-kinetic btn-flat" style="padding:12px; margin-top:14px; width:100%; justify-content:center;" onclick="closeGuildModal()">
        Close
      </button>
    </div>
  </div>

  <!-- Visualizer Studio Modal Sheet -->
  <div class="sheet-backdrop" id="visualizerModal" onclick="if(event.target===this) closeVisualizerModal()">
    <div class="sheet-panel" style="max-width:540px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <div class="cat-icon-badge" style="width:36px; height:36px; border-radius:10px; background:var(--accent-muted); border:1px solid rgba(168,85,247,0.3); color:var(--accent);">
            <svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><path d="M12 2v20M17 5v14M7 9v6M22 10v4M2 10v4"/></svg>
          </div>
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="font-weight:700; font-size:0.95rem; color:#fff;">Audio Reactive Visualizer</div>
              <span class="lt-sync-badge live" id="visActiveBadge">Active</span>
            </div>
            <div style="font-size:0.72rem; color:var(--text-sub); margin-top:1px;">10 Presets • Background &amp; Album Art Dynamics</div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeVisualizerModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- Master Switch -->
      <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:var(--radius-sm); margin-bottom:12px;">
        <div>
          <div style="font-size:0.8rem; font-weight:700; color:#fff;">Reactive Visualizer</div>
          <div style="font-size:0.68rem; color:var(--text-sub);">Full-screen canvas &amp; dynamic cover aura</div>
        </div>
        <button class="btn-kinetic btn-lt-action" id="visToggleMasterBtn" onclick="toggleVisualizerState()">
          <span id="visToggleMasterLabel">Enabled</span>
        </button>
      </div>

      <!-- Presets Grid (10 Presets) -->
      <div style="font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-sub); margin-bottom:6px;">Select Preset</div>
      <div class="vis-preset-grid" id="visPresetList"></div>

      <!-- Sliders for Intensity & Sensitivity -->
      <div style="display:flex; flex-direction:column; gap:10px; padding:12px 14px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:var(--radius-sm); margin-bottom:14px;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <span style="font-size:0.72rem; color:var(--text-muted);">Background Opacity</span>
          <input type="range" min="0.1" max="1" step="0.05" value="0.75" id="visOpacitySlider" class="lt-volume-slider" oninput="updateVisualizerOpacity(this.value)" style="width:160px;">
          <span id="visOpacityVal" style="font-size:0.68rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub); min-width:32px;">75%</span>
        </div>
        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <span style="font-size:0.72rem; color:var(--text-muted);">Motion Sensitivity</span>
          <input type="range" min="0.5" max="2" step="0.1" value="1" id="visSensSlider" class="lt-volume-slider" oninput="updateVisualizerSens(this.value)" style="width:160px;">
          <span id="visSensVal" style="font-size:0.68rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub); min-width:32px;">1.0x</span>
        </div>
      </div>

      <!-- Song Cover Background Controls -->
      <div style="font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-sub); margin-bottom:6px;">Song Cover Background</div>
      <div style="display:flex; flex-direction:column; gap:10px; padding:12px 14px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:var(--radius-sm); margin-bottom:14px;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <div>
            <div style="font-size:0.78rem; font-weight:600; color:#fff;">Cover Art as Background</div>
            <div style="font-size:0.68rem; color:var(--text-sub);">Soft blurred album art backdrop</div>
          </div>
          <label style="display:flex; align-items:center; cursor:pointer;">
            <input type="checkbox" id="visCoverBgToggle" checked style="accent-color:var(--accent); width:18px; height:18px;" onchange="updateCoverBgToggle(this.checked)">
          </label>
        </div>
        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <span style="font-size:0.72rem; color:var(--text-muted);">Background Blur</span>
          <input type="range" min="10" max="80" step="2" value="36" id="visCoverBlurSlider" class="lt-volume-slider" oninput="updateCoverBlur(this.value)" style="width:160px;">
          <span id="visCoverBlurVal" style="font-size:0.68rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub); min-width:36px;">36px</span>
        </div>
        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <span style="font-size:0.72rem; color:var(--text-muted);">Background Dimming</span>
          <input type="range" min="20" max="90" step="5" value="62" id="visCoverDimSlider" class="lt-volume-slider" oninput="updateCoverDim(this.value)" style="width:160px;">
          <span id="visCoverDimVal" style="font-size:0.68rem; font-family:'JetBrains Mono',monospace; color:var(--text-sub); min-width:36px;">62%</span>
        </div>
        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
          <div>
            <div style="font-size:0.75rem; color:#fff;">Reactive Bass Pulse</div>
            <div style="font-size:0.66rem; color:var(--text-sub);">Subtle breathing pulse on heavy beats</div>
          </div>
          <label style="display:flex; align-items:center; cursor:pointer;">
            <input type="checkbox" id="visCoverPulseToggle" checked style="accent-color:var(--accent); width:16px; height:16px;" onchange="updateCoverPulseToggle(this.checked)">
          </label>
        </div>
      </div>

      <div style="display:flex; gap:8px;">
        <button class="btn-kinetic btn-flat" style="padding:10px; flex:1; justify-content:center; color:var(--text-muted);" onclick="resetVisualizerSettings()">
          Reset Defaults
        </button>
        <button class="btn-kinetic btn-primary" style="padding:10px; flex:2; justify-content:center;" onclick="closeVisualizerModal()">
          Done
        </button>
      </div>
    </div>
  </div>

  <!-- Live Telemetry & Daily Usage Full Modal Sheet -->
  <div class="sheet-backdrop" id="statsSheet" onclick="if(event.target===this) closeStatsModal()">
    <div class="sheet-panel" style="max-width:560px;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:12px;">
          <div class="brand-logo-disc" style="width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg, var(--accent), #7928ca); box-shadow:0 0 18px var(--accent-glow); display:flex; align-items:center; justify-content:center;">
            <svg class="icon-svg" style="width:20px;height:20px;color:#fff;" viewBox="0 0 24 24"><path d="M4.93 4.93a10 10 0 0 1 14.14 0"/><path d="M7.76 7.76a6 6 0 0 1 8.48 0"/><circle cx="12" cy="12" r="2"/><path d="M12 14v8"/></svg>
          </div>
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="font-weight:800; font-size:1.02rem; color:#fff;">Live Telemetry &amp; Daily Usage</div>
              <span class="telemetry-live-pill"><span class="pulse-ring"></span>LIVE</span>
            </div>
            <div id="statsSubtitle" style="font-size:0.74rem; color:var(--text-sub); margin-top:2px;">
              Real-time web traffic, unique visitors &amp; 24/7 stream statistics
            </div>
          </div>
        </div>
        <button class="btn-kinetic btn-circle btn-action-sm" onclick="closeStatsModal()">
          <svg class="icon-svg" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- Scope Selector: Current Server vs All Servers (Global) -->
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
          <span class="t-detail-label">Active Listeners / Sessions:</span>
          <span class="t-detail-value"><span class="status-dot"></span> <span id="statsWsCount">1</span> connected now</span>
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
          <span class="t-detail-label">Audio Pipeline:</span>
          <span class="t-detail-value" style="color:var(--accent);">24/7 Lossless PCM • 1:1 Live Sync</span>
        </div>
        <div class="t-detail-row">
          <span class="t-detail-label">Live Gateway:</span>
          <span class="t-detail-value" style="color:var(--accent);">remote.juicevault.space</span>
        </div>
      </div>

      <div style="margin-top:14px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.06); font-size:0.75rem; color:var(--text-sub); display:flex; justify-content:space-between; align-items:center;">
        <span>Bot made by <a href="https://sosocial.lol/ski" target="_blank" rel="noopener" class="credit-author">SKIZZOO</a></span>
        <span>Domain by <a href="https://sosocial.lol/spinti" target="_blank" rel="noopener" class="credit-partner">Spinti</a></span>
      </div>

      <button class="btn-kinetic btn-flat" style="padding:12px; margin-top:14px; width:100%; justify-content:center;" onclick="closeStatsModal()">
        Close
      </button>
    </div>
  </div>

  <audio id="liveAudio" crossorigin="anonymous" preload="auto" playsinline style="display:none;"></audio>
  <audio id="silentAudio" preload="auto" playsinline loop style="display:none;"></audio>

  <script>
    // Silent carrier audio generator for mobile lock screen background playback controls
    function getSilentAudioSrc() {
      try {
        const sampleRate = 8000;
        const numSamples = sampleRate * 30; // 30s buffer prevents rapid loop restarts
        const buffer = new ArrayBuffer(44 + numSamples);
        const view = new DataView(buffer);
        view.setUint32(0, 0x52494646, false); // "RIFF"
        view.setUint32(4, 36 + numSamples, true);
        view.setUint32(8, 0x57415645, false); // "WAVE"
        view.setUint32(12, 0x666d7420, false); // "fmt "
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true); // PCM
        view.setUint16(22, 1, true); // mono
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate, true);
        view.setUint16(32, 1, true);
        view.setUint16(34, 8, true); // 8-bit
        view.setUint32(36, 0x64617461, false); // "data"
        view.setUint32(40, numSamples, true);
        new Uint8Array(buffer, 44, numSamples).fill(128);
        return URL.createObjectURL(new Blob([buffer], { type: 'audio/wav' }));
      } catch (e) {
        return 'data:audio/wav;base64,UklGRiwAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQgAAACAgICAgICAgA==';
      }
    }
    let cachedSilentAudioUrl = null;
    function ensureSilentAudioUrl() {
      if (!cachedSilentAudioUrl) cachedSilentAudioUrl = getSilentAudioSrc();
      return cachedSilentAudioUrl;
    }
    let lastUserSeekTimestamp = 0;
    let lockScreenControlsEnabled = true;
    let mediaSessionConfigured = false;
    let wsReconnectTimer = null;

    // State management
    const urlParams = new URLSearchParams(window.location.search);
    let token = urlParams.get('token') || localStorage.getItem('jv_token') || '';
    if (token) localStorage.setItem('jv_token', token);
    let currentGuildId = urlParams.get('guild_id') || localStorage.getItem('jv_guild_id') || '';
    if (urlParams.get('guild_id')) localStorage.setItem('jv_guild_id', currentGuildId);

    function apiQuery(extra = '') {
      let q = `token=${encodeURIComponent(token)}`;
      if (currentGuildId) {
        q += `&guild_id=${encodeURIComponent(currentGuildId)}`;
      }
      if (extra) {
        q += (extra.startsWith('&') ? extra : `&${extra}`);
      }
      return q;
    }

    function apiHeaders(extraHeaders = {}) {
      const h = { ...extraHeaders };
      if (currentGuildId) {
        h['X-Guild-ID'] = currentGuildId;
      }
      return h;
    }

    let currentState = null;
    let ws = null;
    let progressTimer = null;
    let currentElapsed = 0;
    let durationSeconds = 0;
    let searchMode = 'vault';
    let lockScreenActive = false;
    let lastQueueChecksum = '';
    let currentQueueData = { requested: [], upcoming: [], history: [] };
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
      const idx = ['queue', 'search', 'categories', 'soundboard', 'shortcuts', 'settings'].indexOf(tabId);
      if (idx !== -1) {
        const btns = document.querySelectorAll('.segment-bar.desktop-segment .segment-btn');
        if (btns[idx]) btns[idx].classList.add('active');
      }
      // Sync mobile top nav pill
      const mobIdx = ['player', 'queue', 'search', 'categories', 'soundboard', 'shortcuts', 'settings'].indexOf(tabId);
      if (mobIdx !== -1) {
        const mobBtns = document.querySelectorAll('.nav-btn');
        mobBtns.forEach(el => el.classList.remove('active'));
        if (mobBtns[mobIdx]) {
          mobBtns[mobIdx].classList.add('active');
          try { mobBtns[mobIdx].scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); } catch (_) {}
        }
      }
      if (tabId === 'queue') loadQueue();
      if (tabId === 'categories') { loadCategories(); loadJuiceVaultPlaylists(); }
      if (tabId === 'soundboard') loadSoundboard();
      if (tabId === 'shortcuts') renderShortcuts();
      if (tabId === 'settings') renderSettingsUI();
      if (navigator.vibrate) navigator.vibrate(8);
      // Animated 1-time tutorial popup over UI
      maybeShowTabTutorialPopup(tabId);
    }

    function switchMobileNav(tabId) {
      document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
      const idx = ['player', 'queue', 'search', 'categories', 'soundboard', 'shortcuts', 'settings'].indexOf(tabId);
      if (idx !== -1) {
        const btns = document.querySelectorAll('.nav-btn');
        if (btns[idx]) {
          btns[idx].classList.add('active');
          try { btns[idx].scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); } catch (_) {}
        }
      }

      const playerWrap = document.querySelector('.card-player-wrap');
      const contentWrap = document.querySelector('.card-content-wrap');

      const miniPlayer = document.getElementById('mobileMiniPlayer');
      if (window.innerWidth < 860) {
        if (tabId === 'player') {
          if (playerWrap) playerWrap.style.display = 'block';
          if (contentWrap) contentWrap.style.display = 'none';
          if (miniPlayer) miniPlayer.classList.remove('visible');
        } else {
          if (playerWrap) playerWrap.style.display = 'none';
          if (contentWrap) contentWrap.style.display = 'block';
          if (miniPlayer && currentState && currentState.track) {
            miniPlayer.classList.add('visible');
          }
          if (tabId === 'queue') lastQueueChecksum = '';
          switchTab(tabId);
        }
      } else {
        if (miniPlayer) miniPlayer.classList.remove('visible');
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

    const scrubberTooltip = document.getElementById('scrubberTooltip');

    progressBar.addEventListener('pointermove', (e) => {
      if (durationSeconds > 0) {
        const rect = progressBar.getBoundingClientRect();
        const clientX = e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
        const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        const hoverSec = ratio * durationSeconds;
        if (scrubberTooltip) {
          scrubberTooltip.innerText = formatTime(Math.floor(hoverSec));
          scrubberTooltip.style.left = (ratio * 100) + '%';
        }
      }
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
        lastUserSeekTimestamp = Date.now();
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
        lastUserSeekTimestamp = Date.now();
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
        lastUserSeekTimestamp = Date.now();
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
          currentLiveTrackId = null;
          isAudioLoading = true;
          aligningStuckStartTime = null;
          const a = document.getElementById('liveAudio');
          if (a) {
            try { a.pause(); a.currentTime = 0; } catch (_) {}
          }
          const statusText = document.getElementById('ltStatusText');
          if (statusText) statusText.innerText = 'Aligning...';
          const statusInd = document.getElementById('ltStatusInd');
          if (statusInd) statusInd.className = 'lt-status-indicator buffering';
          const badge = document.getElementById('liveSyncBadge');
          if (badge) {
            badge.innerText = 'BUFFERING';
            badge.className = 'lt-sync-badge connecting';
          }
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
          currentLiveTrackId = null;
          isAudioLoading = true;
          aligningStuckStartTime = null;
          const a = document.getElementById('liveAudio');
          if (a) {
            try { a.pause(); a.currentTime = 0; } catch (_) {}
          }
          const statusText = document.getElementById('ltStatusText');
          if (statusText) statusText.innerText = 'Aligning...';
          const statusInd = document.getElementById('ltStatusInd');
          if (statusInd) statusInd.className = 'lt-status-indicator buffering';
          const badge = document.getElementById('liveSyncBadge');
          if (badge) {
            badge.innerText = 'BUFFERING';
            badge.className = 'lt-sync-badge connecting';
          }
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

      const fullPayload = { guild_id: currentGuildId, ...payload };
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: name, ...fullPayload }));
        return;
      }
      try {
        const endpoint = (name === 'set_eq') ? 'eq' : name;
        const res = await fetch(`/api/playback/${endpoint}?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify(fullPayload)
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
    let analyserNode = null;
    let visDataArray = null;
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
        const isGecko = navigator.userAgent.toLowerCase().includes('firefox') || navigator.userAgent.toLowerCase().includes('zen');
        audioCtx = new AudioContextClass(isGecko ? { latencyHint: 'playback' } : {});
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

        analyserNode = audioCtx.createAnalyser();
        analyserNode.fftSize = 128;
        analyserNode.smoothingTimeConstant = 0.82;
        visDataArray = new Uint8Array(analyserNode.frequencyBinCount);

        masterGainNode.connect(analyserNode);
        analyserNode.connect(audioCtx.destination);
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
        if (!silent.src || (!silent.src.startsWith('data:audio') && !silent.src.startsWith('blob:'))) {
          silent.src = ensureSilentAudioUrl();
        }
        if (currentState && currentState.is_playing && silent.paused) {
          silent.play().catch(() => {});
        }
      }
    }

    function toggleLockScreenControls() {
      lockScreenControlsEnabled = !lockScreenControlsEnabled;
      try {
        localStorage.setItem('jv_lock_screen', lockScreenControlsEnabled ? 'true' : 'false');
      } catch (e) {}
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
    let isAudioPrimed = false;

    function primeLiveAudio(audio) {
      if (!audio) return;
      try {
        audio.crossOrigin = 'anonymous';
        audio.preload = 'auto';
        audio.playsInline = true;
        isAudioPrimed = true;
      } catch (e) {}
    }

    function toggleLiveAudio() {
      const audio = document.getElementById('liveAudio');
      liveStreamActive = !liveStreamActive;
      const banner = document.getElementById('liveAudioBanner');
      const btn = document.getElementById('btnListenLive');
      const controls = document.getElementById('liveAudioControls');
      const title = document.getElementById('liveStatusTitle');
      const badge = document.getElementById('liveSyncBadge');

      if (liveStreamActive) {
        initWebAudio();
        primeLiveAudio(audio);

        const silent = document.getElementById('silentAudio');
        if (silent) silent.pause();
        if (banner) banner.classList.add('active');
        if (btn) {
          btn.classList.add('active');
          btn.innerHTML = '<svg class="icon-svg lt-action-icon" id="liveBtnIcon" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg><span id="liveBtnLabel">Stop Stream</span>';
        }
        if (controls) controls.style.display = 'flex';
        if (title) title.innerText = 'Listen Together';
        if (badge) {
          badge.innerText = 'CONNECTING';
          badge.className = 'lt-sync-badge connecting';
        }

        syncLiveAudio(true);
        setupMediaSession();
        restartLiveSyncLoop();
        showToast('Connecting 1:1 stream...');
      } else {
        if (liveSyncInterval) {
          clearInterval(liveSyncInterval);
          liveSyncInterval = null;
        }
        if (pannerAnimFrame) {
          cancelAnimationFrame(pannerAnimFrame);
          pannerAnimFrame = null;
        }
        if (audio) {
          audio.pause();
          audio.removeAttribute('src');
          audio.load();
        }
        if (banner) banner.classList.remove('active');
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<svg class="icon-svg lt-action-icon" id="liveBtnIcon" viewBox="0 0 24 24"><polygon points="6 3 20 12 6 21 6 3"/></svg><span id="liveBtnLabel">Listen Live</span>';
        }
        if (controls) controls.style.display = 'none';
        if (title) title.innerText = 'Listen Together';
        if (badge) {
          badge.innerText = '1:1 SYNC';
          badge.className = 'lt-sync-badge';
        }
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

    let lastVolWheelTime = 0;
    let volWheelVelocity = 1.0;
    let volTarget = null;
    let volAnimFrame = null;

    function animateVolumeToTarget() {
      const slider = document.getElementById('liveVolumeSlider');
      if (!slider || volTarget === null) {
        volAnimFrame = null;
        return;
      }
      let current = parseFloat(slider.value) || 0;
      const diff = volTarget - current;
      if (Math.abs(diff) < 0.002) {
        slider.value = volTarget.toFixed(2);
        applyVolumeGain(volTarget);
        volTarget = null;
        volAnimFrame = null;
        return;
      }
      // Smooth responsive glide towards target
      const step = diff * 0.32;
      current += step;
      slider.value = current.toFixed(4);
      applyVolumeGain(current);
      volAnimFrame = requestAnimationFrame(animateVolumeToTarget);
    }

    function applyVolumeGain(val) {
      const v = Math.max(0, Math.min(1, parseFloat(val)));
      const audio = document.getElementById('liveAudio');
      if (audio) audio.volume = v;
      if (masterGainNode) masterGainNode.gain.value = v;
      const pctEl = document.getElementById('liveVolPercent');
      if (pctEl) pctEl.innerText = `${Math.round(v * 100)}%`;
      const slider = document.getElementById('liveVolumeSlider');
      if (slider) {
        slider.style.setProperty('--vol-fill', `${(v * 100).toFixed(1)}%`);
      }
      try {
        localStorage.setItem('jv_live_volume', String(v.toFixed(2)));
      } catch (e) {}
    }

    function handleVolumeWheel(e) {
      e.preventDefault();
      e.stopPropagation();
      const slider = document.getElementById('liveVolumeSlider');
      if (!slider) return;

      const now = performance.now();
      const dt = now - lastVolWheelTime;
      lastVolWheelTime = now;

      // Accelerated wheel velocity:
      // Deliberate scroll (>200ms): exactly 1% per notch (0.01)
      // Velocity curve: linear (fixed 1%) or adaptive (1%–5% based on scroll speed)
      let stepPct = 1;
      if (currentVolWheelCurve === 'linear') {
        stepPct = 1;
      } else {
        if (dt > 220) {
          volWheelVelocity = 1.0;
        } else if (dt < 65) {
          volWheelVelocity = Math.min(5.0, volWheelVelocity + 0.45);
        } else if (dt < 130) {
          volWheelVelocity = Math.min(3.5, volWheelVelocity + 0.25);
        } else {
          volWheelVelocity = Math.min(2.0, volWheelVelocity + 0.12);
        }
        stepPct = Math.max(1, Math.min(5, Math.round(volWheelVelocity)));
      }
      const step = stepPct / 100;
      const dir = (e.deltaY < 0) ? 1 : -1;

      let current = volTarget !== null ? volTarget : (parseFloat(slider.value) || 0);
      let nextVol = current + (dir * step);
      nextVol = Math.max(0, Math.min(1, Math.round(nextVol * 100) / 100));

      volTarget = nextVol;
      if (!volAnimFrame) {
        volAnimFrame = requestAnimationFrame(animateVolumeToTarget);
      }
    }

    function updateLiveVolume(val) {
      if (volAnimFrame) {
        cancelAnimationFrame(volAnimFrame);
        volAnimFrame = null;
      }
      volTarget = null;
      applyVolumeGain(val);
    }

    function syncLiveAudio(force = false) {
      if (!liveStreamActive || !currentState) return;
      const audio = document.getElementById('liveAudio');
      if (!audio) return;
      const t = currentState.track;
      const title = document.getElementById('liveStatusTitle');
      const badge = document.getElementById('liveSyncBadge');

      if (!t || !currentState.is_running) {
        if (!audio.paused) audio.pause();
        if (badge) {
          badge.innerText = 'PAUSED';
          badge.className = 'lt-sync-badge paused';
        }
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
        const streamUrl = `/api/stream?token=${encodeURIComponent(token)}&guild_id=${encodeURIComponent(gid)}&t=${encodeURIComponent(trackKey)}${force ? `&_cb=${Date.now()}` : ''}`;
        
        audio.crossOrigin = 'anonymous';
        audio.src = streamUrl;
        audio.load();

        if (title) title.innerText = 'Listen Together';
        if (badge) {
          badge.innerText = 'BUFFERING';
          badge.className = 'lt-sync-badge connecting';
        }

        audio.onwaiting = () => {
          if (badge) {
            badge.innerText = 'BUFFERING';
            badge.className = 'lt-sync-badge connecting';
          }
          const statusText = document.getElementById('ltStatusText');
          if (statusText) statusText.innerText = 'Aligning...';
          const statusInd = document.getElementById('ltStatusInd');
          if (statusInd) statusInd.className = 'lt-status-indicator buffering';
          if (!aligningStuckStartTime) aligningStuckStartTime = Date.now();
        };

        audio.onplaying = () => {
          isAudioLoading = false;
          aligningStuckStartTime = null;
          if (badge) {
            badge.innerText = '1:1 SYNC';
            badge.className = 'lt-sync-badge live';
          }
          if (title) title.innerText = 'Listen Together';
        };

        let readyHandled = false;
        const onReady = () => {
          if (readyHandled) return;
          readyHandled = true;
          isAudioLoading = false;
          try {
            if (audio.readyState >= 1 && currentElapsed > 0.1 && Math.abs(audio.currentTime - currentElapsed) > 0.4) {
              const maxSeek = (audio.duration && !isNaN(audio.duration) && audio.duration > 0.5) ? Math.max(0, audio.duration - 0.4) : currentElapsed;
              audio.currentTime = Math.max(0, Math.min(currentElapsed, maxSeek));
            }
          } catch (e) {}
          applyLiveEQ(currentState.effect);
          if (currentState && currentState.is_playing) {
            audio.play().catch(e => console.warn('Live playback play error:', e));
          }
          if (badge) {
            badge.innerText = '1:1 SYNC';
            badge.className = 'lt-sync-badge live';
          }
          if (title) title.innerText = 'Listen Together';
          const statusText = document.getElementById('ltStatusText');
          if (statusText) statusText.innerText = 'Phase-Locked';
          const statusInd = document.getElementById('ltStatusInd');
          if (statusInd) statusInd.className = 'lt-status-indicator locked';
          aligningStuckStartTime = null;
        };

        audio.onloadedmetadata = onReady;
        audio.oncanplay = onReady;

        audio.onerror = (e) => {
          isAudioLoading = false;
          currentLiveTrackId = null;
          const statusText = document.getElementById('ltStatusText');
          if (statusText) statusText.innerText = 'Reconnecting';
          const statusInd = document.getElementById('ltStatusInd');
          if (statusInd) statusInd.className = 'lt-status-indicator buffering';
          if (!aligningStuckStartTime) aligningStuckStartTime = Date.now();
          if (!liveStreamActive || !currentState || !currentState.is_playing) return;
          console.warn('Live audio stream error, auto-retrying in 1.2s...', e);
          if (badge) {
            badge.innerText = 'RETRYING';
            badge.className = 'lt-sync-badge connecting';
          }
          if (audioRetryTimer) clearTimeout(audioRetryTimer);
          audioRetryTimer = setTimeout(() => {
            if (liveStreamActive && currentState && currentState.is_playing) {
              syncLiveAudio(true);
            }
          }, 1200);
        };
        return;
      }

      if (isAudioLoading) {
        if (audio.readyState >= 2) isAudioLoading = false;
        else {
          if (!aligningStuckStartTime) aligningStuckStartTime = Date.now();
          return;
        }
      }

      applyLiveEQ(currentState.effect);

      if (!currentState.is_playing) {
        if (!audio.paused) audio.pause();
        if (badge) badge.innerText = 'Paused';
        aligningStuckStartTime = null;
        return;
      }

      if (audio.paused && currentState.is_playing) {
        try {
          if (Math.abs(audio.currentTime - currentElapsed) > 0.4) {
            const maxSeek = (audio.duration && !isNaN(audio.duration) && audio.duration > 0.5) ? Math.max(0, audio.duration - 0.4) : currentElapsed;
            audio.currentTime = Math.max(0, Math.min(currentElapsed, maxSeek));
          }
        } catch (e) {}
        audio.play().catch(() => {});
        if (!aligningStuckStartTime) aligningStuckStartTime = Date.now();
      }

      // High-precision 1:1 Phase-Locked Loop (PLL) clock sync with Discord
      if (!audio.paused && audio.duration > 0 && audio.readyState >= 2) {
        const drift = audio.currentTime - currentElapsed;
        const driftMs = Math.round(drift * 1000);
        const driftLabel = document.getElementById('syncDriftLabel');
        if (driftLabel) {
          driftLabel.innerText = (driftMs >= 0 ? `+${driftMs}ms` : `${driftMs}ms`);
        }

        const isGecko = navigator.userAgent.toLowerCase().includes('firefox') || navigator.userAgent.toLowerCase().includes('zen');
        let deadband = 0.08;
        let hardSeekThreshold = 1.5;
        let maxSteer = 0.05;

        if (currentLatencyMode === 'low') {
          deadband = 0.035;
          hardSeekThreshold = 1.0;
          maxSteer = 0.06;
        } else if (currentLatencyMode === 'stable' || isGecko) {
          deadband = 0.22;
          hardSeekThreshold = 2.5;
          maxSteer = 0.035;
        }

        const statusText = document.getElementById('ltStatusText');
        const statusInd = document.getElementById('ltStatusInd');
        if (Math.abs(driftMs) <= Math.round(deadband * 1000) + 40) {
          if (statusText) statusText.innerText = 'Phase-Locked';
          if (statusInd) statusInd.className = 'lt-status-indicator locked';
          aligningStuckStartTime = null;
        } else {
          if (statusText) statusText.innerText = 'Aligning...';
          if (statusInd) statusInd.className = 'lt-status-indicator buffering';
          if (!aligningStuckStartTime) aligningStuckStartTime = Date.now();
        }

        if (Math.abs(drift) > hardSeekThreshold) {
          // Large drift -> Hard seek directly to Discord master position
          const maxSeek = (audio.duration && !isNaN(audio.duration) && audio.duration > 0.5) ? Math.max(0, audio.duration - 0.4) : currentElapsed;
          try { audio.currentTime = Math.max(0, Math.min(currentElapsed, maxSeek)); } catch (e) {}
          if (Math.abs(audio.playbackRate - speed) > 0.005) {
            audio.playbackRate = speed;
          }
          if (!aligningStuckStartTime) aligningStuckStartTime = Date.now();
        } else if (Math.abs(drift) > deadband) {
          // Micro-drift: Proportional rate steering with rate hysteresis to avoid buffer churn
          const steer = Math.min(maxSteer, Math.max(0.012, Math.abs(drift) * 0.10));
          const targetRate = (drift < 0) ? (speed * (1 + steer)) : (speed * (1 - steer));
          if (Math.abs(audio.playbackRate - targetRate) > (isGecko ? 0.015 : 0.004)) {
            audio.playbackRate = targetRate;
          }
        } else {
          // Locked in exact 1:1 sync (within deadband)
          if (Math.abs(audio.playbackRate - speed) > 0.008) {
            audio.playbackRate = speed;
          }
        }

        // Track end boundary detection: fetch state from Discord if song is at end
        if (durationSeconds > 0 && currentElapsed >= durationSeconds - 0.5) {
          if (Date.now() - lastAligningRecoveryTime > 2000) {
            lastAligningRecoveryTime = Date.now();
            fetchStatus();
          }
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
          if (details && details.seekTime != null) {
            // Guard against synthetic OS background seekto 0 while playing
            if (details.seekTime === 0 && currentElapsed > 2.0 && !details.fastSeek) {
              console.warn('Ignored synthetic background seekto: 0');
              return;
            }
            lastUserSeekTimestamp = Date.now();
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
          if (!silent.src || (!silent.src.startsWith('data:audio') && !silent.src.startsWith('blob:'))) {
            silent.src = ensureSilentAudioUrl();
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
        if (!currentGuildId && state.guild.id) {
          currentGuildId = String(state.guild.id);
          localStorage.setItem('jv_guild_id', currentGuildId);
        }
        const bName = document.getElementById('guildBadgeName');
        if (bName) bName.innerText = state.guild.name || state.guild.id;
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
        updateCoverArtBackground(t.cover_url || 'https://api.juicevault.xyz/favicon.ico');
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
          const wasRecentUserSeek = (Date.now() - lastUserSeekTimestamp) < 3000;
          if (!wasRecentUserSeek && currentElapsed > 2.0 && liveDiscordPos < 0.6) {
            // Protect against transient 0-drop glitch while playing the same track
          } else if (Math.abs(currentElapsed - liveDiscordPos) > 0.35) {
            currentElapsed = liveDiscordPos;
          }
        }
        document.getElementById('timeDuration').innerText = t.length || formatTime(durationSeconds);
        updateScrubberUI();
      } else {
        currentTrackKey = '';
        document.getElementById('trackTitle').innerText = state.is_running ? 'Buffering archive…' : 'Player Inactive';
        document.getElementById('trackArtist').innerText = state.is_running ? 'Loading track' : 'Use Play to begin';
        updateCoverArtBackground(null);
      }

      // Play/Pause button, ambient glow and soundwave state
      const playIcon = document.getElementById('playIconSvg');
      const ambient = document.getElementById('artAmbient');
      if (ambient) ambient.classList.toggle('playing', !!state.is_playing);

      if (state.is_playing) {
        playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
        document.getElementById('coverImg').classList.add('playing');
        soundwave.classList.add('playing');
      } else {
        playIcon.innerHTML = '<polygon points="6 3 20 12 6 21 6 3"/>';
        document.getElementById('coverImg').classList.remove('playing');
        soundwave.classList.remove('playing');
      }

      const headerWave = document.getElementById('headerVisualizerWave');
      if (headerWave) headerWave.classList.toggle('playing', !!state.is_playing);

      // Sync mobile mini-player bar
      const mini = document.getElementById('mobileMiniPlayer');
      if (mini && t) {
        const mTitle = document.getElementById('miniTitle');
        const mArtist = document.getElementById('miniArtist');
        const mThumb = document.getElementById('miniThumb');
        const mIcon = document.getElementById('miniPlayIcon');
        if (mTitle) mTitle.innerText = t.title || 'Untitled';
        if (mArtist) mArtist.innerText = t.artist || 'Juice WRLD';
        if (mThumb) mThumb.src = t.cover_url || 'https://api.juicevault.xyz/favicon.ico';
        if (mIcon) {
          mIcon.innerHTML = state.is_playing
            ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
            : '<polygon points="6 3 20 12 6 21 6 3"/>';
        }
      }

      const repeatBtn = document.getElementById('btnRepeat');
      if (state.repeat) repeatBtn.classList.add('active');
      else repeatBtn.classList.remove('active');

      document.getElementById('reqCount').innerText = state.requested_size || 0;
      document.getElementById('queueCount').innerText = state.queue_size || 0;

      updateMediaSession();
      syncLiveAudio();
      applyLiveEQ(state.effect);
      updateFavoriteButtonState();
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
      const pct = (durationSeconds > 0) ? Math.min(100, Math.max(0, (currentElapsed / durationSeconds) * 100)) : 0;
      document.getElementById('progressFill').style.width = pct + '%';
      const miniLine = document.getElementById('miniProgressLine');
      if (miniLine) miniLine.style.width = pct + '%';
    }

    // High-precision 60fps liquid smooth progress ticker matching live playback
    function progressLoop() {
      const now = performance.now();
      const dt = (now - lastTickTime) / 1000;
      lastTickTime = now;

      if (!isScrubbing && currentState && currentState.is_playing && durationSeconds > 0) {
        // Tab background sleep cap: prevent wild leaps when tab wakes from background/blur
        const effectiveDt = Math.min(dt, 0.2);
        const eff = String(currentState.effect || '').toLowerCase();
        const speed = (currentState.track && currentState.track.effect_speed) || (eff.includes('night') ? 1.22 : (eff.includes('slow') ? 0.86 : 1.0));
        currentElapsed = Math.min(durationSeconds, currentElapsed + effectiveDt * speed);
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
      const wsUrl = `${wsProto}//${window.location.host}/ws?${apiQuery()}`;
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
        const res = await fetch(`/api/status?${apiQuery()}`, { headers: apiHeaders() });
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
      const list = source === 'requested' ? currentQueueData.requested : (source === 'history' ? currentQueueData.history : currentQueueData.upcoming);
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

      if (source === 'history') {
        if (actionType === 'play_now') {
          replayHistoryTrack(index);
        } else if (actionType === 'move_next') {
          queueHistoryTrack(index);
        } else {
          showToast('History item cannot be removed');
        }
        return;
      }

      try {
        if (actionType === 'remove') {
          const res = await fetch(`/api/queue/remove?${apiQuery()}`, {
            method: 'POST',
            headers: apiHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ type: source, index, guild_id: currentGuildId })
          });
          const d = await res.json();
          showToast(d.success ? 'Track removed from queue' : 'Remove failed');
          loadQueue();
        } else if (actionType === 'play_now') {
          const res = await fetch(`/api/queue/play_now?${apiQuery()}`, {
            method: 'POST',
            headers: apiHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ type: source, index, guild_id: currentGuildId })
          });
          const d = await res.json();
          showToast(d.message || `Playing now: ${title}`);
          loadQueue();
        } else if (actionType === 'move_next') {
          const res = await fetch(`/api/queue/move_next?${apiQuery()}`, {
            method: 'POST',
            headers: apiHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ type: source, index, guild_id: currentGuildId })
          });
          const d = await res.json();
          showToast(d.message || `Moved to play next: ${title}`);
          loadQueue();
        }
      } catch (err) {
        showToast('Action failed: ' + err.message);
      }
    }

    let queueFilterTerm = '';

    function filterQueueDisplay(term) {
      queueFilterTerm = (term || '').trim().toLowerCase();
      renderQueueLists();
    }

    function renderQueueLists() {
      const filter = queueFilterTerm;
      const reqList = document.getElementById('reqList');
      const upList = document.getElementById('upcomingList');
      const histList = document.getElementById('historyList');
      const histCountEl = document.getElementById('historyCount');
      if (histCountEl) {
        histCountEl.innerText = (currentQueueData.history || []).length;
      }
      if (!reqList || !upList) return;

      const reqFiltered = filter
        ? currentQueueData.requested.filter(t => (t.title && t.title.toLowerCase().includes(filter)) || (t.artist && t.artist.toLowerCase().includes(filter)))
        : currentQueueData.requested;

      if (reqFiltered.length > 0) {
        reqList.innerHTML = reqFiltered.map((t, idx) => `
          <div class="track-card" style="cursor:pointer;" onclick="openTrackModalByIndex('requested', ${idx})">
            <div class="track-meta-col">
              <div class="track-name">${escapeHtml(t.title || 'Untitled')}</div>
              <div class="track-desc">${escapeHtml(t.artist || 'Juice WRLD')} • ${escapeHtml(t.length || '—')}</div>
            </div>
            <span class="btn-badge" style="font-size:0.68rem; padding:3px 7px;">Manage</span>
          </div>
        `).join('');
      } else {
        reqList.innerHTML = filter
          ? '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No matching requested tracks.</div>'
          : '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No requested tracks. Use Search to queue songs.</div>';
      }

      const upFiltered = filter
        ? currentQueueData.upcoming.filter(t => (t.title && t.title.toLowerCase().includes(filter)) || (t.artist && t.artist.toLowerCase().includes(filter)))
        : currentQueueData.upcoming;

      if (upFiltered.length > 0) {
        upList.innerHTML = upFiltered.slice(0, 30).map((t, idx) => `
          <div class="track-card" style="cursor:pointer;" onclick="openTrackModalByIndex('upcoming', ${idx})">
            <div class="track-meta-col">
              <div class="track-name">${idx + 1}. ${escapeHtml(t.title || 'Untitled')}</div>
              <div class="track-desc">${escapeHtml(t.artist || 'Juice WRLD')} • ${escapeHtml(t.length || '—')}</div>
            </div>
            <span class="btn-badge" style="font-size:0.68rem; padding:3px 7px;">Manage</span>
          </div>
        `).join('');
      } else {
        upList.innerHTML = filter
          ? '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No matching archive tracks.</div>'
          : '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Archive queue empty.</div>';
      }

      if (histList) {
        const histFiltered = filter
          ? (currentQueueData.history || []).filter(t => (t.title && t.title.toLowerCase().includes(filter)) || (t.artist && t.artist.toLowerCase().includes(filter)))
          : (currentQueueData.history || []);

        if (histFiltered.length > 0) {
          histList.innerHTML = histFiltered.map((t, idx) => `
            <div class="track-card">
              <div class="track-meta-col" style="cursor:pointer;" onclick="openTrackModalByIndex('history', ${idx})">
                <div class="track-name">${escapeHtml(t.title || 'Untitled')}</div>
                <div class="track-desc">${escapeHtml(t.artist || 'Juice WRLD')} • ${escapeHtml(t.length || '—')}</div>
              </div>
              <div style="display:flex; align-items:center; gap:6px;">
                <button class="btn-kinetic btn-flat" style="padding:4px 8px; font-size:0.7rem;" onclick="replayHistoryTrack(${idx})" title="Play this song right now">
                  <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                  <span>Replay</span>
                </button>
                <button class="btn-kinetic btn-badge" style="padding:4px 8px; font-size:0.7rem;" onclick="queueHistoryTrack(${idx})" title="Add to Requested queue">
                  <span>+ Add</span>
                </button>
              </div>
            </div>
          `).join('');
        } else {
          histList.innerHTML = filter
            ? '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No matching history tracks.</div>'
            : '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">No recently played tracks yet.</div>';
        }
      }
    }

    async function replayHistoryTrack(idx) {
      const track = (currentQueueData.history || [])[idx];
      showToast(track ? `Replaying: ${track.title}` : 'Replaying track...');
      try {
        const res = await fetch(`/api/queue/replay_history?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ index: idx, guild_id: currentGuildId })
        });
        const d = await res.json();
        if (d.success) {
          showToast(d.message || 'Replaying track');
          loadQueue();
        } else {
          showToast(d.error || 'Replay failed');
        }
      } catch (err) {
        showToast('Replay failed: ' + err.message);
      }
    }

    async function queueHistoryTrack(idx) {
      const track = (currentQueueData.history || [])[idx];
      if (!track) return;
      try {
        const res = await fetch(`/api/queue/add?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ track, play_now: false, guild_id: currentGuildId })
        });
        const d = await res.json();
        showToast(d.message || `Added to queue: ${track.title}`);
        loadQueue();
      } catch (err) {
        showToast('Queue failed: ' + err.message);
      }
    }

    // Load Queue
    async function loadQueue() {
      try {
        const res = await fetch(`/api/queue?${apiQuery()}`, { headers: apiHeaders() });
        const data = await res.json();
        currentQueueData = {
          requested: data.requested || [],
          upcoming: data.upcoming || [],
          history: data.history || []
        };
        renderQueueLists();
      } catch (e) {
        console.error('Queue load error:', e);
      }
    }

    // Search Helpers & Debouncing
    let searchDebounceTimer = null;

    function handleSearchInput(e) {
      const q = (e.target.value || '').trim();
      const clearBtn = document.getElementById('clearSearchBtn');
      if (clearBtn) clearBtn.style.display = q ? 'flex' : 'none';
      clearTimeout(searchDebounceTimer);
      if (q.length >= 2) {
        searchDebounceTimer = setTimeout(() => executeSearch(), 320);
      }
    }

    function clearSearchField() {
      const input = document.getElementById('searchInput');
      if (input) {
        input.value = '';
        input.focus();
      }
      const clearBtn = document.getElementById('clearSearchBtn');
      if (clearBtn) clearBtn.style.display = 'none';
      const resContainer = document.getElementById('searchResults');
      if (resContainer) resContainer.innerHTML = '<div class="track-card" style="color: var(--text-sub); font-size: 0.8rem;">Type a query and press Search.</div>';
    }

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
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&source=${searchMode}&${apiQuery()}`, { headers: apiHeaders() });
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
        const res = await fetch(`/api/queue/add?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ track: item, play_now: playNow, guild_id: currentGuildId })
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
        const res = await fetch(`/api/queue/add?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ tracks: currentSearchResults, play_now: playNow, guild_id: currentGuildId })
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
        await fetch(`/api/category?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ category, guild_id: currentGuildId })
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
        const res = await fetch(`/api/category/tracks?category=${encodeURIComponent(category)}&limit=100&${apiQuery()}`, { headers: apiHeaders() });
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
        const res = await fetch(`/api/queue/add?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ track, play_now: true, guild_id: currentGuildId })
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
        const res = await fetch(`/api/queue/add?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ track, play_now: false, guild_id: currentGuildId })
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
        const res = await fetch(`/api/lyrics?${apiQuery()}`, { headers: apiHeaders() });
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
        const res = await fetch(`/api/channels?${apiQuery()}`, { headers: apiHeaders() });
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
        const res = await fetch(`/api/lyrics/send?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ channel_id: channelId, guild_id: currentGuildId })
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

    // ==========================================
    // JuiceVault.xyz Account & Favorites Engine
    // ==========================================
    let currentJvUser = null;
    let userLikesCache = [];
    let userLikesSet = new Set();

    let userPlaylistsCache = [];

    function initJuiceVaultUser() {
      try {
        const savedUserStr = localStorage.getItem('jv_user');
        if (savedUserStr) {
          const user = JSON.parse(savedUserStr);
          renderUserProfile(user);
        }
        const savedLikesStr = localStorage.getItem('jv_likes');
        if (savedLikesStr) {
          userLikesCache = JSON.parse(savedLikesStr);
          userLikesSet = new Set(userLikesCache.map(x => String(x.id || x.songId || x.title).toLowerCase()));
          const favCountEl = document.getElementById('userFavsBtnCount');
          if (favCountEl) favCountEl.innerText = userLikesCache.length;
        }
        const username = localStorage.getItem('jv_username');
        if (username) {
          refreshJuiceVaultUserData(username);
          loadJuiceVaultPlaylists();
        }
      } catch (e) {
        console.warn('JuiceVault user init failed:', e);
      }
      updateFavoriteButtonState();
    }

    function switchAuthMode(mode) {
      const tabLogin = document.getElementById('authTabLogin');
      const tabPub = document.getElementById('authTabPublic');
      const panelLogin = document.getElementById('authPanelLogin');
      const panelPub = document.getElementById('authPanelPublic');
      const err = document.getElementById('jvLoginError');
      if (err) err.style.display = 'none';

      if (mode === 'login') {
        if (tabLogin) { tabLogin.style.background = 'var(--accent)'; tabLogin.style.color = '#fff'; }
        if (tabPub) { tabPub.style.background = 'transparent'; tabPub.style.color = 'var(--text-muted)'; }
        if (panelLogin) panelLogin.style.display = 'block';
        if (panelPub) panelPub.style.display = 'none';
      } else {
        if (tabPub) { tabPub.style.background = 'var(--accent)'; tabPub.style.color = '#fff'; }
        if (tabLogin) { tabLogin.style.background = 'transparent'; tabLogin.style.color = 'var(--text-muted)'; }
        if (panelLogin) panelLogin.style.display = 'none';
        if (panelPub) panelPub.style.display = 'block';
      }
    }

    function openUserModal() {
      const sheet = document.getElementById('userSheet');
      if (sheet) sheet.classList.add('active');
      const err = document.getElementById('jvLoginError');
      if (err) err.style.display = 'none';
      const input = document.getElementById('jvAuthLoginInput') || document.getElementById('jvUsernameInput');
      if (input && !currentJvUser) {
        setTimeout(() => input.focus(), 100);
      }
    }

    function closeUserModal() {
      const sheet = document.getElementById('userSheet');
      if (sheet) sheet.classList.remove('active');
    }

    async function loginJuiceVaultUserFull() {
      const loginInput = document.getElementById('jvAuthLoginInput');
      const passInput = document.getElementById('jvAuthPassInput');
      const errEl = document.getElementById('jvLoginError');
      const btn = document.getElementById('jvAuthLoginBtn');
      const username = (loginInput ? loginInput.value : '').trim();
      const password = (passInput ? passInput.value : '').trim();

      if (!username || !password) {
        if (errEl) {
          errEl.innerText = 'Please enter both username/email and password';
          errEl.style.display = 'block';
        }
        return;
      }

      if (errEl) errEl.style.display = 'none';
      if (btn) {
        btn.disabled = true;
        btn.innerText = 'Signing in...';
      }
      showToast(`Logging in to JuiceVault.xyz...`);

      try {
        const res = await fetch(`/api/user/auth?${apiQuery()}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...apiHeaders() },
          body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (btn) {
          btn.disabled = false;
          btn.innerText = 'Sign In to JuiceVault.xyz';
        }

        if (!data.ok || !data.user) {
          if (errEl) {
            errEl.innerText = data.error || 'Authentication failed. Check credentials.';
            errEl.style.display = 'block';
          }
          return;
        }

        const user = data.user;
        const token = data.token;
        if (token) localStorage.setItem('jv_token', token);
        localStorage.setItem('jv_username', user.username || username);
        localStorage.setItem('jv_user', JSON.stringify(user));
        renderUserProfile(user);
        showToast(`Connected as @${user.username || username}!`);
        closeUserModal();
        await loadJuiceVaultPlaylists(true);
      } catch (err) {
        if (btn) {
          btn.disabled = false;
          btn.innerText = 'Sign In to JuiceVault.xyz';
        }
        if (errEl) {
          errEl.innerText = `Connection failed: ${err.message}`;
          errEl.style.display = 'block';
        }
      }
    }

    async function loginJuiceVaultUser() {
      const input = document.getElementById('jvUsernameInput');
      const errEl = document.getElementById('jvLoginError');
      const username = (input ? input.value : '').trim();
      if (!username) {
        if (errEl) {
          errEl.innerText = 'Please enter a JuiceVault.xyz username';
          errEl.style.display = 'block';
        }
        return;
      }
      if (errEl) errEl.style.display = 'none';
      showToast(`Connecting @${username}...`);

      try {
        const res = await fetch(`/api/user/profile?username=${encodeURIComponent(username)}&${apiQuery()}`, { headers: apiHeaders() });
        const data = await res.json();
        const user = data.user || data.data;
        if (data.error || !user) {
          if (errEl) {
            errEl.innerText = data.error || 'User not found on JuiceVault.xyz';
            errEl.style.display = 'block';
          }
          return;
        }
        localStorage.setItem('jv_username', username);
        localStorage.setItem('jv_user', JSON.stringify(user));
        renderUserProfile(user);
        showToast(`Connected as @${user.username || username}`);
        closeUserModal();
        await refreshJuiceVaultLikes(username);
        await loadJuiceVaultPlaylists(true);
      } catch (err) {
        if (errEl) {
          errEl.innerText = `Connection failed: ${err.message}`;
          errEl.style.display = 'block';
        }
      }
    }

    async function refreshJuiceVaultUserData(username) {
      try {
        const res = await fetch(`/api/user/profile?username=${encodeURIComponent(username)}&${apiQuery()}`, { headers: apiHeaders() });
        const data = await res.json();
        const user = data.user || data.data;
        if (user) {
          localStorage.setItem('jv_user', JSON.stringify(user));
          renderUserProfile(user);
        }
        await refreshJuiceVaultLikes(username);
      } catch (e) {}
    }

    async function refreshJuiceVaultLikes(username) {
      try {
        const res = await fetch(`/api/user/likes?username=${encodeURIComponent(username)}&${apiQuery()}`, { headers: apiHeaders() });
        const data = await res.json();
        const likes = data.likes || data.data;
        if (likes && Array.isArray(likes)) {
          userLikesCache = likes;
          userLikesSet = new Set(userLikesCache.map(x => String(x.id || x.songId || x.title).toLowerCase()));
          localStorage.setItem('jv_likes', JSON.stringify(userLikesCache));
          const favCountEl = document.getElementById('userFavsBtnCount');
          if (favCountEl) favCountEl.innerText = userLikesCache.length;
          updateFavoriteButtonState();
        }
      } catch (e) {}
    }

    async function loadJuiceVaultPlaylists(force = false) {
      const container = document.getElementById('jvPlaylistsContent');
      if (!container) return;

      const username = localStorage.getItem('jv_username');
      const userToken = localStorage.getItem('jv_token') || '';
      if (!username) {
        container.innerHTML = `
          <div style="font-size:0.78rem; color:var(--text-sub); text-align:center; padding:16px 8px;">
            Connect your JuiceVault.xyz account to access your personal playlists and liked songs.
            <div style="margin-top:10px;">
              <button class="btn-kinetic btn-primary" style="padding:6px 14px; font-size:0.75rem;" onclick="openUserModal()">Connect Account</button>
            </div>
          </div>`;
        return;
      }

      if (!force && userPlaylistsCache.length > 0) {
        renderJuiceVaultPlaylists();
        return;
      }

      container.innerHTML = '<div style="font-size:0.75rem; color:var(--text-muted); text-align:center; padding:12px;">Syncing playlists from JuiceVault.xyz...</div>';

      try {
        const q = new URLSearchParams({
          username: username,
          token: userToken
        });
        const res = await fetch(`/api/user/playlists?${q.toString()}&${apiQuery()}`, { headers: apiHeaders() });
        const data = await res.json();
        if (!data.ok) {
          container.innerHTML = `<div style="font-size:0.75rem; color:var(--text-sub); padding:10px; text-align:center;">Could not load playlists: ${escapeHtml(data.error || 'Server error')}</div>`;
          return;
        }

        userPlaylistsCache = data.playlists || [];
        if (data.likes && Array.isArray(data.likes)) {
          userLikesCache = data.likes;
          userLikesSet = new Set(userLikesCache.map(x => String(x.id || x.songId || x.title).toLowerCase()));
          localStorage.setItem('jv_likes', JSON.stringify(userLikesCache));
          const favCountEl = document.getElementById('userFavsBtnCount');
          if (favCountEl) favCountEl.innerText = userLikesCache.length;
          updateFavoriteButtonState();
        }

        renderJuiceVaultPlaylists();
      } catch (err) {
        container.innerHTML = `<div style="font-size:0.75rem; color:var(--danger); padding:10px; text-align:center;">Sync error: ${escapeHtml(err.message)}</div>`;
      }
    }

    function renderJuiceVaultPlaylists() {
      const container = document.getElementById('jvPlaylistsContent');
      if (!container) return;

      let html = '<div class="jv-playlists-list">';

      const likesCount = userLikesCache ? userLikesCache.length : 0;
      html += `
        <div class="jv-playlist-card">
          <div class="jv-playlist-left">
            <div class="jv-playlist-disc" style="background:linear-gradient(135deg, rgba(244,63,94,0.3), rgba(168,85,247,0.3)); border-color:rgba(244,63,94,0.4);">
              <svg class="icon-svg" style="width:16px;height:16px;color:#f43f5e;" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            </div>
            <div class="jv-playlist-meta">
              <div class="jv-playlist-title">Liked Songs</div>
              <div class="jv-playlist-sub">${likesCount} track${likesCount === 1 ? '' : 's'} • Saved Vault Favorites</div>
            </div>
          </div>
          <div class="jv-playlist-actions">
            <button class="btn-kinetic btn-primary" style="padding:5px 10px; font-size:0.72rem;" onclick="playUserLikes(true)" title="Shuffle and queue all liked songs">
              <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
              <span>Shuffle</span>
            </button>
            <button class="btn-kinetic btn-flat" style="padding:5px 8px; font-size:0.72rem;" onclick="viewUserFavorites()" title="View track list in search view">
              <span>View</span>
            </button>
          </div>
        </div>`;

      if (userPlaylistsCache && userPlaylistsCache.length > 0) {
        userPlaylistsCache.forEach(pl => {
          const count = (pl.songs && Array.isArray(pl.songs)) ? pl.songs.length : (pl.songCount || 0);
          html += `
            <div class="jv-playlist-card">
              <div class="jv-playlist-left">
                <div class="jv-playlist-disc">
                  <svg class="icon-svg" style="width:16px;height:16px;" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </div>
                <div class="jv-playlist-meta">
                  <div class="jv-playlist-title">${escapeHtml(pl.name || pl.title || 'Playlist')}</div>
                  <div class="jv-playlist-sub">${count} track${count === 1 ? '' : 's'}${pl.author ? ` • by ${escapeHtml(pl.author)}` : ''}</div>
                </div>
              </div>
              <div class="jv-playlist-actions">
                <button class="btn-kinetic btn-primary" style="padding:5px 10px; font-size:0.72rem;" onclick="playJuiceVaultCustomPlaylist('${escapeHtml(pl.id || pl.name)}', true)" title="Shuffle playlist on Discord">
                  <svg class="icon-svg" style="width:12px;height:12px;" viewBox="0 0 24 24"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>
                  <span>Play</span>
                </button>
              </div>
            </div>`;
        });
      }

      html += '</div>';
      container.innerHTML = html;
    }

    async function playUserLikes(shuffle = true) {
      if (!userLikesCache || userLikesCache.length === 0) {
        showToast('No liked songs in your JuiceVault account');
        return;
      }
      showToast(`Queueing ${userLikesCache.length} liked tracks on Discord...`);
      const tracksToQueue = [...userLikesCache];
      if (shuffle) {
        for (let i = tracksToQueue.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [tracksToQueue[i], tracksToQueue[j]] = [tracksToQueue[j], tracksToQueue[i]];
        }
      }
      for (let i = 0; i < Math.min(tracksToQueue.length, 25); i++) {
        const item = tracksToQueue[i];
        await action('play_track', { track_id: item.id || item.songId || item.title });
        await new Promise(r => setTimeout(r, 60));
      }
      showToast(`Queued ${Math.min(tracksToQueue.length, 25)} favorites!`);
    }

    async function playJuiceVaultCustomPlaylist(plId, shuffle = true) {
      const pl = userPlaylistsCache.find(x => (x.id === plId || x.name === plId));
      if (!pl || !pl.songs || pl.songs.length === 0) {
        showToast('Playlist is empty');
        return;
      }
      const list = [...pl.songs];
      if (shuffle) {
        for (let i = list.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [list[i], list[j]] = [list[j], list[i]];
        }
      }
      showToast(`Queueing "${pl.name || 'Playlist'}" on Discord...`);
      for (let i = 0; i < Math.min(list.length, 25); i++) {
        const song = list[i];
        await action('play_track', { track_id: song.id || song.songId || song.title });
        await new Promise(r => setTimeout(r, 60));
      }
      showToast(`Queued ${Math.min(list.length, 25)} tracks from ${pl.name || 'Playlist'}!`);
    }

    function renderUserProfile(user) {
      currentJvUser = user;
      const profileView = document.getElementById('userProfileView');
      const loginForm = document.getElementById('userLoginForm');
      if (profileView) profileView.style.display = 'block';
      if (loginForm) loginForm.style.display = 'none';

      const avatar = document.getElementById('userCardAvatar');
      if (avatar) avatar.src = user.avatar_url || 'https://api.juicevault.xyz/favicon.ico';

      const nameEl = document.getElementById('userCardDisplayName');
      if (nameEl) nameEl.innerText = user.display_name || user.username || 'User';

      const handleEl = document.getElementById('userCardHandle');
      if (handleEl) handleEl.innerText = `@${user.username || ''}`;

      const bioEl = document.getElementById('userCardBio');
      if (bioEl) {
        bioEl.innerText = user.bio || '';
        bioEl.style.display = user.bio ? 'block' : 'none';
      }

      const likesCount = document.getElementById('userLikedCount');
      if (likesCount) likesCount.innerText = user.likes_count || (user.stats && user.stats.likedCount) || (userLikesCache ? userLikesCache.length : 0);

      const listensCount = document.getElementById('userListensCount');
      if (listensCount) listensCount.innerText = user.play_count || (user.listening && user.listening.totalListens) || 0;

      const uniqueCount = document.getElementById('userUniqueCount');
      if (uniqueCount) uniqueCount.innerText = (user.listening && user.listening.uniqueSongs) || (user.listening && user.listening.totalSongs) || 0;

      const streakCount = document.getElementById('userStreakCount');
      if (streakCount) streakCount.innerText = `${(user.listening && user.listening.streak) || user.streak || 0}d`;

      const favCountEl = document.getElementById('userFavsBtnCount');
      if (favCountEl) favCountEl.innerText = userLikesCache.length || user.likes_count || 0;

      const badgesContainer = document.getElementById('userCardBadges');
      if (badgesContainer) {
        const badges = user.badges || [];
        badgesContainer.innerHTML = badges.map(b => {
          const lbl = (typeof b === 'object' && b !== null) ? (b.label || b.id) : String(b);
          const tone = (typeof b === 'object' && b !== null && b.tone) ? b.tone : 'accent';
          let toneStyle = 'background:rgba(168,85,247,0.15); color:var(--accent); border:1px solid rgba(168,85,247,0.3);';
          if (tone === 'owner' || tone === 'rose') toneStyle = 'background:rgba(244,63,94,0.15); color:#fb7185; border:1px solid rgba(244,63,94,0.3);';
          else if (tone === 'cyan' || tone === 'verified') toneStyle = 'background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3);';
          else if (tone === 'green') toneStyle = 'background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.3);';
          return `<span class="status-badge" style="font-size:0.65rem; padding:2px 7px; border-radius:4px; ${toneStyle}">${escapeHtml(lbl)}</span>`;
        }).join('');
      }

      const userBtn = document.getElementById('userBtn');
      if (userBtn) {
        userBtn.style.color = 'var(--accent)';
        userBtn.title = `Connected: @${user.username}`;
      }

      const headerAvatar = document.getElementById('headerUserAvatar');
      if (headerAvatar && user.avatar_url) headerAvatar.src = user.avatar_url;
      const headerName = document.getElementById('headerUserName');
      if (headerName) headerName.innerText = `@${user.username || user.display_name || 'User'}`;

      renderSettingsUI();
      updateFavoriteButtonState();
    }

    function logoutUser() {
      currentJvUser = null;
      userLikesCache = [];
      userLikesSet.clear();
      userPlaylistsCache = [];
      localStorage.removeItem('jv_token');
      localStorage.removeItem('jv_username');
      localStorage.removeItem('jv_user');
      localStorage.removeItem('jv_likes');

      const profileView = document.getElementById('userProfileView');
      const loginForm = document.getElementById('userLoginForm');
      if (profileView) profileView.style.display = 'none';
      if (loginForm) loginForm.style.display = 'block';

      const input = document.getElementById('jvUsernameInput');
      if (input) input.value = '';
      const loginInput = document.getElementById('jvAuthLoginInput');
      if (loginInput) loginInput.value = '';
      const passInput = document.getElementById('jvAuthPassInput');
      if (passInput) passInput.value = '';

      const userBtn = document.getElementById('userBtn');
      if (userBtn) {
        userBtn.style.color = '';
        userBtn.title = 'JuiceVault Account';
      }

      const headerAvatar = document.getElementById('headerUserAvatar');
      if (headerAvatar) headerAvatar.src = 'https://api.juicevault.xyz/favicon.ico';
      const headerName = document.getElementById('headerUserName');
      if (headerName) headerName.innerText = 'Sign In';

      loadJuiceVaultPlaylists();
      renderSettingsUI();
      updateFavoriteButtonState();
      showToast('JuiceVault account disconnected');
    }

    // ==========================================
    // Remote Settings Management Engine
    // ==========================================
    let currentTheme = 'purple';
    let currentCoverShape = 'modern';
    let currentGlassBlur = 'frosted';
    let currentLatencyMode = (navigator.userAgent.toLowerCase().includes('firefox') || navigator.userAgent.toLowerCase().includes('zen')) ? 'stable' : 'balanced';
    let currentVolWheelCurve = 'adaptive';
    let soundboardPreviewEnabled = false;
    let soundboardPreviewVol = 0.75;
    lockScreenControlsEnabled = true;
    let auroraDefaultEnabled = true;

    function loadSettings() {
      try {
        const savedStr = localStorage.getItem('jv_settings');
        if (savedStr) {
          const cfg = JSON.parse(savedStr);
          if (cfg.theme) currentTheme = cfg.theme;
          if (cfg.coverShape) currentCoverShape = cfg.coverShape;
          if (cfg.glassBlur) currentGlassBlur = cfg.glassBlur;
          if (cfg.latencyMode) currentLatencyMode = cfg.latencyMode;
          if (cfg.volWheelCurve) currentVolWheelCurve = cfg.volWheelCurve;
          if (cfg.sbPreview !== undefined) soundboardPreviewEnabled = !!cfg.sbPreview;
          if (cfg.sbPreviewVol !== undefined) soundboardPreviewVol = parseFloat(cfg.sbPreviewVol) || 0.75;
          if (cfg.lockScreen !== undefined) lockScreenControlsEnabled = !!cfg.lockScreen;
          if (cfg.auroraDefault !== undefined) auroraDefaultEnabled = !!cfg.auroraDefault;
        }
      } catch (e) {
        console.warn('Settings load error:', e);
      }
      applyAllSettings();
    }

    function saveSettings() {
      try {
        const cfg = {
          theme: currentTheme,
          coverShape: currentCoverShape,
          glassBlur: currentGlassBlur,
          latencyMode: currentLatencyMode,
          volWheelCurve: currentVolWheelCurve,
          sbPreview: soundboardPreviewEnabled,
          sbPreviewVol: soundboardPreviewVol,
          lockScreen: lockScreenControlsEnabled,
          auroraDefault: auroraDefaultEnabled
        };
        localStorage.setItem('jv_settings', JSON.stringify(cfg));
      } catch (e) {}
    }

    function applyAllSettings() {
      setThemeAccent(currentTheme, false);
      setCoverShape(currentCoverShape, false);
      setGlassBlur(currentGlassBlur, false);
      setLatencyMode(currentLatencyMode, false);
      setVolWheelCurve(currentVolWheelCurve, false);
      setSoundboardPreview(soundboardPreviewEnabled, false);
      setSoundboardPreviewVol(soundboardPreviewVol, false);
      setLockScreenControls(lockScreenControlsEnabled, false);
      setAuroraDefaultToggle(auroraDefaultEnabled, false);
      renderSettingsUI();
    }

    function setThemeAccent(theme, persist = true) {
      currentTheme = theme;
      document.body.classList.remove('theme-cyan', 'theme-rose', 'theme-green', 'theme-gold');
      if (theme !== 'purple') {
        document.body.classList.add(`theme-${theme}`);
      }
      document.querySelectorAll('.color-swatch').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-theme') === theme);
      });
      if (persist) {
        saveSettings();
        showToast(`Theme updated: ${theme.toUpperCase()}`);
      }
    }

    function setCoverShape(shape, persist = true) {
      currentCoverShape = shape;
      document.body.classList.remove('cover-shape-squircle', 'cover-shape-circle');
      if (shape === 'squircle') document.body.classList.add('cover-shape-squircle');
      else if (shape === 'circle') document.body.classList.add('cover-shape-circle');
      document.querySelectorAll('#settingCoverShapeSelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === shape);
      });
      if (persist) {
        saveSettings();
        showToast(`Album art shape: ${shape}`);
      }
    }

    function setGlassBlur(mode, persist = true) {
      currentGlassBlur = mode;
      document.body.classList.remove('blur-none', 'blur-frosted');
      if (mode === 'none') document.body.classList.add('blur-none');
      else if (mode === 'deep') document.body.classList.add('blur-frosted');
      document.querySelectorAll('#settingGlassSelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === mode);
      });
      if (persist) {
        saveSettings();
        showToast(`Glassmorphism: ${mode}`);
      }
    }

    function setLatencyMode(mode, persist = true) {
      currentLatencyMode = mode;
      document.querySelectorAll('#settingLatencySelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === mode);
      });
      restartLiveSyncLoop();
      if (persist) {
        saveSettings();
        showToast(`Buffer mode: ${mode.toUpperCase()}`);
      }
    }

    function setVolWheelCurve(curve, persist = true) {
      currentVolWheelCurve = curve;
      document.querySelectorAll('#settingVolCurveSelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === curve);
      });
      if (persist) {
        saveSettings();
        showToast(`Volume curve: ${curve === 'adaptive' ? 'Adaptive (1%–5%)' : 'Fixed 1%'}`);
      }
    }

    function setSoundboardPreview(val, persist = true) {
      soundboardPreviewEnabled = !!val;
      const t = document.getElementById('settingSbPreviewToggle');
      if (t) t.checked = soundboardPreviewEnabled;
      const sbRow = document.getElementById('settingSbVolRow');
      if (sbRow) sbRow.style.display = soundboardPreviewEnabled ? 'flex' : 'none';
      if (persist) {
        saveSettings();
        showToast(`Soundboard preview: ${soundboardPreviewEnabled ? 'ON' : 'OFF'}`);
      }
    }

    function setSoundboardPreviewVol(val, persist = true) {
      soundboardPreviewVol = parseFloat(val) || 0.75;
      const sl = document.getElementById('settingSbVolSlider');
      if (sl) sl.value = soundboardPreviewVol;
      const pct = document.getElementById('settingSbVolPct');
      if (pct) pct.innerText = `${Math.round(soundboardPreviewVol * 100)}%`;
      if (persist) saveSettings();
    }

    function setLockScreenControls(val, persist = true) {
      lockScreenControlsEnabled = !!val;
      const t = document.getElementById('settingMediaSessionToggle');
      if (t) t.checked = lockScreenControlsEnabled;
      if (persist) {
        saveSettings();
        showToast(`Media keys / Lockscreen: ${lockScreenControlsEnabled ? 'ON' : 'OFF'}`);
      }
    }

    function setAuroraDefaultToggle(val, persist = true) {
      auroraDefaultEnabled = !!val;
      const t = document.getElementById('settingAuroraToggle');
      if (t) t.checked = auroraDefaultEnabled;
      if (persist) {
        saveSettings();
        showToast(`Aurora background default: ${auroraDefaultEnabled ? 'ON' : 'OFF'}`);
      }
    }

    function restartLiveSyncLoop() {
      if (liveSyncInterval) {
        clearInterval(liveSyncInterval);
        liveSyncInterval = null;
      }
      if (!liveStreamActive) return;
      let intervalMs = 300;
      if (currentLatencyMode === 'low') intervalMs = 200;
      else if (currentLatencyMode === 'stable') intervalMs = 800;
      else intervalMs = 450;
      liveSyncInterval = setInterval(() => {
        if (liveStreamActive) {
          syncLiveAudio(false);
          checkAligningWatchdog();
        }
      }, intervalMs);
    }

    // ========================================================
    // Stream Alignment Watchdog & 5-Second Force-Refresh Engine
    // ========================================================
    let aligningStuckStartTime = null;
    let lastAligningRecoveryTime = 0;

    function forceStreamRefresh(fromWatchdog = false) {
      console.warn(`[JuiceVault] Forcing stream refresh (triggered by ${fromWatchdog ? '5s aligning watchdog' : 'user click'})...`);

      // 1. Save auto-resume flag so Listen Together reconnects immediately on page reload
      try {
        sessionStorage.setItem('jv_auto_resume_stream', 'true');
      } catch (e) {}

      // 2. Prevent infinite reload loops if server or Discord VC has persistent issue
      const lastReload = parseInt(sessionStorage.getItem('jv_last_align_reload') || '0', 10);
      const now = Date.now();

      if (now - lastReload > 10000) {
        try { sessionStorage.setItem('jv_last_align_reload', String(now)); } catch (e) {}
        showToast(fromWatchdog ? 'Stuck in aligning for 5s — refreshing...' : 'Refreshing stream & web page...');
        setTimeout(() => {
          window.location.reload();
        }, 180);
      } else {
        // Reloaded very recently: perform aggressive in-place audio pipeline reset
        showToast('Resyncing live audio pipeline...');
        aligningStuckStartTime = null;
        const audio = document.getElementById('liveAudio');
        if (audio) {
          audio.pause();
          audio.removeAttribute('src');
          audio.load();
        }
        currentLiveTrackId = null;
        isAudioLoading = false;
        fetchStatus().then(() => {
          setTimeout(() => {
            if (liveStreamActive) syncLiveAudio(true);
          }, 350);
        });
      }
    }

    function checkAligningWatchdog() {
      if (!liveStreamActive) {
        aligningStuckStartTime = null;
        return;
      }

      const statusText = document.getElementById('ltStatusText');
      const statusInd = document.getElementById('ltStatusInd');
      const text = (statusText ? statusText.innerText : '').toLowerCase();
      const isBuffering = statusInd && statusInd.classList.contains('buffering');
      const isAligning = text.includes('align') || text.includes('buffer') || text.includes('reconnect') || isBuffering;

      if (!isAligning) {
        aligningStuckStartTime = null;
        return;
      }

      if (!aligningStuckStartTime) {
        aligningStuckStartTime = Date.now();
        return;
      }

      const stuckDuration = Date.now() - aligningStuckStartTime;

      // Soft recovery at ~2.5s: fetch status in case track changed on Discord
      if (stuckDuration >= 2500 && (Date.now() - lastAligningRecoveryTime > 2500)) {
        lastAligningRecoveryTime = Date.now();
        fetchStatus().then(() => {
          if (liveStreamActive) syncLiveAudio(true);
        });
      }

      // Hard refresh at 5 seconds: exact user requirement
      if (stuckDuration >= 5000) {
        aligningStuckStartTime = null;
        forceStreamRefresh(true);
      }
    }

    setInterval(checkAligningWatchdog, 500);

    function renderSettingsUI() {
      document.querySelectorAll('.color-swatch').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-theme') === currentTheme);
      });
      document.querySelectorAll('#settingCoverShapeSelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === currentCoverShape);
      });
      document.querySelectorAll('#settingGlassSelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === currentGlassBlur);
      });
      document.querySelectorAll('#settingLatencySelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === currentLatencyMode);
      });
      document.querySelectorAll('#settingVolCurveSelector .pill-opt').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-val') === currentVolWheelCurve);
      });
      const tPreview = document.getElementById('settingSbPreviewToggle');
      if (tPreview) tPreview.checked = soundboardPreviewEnabled;
      const sbRow = document.getElementById('settingSbVolRow');
      if (sbRow) sbRow.style.display = soundboardPreviewEnabled ? 'flex' : 'none';
      const slVol = document.getElementById('settingSbVolSlider');
      if (slVol) slVol.value = soundboardPreviewVol;
      const pct = document.getElementById('settingSbVolPct');
      if (pct) pct.innerText = `${Math.round(soundboardPreviewVol * 100)}%`;
      const tLock = document.getElementById('settingMediaSessionToggle');
      if (tLock) tLock.checked = lockScreenControlsEnabled;
      const tAurora = document.getElementById('settingAuroraToggle');
      if (tAurora) tAurora.checked = auroraDefaultEnabled;

      const setLbl = document.getElementById('settingUserStatusLabel');
      const setDesc = document.getElementById('settingUserStatusDesc');
      const setBtn = document.getElementById('settingUserActionBtn');
      const setSyncRow = document.getElementById('settingUserSyncRow');
      if (currentJvUser) {
        if (setLbl) setLbl.innerText = `Connected (@${currentJvUser.username || 'User'})`;
        if (setDesc) setDesc.innerText = `Signed in as ${currentJvUser.display_name || currentJvUser.username}. Real-time profile, playlists & likes synced.`;
        if (setBtn) { setBtn.innerText = 'Account Profile'; setBtn.className = 'btn-kinetic btn-flat'; }
        if (setSyncRow) setSyncRow.style.display = 'flex';
      } else {
        if (setLbl) setLbl.innerText = 'Account Status';
        if (setDesc) setDesc.innerText = 'Not signed in. Connect to sync your playlists and liked tracks.';
        if (setBtn) { setBtn.innerText = 'Connect Account'; setBtn.className = 'btn-kinetic btn-primary'; }
        if (setSyncRow) setSyncRow.style.display = 'none';
      }
    }

    function clearAppCache() {
      try {
        lastQueueChecksum = '';
        currentSearchResults = [];
        localStorage.removeItem('jv_queue_cache');
        localStorage.removeItem('jv_cached_state');
        showToast('App cache cleared successfully');
        loadQueue();
      } catch (e) {
        showToast('Cache cleared');
      }
    }

    function resetAllSettings() {
      try {
        localStorage.removeItem('jv_settings');
        localStorage.removeItem('jv_vis_preset');
        localStorage.removeItem('jv_vis_enabled');
        localStorage.removeItem('jv_vis_opacity');
        localStorage.removeItem('jv_vis_sensitivity');
        localStorage.removeItem('jv_vis_cover_bg');
        ['search', 'library', 'sounds', 'shortcuts', 'settings'].forEach(k => {
          try { localStorage.removeItem('jv_guide_dismissed_' + k); } catch (e) {}
        });
        currentTheme = 'purple';
        currentCoverShape = 'modern';
        currentGlassBlur = 'frosted';
        currentLatencyMode = (navigator.userAgent.toLowerCase().includes('firefox') || navigator.userAgent.toLowerCase().includes('zen')) ? 'stable' : 'balanced';
        currentVolWheelCurve = 'adaptive';
        soundboardPreviewEnabled = false;
        soundboardPreviewVol = 0.75;
        lockScreenControlsEnabled = true;
        auroraDefaultEnabled = true;
        applyAllSettings();
        initTabTutorials();
        showToast('All settings restored to defaults');
      } catch (e) {
        showToast('Settings reset');
      }
    }

    // ==========================================
    // Interactive Tab Tutorials & Popup Guides
    // ==========================================
    const TAB_TUTORIALS = {
      search: {
        title: 'Track Search & Discovery Guide',
        sub: 'Search 3,800+ lossless archive songs or stream online',
        icon: '<svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        steps: [
          { badge: 'STEP 1 • QUERY', text: 'Type any title, artist, or album and press <strong>Search</strong>.' },
          { badge: 'STEP 2 • SOURCES', text: 'Toggle between <strong>JuiceVault Archive</strong> (instant lossless) and <strong>Online</strong> (YouTube & SoundCloud).' },
          { badge: 'STEP 3 • 1-CLICK QUEUE', text: 'Click any song row to immediately add to the Discord VC queue.' }
        ],
        tip: '💡 Tip: Press <code>/</code> anywhere on desktop to focus the search field instantly.'
      },
      library: {
        title: 'Collections & Library Guide',
        sub: 'Curated discography, JuiceVault account playlists & favorites',
        icon: '<svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>',
        steps: [
          { badge: 'STEP 1 • CHOOSE COLLECTION', text: 'Select curated eras (e.g. <em>Death Race For Love</em>, <em>Studio Sessions</em>, <em>Unreleased Bangers</em>).' },
          { badge: 'STEP 2 • SHUFFLE & PLAY', text: 'Click <strong>Shuffle & Play</strong> on any collection to load hundreds of tracks into Discord VC.' },
          { badge: 'STEP 3 • ACCOUNT PLAYLISTS', text: 'Sign in to JuiceVault.xyz to sync your personal cloud playlists and liked tracks.' }
        ],
        tip: '💡 Tip: Switching collections does not stop active playback until you trigger Shuffle & Play.'
      },
      soundboard: {
        title: 'Discord Soundboard & Audition Guide',
        sub: '50 meme sounds with voice ducking & local preview',
        icon: '<svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>',
        steps: [
          { badge: 'STEP 1 • INSTANT TRIGGER', text: 'Click any pad to play on Discord VC. Music automatically ducks or pauses, then resumes.' },
          { badge: 'STEP 2 • LOCAL AUDITION', text: 'Enable <strong>Play preview locally</strong> to test sounds in your headphones first.' },
          { badge: 'STEP 3 • LIVE FILTER', text: 'Use the filter input to instantly find clips like <em>bruh</em>, <em>airhorn</em>, or <em>vine_boom</em>.' }
        ],
        tip: '💡 Tip: Click <strong>Stop Sound</strong> or "Resume Song" to immediately return to music.'
      },
      shortcuts: {
        title: 'Hotkeys & Remote Controls Guide',
        sub: 'Desktop keys, headphone media session & webhook REST API',
        icon: '<svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        steps: [
          { badge: 'STEP 1 • KEYBOARD HOTKEYS', text: 'Press <strong>Space</strong> for Play/Pause, <strong>Shift+→</strong> to Skip, <strong>M</strong> to Mute, and <strong>↑ / ↓</strong> for Volume.' },
          { badge: 'STEP 2 • MEDIA CONTROLS', text: 'Wireless headphones, keyboard volume dials, and mobile lockscreens control the bot directly.' },
          { badge: 'STEP 3 • WEBHOOK REST API', text: 'Copy 1-click webhook URLs for Siri Shortcuts, back-taps, or Stream Deck buttons.' }
        ],
        tip: '💡 Tip: Hotkeys operate globally anywhere on the web remote without needing to click the player.'
      },
      settings: {
        title: 'Studio Remote & Audio Settings Guide',
        sub: 'Latency buffer modes, smooth volume wheel & visual themes',
        icon: '<svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
        steps: [
          { badge: 'STEP 1 • BUFFER LATENCY', text: 'Keep on <strong>Stable (Gecko/Firefox)</strong> to prevent pops, or switch to <strong>Ultra (250ms)</strong> for near-zero lag.' },
          { badge: 'STEP 2 • TACTILE WHEEL', text: 'Mouse wheel smoothly moves at <strong>1% per notch</strong>, accelerating dynamically on rapid spins.' },
          { badge: 'STEP 3 • ACCENT THEMES', text: 'Choose from 5 neon accent color themes and customize live audio reactive backdrops.' }
        ],
        tip: '💡 Tip: All preferences auto-save to browser storage and persist on every session.'
      },
      queue: {
        title: 'Queue & Playback Flow Guide',
        sub: 'Manage live requests, upcoming archive & playback history',
        icon: '<svg class="icon-svg" style="width:18px;height:18px;" viewBox="0 0 24 24"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
        steps: [
          { badge: 'STEP 1 • REQUEST PRIORITY', text: 'User-requested tracks sit at the top of the queue and play with highest priority.' },
          { badge: 'STEP 2 • UPCOMING ARCHIVE', text: 'Upcoming archive songs automatically fill in when no user requests remain.' },
          { badge: 'STEP 3 • QUEUE ACTIONS', text: 'Tap any queued track for options to Play Right Now, Move to Next, or Remove.' }
        ],
        tip: '💡 Tip: Audio plays lossless PCM stream directly synchronized with your Discord voice channel.'
      }
    };

    function openTutorialPopup(tabKey, isAuto = false) {
      if (tabKey === 'categories') tabKey = 'library';
      if (tabKey === 'sounds') tabKey = 'soundboard';
      const data = TAB_TUTORIALS[tabKey];
      if (!data) return;

      const modal = document.getElementById('tutorialModal');
      if (!modal) return;

      const iconEl = document.getElementById('tutModalIcon');
      if (iconEl) iconEl.innerHTML = data.icon;
      const titleEl = document.getElementById('tutModalTitle');
      if (titleEl) titleEl.textContent = data.title;
      const subEl = document.getElementById('tutModalSub');
      if (subEl) subEl.textContent = data.sub;

      const stepsContainer = document.getElementById('tutModalSteps');
      if (stepsContainer) {
        stepsContainer.innerHTML = data.steps.map(s => `
          <div class="tutorial-step-tile">
            <div class="tutorial-step-badge">
              <svg class="icon-svg" style="width:11px;height:11px;" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
              ${escapeHtml(s.badge)}
            </div>
            <div class="tutorial-step-text">${s.text}</div>
          </div>
        `).join('');
      }

      const tipEl = document.getElementById('tutModalTip');
      if (tipEl) tipEl.innerHTML = data.tip;

      const noteEl = document.getElementById('tutModalFooterNote');
      if (noteEl) noteEl.textContent = isAuto ? 'First-Time Tab Tour • Shown 1 Time' : 'Tab Guide & Walkthrough';

      modal.classList.add('active');
    }

    function closeTutorialPopup() {
      const modal = document.getElementById('tutorialModal');
      if (modal) modal.classList.remove('active');
    }

    function maybeShowTabTutorialPopup(tabKey) {
      if (tabKey === 'categories') tabKey = 'library';
      if (tabKey === 'sounds') tabKey = 'soundboard';
      if (!TAB_TUTORIALS[tabKey]) return;
      try {
        const key = 'jv_popup_seen_' + tabKey;
        if (localStorage.getItem(key) === 'true') return;
        localStorage.setItem(key, 'true');
        setTimeout(() => {
          openTutorialPopup(tabKey, true);
        }, 260);
      } catch (e) {}
    }

    function resetAllTabTutorials() {
      ['search', 'library', 'soundboard', 'shortcuts', 'settings', 'queue'].forEach(k => {
        try {
          localStorage.removeItem('jv_popup_seen_' + k);
          localStorage.removeItem('jv_guide_dismissed_' + k);
        } catch (e) {}
      });
      showToast('All tab tutorials & walkthrough popups restored');
    }

    function initTabTutorials() {
      // Kept for settings reset backwards compatibility
    }

    function updateFavoriteButtonState() {
      const favBtn = document.getElementById('btnFavoriteSong');
      if (!favBtn) return;
      const t = currentState && currentState.track;
      if (!t || !currentState.is_running) {
        favBtn.style.display = 'none';
        favBtn.classList.remove('is-favorite');
        return;
      }
      favBtn.style.display = 'inline-flex';
      const tid = String(t.id || t.title || '').toLowerCase();
      const isFav = userLikesSet.has(tid) || userLikesSet.has(String(t.title || '').toLowerCase());
      if (isFav) {
        favBtn.classList.add('is-favorite');
        favBtn.title = 'Remove from favorites (JuiceVault)';
      } else {
        favBtn.classList.remove('is-favorite');
        favBtn.title = 'Add to favorites (JuiceVault)';
      }
    }

    async function toggleCurrentSongFavorite() {
      if (!currentJvUser) {
        openUserModal();
        showToast('Connect your JuiceVault account first to favorite tracks');
        return;
      }
      const t = currentState && currentState.track;
      if (!t) return;

      const tid = String(t.id || t.title || '').toLowerCase();
      const isFav = userLikesSet.has(tid) || userLikesSet.has(String(t.title || '').toLowerCase());

      if (isFav) {
        userLikesSet.delete(tid);
        userLikesSet.delete(String(t.title || '').toLowerCase());
        userLikesCache = userLikesCache.filter(x => {
          const xid = String(x.id || x.songId || x.title || '').toLowerCase();
          return xid !== tid && xid !== String(t.title || '').toLowerCase();
        });
        showToast(`Removed "${t.title}" from favorites`);
      } else {
        const newFav = {
          id: t.id || tid,
          title: t.title || 'Untitled Track',
          artist: t.artist || 'Juice WRLD',
          cover_url: t.cover_url || (t.id ? `https://api.juicevault.xyz/cdn/music/covers/${t.id}` : ''),
          length: t.length || '—'
        };
        userLikesSet.add(tid);
        if (t.title) userLikesSet.add(String(t.title).toLowerCase());
        userLikesCache.unshift(newFav);
        showToast(`Added "${t.title}" to favorites! ❤️`);
      }

      localStorage.setItem('jv_likes', JSON.stringify(userLikesCache));
      const favCountEl = document.getElementById('userFavsBtnCount');
      if (favCountEl) favCountEl.innerText = userLikesCache.length;
      const likedCountEl = document.getElementById('userLikedCount');
      if (likedCountEl) likedCountEl.innerText = userLikesCache.length;
      updateFavoriteButtonState();
    }

    function viewUserFavorites() {
      closeUserModal();
      if (!userLikesCache || userLikesCache.length === 0) {
        showToast('No favorite songs saved yet');
        return;
      }
      switchTab('search');
      currentSearchResults = userLikesCache;
      const resContainer = document.getElementById('searchResults');
      if (!resContainer) return;

      let html = `
        <div style="background:linear-gradient(135deg, rgba(244,63,94,0.12), rgba(168,85,247,0.08)); border:1px solid rgba(244,63,94,0.3); border-radius:12px; padding:12px 16px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; color:#f43f5e; font-weight:700;">JuiceVault Favorites</div>
            <div style="font-weight:700; font-size:0.92rem; color:#fff;">@${escapeHtml(currentJvUser ? currentJvUser.username : 'User')} • ${userLikesCache.length} track${userLikesCache.length === 1 ? '' : 's'}</div>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-kinetic btn-badge" style="background:#f43f5e; color:#fff;" onclick="addAllPlaylistTracks(true)">Play All</button>
            <button class="btn-kinetic btn-badge" onclick="addAllPlaylistTracks(false)">Queue All</button>
          </div>
        </div>
      `;

      html += userLikesCache.map((item, idx) => `
        <div class="track-card">
          <div class="track-meta-col">
            <div class="track-name">${escapeHtml(item.title || 'Untitled')}</div>
            <div class="track-desc">${escapeHtml(item.artist || 'Juice WRLD')} • ${escapeHtml(item.length || '—')}</div>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-kinetic btn-badge" onclick="addSearchResultByIndex(${idx}, true)" title="Play Now">Play</button>
            <button class="btn-kinetic btn-badge" onclick="addSearchResultByIndex(${idx}, false)" title="Add to Queue">+ Add</button>
          </div>
        </div>
      `).join('');

      resContainer.innerHTML = html;
    }

    // Discord Server / Guild Switcher Engine
    async function openGuildModal() {
      const sheet = document.getElementById('guildSheet');
      if (sheet) sheet.classList.add('active');
      const container = document.getElementById('guildListContainer');
      if (!container) return;
      container.innerHTML = '<div style="text-align:center; padding:18px; color:var(--text-sub); font-size:0.8rem;">Loading servers…</div>';
      try {
        const res = await fetch(`/api/guilds?${apiQuery()}`, { headers: apiHeaders() });
        const data = await res.json();
        const guilds = (data && data.guilds) || [];
        if (guilds.length === 0) {
          container.innerHTML = '<div style="text-align:center; padding:18px; color:var(--text-sub); font-size:0.8rem;">No Discord servers found.</div>';
          return;
        }
        container.innerHTML = guilds.map(g => {
          const isSelected = String(g.id) === String(currentGuildId);
          const activeTag = g.is_active ? '<span class="status-badge" style="padding:2px 7px; font-size:0.65rem; color:#10b981; border-color:rgba(16,185,129,0.3); background:rgba(16,185,129,0.08);"><span class="status-dot" style="background:#10b981;"></span>Playing</span>' : '<span style="font-size:0.68rem; color:var(--text-sub);">Idle</span>';
          const borderStyle = isSelected ? 'border:1px solid #c084fc; background:rgba(192, 132, 252, 0.12);' : 'border:1px solid var(--border); background:var(--surface);';
          const escapedName = escapeHtml(g.name).replace(/'/g, "\\'");
          return `
            <div class="track-card btn-kinetic" style="cursor:pointer; display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-radius:12px; ${borderStyle}" onclick="selectGuild('${g.id}', '${escapedName}')">
              <div style="display:flex; align-items:center; gap:10px; min-width:0;">
                <div style="width:34px; height:34px; border-radius:10px; background:rgba(255,255,255,0.06); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                  <svg class="icon-svg" style="width:16px;height:16px;color:${isSelected ? '#c084fc' : 'var(--text-muted)'};" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                <div style="min-width:0;">
                  <div style="font-weight:600; font-size:0.86rem; color:#fff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(g.name)}</div>
                  <div style="font-size:0.68rem; color:var(--text-muted); font-family:'JetBrains Mono',monospace;">ID: ${g.id}</div>
                </div>
              </div>
              <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
                ${activeTag}
                ${isSelected ? '<svg class="icon-svg" style="width:16px;height:16px;color:#c084fc;" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        container.innerHTML = `<div style="text-align:center; padding:18px; color:var(--danger); font-size:0.8rem;">Failed to load servers: ${escapeHtml(err.message)}</div>`;
      }
    }

    function closeGuildModal() {
      const sheet = document.getElementById('guildSheet');
      if (sheet) sheet.classList.remove('active');
    }

    async function selectGuild(gid, gname) {
      if (String(currentGuildId) === String(gid)) {
        closeGuildModal();
        return;
      }
      currentGuildId = String(gid);
      localStorage.setItem('jv_guild_id', currentGuildId);

      const badge = document.getElementById('guildBadgeName');
      if (badge) badge.innerText = gname || gid;
      const gNameEl = document.getElementById('guildName');
      if (gNameEl) gNameEl.innerText = gname || gid;

      try {
        const u = new URL(window.location.href);
        u.searchParams.set('guild_id', currentGuildId);
        window.history.replaceState({}, '', u.toString());
      } catch (e) {}

      closeGuildModal();
      showToast(`Switched to: ${gname}`);

      // Notify WebSocket of active guild
      if (ws && ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify({ action: 'set_guild', guild_id: currentGuildId }));
        } catch (e) {}
      } else {
        connectWS();
      }

      // If Listen Together live stream is active, resync stream to new server
      if (liveStreamActive) {
        syncLiveAudio(true);
      }

      await fetchStatus();
      loadQueue();
      fetchTelemetry();
    }

    // Live Global Telemetry & Daily Usage Engine
    let cachedTelemetryData = null;

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
        const res = await fetch(`/api/stats?${apiQuery()}`);
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
      cachedTelemetryData = stats;

      const target = stats.global || stats;
      const views = target.views || {};
      const daily = target.daily_usage || {};
      const allTime = target.all_time || {};

      const fmt = (n) => (n !== undefined && n !== null) ? Number(n).toLocaleString() : '--';
      const setValWithPop = (el, val) => {
        if (!el) return;
        const s = String(val);
        if (el.innerText !== s) {
          el.innerText = s;
          el.classList.remove('stat-pop');
          void el.offsetWidth;
          el.classList.add('stat-pop');
        }
      };

      // Active VC session stream time priority
      const streamTimeToday = (stats.session && stats.session.active && stats.session.seconds > 60)
        ? stats.session.formatted
        : (daily.listening_formatted || '0m');

      // Header badge
      const hCount = document.getElementById('headerViewsCount');
      if (hCount) setValWithPop(hCount, fmt(views.total) + ' views');
      const hDaily = document.getElementById('headerDailyCount');
      if (hDaily) setValWithPop(hDaily, fmt(views.today) + ' today');

      const sSubtitle = document.getElementById('statsSubtitle');
      if (sSubtitle && stats.session && stats.session.active && stats.session.formatted) {
        sSubtitle.innerText = `Continuous Voice Session: ${stats.session.formatted} • Real-time Bot Telemetry`;
      }

      // Compact quick bar
      const qTot = document.getElementById('quickTotalViews');
      setValWithPop(qTot, fmt(views.total));
      const qDay = document.getElementById('quickDailyViews');
      setValWithPop(qDay, fmt(views.today));
      const qTime = document.getElementById('quickDailyTime');
      setValWithPop(qTime, streamTimeToday);
      const qTracks = document.getElementById('quickDailyTracks');
      setValWithPop(qTracks, fmt(daily.tracks_played));

      // Modal sheet values
      const sTot = document.getElementById('statsTotalViews');
      setValWithPop(sTot, fmt(views.total));
      const sDay = document.getElementById('statsDailyViews');
      setValWithPop(sDay, fmt(views.today));
      const sUniq = document.getElementById('statsUniqueViews');
      setValWithPop(sUniq, fmt(views.unique_today));
      const sSess = document.getElementById('statsSessionsNow');
      if (sSess) sSess.innerText = (views.active_sessions || 1) + ' active now';
      const sTime = document.getElementById('statsDailyTime');
      setValWithPop(sTime, streamTimeToday);
      const sAllTime = document.getElementById('statsAllTimeTime');
      if (sAllTime) sAllTime.innerText = (allTime.listening_formatted || '0m') + ' total';
      const sTracks = document.getElementById('statsDailyTracks');
      setValWithPop(sTracks, fmt(daily.tracks_played));
      const sReqs = document.getElementById('statsDailyReqs');
      setValWithPop(sReqs, fmt(daily.requests_queued));
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
      setValWithPop(cTot, fmt(views.total));
      const cDay = document.getElementById('cardDailyViews');
      setValWithPop(cDay, fmt(views.today));
      const cUniq = document.getElementById('cardUniqueViews');
      setValWithPop(cUniq, fmt(views.unique_today));
      const cSess = document.getElementById('cardSessionsNow');
      if (cSess) cSess.innerText = (views.active_sessions || 1) + ' active';
      const cTime = document.getElementById('cardDailyTime');
      setValWithPop(cTime, streamTimeToday);
      const cAllTime = document.getElementById('cardAllTimeTime');
      if (cAllTime) cAllTime.innerText = (allTime.listening_formatted || '0m') + ' total';
      const cTracks = document.getElementById('cardDailyTracks');
      setValWithPop(cTracks, fmt(daily.tracks_played));
      const cReqs = document.getElementById('cardDailyReqs');
      setValWithPop(cReqs, fmt(daily.requests_queued));
      const cAllTracks = document.getElementById('cardAllTimeTracks');
      if (cAllTracks) cAllTracks.innerText = fmt(allTime.tracks_played) + ' total';

      renderActivityBars('statsActivityBars', daily.tracks_played || 1, views.today || 1, target.hourly_activity);
      renderActivityBars('cardActivityBars', daily.tracks_played || 1, views.today || 1, target.hourly_activity);
    }

    function renderActivityBars(containerId, tracksCount, viewsCount, hourlyData) {
      const container = document.getElementById(containerId);
      if (!container) return;
      const currentHour = new Date().getUTCHours();
      let html = '';
      for (let h = 0; h < 24; h++) {
        let cls = 'activity-bar';
        let pct = 8;
        if (Array.isArray(hourlyData) && hourlyData.length === 24) {
          const val = hourlyData[h] || 0;
          pct = Math.min(100, Math.max(8, val * 12));
        } else {
          const wave = Math.sin((h + 2) / 3.2) * 35 + 45;
          pct = Math.max(12, Math.min(95, Math.round(wave + ((h * 7) % 20))));
        }
        if (h === currentHour) {
          cls += ' current';
          pct = Math.max(pct, 40);
        } else if (h < currentHour) {
          cls += ' active';
          if (pct > 65) cls += ' high';
        }
        const hourLabel = String(h).padStart(2, '0') + ':00 UTC';
        html += `<div class="activity-bar-slot" title="${hourLabel} • ${pct}% activity"><div class="${cls}" style="height:${pct}%;"></div></div>`;
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
        const res = await fetch(`/api/soundboard?${apiQuery()}`, { headers: apiHeaders() });
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
        const res = await fetch(`/api/soundboard/play?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ sound_id: soundId, guild_id: currentGuildId })
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
        await fetch(`/api/soundboard/stop?${apiQuery()}`, {
          method: 'POST',
          headers: apiHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ guild_id: currentGuildId })
        });
      } catch (e) {
        showToast('Error stopping: ' + e.message);
      }
    }

    // Lifecycle listeners for instant mobile reconnect on unlock / tab focus with 1s debounce
    let lastLifecycleSyncTime = 0;
    function handleLifecycleSync() {
      const now = Date.now();
      if (now - lastLifecycleSyncTime < 1000) return;
      lastLifecycleSyncTime = now;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWS();
      } else {
        try { ws.send(JSON.stringify({ action: 'ping' })); } catch (e) {}
      }
      fetchStatus();
      armBackgroundMediaSession();
    }

    // ==========================================
    // 10-PRESET AUDIO REACTIVE VISUALIZER ENGINE
    // ==========================================
    const VISUALIZER_PRESETS = [
      { id: 'cyber_bars', name: 'Cyber Neon Bars', desc: 'Dual-gradient 32-band spectrum with peak caps', tag: 'Studio' },
      { id: 'oscilloscope', name: 'Phosphor Oscilloscope', desc: 'High-voltage vector beam sine wave', tag: 'Vector' },
      { id: 'vinyl_aura', name: 'Circular Vinyl Aura', desc: 'Pulsing reactive rings surrounding album cover', tag: 'Cover' },
      { id: 'aurora_mesh', name: 'Ambient Aurora Waves', desc: 'Fluid cosmic northern lights across background', tag: 'Background' },
      { id: 'quantum_stars', name: 'Quantum Starfield', desc: 'Drifting galaxy stars bursting with bass drops', tag: 'Background' },
      { id: 'synthwave_grid', name: 'Retro Synthwave Grid', desc: '80s wireframe horizon with reactive rolling hills', tag: 'Background' },
      { id: 'glass_ribbons', name: 'Glass Frequency Ribbons', desc: 'Translucent glowing harmonic ribbons weaving behind cover', tag: 'Cover+BG' },
      { id: 'analog_vu', name: 'Analog Studio VU Meters', desc: 'Dual Left/Right ballistic dB peak needles', tag: 'Studio' },
      { id: 'sunburst_orbit', name: 'Radial Sunburst Coronal', desc: '360° solar flare rays emitting from vinyl disc', tag: 'Cover' },
      { id: 'hyper_tunnel', name: 'Hyperdrive Warp Tunnel', desc: 'Infinite geometric tunnel rings zooming outward', tag: 'Background' }
    ];

    let visEnabled = localStorage.getItem('jv_vis_enabled') !== 'false';
    let visPreset = localStorage.getItem('jv_vis_preset') || 'aurora_mesh';
    let visOpacity = parseFloat(localStorage.getItem('jv_vis_opacity') || '0.75');
    let visSensitivity = parseFloat(localStorage.getItem('jv_vis_sensitivity') || '1.0');
    let visCoverBgEnabled = localStorage.getItem('jv_vis_cover_bg') !== 'false';
    let visCoverBlur = parseInt(localStorage.getItem('jv_vis_cover_blur') || '36', 10);
    let visCoverDim = parseInt(localStorage.getItem('jv_vis_cover_dim') || '62', 10);
    let visCoverPulse = localStorage.getItem('jv_vis_cover_pulse') !== 'false';
    let currentCoverBgUrl = '';
    let visSimTime = 0;
    let visAnimFrame = null;
    let visStars = [];
    let visGridOffset = 0;
    let visPeaks = new Float32Array(64);

    function initVisualizerStars() {
      visStars = [];
      const w = window.innerWidth || 1200;
      const h = window.innerHeight || 800;
      for (let i = 0; i < 75; i++) {
        visStars.push({
          x: (Math.random() - 0.5) * w * 1.5,
          y: (Math.random() - 0.5) * h * 1.5,
          z: Math.random() * 1000 + 1,
          size: Math.random() * 2 + 1,
          hue: Math.random() > 0.5 ? 275 : 195
        });
      }
    }

    function renderVisualizerPresetsList() {
      const container = document.getElementById('visPresetList');
      if (!container) return;
      container.innerHTML = VISUALIZER_PRESETS.map(p => {
        const isActive = p.id === visPreset;
        let tagClass = 'accent';
        if (p.tag === 'Background') tagClass = 'ambient';
        if (p.tag === 'Cover' || p.tag === 'Cover+BG') tagClass = 'cover';
        return `
          <div class="vis-preset-card ${isActive ? 'active' : ''}" onclick="setVisualizerPreset('${p.id}')">
            <div class="p-left">
              <span class="p-name">${p.name}</span>
              <span class="p-desc">${p.desc}</span>
            </div>
            <span class="vis-tag ${tagClass}">${p.tag}</span>
          </div>
        `;
      }).join('');
    }

    function openVisualizerModal() {
      renderVisualizerPresetsList();
      const modal = document.getElementById('visualizerModal');
      if (modal) {
        modal.classList.add('visible');
        modal.classList.add('active');
      }
      const opSlider = document.getElementById('visOpacitySlider');
      if (opSlider) opSlider.value = visOpacity;
      const opVal = document.getElementById('visOpacityVal');
      if (opVal) opVal.innerText = `${Math.round(visOpacity * 100)}%`;
      const sensSlider = document.getElementById('visSensSlider');
      if (sensSlider) sensSlider.value = visSensitivity;
      const sensVal = document.getElementById('visSensVal');
      if (sensVal) sensVal.innerText = `${visSensitivity.toFixed(1)}x`;

      const bgToggle = document.getElementById('visCoverBgToggle');
      if (bgToggle) bgToggle.checked = visCoverBgEnabled;
      const blurSlider = document.getElementById('visCoverBlurSlider');
      if (blurSlider) blurSlider.value = visCoverBlur;
      const blurVal = document.getElementById('visCoverBlurVal');
      if (blurVal) blurVal.innerText = `${visCoverBlur}px`;
      const dimSlider = document.getElementById('visCoverDimSlider');
      if (dimSlider) dimSlider.value = visCoverDim;
      const dimVal = document.getElementById('visCoverDimVal');
      if (dimVal) dimVal.innerText = `${visCoverDim}%`;
      const pulseToggle = document.getElementById('visCoverPulseToggle');
      if (pulseToggle) pulseToggle.checked = visCoverPulse;

      updateVisualizerMasterBtnUI();
    }

    function updateCoverArtBackground(coverUrl) {
      currentCoverBgUrl = coverUrl || '';
      const bgContainer = document.getElementById('dynamicCoverBg');
      const bgImg = document.getElementById('dynamicCoverImg');
      if (!bgContainer || !bgImg) return;
      if (coverUrl && visCoverBgEnabled) {
        if (bgImg.src !== coverUrl) {
          bgImg.src = coverUrl;
        }
        bgContainer.classList.add('active');
      } else {
        bgContainer.classList.remove('active');
      }
    }

    function updateCoverBgToggle(enabled) {
      visCoverBgEnabled = !!enabled;
      try { localStorage.setItem('jv_vis_cover_bg', visCoverBgEnabled ? 'true' : 'false'); } catch (e) {}
      const bgContainer = document.getElementById('dynamicCoverBg');
      if (bgContainer) {
        if (visCoverBgEnabled && currentCoverBgUrl) bgContainer.classList.add('active');
        else bgContainer.classList.remove('active');
      }
    }

    function updateCoverBlur(val) {
      visCoverBlur = parseInt(val, 10);
      try { localStorage.setItem('jv_vis_cover_blur', String(visCoverBlur)); } catch (e) {}
      const bgImg = document.getElementById('dynamicCoverImg');
      if (bgImg) bgImg.style.filter = `blur(${visCoverBlur}px) saturate(1.35)`;
      const lbl = document.getElementById('visCoverBlurVal');
      if (lbl) lbl.innerText = `${visCoverBlur}px`;
    }

    function updateCoverDim(val) {
      visCoverDim = parseInt(val, 10);
      try { localStorage.setItem('jv_vis_cover_dim', String(visCoverDim)); } catch (e) {}
      const overlay = document.getElementById('dynamicCoverOverlay');
      if (overlay) overlay.style.background = `rgba(9, 9, 13, ${visCoverDim / 100})`;
      const lbl = document.getElementById('visCoverDimVal');
      if (lbl) lbl.innerText = `${visCoverDim}%`;
    }

    function updateCoverPulseToggle(enabled) {
      visCoverPulse = !!enabled;
      try { localStorage.setItem('jv_vis_cover_pulse', visCoverPulse ? 'true' : 'false'); } catch (e) {}
      if (!visCoverPulse) {
        const bgImg = document.getElementById('dynamicCoverImg');
        if (bgImg) bgImg.style.transform = 'scale(1.04)';
      }
    }

    function resetVisualizerSettings() {
      visPreset = 'aurora_mesh';
      visOpacity = 0.75;
      visSensitivity = 1.0;
      visCoverBgEnabled = true;
      visCoverBlur = 36;
      visCoverDim = 62;
      visCoverPulse = true;
      try {
        localStorage.setItem('jv_vis_preset', 'aurora_mesh');
        localStorage.setItem('jv_vis_opacity', '0.75');
        localStorage.setItem('jv_vis_sensitivity', '1.0');
        localStorage.setItem('jv_vis_cover_bg', 'true');
        localStorage.setItem('jv_vis_cover_blur', '36');
        localStorage.setItem('jv_vis_cover_dim', '62');
        localStorage.setItem('jv_vis_cover_pulse', 'true');
      } catch (e) {}
      updateVisualizerOpacity(visOpacity);
      updateVisualizerSens(visSensitivity);
      updateCoverBlur(visCoverBlur);
      updateCoverDim(visCoverDim);
      updateCoverBgToggle(true);
      updateCoverPulseToggle(true);
      openVisualizerModal();
      showToast('Visualizer reset to Aurora Waves & defaults');
    }

    function closeVisualizerModal() {
      const modal = document.getElementById('visualizerModal');
      if (modal) {
        modal.classList.remove('visible');
        modal.classList.remove('active');
      }
    }

    function updateVisualizerMasterBtnUI() {
      const btn = document.getElementById('visToggleMasterBtn');
      const lbl = document.getElementById('visToggleMasterLabel');
      const badge = document.getElementById('visActiveBadge');
      const headerBtn = document.getElementById('visualizerBtn');
      if (visEnabled) {
        if (btn) btn.classList.add('active');
        if (lbl) lbl.innerText = 'Enabled';
        if (badge) { badge.innerText = 'Active'; badge.className = 'lt-sync-badge live'; }
        if (headerBtn) headerBtn.classList.add('active');
      } else {
        if (btn) btn.classList.remove('active');
        if (lbl) lbl.innerText = 'Disabled';
        if (badge) { badge.innerText = 'Off'; badge.className = 'lt-sync-badge paused'; }
        if (headerBtn) headerBtn.classList.remove('active');
      }
    }

    function toggleVisualizerState() {
      visEnabled = !visEnabled;
      localStorage.setItem('jv_vis_enabled', visEnabled ? 'true' : 'false');
      updateVisualizerMasterBtnUI();
      const canvas = document.getElementById('ambientVisualizerCanvas');
      const aura = document.getElementById('coverVisualizerAura');
      if (visEnabled) {
        if (canvas) canvas.classList.add('active');
        showToast('Visualizer activated');
      } else {
        if (canvas) {
          canvas.classList.remove('active');
          const ctx = canvas.getContext('2d');
          if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        if (aura) aura.classList.remove('active');
        showToast('Visualizer deactivated');
      }
    }

    function setVisualizerPreset(id) {
      visPreset = id;
      localStorage.setItem('jv_vis_preset', id);
      renderVisualizerPresetsList();
      const p = VISUALIZER_PRESETS.find(x => x.id === id);
      showToast(`Preset: ${p ? p.name : id}`);
    }

    function updateVisualizerOpacity(val) {
      visOpacity = parseFloat(val);
      localStorage.setItem('jv_vis_opacity', visOpacity);
      const canvas = document.getElementById('ambientVisualizerCanvas');
      if (canvas) canvas.style.opacity = visOpacity;
      const opVal = document.getElementById('visOpacityVal');
      if (opVal) opVal.innerText = `${Math.round(visOpacity * 100)}%`;
    }

    function updateVisualizerSens(val) {
      visSensitivity = parseFloat(val);
      localStorage.setItem('jv_vis_sensitivity', visSensitivity);
      const sensVal = document.getElementById('visSensVal');
      if (sensVal) sensVal.innerText = `${visSensitivity.toFixed(1)}x`;
    }

    function getActiveFrequencies() {
      const bins = new Uint8Array(64);
      if (liveStreamActive && analyserNode && visDataArray) {
        analyserNode.getByteFrequencyData(visDataArray);
        for (let i = 0; i < 64; i++) {
          const idx = Math.floor((i / 64) * visDataArray.length * 0.85);
          bins[i] = Math.min(255, Math.floor((visDataArray[idx] || 0) * visSensitivity));
        }
        return bins;
      }
      const isPlaying = !!(currentState && currentState.is_playing);
      const speed = (currentState && currentState.track && currentState.track.effect_speed) || 1.0;
      // Calm, fluid ambient motion when not actively streaming in browser
      visSimTime += isPlaying ? (0.016 * speed) : 0.004;
      for (let i = 0; i < 64; i++) {
        if (!isPlaying) {
          bins[i] = Math.max(0, Math.floor(8 + Math.sin(visSimTime + i * 0.2) * 5));
          continue;
        }
        // Smooth serene wave harmonics without aggressive kick pulses
        const wave1 = Math.sin(visSimTime * 1.0 + i * 0.09) * 0.5 + 0.5;
        const wave2 = Math.cos(visSimTime * 0.6 + i * 0.15) * 0.5 + 0.5;
        const breathing = Math.sin(visSimTime * 0.45) * 0.15 + 0.85;
        let v = (wave1 * 0.65 + wave2 * 0.35) * breathing;
        bins[i] = Math.min(130, Math.floor(v * 105 * visSensitivity));
      }
      return bins;
    }

    function renderVisualizerLoop(now) {
      visAnimFrame = requestAnimationFrame(renderVisualizerLoop);
      const canvas = document.getElementById('ambientVisualizerCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const dpr = Math.min(window.devicePixelRatio || 1, 2.0);
      const w = window.innerWidth;
      const h = window.innerHeight;
      const bufW = Math.floor(w * dpr);
      const bufH = Math.floor(h * dpr);
      if (canvas.width !== bufW || canvas.height !== bufH) {
        canvas.width = bufW;
        canvas.height = bufH;
      }

      if (!visEnabled) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const aura = document.getElementById('coverVisualizerAura');
        if (aura) aura.classList.remove('active');
        return;
      }

      const bins = getActiveFrequencies();
      let bassSum = 0;
      for (let i = 0; i < 8; i++) bassSum += bins[i];
      const avgBass = bassSum / 8;
      const bassRatio = Math.min(1.0, avgBass / 220);

      // Reactive pulse for dynamic song cover background
      if (visCoverBgEnabled && visCoverPulse) {
        const bgImg = document.getElementById('dynamicCoverImg');
        if (bgImg) {
          const pScale = 1.04 + (bassRatio * 0.04);
          bgImg.style.transform = `scale(${pScale.toFixed(3)})`;
        }
      }

      const coverWrap = document.getElementById('artContainer');
      const coverAura = document.getElementById('coverVisualizerAura');
      let cx = w / 2;
      let cy = h / 2;
      let coverRadius = 110;
      if (coverWrap) {
        const rect = coverWrap.getBoundingClientRect();
        if (rect.width > 0) {
          cx = rect.left + rect.width / 2;
          cy = rect.top + rect.height / 2;
          coverRadius = rect.width / 2;
        }
      }

      // Update Cover Aura element for reactive presets
      if (['vinyl_aura', 'glass_ribbons', 'sunburst_orbit'].includes(visPreset)) {
        if (coverAura) {
          coverAura.classList.add('active');
          const scale = 1.0 + (bassRatio * 0.18);
          coverAura.style.transform = `scale(${scale})`;
          coverAura.style.opacity = `${0.35 + bassRatio * 0.6}`;
        }
      } else {
        if (coverAura) coverAura.classList.remove('active');
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, w, h);

      // PRESET 1: CYBER NEON BARS
      if (visPreset === 'cyber_bars') {
        const numBars = 36;
        const totalW = Math.min(w * 0.9, 720);
        const startX = (w - totalW) / 2;
        const barW = (totalW / numBars) - 4;
        const maxH = Math.min(h * 0.35, 220);
        const baseY = h - 18;

        for (let i = 0; i < numBars; i++) {
          const val = bins[i] || 0;
          const barH = Math.max(4, (val / 255) * maxH);
          const x = startX + i * (barW + 4);
          const y = baseY - barH;

          if (val > (visPeaks[i] || 0)) visPeaks[i] = val;
          else visPeaks[i] = Math.max(0, (visPeaks[i] || 0) - 1.8);
          const peakY = baseY - Math.max(4, ((visPeaks[i] || 0) / 255) * maxH) - 4;

          const grad = ctx.createLinearGradient(0, y, 0, baseY);
          grad.addColorStop(0, '#c084fc');
          grad.addColorStop(0.5, '#a855f7');
          grad.addColorStop(1, 'rgba(107, 33, 168, 0.2)');

          ctx.fillStyle = grad;
          if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0]);
            ctx.fill();
          } else {
            ctx.fillRect(x, y, barW, barH);
          }

          ctx.fillStyle = '#fff';
          ctx.fillRect(x, peakY, barW, 2.5);
        }
      }

      // PRESET 2: OSCILLOSCOPE BEAM
      else if (visPreset === 'oscilloscope') {
        ctx.beginPath();
        const centerY = h * 0.65;
        const amp = Math.min(140, h * 0.22) * (0.6 + bassRatio * 0.8);
        ctx.moveTo(0, centerY);

        for (let x = 0; x < w; x += 4) {
          const normX = x / w;
          const binIdx = Math.floor(normX * 32);
          const val = (bins[binIdx] || 0) / 255;
          const wave1 = Math.sin(normX * 12 + visSimTime * 3) * val;
          const wave2 = Math.cos(normX * 24 - visSimTime * 2) * (val * 0.5);
          const y = centerY + (wave1 + wave2) * amp;
          ctx.lineTo(x, y);
        }

        ctx.strokeStyle = '#c084fc';
        ctx.lineWidth = 3;
        ctx.shadowColor = '#a855f7';
        ctx.shadowBlur = 18;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // PRESET 3: CIRCULAR VINYL AURA (Cover Art)
      else if (visPreset === 'vinyl_aura') {
        const numRings = 5;
        for (let r = 0; r < numRings; r++) {
          const binVal = (bins[r * 4] || 0) / 255;
          const radius = coverRadius + 14 + (r * 22) + (binVal * 28 * bassRatio);

          ctx.beginPath();
          ctx.arc(cx, cy, radius, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(192, 132, 252, ${0.18 + binVal * 0.45})`;
          ctx.lineWidth = 2 + binVal * 3;
          ctx.shadowColor = '#a855f7';
          ctx.shadowBlur = 14;
          ctx.stroke();

          const ticks = 16;
          for (let t = 0; t < ticks; t++) {
            const angle = (t / ticks) * Math.PI * 2 + (visSimTime * (r % 2 === 0 ? 0.4 : -0.4));
            const tx1 = cx + Math.cos(angle) * (radius - 3);
            const ty1 = cy + Math.sin(angle) * (radius - 3);
            const tx2 = cx + Math.cos(angle) * (radius + 5 + binVal * 8);
            const ty2 = cy + Math.sin(angle) * (radius + 5 + binVal * 8);
            ctx.beginPath();
            ctx.moveTo(tx1, ty1);
            ctx.lineTo(tx2, ty2);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }
        }
        ctx.shadowBlur = 0;
      }

      // PRESET 4: AMBIENT AURORA WAVES (Website Background)
      else if (visPreset === 'aurora_mesh') {
        const layers = 3;
        for (let l = 0; l < layers; l++) {
          ctx.beginPath();
          const baseWaveY = h * (0.45 + l * 0.18);
          ctx.moveTo(0, h);
          ctx.lineTo(0, baseWaveY);

          for (let x = 0; x <= w; x += 18) {
            const normX = x / w;
            const binIdx = Math.floor(normX * 24);
            const freq = (bins[binIdx] || 0) / 255;
            const wave = Math.sin(normX * 4 + visSimTime * (1.2 + l * 0.4)) * 60 * (1 + bassRatio);
            const waveSub = Math.cos(normX * 8 - visSimTime) * 30 * freq;
            const y = baseWaveY + wave + waveSub;
            ctx.lineTo(x, y);
          }

          ctx.lineTo(w, h);
          ctx.closePath();

          const grad = ctx.createLinearGradient(0, baseWaveY - 80, 0, h);
          if (l === 0) {
            grad.addColorStop(0, 'rgba(168, 85, 247, 0.28)');
            grad.addColorStop(1, 'rgba(107, 33, 168, 0)');
          } else if (l === 1) {
            grad.addColorStop(0, 'rgba(56, 189, 248, 0.24)');
            grad.addColorStop(1, 'rgba(14, 165, 233, 0)');
          } else {
            grad.addColorStop(0, 'rgba(244, 63, 94, 0.2)');
            grad.addColorStop(1, 'rgba(225, 29, 72, 0)');
          }
          ctx.fillStyle = grad;
          ctx.fill();
        }
      }

      // PRESET 5: QUANTUM STARFIELD (Website Background)
      else if (visPreset === 'quantum_stars') {
        if (!visStars.length) initVisualizerStars();
        const speed = 2 + bassRatio * 18;

        for (let s of visStars) {
          s.z -= speed;
          if (s.z <= 0) {
            s.z = 1000;
            s.x = (Math.random() - 0.5) * w * 1.5;
            s.y = (Math.random() - 0.5) * h * 1.5;
          }

          const k = 280 / s.z;
          const px = s.x * k + w / 2;
          const py = s.y * k + h / 2;

          if (px >= 0 && px <= w && py >= 0 && py <= h) {
            const size = Math.max(0.8, (1 - s.z / 1000) * 3.5 * s.size * (1 + bassRatio * 0.4));
            const alpha = Math.min(1, (1 - s.z / 1000) * 0.85);

            ctx.beginPath();
            ctx.arc(px, py, size, 0, Math.PI * 2);
            ctx.fillStyle = s.hue === 275 ? `rgba(192, 132, 252, ${alpha})` : `rgba(56, 189, 248, ${alpha})`;
            ctx.shadowColor = s.hue === 275 ? '#a855f7' : '#38bdf8';
            ctx.shadowBlur = 8;
            ctx.fill();
          }
        }
        ctx.shadowBlur = 0;
      }

      // PRESET 6: RETRO SYNTHWAVE GRID (Website Background)
      else if (visPreset === 'synthwave_grid') {
        const horizonY = h * 0.62;
        visGridOffset = (visGridOffset + 2 + bassRatio * 6) % 36;

        ctx.beginPath();
        ctx.moveTo(0, horizonY);
        for (let x = 0; x <= w; x += 16) {
          const normX = x / w;
          const binIdx = Math.floor(Math.abs(normX - 0.5) * 48);
          const mH = ((bins[binIdx] || 0) / 255) * 75 * (0.8 + bassRatio * 0.6);
          ctx.lineTo(x, horizonY - mH);
        }
        ctx.lineTo(w, horizonY);
        ctx.closePath();
        ctx.fillStyle = 'rgba(168, 85, 247, 0.12)';
        ctx.strokeStyle = '#c084fc';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fill();

        for (let y = horizonY; y < h; y += 18) {
          const progress = (y - horizonY) / (h - horizonY);
          const renderY = horizonY + Math.pow(progress, 1.8) * (h - horizonY) + (visGridOffset * progress * 0.4);
          if (renderY > horizonY && renderY <= h) {
            ctx.beginPath();
            ctx.moveTo(0, renderY);
            ctx.lineTo(w, renderY);
            ctx.strokeStyle = `rgba(192, 132, 252, ${0.1 + progress * 0.4})`;
            ctx.lineWidth = 1 + progress * 1.5;
            ctx.stroke();
          }
        }

        const numVLines = 28;
        for (let i = -numVLines; i <= numVLines; i++) {
          ctx.beginPath();
          ctx.moveTo(w / 2 + i * 18, horizonY);
          ctx.lineTo(w / 2 + i * 75, h);
          ctx.strokeStyle = 'rgba(168, 85, 247, 0.22)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }

      // PRESET 7: GLASS FREQUENCY RIBBONS (Cover & Background)
      else if (visPreset === 'glass_ribbons') {
        const numRibbons = 3;
        for (let r = 0; r < numRibbons; r++) {
          ctx.beginPath();
          const startY = cy + (r - 1) * 60;
          ctx.moveTo(0, startY);

          for (let x = 0; x <= w; x += 24) {
            const normX = x / w;
            const binIdx = Math.floor(normX * 30);
            const val = (bins[binIdx] || 0) / 255;
            const distFromCover = Math.abs(x - cx);
            const coverDodge = Math.max(0, 1 - distFromCover / 220);
            const y = startY + Math.sin(normX * 8 + visSimTime * 2 + r) * 45 * (1 + bassRatio) + (coverDodge * (r === 0 ? -40 : 40) * bassRatio);
            ctx.lineTo(x, y);
          }

          ctx.strokeStyle = r === 0 ? 'rgba(192, 132, 252, 0.55)' : (r === 1 ? 'rgba(56, 189, 248, 0.45)' : 'rgba(244, 63, 94, 0.4)');
          ctx.lineWidth = 3 + bassRatio * 4;
          ctx.shadowColor = '#a855f7';
          ctx.shadowBlur = 16;
          ctx.stroke();
        }
        ctx.shadowBlur = 0;
      }

      // PRESET 8: STUDIO ANALOG VU METERS
      else if (visPreset === 'analog_vu') {
        const meterW = Math.min(220, w * 0.4);
        const meterH = 110;
        const startY = h - meterH - 25;
        const centers = [w / 2 - meterW - 14, w / 2 + 14];

        centers.forEach((mx, idx) => {
          const val = ((bins[idx * 8] || 0) / 255);
          ctx.fillStyle = 'rgba(18, 18, 25, 0.85)';
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
          ctx.lineWidth = 1;
          if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(mx, startY, meterW, meterH, 8);
            ctx.fill();
            ctx.stroke();
          } else {
            ctx.fillRect(mx, startY, meterW, meterH);
          }

          const arcCx = mx + meterW / 2;
          const arcCy = startY + meterH - 12;
          const arcR = meterH * 0.72;
          ctx.beginPath();
          ctx.arc(arcCx, arcCy, arcR, Math.PI * 1.2, Math.PI * 1.8);
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
          ctx.lineWidth = 2;
          ctx.stroke();

          const needleAngle = Math.PI * 1.2 + val * (Math.PI * 0.6);
          const nx = arcCx + Math.cos(needleAngle) * (arcR - 4);
          const ny = arcCy + Math.sin(needleAngle) * (arcR - 4);
          ctx.beginPath();
          ctx.moveTo(arcCx, arcCy);
          ctx.lineTo(nx, ny);
          ctx.strokeStyle = val > 0.85 ? '#f43f5e' : '#c084fc';
          ctx.lineWidth = 2.5;
          ctx.stroke();

          ctx.fillStyle = 'var(--text-sub)';
          ctx.font = '600 0.65rem JetBrains Mono, monospace';
          ctx.fillText(idx === 0 ? 'CH-L (VU)' : 'CH-R (VU)', mx + 10, startY + 18);
        });
      }

      // PRESET 9: RADIAL SUNBURST ORBIT (Cover Art)
      else if (visPreset === 'sunburst_orbit') {
        const numRays = 48;
        for (let i = 0; i < numRays; i++) {
          const angle = (i / numRays) * Math.PI * 2 + (visSimTime * 0.3);
          const binIdx = Math.floor((i / numRays) * 32);
          const val = (bins[binIdx] || 0) / 255;
          const innerR = coverRadius + 12;
          const rayLen = 14 + val * 65 * (0.8 + bassRatio * 0.8);
          const outerR = innerR + rayLen;

          const x1 = cx + Math.cos(angle) * innerR;
          const y1 = cy + Math.sin(angle) * innerR;
          const x2 = cx + Math.cos(angle) * outerR;
          const y2 = cy + Math.sin(angle) * outerR;

          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.strokeStyle = `rgba(192, 132, 252, ${0.25 + val * 0.65})`;
          ctx.lineWidth = 2.5;
          ctx.stroke();
        }
      }

      // PRESET 10: HYPERDRIVE WARP TUNNEL (Background)
      else if (visPreset === 'hyper_tunnel') {
        const numTunnels = 8;
        for (let t = 0; t < numTunnels; t++) {
          const progress = ((t / numTunnels) + (visSimTime * 0.4)) % 1.0;
          const maxR = Math.max(w, h) * 0.8;
          const r = coverRadius + progress * maxR * (1 + bassRatio * 0.3);
          const alpha = (1 - progress) * 0.65;

          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(168, 85, 247, ${alpha})`;
          ctx.lineWidth = 1.5 + bassRatio * 3;
          ctx.stroke();
        }
      }
      ctx.restore();
    }

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') handleLifecycleSync();
    });

    window.addEventListener('pageshow', handleLifecycleSync);
    window.addEventListener('focus', handleLifecycleSync);

    // Global Arming on Any User Touch/Click/Key to Guarantee MediaSession Routing
    ['pointerdown', 'mousedown', 'keydown', 'touchstart'].forEach(evt => {
      window.addEventListener(evt, () => {
        armBackgroundMediaSession();
      }, { passive: true });
    });

    // Gaming Mouse Media Buttons (Razer Viper V3 Hyperspeed side buttons 3 & 4)
    window.addEventListener('auxclick', (e) => {
      const tag = (e.target.tagName || '').toLowerCase();
      if (['input', 'textarea', 'select', 'a', 'button'].includes(tag)) return;
      if (e.button === 3) {
        // Razer Viper V3 / Side Button Back
        e.preventDefault();
        action('previous');
        showToast('Mouse: Previous Track');
      } else if (e.button === 4) {
        // Razer Viper V3 / Side Button Forward
        e.preventDefault();
        action('skip');
        showToast('Mouse: Next Track');
      }
    });

    // Desktop Pro Keyboard Navigation & Hotkeys (Fn+F11, Media Keys, F-keys)
    window.addEventListener('keydown', (e) => {
      // 1. Hardware Media Keys (Fn+F11 on keyboards, Razer Synapse, Logitech G Hub, Windows HID)
      if (e.key === 'MediaPlayPause' || e.code === 'MediaPlayPause') {
        e.preventDefault();
        action('toggle');
        showToast('Media: Play / Pause');
        return;
      }
      if (e.key === 'MediaTrackNext' || e.code === 'MediaTrackNext') {
        e.preventDefault();
        action('skip');
        showToast('Media: Next Track');
        return;
      }
      if (e.key === 'MediaTrackPrevious' || e.code === 'MediaTrackPrevious') {
        e.preventDefault();
        action('previous');
        showToast('Media: Previous Track');
        return;
      }
      if (e.key === 'MediaStop' || e.code === 'MediaStop') {
        e.preventDefault();
        action('stop');
        showToast('Media: Stop Playback');
        return;
      }

      // Fn+F11 on keyboards that pass raw F11 keycode
      if (e.key === 'F11' || e.code === 'F11') {
        const tag = (e.target.tagName || '').toLowerCase();
        if (!['input', 'textarea', 'select'].includes(tag)) {
          e.preventDefault();
          action('toggle');
          showToast('Fn+F11: Play / Pause');
          return;
        }
      }
      if (e.key === 'F10' || e.code === 'F10') {
        const tag = (e.target.tagName || '').toLowerCase();
        if (!['input', 'textarea', 'select'].includes(tag) && (e.ctrlKey || e.altKey || e.shiftKey)) {
          e.preventDefault();
          action('previous');
          showToast('Previous Track');
          return;
        }
      }
      if (e.key === 'F12' || e.code === 'F12') {
        const tag = (e.target.tagName || '').toLowerCase();
        if (!['input', 'textarea', 'select'].includes(tag) && (e.ctrlKey || e.altKey || e.shiftKey)) {
          e.preventDefault();
          action('skip');
          showToast('Next Track');
          return;
        }
      }

      const tag = (e.target.tagName || '').toLowerCase();
      if (['input', 'textarea', 'select'].includes(tag) || e.target.isContentEditable) {
        if (e.key === 'Escape') e.target.blur();
        return;
      }
      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        action('toggle');
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        if (e.shiftKey) action('skip'); else action('seek', { delta: 10 });
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        if (e.shiftKey) action('previous'); else action('seek', { delta: -10 });
      } else if (e.key === 's' || e.key === 'S') {
        action('shuffle');
      } else if (e.key === 'r' || e.key === 'R') {
        action('repeat');
      } else if (e.key === 'l' || e.key === 'L') {
        openLyrics();
      } else if (e.key === 'q' || e.key === 'Q') {
        switchTab('queue');
      } else if (e.key === 'v' || e.key === 'V') {
        toggleVisualizerState();
      } else if (e.key === '/') {
        e.preventDefault();
        switchTab('search');
        const sInput = document.getElementById('searchInput');
        if (sInput) { sInput.focus(); sInput.select(); }
      } else if (e.key === 'Escape') {
        closeTutorialPopup();
        closeEqModal();
        closeVisualizerModal();
        closeTrackModal();
        closeLyricsModal();
        closeGuildModal();
        closeStatsModal();
        closeUserModal();
      }
    });

    window.addEventListener('resize', () => {
      const mini = document.getElementById('mobileMiniPlayer');
      if (window.innerWidth >= 860 && mini) {
        mini.classList.remove('visible');
      }
    });

    // Instant paint from local cache (0ms perceived startup)
    try {
      const cachedState = localStorage.getItem('jv_state_cache');
      if (cachedState) {
        applyState(JSON.parse(cachedState));
      }
    } catch (e) {
      console.error('State cache load failed:', e);
    }

    // Initialize visualizer engine
    initVisualizerStars();
    renderVisualizerPresetsList();
    updateVisualizerMasterBtnUI();
    const visCanvasEl = document.getElementById('ambientVisualizerCanvas');
    if (visCanvasEl && visEnabled) {
      visCanvasEl.classList.add('active');
      visCanvasEl.style.opacity = visOpacity;
    }
    visAnimFrame = requestAnimationFrame(renderVisualizerLoop);

    // Restore persistent user settings
    try {
      loadSettings();
      updateCoverBlur(visCoverBlur);
      updateCoverDim(visCoverDim);
      updateCoverBgToggle(visCoverBgEnabled);
      updateCoverPulseToggle(visCoverPulse);
      if (currentState && currentState.track && currentState.track.cover_url) {
        updateCoverArtBackground(currentState.track.cover_url);
      }
      const savedVol = localStorage.getItem('jv_live_volume');
      if (savedVol !== null) {
        const v = parseFloat(savedVol);
        if (!isNaN(v)) {
          const slider = document.getElementById('liveVolumeSlider');
          if (slider) slider.value = v;
          updateLiveVolume(v);
        }
      }
      const sbPrevVal = localStorage.getItem('jv_sb_preview');
      if (sbPrevVal !== null) {
        const sbToggle = document.getElementById('sbPreviewToggle');
        if (sbToggle) sbToggle.checked = (sbPrevVal === 'true');
      }
      const savedLock = localStorage.getItem('jv_lock_screen');
      if (savedLock === 'true' && !lockScreenControlsEnabled) {
        toggleLockScreenControls();
      }
    } catch (e) {}

    // Initialize JuiceVault account, playlists & favorites
    try {
      initJuiceVaultUser();
      loadJuiceVaultPlaylists();
    } catch (e) {
      console.warn('JuiceVault user/playlist init error:', e);
    }

    // Startup
    initTabTutorials();
    fetchTelemetry();
    if (!token) {
      document.getElementById('authBox').classList.add('active');
    } else {
      connectWS();
      fetchStatus();
    }

    // Auto-resume Listen Together stream if page was refreshed by alignment watchdog
    try {
      if (sessionStorage.getItem('jv_auto_resume_stream') === 'true') {
        sessionStorage.removeItem('jv_auto_resume_stream');
        setTimeout(() => {
          if (!liveStreamActive) {
            toggleLiveAudio();
            showToast('Live stream auto-resumed');
          }
        }, 600);
      }
    } catch (e) {}
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
