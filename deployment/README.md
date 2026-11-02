# Deployment Guide: Groww AI Discovery Engine

This application can be deployed to **Streamlit Community Cloud** or **Hugging Face Spaces**.

---

## 1. Streamlit Community Cloud (Recommended)

1. **Push Repository to GitHub:**
   Ensure `requirements.txt`, `.streamlit/config.toml`, `app/`, and `data/` (or seed scripts) are committed.

2. **Connect to Streamlit Cloud:**
   - Navigate to [share.streamlit.io](https://share.streamlit.io/).
   - Click **New app**.
   - Select your GitHub repository, branch `main`.
   - Set **Main file path** to: `app/streamlit_app.py`.

3. **Configure Environment Secrets (Optional):**
   In the Streamlit App Settings -> **Secrets**, paste:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   YOUTUBE_API_KEY = "your-youtube-api-key"
   REDDIT_CLIENT_ID = "your-reddit-client-id"
   REDDIT_CLIENT_SECRET = "your-reddit-client-secret"
   REDDIT_USER_AGENT = "GrowwSIPDiscoveryEngine/1.0"
   ```
   *(Note: The engine features built-in offline fallbacks and local heuristic extraction, so it runs smoothly even without API keys!)*

4. **Click Deploy:**
   Your public live URL will be active in ~2 minutes!

---

## 2. Hugging Face Spaces (Docker / Streamlit SDK)

1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces).
2. Select **Streamlit** as the Space SDK.
3. Push your repository to the Space remote.
4. Set the app file to `app/streamlit_app.py` in `README.md` frontmatter:
   ```yaml
   title: Groww SIP Discovery Engine
   emoji: 📈
   colorFrom: green
   colorTo: gray
   sdk: streamlit
   sdk_version: "1.35.0"
   app_file: app/streamlit_app.py
   pinned: false
   ```

---

## 3. Local Verification

To run the dashboard locally:
```bash
.venv\Scripts\streamlit run app/streamlit_app.py
```
Default local port: `http://localhost:8501/`

