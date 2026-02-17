"""
Reusable Streamlit UI components for the AI journaling app.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.time_helper import format_local_date_only, to_local_for_chart


# ---------------------------------------------------------------------------
# Global helpers
# ---------------------------------------------------------------------------


def load_css() -> None:
  """
  Load the Pinterest-inspired CSS and Google Fonts into the Streamlit app.
  """
  assets_dir = Path(__file__).resolve().parent

  css_path_candidates = [assets_dir / "style.css", assets_dir / "styles.css"]
  css_text: Optional[str] = None
  for path in css_path_candidates:
    if path.exists():
      css_text = path.read_text(encoding="utf-8")
      break

  if css_text:
    st.markdown("<style>" + css_text + "</style>", unsafe_allow_html=True)

  # Google Fonts
  st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Crimson+Text:wght@400;600&display=swap" rel="stylesheet">
    """,
    unsafe_allow_html=True,
  )


def get_emotion_emoji(emotion: str) -> str:
  """
  Map a dominant emotion label to a friendly emoji.
  """
  mapping = {
    "happy": "😊",
    "sad": "😢",
    "anxious": "😰",
    "calm": "😌",
    "angry": "😠",
    "neutral": "😐",
  }
  return mapping.get((emotion or "").lower(), "😐")


# ---------------------------------------------------------------------------
# HTML components
# ---------------------------------------------------------------------------


def render_mood_badge(emotion: str, color: str) -> str:
  """
  Create HTML for a small circular mood badge.
  """
  emoji = get_emotion_emoji(emotion)
  safe_emotion = escape(emotion or "").title() or "Neutral"

  html = f"""
  <span class="mood-badge mood-badge--{escape((emotion or '').lower())}" style="background: radial-gradient(circle at 30% 30%, #fff, {color});">
    <span class="mood-badge-dot"></span>
    <span>{emoji} {safe_emotion}</span>
  </span>
  """
  return html


def _emotion_class(emotion: Optional[str]) -> str:
  """
  Helper to build a CSS class suffix for emotion-based styling.
  """
  e = (emotion or "neutral").strip().lower()
  if e not in {"happy", "sad", "anxious", "calm", "angry", "neutral"}:
    e = "neutral"
  return e


EMOTION_COLORS = {
  "happy": "#FFE5E5",
  "sad": "#E5F3FF",
  "anxious": "#FFF5E5",
  "calm": "#E5FFE5",
  "angry": "#FFE5F0",
  "neutral": "#F5F5F5",
}


def render_journal_card(entry_data: Dict[str, Any]) -> str:
  """
  Render a single journal entry as a Pinterest-style HTML card.
  """
  entry_id = entry_data.get("id")
  date = entry_data.get("date")
  title = entry_data.get("title") or "Untitled entry"
  content = entry_data.get("content") or ""
  mood_score = entry_data.get("mood_score")
  emotion = entry_data.get("dominant_emotion") or "neutral"
  keywords_raw = entry_data.get("keywords") or []

  if isinstance(keywords_raw, str):
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
  else:
    keywords = [str(k).strip() for k in (keywords_raw or []) if str(k).strip()]

  # Date formatting
  # Date formatting - FIXED: Convert UTC to local time
  if isinstance(date, datetime):
      date_str = format_local_date_only(date)
  else:
      date_str = str(date) if date is not None else ""

  # Content preview
  preview = content.strip()
  if len(preview) > 150:
    preview = preview[:150].rstrip() + "..."

  # Mood score
  try:
    score_val = float(mood_score)
  except (TypeError, ValueError):
    score_val = 0.0

  emoji = get_emotion_emoji(emotion)
  emotion_class = _emotion_class(emotion)

  # Keywords as tags
  tags_html = "".join(
    f'<span style="display:inline-block;background:rgba(44,62,80,0.06);'
    f'border-radius:999px;padding:4px 12px;font-size:0.8rem;color:#2c3e50;'
    f'margin-right:8px;margin-bottom:6px;">{escape(tag)}</span>'
    for tag in keywords
  )

  # Mood score formatted
  score_str = f"+{score_val:.2f}" if score_val >= 0 else f"{score_val:.2f}"
  emotion_color = EMOTION_COLORS.get(emotion_class, "#F5F5F5")

  # Mood badge
  mood_badge_html = (
    f'<span style="display:inline-flex;align-items:center;gap:6px;'
    f'background:{emotion_color};border-radius:999px;padding:5px 12px;'
    f'font-size:0.85rem;font-weight:500;color:#2c3e50;">'
    f'{emoji} {(emotion or "neutral").title()}</span>'
  )

  card_html = (
    f'<div class="journal-card" style="position:relative;background:#fff;'
    f'border-radius:12px;box-shadow:0 8px 24px rgba(15,23,42,0.08);'
    f'padding:20px;margin-bottom:16px;border-left:4px solid {emotion_color};">'
    f'<div style="position:absolute;top:14px;right:16px;font-size:0.8rem;'
    f'color:rgba(44,62,80,0.6);">{escape(date_str)}</div>'
    f'<div class="journal-card-title" style="font-family:Playfair Display,serif;'
    f'font-size:1.15rem;margin-bottom:8px;padding-right:80px;">{escape(title)}</div>'
    f'<div class="journal-card-content" style="font-family:Crimson Text,Georgia,serif;'
    f'font-size:0.95rem;line-height:1.65;margin-bottom:12px;max-height:4.5em;'
    f'overflow:hidden;position:relative;">{escape(preview)}'
    f'<span style="position:absolute;bottom:0;left:0;right:0;height:1.5em;'
    f'background:linear-gradient(transparent,#fff);"></span></div>'
    f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">'
    f'{mood_badge_html}'
    f'<span style="font-size:0.9rem;font-weight:600;color:#22c55e;">{score_str}</span>'
    f'</div>'
    f'<div style="margin-top:8px;">{tags_html}</div>'
    f'</div>'
  )

  st.markdown(card_html, unsafe_allow_html=True)
  return card_html


