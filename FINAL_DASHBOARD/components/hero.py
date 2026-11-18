"""Landing hero: an original SVG drawing of a floodlit stadium (drawn in code, no photograph, no external URL).

The drawing is decorative. It carries no data, no team branding and no affiliation with any franchise."""
import streamlit as st

STADIUM_SVG = """
<svg viewBox="0 0 1200 300" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#050d1c"/><stop offset="1" stop-color="#0b2545"/>
    </linearGradient>
    <radialGradient id="glow"><stop offset="0" stop-color="#f7e7a1" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#f7e7a1" stop-opacity="0"/></radialGradient>
    <linearGradient id="stand" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1b3a63"/><stop offset="1" stop-color="#0a1a31"/></linearGradient>
  </defs>
  <rect width="1200" height="300" fill="url(#sky)"/>
  <g fill="#f5f0e1" opacity="0.7">
    <circle cx="110" cy="40" r="1.4"/><circle cx="260" cy="26" r="1"/><circle cx="420" cy="58" r="1.2"/>
    <circle cx="640" cy="22" r="1.1"/><circle cx="820" cy="48" r="1.4"/><circle cx="980" cy="30" r="1"/>
    <circle cx="1090" cy="70" r="1.2"/>
  </g>
  <g>
    <rect x="120" y="60" width="16" height="170" fill="#2b3f5c"/><rect x="1064" y="60" width="16" height="170" fill="#2b3f5c"/>
    <rect x="300" y="50" width="14" height="180" fill="#2b3f5c"/><rect x="886" y="50" width="14" height="180" fill="#2b3f5c"/>
    <g fill="#f7e7a1"><rect x="108" y="48" width="40" height="14"/><rect x="1052" y="48" width="40" height="14"/>
      <rect x="290" y="38" width="34" height="12"/><rect x="876" y="38" width="34" height="12"/></g>
    <circle cx="128" cy="55" r="70" fill="url(#glow)"/><circle cx="1072" cy="55" r="70" fill="url(#glow)"/>
    <circle cx="307" cy="45" r="55" fill="url(#glow)"/><circle cx="893" cy="45" r="55" fill="url(#glow)"/>
  </g>
  <g fill="none" stroke-linecap="round">
    <path d="M40 300 Q600 70 1160 300" stroke="#16325a" stroke-width="46"/>
    <path d="M40 300 Q600 70 1160 300" stroke="#2f5d8f" stroke-width="46" stroke-dasharray="2 7" opacity="0.55"/>
    <path d="M120 300 Q600 130 1080 300" stroke="#1f4a7a" stroke-width="30" stroke-dasharray="2 6" opacity="0.5"/>
    <path d="M200 300 Q600 180 1000 300" stroke="#2b5e91" stroke-width="18" stroke-dasharray="2 5" opacity="0.45"/>
  </g>
  <ellipse cx="600" cy="262" rx="330" ry="58" fill="#1e5a3a"/>
  <ellipse cx="600" cy="262" rx="330" ry="58" fill="none" stroke="#c9a227" stroke-width="2" opacity="0.6"/>
  <rect x="588" y="222" width="24" height="80" fill="#d9c98a" opacity="0.85"/>
</svg>
"""

CSS = """
.hero { position: relative; border-radius: 14px; overflow: hidden; margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px rgba(11,37,69,0.25); }
.hero svg { display: block; width: 100%; height: 280px; }
.hero-text { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center;
             padding: 0 2.4rem; background: linear-gradient(90deg, rgba(5,13,28,0.88) 0%, rgba(5,13,28,0.35) 70%); }
.hero-kicker { color: #c9a227; font-size: 0.85rem; letter-spacing: 0.18em; text-transform: uppercase; }
.hero-title { color: #f5f0e1; font-size: 2.3rem; font-weight: 600; margin: 0.2rem 0 0.4rem; line-height: 1.1; }
.hero-sub { color: #d7dde8; font-size: 1rem; max-width: 42rem; }
"""


def hero(title="IPL 2027 Auction Intelligence", kicker="SupeRR Selector Season 2",
         subtitle="Pressure analytics for batters and bowlers: what the evidence supports, and what it does not."):
    st.markdown(
        f'<div class="hero">{STADIUM_SVG}<div class="hero-text">'
        f'<div class="hero-kicker">{kicker}</div><div class="hero-title">{title}</div>'
        f'<div class="hero-sub">{subtitle}</div></div></div>', unsafe_allow_html=True)
