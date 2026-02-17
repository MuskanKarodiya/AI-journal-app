"""
Main Streamlit app for the AI Journaling experience.
"""

from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.express as px
import streamlit as st

from assets.ui_components import (
    get_emotion_emoji,
    load_css,
    render_emotion_timeline,
    render_journal_card,
    render_stats_card,
)
from config import APP_TITLE
from utils.journal_manager import JournalManager


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
from database.db_setup import init_database

try:
    init_database()
except Exception as e:
    st.error(f"Database initialization failed: {e}")
    
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="✨",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "journal_manager" not in st.session_state:
    st.session_state.journal_manager = JournalManager()

if "current_view" not in st.session_state:
    st.session_state.current_view = "home"

if "selected_entry_id" not in st.session_state:
    st.session_state.selected_entry_id = None


jm: JournalManager = st.session_state.journal_manager


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def switch_view(view: str, entry_id: int | None = None) -> None:
    """Update the current view and optionally the selected entry, then rerun."""
    st.session_state.current_view = view
    st.session_state.selected_entry_id = entry_id
    # Support both older and newer Streamlit APIs
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def compute_streak(entries: List[Dict[str, Any]]) -> int:
    """
    Compute a simple "mood streak" in days based on positive or neutral mood.

    We treat mood_score >= 0 as a "non-negative" day and count consecutive days
    backwards from today until a negative day or a gap.
    """
    if not entries:
        return 0

    # Build a mapping date -> best mood_score for that day
    by_date: Dict[str, float] = {}
    for e in entries:
        date_val = e.get("date")
        if isinstance(date_val, datetime):
            d = date_val.date()
        else:
            try:
                d = datetime.fromisoformat(str(date_val)).date()
            except Exception:  # noqa: BLE001
                continue
        key = d.isoformat()
        score = float(e.get("mood_score") or 0.0)
        if key not in by_date or score > by_date[key]:
            by_date[key] = score

    streak = 0
    today = datetime.utcnow().date()

    while True:
        key = today.isoformat()
        if key not in by_date or by_date[key] < 0:
            break
        streak += 1
        today -= timedelta(days=1)

    return streak


def get_recent_mood_timeline(days: int = 60) -> List[Dict[str, Any]]:
    """Prepare mood timeline data - FIXED: Uses local time."""
    from utils.time_helper import to_local_for_chart
    
    entries = jm.get_all_entries(limit=500)
    
    # Use local time for cutoff comparison
    from datetime import timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    data: List[Dict[str, Any]] = []
    
    for e in entries:
        date_val = e.get("date")
        
        if not isinstance(date_val, datetime):
            try:
                date_val = datetime.fromisoformat(str(date_val))
            except Exception:
                continue
        
        # Make timezone aware for comparison
        if date_val.tzinfo is None:
            date_val = date_val.replace(tzinfo=timezone.utc)
        
        if date_val < cutoff:
            continue
        
        # Convert to local time for display
        local_date = to_local_for_chart(date_val)
        
        data.append({
            "date": local_date,  # LOCAL TIME for chart
            "mood_score": e.get("mood_score"),
            "emotion": e.get("dominant_emotion"),
        })
    
    return sorted(data, key=lambda x: x["date"])