def render_stats_card(title: str, value: str, color: str) -> str:
  """
  Render a Pinterest-style statistics card.
  """
  html = f"""
  <div style="
    background: linear-gradient(135deg,{color},rgba(255,255,255,0.9));
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 10px 30px rgba(15,23,42,0.18);
    text-align: left;
    color: #2c3e50;
    min-width: 180px;
  ">
    <div style="font-size:1.6rem;font-weight:700;margin-bottom:4px;">
      {escape(value)}
    </div>
    <div style="font-size:0.9rem;opacity:0.8;">
      {escape(title)}
    </div>
  </div>
  """
  st.markdown(html, unsafe_allow_html=True)
  return html


# ---------------------------------------------------------------------------
# Plotly components - FIXED FOR VISIBILITY
# ---------------------------------------------------------------------------


def render_emotion_timeline(mood_data: List[Dict[str, Any]]):
  """
  Build a Plotly line chart showing mood over time - ENHANCED VISIBILITY.
  
  FIXED: Thicker lines, larger markers, vibrant colors, taller chart.
  """
  if not mood_data:
    return go.Figure()  # empty figure

  # Normalize into lists
  dates = []
  scores = []
  emotions = []
  
  for item in mood_data:
    date_val = item.get("date")
    
    # Handle string dates
    if isinstance(date_val, str):
        try:
            date_val = datetime.fromisoformat(date_val)
        except ValueError:
            continue
    
    # FIXED: Convert UTC to local time for correct chart display
    if isinstance(date_val, datetime):
        date_val = to_local_for_chart(date_val)
    
    dates.append(date_val)
    scores.append(float(item.get("mood_score", 0.0)))
    emotions.append(str(item.get("emotion") or "neutral").lower())

  # VIBRANT color mapping - much more visible!
  emotion_colors = {
    "happy": "#FF6B9D",     # bright pink
    "sad": "#4A90E2",       # bright blue
    "anxious": "#F5A623",   # bright orange
    "calm": "#7ED321",      # bright green
    "angry": "#D0021B",     # bright red
    "neutral": "#9B9B9B"    # medium gray
  }
  
  # Get color for each point
  colors = [emotion_colors.get(e, "#9B9B9B") for e in emotions]
  
  # Create figure
  fig = go.Figure()
  
  # Add the main line with ENHANCED VISIBILITY
  fig.add_trace(go.Scatter(
    x=dates,
    y=scores,
    mode='lines+markers',
    name='Mood Timeline',
    line=dict(
      color='rgba(100, 100, 100, 0.4)',
      width=3  # THICKER line
    ),
    marker=dict(
      size=14,  # LARGER markers
      color=colors,
      line=dict(color='white', width=2),
      opacity=1.0  # FULLY OPAQUE
    ),
    hovertemplate='<b>%{x|%b %d, %Y}</b><br>' +
                  'Mood: %{y:.2f}<br>' +
                  '<extra></extra>',
  ))
  
  # Add reference line at y=0
  fig.add_hline(
    y=0, 
    line_dash="dot", 
    line_color="rgba(100,100,100,0.4)",
    annotation_text="Neutral",
    annotation_position="right"
  )
  
  # Update layout for BETTER VISIBILITY
  fig.update_layout(
    title={
      'text': 'Mood Over Time',
      'font': {'size': 18, 'family': 'Inter, sans-serif', 'color': '#2c3e50'}
    },
    xaxis_title='Date',
    yaxis_title='Mood Score',
    height=500,  # TALLER chart
    hovermode='x unified',
    template='plotly_white',
    yaxis=dict(
      range=[-1.1, 1.1],
      tickmode='linear',
      tick0=-1.0,
      dtick=0.25,
      gridcolor='rgba(200,200,200,0.3)',  # MORE VISIBLE grid
      gridwidth=1,
      zeroline=True,
      zerolinecolor='rgba(100,100,100,0.4)',
      zerolinewidth=2
    ),
    xaxis=dict(
      gridcolor='rgba(200,200,200,0.2)',
      showgrid=True
    ),
    font=dict(
      family='Inter, sans-serif',
      size=13,
      color='#2c3e50'
    ),
    plot_bgcolor='#FAFAFA',
    paper_bgcolor='white',
    margin=dict(l=60, r=40, t=80, b=60),
    showlegend=False
  )
  
  return fig