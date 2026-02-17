# ✨ AI-Powered Daily Journaling Assistant

> A beautiful, intelligent journaling app built **entirely using free AI tools** — from architecture to deployment.

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red?style=flat-square&logo=streamlit)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-green?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue?style=flat-square&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📖 Overview

**AI-Powered Daily Journaling Assistant** is a full-stack Python application that helps users reflect on their daily experiences through intelligent mood analysis and beautiful visualizations.

What makes this project unique:
- 🤖 **100% AI-assisted development** — every component was built using free AI tools
- 🔒 **Fully private** — all AI runs locally via Ollama (no data sent to external APIs)
- 🎨 **Pinterest-inspired UI** — soft pastels, card-based masonry layout
- 🧠 **Smart mood detection** — hybrid AI + rule-based emotion analysis
- 📊 **Rich analytics** — mood timelines, emotion distribution, keyword trends

---

## ✨ Features

### 📝 Journal Management
- Write and save journal entries with optional titles
- Beautiful card-based display with emotion-colored borders
- Full entry view with edit and delete functionality
- Word count tracking per entry

### 🧠 AI Mood Analysis
- Automatic emotion detection (happy, sad, anxious, calm, angry, neutral)
- Mood score from -1.0 (very negative) to +1.0 (very positive)
- Confidence scoring for each analysis
- Smart keyword extraction from entry content
- Hybrid system: Local LLM + rule-based fallback for reliability

### 📊 Analytics Dashboard
- Interactive mood timeline chart (last 90 days)
- Emotion distribution pie chart
- Monthly mood trend bar chart
- Most common keywords visualization
- Current journaling streak tracking
- 30-day average mood score

### 🎨 Pinterest-Inspired Design
- Soft pastel color palette
- Elegant card layout with hover animations
- Playfair Display serif typography
- Emotion-colored left borders on cards
- Responsive grid layout

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit | Web interface |
| Backend | Python 3.13 | Core logic |
| Database | SQLite + SQLAlchemy | Data storage |
| AI Model | Ollama (Llama 3.2) | Mood analysis |
| Charts | Plotly | Analytics visualization |
| Styling | Custom CSS | Pinterest aesthetic |

---

## 🤖 Built Entirely With Free AI Tools

This project was developed using **only free AI tools** — demonstrating modern AI-assisted development:

| Tool | Usage |
|------|-------|
| **Claude (Anthropic)** | Architecture design, backend logic, debugging |
| **Cursor AI** | Code generation, refactoring, file management |
| **Ollama + Llama 3.2** | Local mood analysis (free, private, offline) |
| **GitHub Copilot** | Code completion and suggestions |

> 💡 **Key insight:** This entire application — from database schema to UI components — was built through AI tool orchestration, demonstrating how modern developers can 10x their productivity using free AI tools.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.com/download) installed and running

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/ai-journal-app.git
cd ai-journal-app
```

**2. Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Download the AI model:**
```bash
ollama pull llama3.2:1b
```

**5. Run the app:**
```bash
streamlit run app.py
```

**6. Open in browser:**
```
http://localhost:8501
```

---

## 📁 Project Structure

```
ai-journal-app/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── assets/
│   ├── styles.css              # Pinterest-inspired CSS
│   └── ui_components.py        # Reusable UI components
│
├── components/                 # Additional UI components
│
├── database/
│   ├── models.py               # SQLAlchemy database models
│   └── db_setup.py             # Database initialization
│
└── utils/
    ├── mood_analyzer.py        # AI mood analysis engine
    ├── emotion_validator.py    # Permanent emotion correction layer
    ├── journal_manager.py      # Journal CRUD operations
    └── time_helper.py          # Timezone utilities
```

---

## 🗄️ Database Schema

```
JournalEntry          MoodAnalysis           ReflectionPrompt
─────────────         ────────────           ────────────────
id (PK)               id (PK)                id (PK)
date                  entry_id (FK)          prompt_text
title                 mood_score             category
content               dominant_emotion       is_active
word_count            confidence
created_at            keywords
updated_at            analyzed_at
```

---

## 🧠 How Mood Analysis Works

The app uses a **3-layer hybrid system** for reliable emotion detection:

```
Journal Entry
      ↓
┌─────────────────┐
│  Ollama LLM     │  → Fast local AI analysis
│  (Llama 3.2)    │
└─────────────────┘
      ↓
┌─────────────────┐
│  Rule-Based     │  → Instant fallback if AI is slow/fails
│  Fallback       │
└─────────────────┘
      ↓
┌─────────────────┐
│  Emotion        │  → Permanent validation & correction
│  Validator      │     • Sign consistency check
└─────────────────┘     • Text evidence cross-validation
      ↓                 • Keyword quality control
  Final Result
```

---

## 📸 Screenshots

### Home Dashboard
- Stats cards showing total entries, average mood, streak
- New entry form with character counter
- Recent entries in Pinterest-style card grid

### Analytics View
- Mood timeline with emotion-colored data points
- Emotion distribution donut chart
- Monthly average mood bar chart
- Top keywords frequency display

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# AI Model (faster = llama3.2:1b, smarter = llama3.2)
OLLAMA_MODEL_NAME = "llama3.2:1b"

# Database location
DATABASE_PATH = "./database/journal.db"

# App title
APP_TITLE = "My AI Journal"
```

---

## 🔒 Privacy

- ✅ All data stored **locally** on your machine
- ✅ AI runs **locally** via Ollama (no internet required)
- ✅ No data sent to external APIs
- ✅ Database file stays on your computer
- ✅ `.env` and `.db` files excluded from git

---

## 📦 Dependencies

```
streamlit==1.31.0
sqlalchemy==2.0.25
pandas==2.1.4
plotly==5.18.0
python-dotenv==1.0.0
requests==2.31.0
```

---

## 🗺️ Roadmap

- [ ] Export journal entries as PDF/Markdown
- [ ] Weekly mood summary email
- [ ] Voice-to-text journal entry
- [ ] Mobile PWA support
- [ ] Multi-language support
- [ ] Reflection prompts based on mood trends
- [ ] Dark mode theme
- [ ] Cloud sync (optional)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io) for the amazing web framework
- [Ollama](https://ollama.com) for free local AI inference
- [Plotly](https://plotly.com) for beautiful interactive charts
- [SQLAlchemy](https://sqlalchemy.org) for elegant database ORM
- **Anthropic Claude** for guiding the entire development process

---

## 👨‍💻 Author

Built with ❤️ and AI tools as a demonstration of modern AI-assisted development.

> *"I built a complete full-stack AI application using only free AI tools — from architecture to deployment."*

---

⭐ **If you found this project helpful, please give it a star!**