def render_header() -> None:
    """Render the main page header with navigation."""
    with st.container():
        st.markdown(
            """
            <div style="text-align:center; margin-top: 0.5rem; margin-bottom: 1.5rem;">
              <h1 style="
                font-family: 'Playfair Display', serif;
                font-size: 2.4rem;
                margin-bottom: 0.3rem;
              ">
                ✨ My AI Journal
              </h1>
              <p style="
                font-family: 'Inter', sans-serif;
                font-size: 0.98rem;
                color: rgba(44,62,80,0.75);
                margin-bottom: 0.8rem;
              ">
                Your personal space for reflection and growth.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3, _ = st.columns([1, 1, 1, 3])
        with col1:
            if st.button("🏠 Home", use_container_width=True):
                switch_view("home")
        with col2:
            if st.button("✍️ New Entry", use_container_width=True):
                switch_view("new_entry")
        with col3:
            if st.button("📊 Analytics", use_container_width=True):
                switch_view("analytics")


def render_stats_section() -> None:
    """Show high-level mood statistics on the home view."""
    stats = jm.get_mood_statistics(days=30)
    entries = jm.get_all_entries(limit=500)

    avg = stats.get("average_mood_score")
    dom_dist = stats.get("emotion_distribution") or {}
    total_entries = stats.get("total_entries", 0)

    # Dominant emotion
    dominant_emotion = None
    if dom_dist:
        dominant_emotion = max(dom_dist.items(), key=lambda kv: kv[1])[0]

    avg_display = f"{avg:.2f}" if avg is not None else "–"
    avg_emoji = get_emotion_emoji(dominant_emotion if dominant_emotion else "neutral")

    streak = compute_streak(entries)

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        render_stats_card("Total entries", str(total_entries), "var(--color-secondary)")
    with col_b:
        render_stats_card("Average mood (30 days)", f"{avg_display} {avg_emoji}", "var(--color-primary)")
    with col_c:
        render_stats_card("Current streak (days)", str(streak), "var(--color-success)")
    with col_d:
        render_stats_card(
            "Dominant emotion",
            (dominant_emotion or "Not enough data").title(),
            "var(--color-accent)",
        )


def render_new_entry_section(show_title: bool = True) -> None:
    """Render the form for creating a new journal entry."""
    st.markdown("### ✍️ New entry")

    with st.form("new_entry_form", clear_on_submit=True):
        title = st.text_input("Title (optional)")
        content = st.text_area(
            "How are you feeling today?",
            height=220,
        )

        # Character count
        char_count = len(content or "")
        st.markdown(
            f"<div style='text-align:right;font-size:0.8rem;color:rgba(44,62,80,0.55);'>"
            f"{char_count} characters</div>",
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("Save & Analyze")

    if submitted:
        if not (content or "").strip():
            st.error("Please write something in your journal entry before saving.")
        else:
            with st.spinner("Analyzing your entry..."):
                result = jm.create_entry(content=content, title=title or None)

            if result["success"]:
                st.success("Entry saved and analyzed successfully.")
                mood = result["mood"] or {}
                
                # Show mood analysis nicely
                col1, col2, col3 = st.columns(3)
                with col1:
                    emotion = mood.get("dominant_emotion", "neutral")
                    emoji = get_emotion_emoji(emotion)
                    st.markdown(f"**Mood:** {emoji} {emotion.title()}")
                with col2:
                    score = mood.get("mood_score", 0)
                    st.markdown(f"**Score:** {score:.2f}")
                with col3:
                    confidence = mood.get("confidence", 0)
                    st.markdown(f"**Confidence:** {confidence:.0%}")
                
                keywords = mood.get("keywords", [])
                if keywords:
                    st.markdown(f"**Keywords:** {', '.join(keywords)}")
                
                # Force refresh to show new entry
                st.balloons()
                st.success("Refreshing to show your new entry...")
                if hasattr(st, "rerun"):
                    st.rerun()
                elif hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
            else:
                st.error(f"Something went wrong while saving your entry: {result.get('error', 'Unknown error')}")


def render_recent_entries_section() -> None:
    """Show recent entries as vertically stacked full-width cards."""
    st.markdown("### 📖 Recent Entries")

    # Get all entries
    all_entries = jm.get_all_entries(limit=20)
    
    # Debug: Show count
    st.caption(f"Found {len(all_entries)} entries in database")
    
    if not all_entries:
        st.info("✨ No entries yet. Start by writing your first reflection above!")
        return

    # Display entries in a nice grid
    for i in range(0, len(all_entries), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(all_entries):
                with col:
                    entry = all_entries[i + j]
                    render_journal_card(entry)
                    # Add view button
                    if st.button(f"Read More", key=f"view_{entry['id']}", use_container_width=True):
                        switch_view("view_entry", entry_id=entry["id"])


def render_analytics_view() -> None:
    """Render the analytics dashboard: timeline, distribution, trends."""
    st.markdown("### 📊 Mood analytics")

    # Timeline
    mood_timeline = get_recent_mood_timeline(days=90)
    if mood_timeline:
        fig_timeline = render_emotion_timeline(mood_timeline)
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("Not enough data to show a mood timeline yet. Write a few entries first.")

    # Emotion distribution + simple monthly trend
    stats = jm.get_mood_statistics(days=90)
    entries = jm.get_all_entries(limit=500)

    col1, col2 = st.columns(2)

    with col1:
        dist = stats.get("emotion_distribution") or {}
        if dist:
            df_dist = pd.DataFrame(
                [{"emotion": k.title(), "count": v} for k, v in dist.items()]
            )
            fig_pie = px.pie(
                df_dist,
                names="emotion",
                values="count",
                color="emotion",
                color_discrete_map={
                    "Happy": "#FFE5E5",
                    "Sad": "#E5F3FF",
                    "Anxious": "#FFF5E5",
                    "Calm": "#E5FFE5",
                    "Angry": "#FFE5F0",
                    "Neutral": "#F5F5F5",
                },
                hole=0.4,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(
                title_text="Emotion distribution (last 90 days)",
                showlegend=False,
                template="simple_white",
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No emotion distribution yet. Once you add entries, you'll see it here.")

    with col2:
        # Monthly mood trends: average mood per calendar month
        if entries:
            rows = []
            for e in entries:
                date_val = e.get("date")
                if not isinstance(date_val, datetime):
                    try:
                        date_val = datetime.fromisoformat(str(date_val))
                    except Exception:  # noqa: BLE001
                        continue
                mood_score = e.get("mood_score")
                try:
                    mood_score = float(mood_score)
                except (TypeError, ValueError):
                    continue
                rows.append(
                    {
                        "month": date_val.strftime("%Y-%m"),
                        "mood_score": mood_score,
                    }
                )
            if rows:
                df_month = pd.DataFrame(rows)
                df_grouped = df_month.groupby("month", as_index=False)["mood_score"].mean()
                fig_bar = px.bar(
                    df_grouped,
                    x="month",
                    y="mood_score",
                    title="Average mood by month",
                    labels={"month": "Month", "mood_score": "Average mood"},
                )
                fig_bar.update_layout(template="simple_white")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Not enough data to compute monthly trends yet.")

    # Simple keyword cloud proxy: top keywords list
    keyword_rows: List[str] = []
    for e in entries:
        kws = e.get("keywords") or []
        if isinstance(kws, str):
            kws = [k.strip() for k in kws.split(",") if k.strip()]
        for k in kws:
            keyword_rows.append(k.lower())

    if keyword_rows:
        freq: Dict[str, int] = {}
        for k in keyword_rows:
            freq[k] = freq.get(k, 0) + 1
        top_keywords = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:20]

        st.markdown("#### Most common keywords")
        tags_html = "".join(
            f'<span style="display:inline-block;background:rgba(44,62,80,0.04);'
            f'border-radius:999px;padding:6px 14px;font-size:0.8rem;'
            f'margin-right:8px;margin-bottom:6px;">{k} × {v}</span>'
            for k, v in top_keywords
        )
        st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)


def render_single_entry_view(entry_id: int) -> None:
    """Display a full entry with options to edit or delete."""
    entry = jm.get_entry_by_id(entry_id)
    if not entry:
        st.error("Entry not found.")
        if st.button("⬅️ Back to home"):
            switch_view("home")
        return

    st.markdown("### 📖 Entry details")

    st.markdown(
        f"**Title:** {entry['title'] or 'Untitled entry'}  \n"
        f"**Date:** {entry['date']}",
    )

    st.markdown("**Content**")
    st.markdown(
        f"<div class='journal-text' style='background:#ffffff;border-radius:12px;"
        f"padding:16px;border:1px solid rgba(44,62,80,0.06);'>"
        f"{entry['content'].replace(chr(10), '<br>')}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Mood**")
    st.json(
        {
            "mood_score": entry.get("mood_score"),
            "dominant_emotion": entry.get("dominant_emotion"),
            "confidence": entry.get("confidence"),
            "keywords": entry.get("keywords"),
        }
    )

    col_back, col_edit, col_delete = st.columns([1, 1, 1])
    with col_back:
        if st.button("⬅️ Back to home", use_container_width=True):
            switch_view("home")
    with col_edit:
        if st.button("✏️ Edit", use_container_width=True):
            # Simple inline edit form
            with st.form("edit_entry_form"):
                new_title = st.text_input("Title", value=entry["title"] or "")
                new_content = st.text_area("Content", value=entry["content"], height=220)
                submitted = st.form_submit_button("Save changes")
                if submitted:
                    success = jm.update_entry(
                        entry_id=entry_id,
                        content=new_content,
                        title=new_title or None,
                    )
                    if success:
                        st.success("Entry updated.")
                        switch_view("view_entry", entry_id=entry_id)
                    else:
                        st.error("Failed to update entry.")
    with col_delete:
        if st.button("🗑️ Delete", use_container_width=True):
            confirm = st.checkbox("Confirm delete?")
            if confirm:
                success = jm.delete_entry(entry_id)
                if success:
                    st.success("Entry deleted.")
                    switch_view("home")
                else:
                    st.error("Failed to delete entry.")


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

render_header()

view = st.session_state.current_view

if view == "home":
    render_stats_section()
    st.markdown("---")
    render_new_entry_section()
    st.markdown("---")
    render_recent_entries_section()
elif view == "new_entry":
    render_new_entry_section()
    st.markdown("---")
    render_recent_entries_section()
elif view == "analytics":
    render_analytics_view()
elif view == "view_entry":
    if st.session_state.selected_entry_id is not None:
        render_single_entry_view(st.session_state.selected_entry_id)
    else:
        st.info("No entry selected. Returning to home.")
        switch_view("home")
else:
    # Fallback
    render_stats_section()
    render_recent_entries_section()