from __future__ import annotations

import re
from html import escape
from urllib.parse import quote

import streamlit as st

from wiki_mystery_engine import (
    LINK_PATTERN,
    MAIN_ARTICLE,
    display_title,
    generate_article,
    get_article,
    list_articles,
    score_theory,
)


def main() -> None:
    st.set_page_config(
        page_title="Mizukawa Archive",
        page_icon="M",
        layout="wide",
    )
    render_styles()
    init_state()
    render_sidebar()

    if get_current_view() == "solve":
        render_solve_page()
    else:
        render_article_page()


def render_styles() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 1180px;
            padding-top: 1.4rem;
        }
        .wiki-title {
            border-bottom: 1px solid #a2a9b1;
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 2.4rem;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }
        .wiki-summary {
            color: #54595d;
            font-size: 0.98rem;
            margin-bottom: 1rem;
        }
        .wiki-body {
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 1.05rem;
            line-height: 1.65;
        }
        .wiki-body a {
            color: #0645ad;
            text-decoration: none;
        }
        .wiki-body a:hover {
            text-decoration: underline;
        }
        .infobox {
            border: 1px solid #a2a9b1;
            background: #f8f9fa;
            padding: 0.7rem;
            font-size: 0.9rem;
        }
        .infobox-title {
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.55rem;
        }
        .infobox-row {
            border-top: 1px solid #eaecf0;
            padding: 0.35rem 0;
        }
        .small-muted {
            color: #6b7280;
            font-size: 0.86rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "discovered_clues" not in st.session_state:
        st.session_state.discovered_clues = []
    if "last_generated" not in st.session_state:
        st.session_state.last_generated = None


def get_current_view() -> str:
    view = st.query_params.get("view", "article")
    if isinstance(view, list):
        return view[0] if view else "article"
    return view or "article"


def get_current_title() -> str:
    title = st.query_params.get("article", MAIN_ARTICLE)
    if isinstance(title, list):
        title = title[0] if title else MAIN_ARTICLE
    return display_title(title)


def go_to_article(title: str) -> None:
    st.query_params.clear()
    st.query_params["article"] = display_title(title)
    st.rerun()


def go_to_solve() -> None:
    st.query_params.clear()
    st.query_params["view"] = "solve"
    st.rerun()


def mark_discovered(article: dict) -> None:
    known = set(st.session_state.discovered_clues)
    for clue in article.get("clues", []):
        if clue and clue not in known:
            st.session_state.discovered_clues.append(clue)
            known.add(clue)


def load_or_generate_article(title: str) -> dict | None:
    article = get_article(title)
    if article:
        mark_discovered(article)
        return article

    with st.spinner(f"Generating archive entry for {display_title(title)}..."):
        try:
            article = generate_article(title, st.session_state.discovered_clues)
        except Exception as exc:  # noqa: BLE001 - show setup/API errors in the app.
            st.error(str(exc))
            return None

    st.session_state.last_generated = article["title"]
    mark_discovered(article)
    return article


def wiki_link_url(title: str) -> str:
    return f"?article={quote(display_title(title))}"


def render_link(match: re.Match[str]) -> str:
    raw = match.group(1)
    if "|" in raw:
        target, label = raw.split("|", 1)
    else:
        target = label = raw
    target = display_title(target)
    label = label.strip() or target
    return f'<a href="{wiki_link_url(target)}">{escape(label)}</a>'


def render_wiki_body(body: str) -> str:
    rendered = []
    cursor = 0
    for match in LINK_PATTERN.finditer(body or ""):
        rendered.append(escape(body[cursor : match.start()]))
        rendered.append(render_link(match))
        cursor = match.end()
    rendered.append(escape((body or "")[cursor:]))

    html_body = "".join(rendered)
    paragraphs = re.split(r"\n\s*\n", html_body)
    return "".join(
        f"<p>{paragraph.replace(chr(10), '<br>')}</p>"
        for paragraph in paragraphs
        if paragraph.strip()
    )


def render_sidebar() -> None:
    st.sidebar.title("Mizukawa Archive")

    lookup = st.sidebar.text_input("Search or open article", placeholder="Shirohane Clinic")
    if st.sidebar.button("Open article", use_container_width=True):
        if lookup.strip():
            go_to_article(lookup)

    st.sidebar.divider()
    if st.sidebar.button("Main article", use_container_width=True):
        go_to_article(MAIN_ARTICLE)
    if st.sidebar.button("Submit theory", use_container_width=True):
        go_to_solve()

    st.sidebar.divider()
    st.sidebar.subheader("Discovered clues")
    if st.session_state.discovered_clues:
        for clue in st.session_state.discovered_clues:
            st.sidebar.markdown(f"- {clue}")
    else:
        st.sidebar.markdown(
            '<p class="small-muted">Open articles to collect clues.</p>',
            unsafe_allow_html=True,
        )

    st.sidebar.divider()
    with st.sidebar.expander("Known pages"):
        for article in list_articles():
            st.markdown(f"[{article['title']}]({wiki_link_url(article['title'])})")


def render_infobox(article: dict) -> None:
    rows = article.get("infobox", {})
    if not rows:
        return

    html_rows = "".join(
        f"<div class='infobox-row'><strong>{escape(str(key))}</strong><br>{escape(str(value))}</div>"
        for key, value in rows.items()
    )
    st.markdown(
        f"""
        <div class="infobox">
            <div class="infobox-title">{escape(str(article["title"]))}</div>
            <div class="infobox-row"><strong>Type</strong><br>{escape(str(article.get("type", "document")))}</div>
            {html_rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_article_page() -> None:
    title = get_current_title()
    article = load_or_generate_article(title)
    if not article:
        st.button("Back to main article", on_click=go_to_article, args=(MAIN_ARTICLE,))
        return

    if st.session_state.last_generated == article["title"]:
        st.success(f"Generated and saved {article['title']}.")
        st.session_state.last_generated = None

    top_left, top_right = st.columns([1, 1])
    with top_left:
        if article["title"] != MAIN_ARTICLE:
            st.button("Back to main article", on_click=go_to_article, args=(MAIN_ARTICLE,))
    with top_right:
        st.button("Submit theory", on_click=go_to_solve)

    main_col, info_col = st.columns([3.2, 1], gap="large")
    with main_col:
        st.markdown(
            f'<div class="wiki-title">{escape(str(article["title"]))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="wiki-summary">{escape(str(article["summary"]))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="wiki-body">{render_wiki_body(article["body"])}</div>',
            unsafe_allow_html=True,
        )

        links = article.get("links", [])
        if links:
            st.markdown("#### Related pages")
            st.markdown(" | ".join(f"[{link}]({wiki_link_url(link)})" for link in links))

    with info_col:
        render_infobox(article)


def render_solve_page() -> None:
    st.markdown('<div class="wiki-title">Submit Theory</div>', unsafe_allow_html=True)
    st.write(
        "Explain what you think happened to Emi Kuroda. The evaluator compares your theory "
        "against the hidden canon and gives spoiler-light feedback unless you ask for the answer."
    )

    theory = st.text_area("Your theory", height=220, placeholder="I think Emi discovered...")
    reveal_answer = st.checkbox("Reveal answer after scoring")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        submitted = st.button("Score theory", type="primary")
    with col_b:
        st.button("Back to archive", on_click=go_to_article, args=(MAIN_ARTICLE,))

    if not submitted:
        return

    if not theory.strip():
        st.warning("Write a theory first.")
        return

    with st.spinner("Comparing theory with the hidden canon..."):
        try:
            result = score_theory(theory, st.session_state.discovered_clues, reveal_answer)
        except Exception as exc:  # noqa: BLE001 - show setup/API errors in the app.
            st.error(str(exc))
            return

    st.metric("Accuracy", f"{result['accuracy_percentage']}%")
    st.subheader("What you got right")
    for item in result["got_right"] or ["No major matches yet."]:
        st.markdown(f"- {item}")

    st.subheader("What you missed")
    for item in result["missed"] or ["No major misses listed."]:
        st.markdown(f"- {item}")

    if result["feedback"]:
        st.subheader("Feedback")
        st.write(result["feedback"])

    if reveal_answer and result["answer"]:
        st.subheader("Answer")
        st.write(result["answer"])
