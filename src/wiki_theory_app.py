from __future__ import annotations

import difflib
import random
import re
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from wiki_mystery_engine import (
    LINK_PATTERN,
    MAIN_ARTICLE,
    add_to_watchlist,
    article_exists,
    display_title,
    generate_article,
    get_contribution_target,
    get_contribution_targets,
    get_article,
    get_watchlist,
    is_generated_article,
    is_seed_article,
    is_watched,
    list_articles,
    mark_watched_viewed,
    remove_from_watchlist,
    review_contribution,
    timestamp_label,
)


BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "wiki_theory.css"

TAB_LABELS = {
    "article": "Article",
    "discussion": "Discussion",
    "source": "View source",
    "history": "History",
}


def main() -> None:
    st.set_page_config(
        page_title="WikiTheory",
        page_icon="W",
        layout="wide",
    )
    load_styles()
    init_state()
    render_sidebar()
    render_header()

    view = get_param("view", "article")
    if view == "contribute":
        render_contribution_page()
    elif view == "inbox":
        render_inbox_page()
    elif view == "profile":
        render_profile_page()
    elif view == "watchlist":
        render_watchlist_page()
    elif view == "category":
        render_category_page(get_param("category", "Mizukawa Town"))
    elif view == "placeholder":
        render_placeholder_page(get_param("page", "Recent changes"))
    else:
        render_article_page()


def load_styles() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def init_state() -> None:
    if "discovered_clues" not in st.session_state:
        st.session_state.discovered_clues = []
    if "last_generated" not in st.session_state:
        st.session_state.last_generated = None
    if "contributor_profile" not in st.session_state:
        st.session_state.contributor_profile = {
            "name": "GuestEditor",
            "prestige": 0,
            "approvedEdits": 0,
            "rejectedEdits": 0,
            "pendingEdits": 0,
            "submittedEdits": 0,
            "unlockedMysteries": ["Mizukawa case index"],
        }
    if "inbox_messages" not in st.session_state:
        st.session_state.inbox_messages = [
            {
                "from": "WikiTheory Review Board",
                "subject": "Welcome to WikiTheory",
                "body": (
                    "Your contributor account is ready. Incomplete article sections are open "
                    "for public review."
                ),
            }
        ]
    if "contribution_statuses" not in st.session_state:
        st.session_state.contribution_statuses = {}
    if "review_threads" not in st.session_state:
        st.session_state.review_threads = {}
    if "approved_patches" not in st.session_state:
        st.session_state.approved_patches = {}
    if "recently_viewed_articles" not in st.session_state:
        st.session_state.recently_viewed_articles = []
    if "contribution_updated_at" not in st.session_state:
        st.session_state.contribution_updated_at = {}


def get_param(name: str, default: str) -> str:
    value = st.query_params.get(name, default)
    if isinstance(value, list):
        return value[0] if value else default
    return value or default


def get_current_title() -> str:
    return display_title(get_param("article", MAIN_ARTICLE))


def get_current_tab() -> str:
    tab = get_param("tab", "article")
    return tab if tab in TAB_LABELS else "article"


def go_to_article(title: str, tab: str = "article") -> None:
    st.query_params.clear()
    st.query_params["article"] = display_title(title)
    st.query_params["tab"] = tab
    st.rerun()


def go_to_contribute() -> None:
    st.query_params.clear()
    st.query_params["view"] = "contribute"
    st.rerun()


def article_url(title: str, tab: str = "article") -> str:
    return f"?article={quote(display_title(title))}&tab={quote(tab)}"


def category_url(category: str) -> str:
    return f"?view=category&category={quote(category)}"


def placeholder_url(page: str) -> str:
    return f"?view=placeholder&page={quote(page)}"


def render_header() -> None:
    st.markdown(
        """
        <div class="WikiHeader">
            <div class="WikiHeader-brand">
                <span class="WikiHeader-symbol">W</span>
                <span class="WikiHeader-name">WikiTheory</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("WikiHeaderSearch"):
        search_col, button_col = st.columns([5, 1])
        query = search_col.text_input(
            "Search WikiTheory",
            placeholder="Search or open an article title",
            label_visibility="collapsed",
        )
        submitted = button_col.form_submit_button("Search", use_container_width=True)

    if submitted and query.strip():
        go_to_article(query)


def render_sidebar() -> None:
    st.sidebar.markdown(
        """
        <div class="WikiSidebar-brand">
            <div class="WikiSidebar-name">WikiTheory</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f"""
        <div class="WikiSidebar-list">
            <p><a href="{article_url(MAIN_ARTICLE)}">Main page</a></p>
            <p><a href="{placeholder_url("Recent changes")}">Recent changes</a></p>
            <p><a href="{placeholder_url("Mystery index")}">Mystery index</a></p>
            <p><a href="{placeholder_url("People")}">People</a></p>
            <p><a href="{placeholder_url("Places")}">Places</a></p>
            <p><a href="{placeholder_url("Organizations")}">Organizations</a></p>
            <p><a href="{placeholder_url("Documents")}">Documents</a></p>
            <p><a href="?view=contribute">Contribute an Article</a></p>
            <p><a href="?view=inbox">Inbox</a></p>
            <p><a href="?view=profile">Contributor profile</a></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Random article", use_container_width=True):
        go_to_article(random.choice(list_articles())["title"])

    render_sidebar_watchlist()

    st.sidebar.divider()
    with st.sidebar.expander("Known pages"):
        for article in list_articles():
            st.markdown(f"[{article['title']}]({article_url(article['title'])})")


def render_sidebar_watchlist() -> None:
    st.sidebar.divider()
    st.sidebar.subheader("Watchlist")
    watched_pages = get_watchlist()
    if watched_pages:
        for item in watched_pages[:8]:
            st.sidebar.markdown(f"- [{item['title']}]({article_url(item['title'])})")
    else:
        st.sidebar.markdown(
            '<div class="WikiSidebar-small">No watched pages yet.</div>',
            unsafe_allow_html=True,
        )
    st.sidebar.markdown("[View full watchlist](?view=watchlist)")


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


def render_article_page() -> None:
    title = get_current_title()
    tab = get_current_tab()
    render_tabs(title, tab)

    if tab != "article":
        render_tab_placeholder(title, tab)
        return

    article = load_or_generate_article(title)
    if not article:
        st.button("Back to main article", on_click=go_to_article, args=(MAIN_ARTICLE,))
        return

    if st.session_state.last_generated == article["title"]:
        st.success(f"Generated and saved {article['title']}.")
        st.session_state.last_generated = None
    record_article_view(article["title"])

    main_col, info_col = st.columns([3.25, 1.05], gap="large")
    with main_col:
        render_article(article)
    with info_col:
        render_infobox(article)


def render_tabs(title: str, active_tab: str) -> None:
    links = []
    for tab, label in TAB_LABELS.items():
        active = " is-active" if tab == active_tab else ""
        links.append(f'<a class="{active.strip()}" href="{article_url(title, tab)}">{label}</a>')
    st.markdown(f'<div class="WikiTabs">{"".join(links)}</div>', unsafe_allow_html=True)


def render_tab_placeholder(title: str, tab: str) -> None:
    st.markdown('<div class="WikiLayout">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="WikiArticle-title">{escape(display_title(title))}: {escape(TAB_LABELS[tab])}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="WikiNotice">
            This WikiTheory prototype only implements the Article tab. Discussion,
            source, and history pages are preserved as archive affordances.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_article(article: dict) -> None:
    lead_paragraphs = article_lead_paragraphs(article)
    sections = article_sections(article)
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="WikiArticle-title">{escape(str(article["title"]))}</h1>',
        unsafe_allow_html=True,
    )
    render_watch_action(article["title"])
    st.markdown(
        f'<div class="WikiArticle-summary">{escape(str(article["summary"]))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="WikiArticle-body WikiArticle-lead">{render_wiki_paragraphs(lead_paragraphs)}</div>',
        unsafe_allow_html=True,
    )
    render_toc(sections, bool(article.get("references")), bool(article.get("externalLinks")))

    for section in sections:
        heading = str(section.get("heading", "Section"))
        anchor = slugify(heading)
        st.markdown(
            f'<h2 id="{anchor}" class="WikiArticle-sectionTitle">{escape(heading)}</h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="WikiArticle-body">{render_wiki_paragraphs(section.get("paragraphs", []))}</div>',
            unsafe_allow_html=True,
        )

    render_approved_contributions(article["title"])
    render_pending_sections(article)
    render_references(article)
    render_external_links(article)
    render_categories(article)
    st.markdown("</div>", unsafe_allow_html=True)


def render_watch_action(title: str) -> None:
    watched = is_watched(title)
    label = "Remove from watchlist" if watched else "Watch this page"
    if st.button(label, key=f"watch_{normalize_key(title)}"):
        if watched:
            remove_from_watchlist(title)
            st.toast(f"Removed {title} from watchlist.")
        else:
            add_to_watchlist(title)
            st.toast(f"Added {title} to watchlist.")
        st.rerun()


def record_article_view(title: str) -> None:
    viewed = [item for item in st.session_state.recently_viewed_articles if item != title]
    viewed.insert(0, title)
    st.session_state.recently_viewed_articles = viewed[:10]
    mark_watched_viewed(title)


def render_approved_contributions(article_title: str) -> None:
    patches = [
        patch
        for patch in st.session_state.approved_patches.values()
        if patch.get("articleTitle") == article_title
    ]
    for patch in patches:
        heading = patch.get("sectionTitle", "Contributor revision")
        st.markdown(
            f'<h2 id="{slugify(heading)}" class="WikiArticle-sectionTitle">{escape(heading)}</h2>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="WikiMeta">Approved contributor revision by {escape(st.session_state.contributor_profile["name"])}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="WikiArticle-body">{render_wiki_text(patch.get("text", ""))}</div>',
            unsafe_allow_html=True,
        )


def render_pending_sections(article: dict) -> None:
    sections = [
        section
        for section in article.get("incompleteSections", [])
        if contribution_status(section.get("id", "")) != "Approved"
    ]
    if not sections:
        return

    items = "".join(
        f'<li><a href="{contribution_url(section["id"])}">{escape(section["kind"])}: '
        f'{escape(section["title"])}</a> '
        f'<span class="WikiMeta">({escape(contribution_status(section["id"]))})</span></li>'
        for section in sections
    )
    st.markdown(
        f"""
        <div class="WikiNotice">
            <strong>Pending Review:</strong>
            <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def article_lead_paragraphs(article: dict) -> list[str]:
    lead = article.get("leadParagraphs", [])
    if isinstance(lead, list):
        paragraphs = [str(paragraph).strip() for paragraph in lead if str(paragraph).strip()]
        if paragraphs:
            return paragraphs

    paragraphs = split_paragraphs(article.get("body", ""))
    return paragraphs[:2] if paragraphs else [str(article.get("summary", ""))]


def article_sections(article: dict) -> list[dict]:
    raw_sections = article.get("sections", [])
    sections: list[dict] = []
    if isinstance(raw_sections, list):
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            heading = str(section.get("heading") or section.get("title") or "").strip()
            paragraphs = section.get("paragraphs", [])
            if isinstance(paragraphs, str):
                paragraphs = split_paragraphs(paragraphs)
            if not isinstance(paragraphs, list):
                paragraphs = []
            clean_paragraphs = [
                str(paragraph).strip()
                for paragraph in paragraphs
                if str(paragraph).strip()
            ]
            if heading and clean_paragraphs:
                sections.append({"heading": heading, "paragraphs": clean_paragraphs})

    if sections:
        return sections

    paragraphs = split_paragraphs(article.get("body", ""))
    fallback_body = paragraphs[1:] or [article.get("summary", "")]
    headings = fallback_section_headings(article.get("articleType") or article.get("type"))
    for index, paragraph in enumerate(fallback_body):
        sections.append(
            {
                "heading": headings[min(index, len(headings) - 1)],
                "paragraphs": [paragraph],
            }
        )
    return sections


def fallback_section_headings(article_type: str | None) -> list[str]:
    templates = {
        "case": ["Disappearance", "Missing person", "Initial search", "Investigation", "Later developments"],
        "person": ["Early life", "Disappearance", "Last known movements", "Later references"],
        "place": ["Geography", "History", "Local institutions", "Public records"],
        "organization": ["Establishment", "Services", "Records and ownership", "Connection to later inquiries"],
        "document": ["Contents", "Publication history", "Revisions", "Archive status"],
        "record": ["Contents", "Custody", "Referenced properties", "Archive status"],
        "investigation": ["Scope", "Timeline", "Documentary record", "Competing interpretations"],
        "timeline": ["Chronology", "Reported movements", "Documented gaps", "Later reconstruction"],
        "theory": ["Summary", "Support cited by contributors", "Objections", "Related pages"],
    }
    return templates.get(str(article_type or "document"), templates["document"])


def split_paragraphs(body: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body or "") if paragraph.strip()]


def render_toc(sections: list[dict], has_references: bool = True, has_external_links: bool = False) -> None:
    items = "".join(
        f'<li><a href="#{slugify(str(section.get("heading", "Section")))}">{escape(str(section.get("heading", "Section")))}</a></li>'
        for section in sections
    )
    if has_references:
        items += '<li><a href="#references">References</a></li>'
    if has_external_links:
        items += '<li><a href="#external-links">External links</a></li>'
    st.markdown(
        f"""
        <div class="WikiTableOfContents">
            <div class="WikiTableOfContents-title">Contents</div>
            <ol>{items}</ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_infobox(article: dict) -> None:
    infobox = article.get("infobox", {})
    if not isinstance(infobox, dict):
        infobox = {}
    fields = infobox.get("fields", [])
    if not isinstance(fields, list):
        fields = []
    html_rows = "".join(
        """
        <div class="WikiInfobox-row">
            <div class="WikiInfobox-key">{key}</div>
            <div class="WikiInfobox-value">{value}</div>
        </div>
        """.format(
            key=escape(str(field.get("label", ""))),
            value=render_wiki_inline(str(field.get("value", ""))),
        )
        for field in fields
        if isinstance(field, dict) and str(field.get("label", "")).strip() and str(field.get("value", "")).strip()
    )
    caption = str(infobox.get("imageCaption") or "").strip()
    caption_html = (
        f'<div class="WikiInfobox-caption">{render_wiki_inline(caption)}</div>'
        if caption
        else ""
    )
    st.markdown(
        f"""
        <div class="WikiInfobox">
            <div class="WikiInfobox-title">{escape(str(infobox.get("title") or article["title"]))}</div>
            {caption_html}
            {html_rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_references(article: dict) -> None:
    references = article.get("references", [])
    if not references:
        return
    items = "".join(f"<li>{render_wiki_inline(str(ref))}</li>" for ref in references)
    st.markdown(
        f"""
        <div id="references" class="WikiReferences">
            <h2>References</h2>
            <ol>{items}</ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_external_links(article: dict) -> None:
    external_links = article.get("externalLinks", [])
    if not external_links:
        return
    items = "".join(f"<li>{render_wiki_inline(str(link))}</li>" for link in external_links)
    st.markdown(
        f"""
        <div id="external-links" class="WikiReferences WikiExternalLinks">
            <h2>External links</h2>
            <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_categories(article: dict) -> None:
    categories = article.get("categories", [])
    links = "".join(
        f'<span class="WikiCategory-pill"><a href="{category_url(str(category))}">{escape(str(category))}</a></span>'
        for category in categories
    )
    st.markdown(
        f"""
        <div class="WikiCategories">
            <strong>Categories:</strong> {links}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_wiki_text(text: str) -> str:
    return render_wiki_paragraphs(split_paragraphs(text))


def render_wiki_paragraphs(paragraphs: list[str]) -> str:
    return "".join(
        f"<p>{render_wiki_inline(str(paragraph)).replace(chr(10), '<br>')}</p>"
        for paragraph in paragraphs
        if str(paragraph).strip()
    )


def render_wiki_inline(text: str) -> str:
    rendered = []
    cursor = 0
    for match in LINK_PATTERN.finditer(text or ""):
        rendered.append(escape(text[cursor : match.start()]))
        rendered.append(render_link(match))
        cursor = match.end()
    rendered.append(escape((text or "")[cursor:]))
    return "".join(rendered)


def render_link(match: re.Match[str]) -> str:
    raw = match.group(1)
    if "|" in raw:
        target, label = raw.split("|", 1)
    else:
        target = label = raw
    target = display_title(target)
    label = label.strip() or target
    link_class = wiki_link_class(target)
    return (
        f'<a class="WikiLink {link_class}" href="{article_url(target)}" '
        f'title="{escape(link_title(target))}">{escape(label)}</a>'
    )


def wiki_link_class(title: str) -> str:
    if is_seed_article(title):
        return "WikiLink-existing"
    if is_generated_article(title):
        return "WikiLink-generated"
    if article_exists(title):
        return "WikiLink-existing"
    return "WikiLink-missing"


def link_title(title: str) -> str:
    if article_exists(title):
        return f"Open {display_title(title)}"
    return f"Generate article for {display_title(title)}"


def contribution_url(target_id: str) -> str:
    return f"?view=contribute&target={quote(target_id)}"


def render_contribution_page() -> None:
    target_id = get_param("target", "")
    if target_id:
        render_contribution_editor(target_id)
    else:
        render_contribution_index()


def render_contribution_index() -> None:
    targets = get_contribution_targets()
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown('<h1 class="WikiArticle-title">Contribute an Article</h1>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="WikiNotice">
            <strong>Pages requiring review or expansion.</strong>
            Only selected protected sections are open for public revision in this prototype.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_contribution_target_table(targets)
    st.markdown("</div>", unsafe_allow_html=True)


def render_contribution_target_table(targets: list[dict]) -> None:
    contribution_targets = []
    for target in targets:
        status = contribution_status(target["id"])
        contribution_targets.append(
            {
                "Page": route_with_label(
                    article_url(target["articleTitle"]),
                    str(target["articleTitle"]),
                ),
                "Section": route_with_label(
                    contribution_url(target["id"]),
                    str(target["sectionTitle"]),
                ),
                "Issue": str(target["kind"]),
                "Status": status,
                "Last updated": contribution_last_updated(target["id"]),
            }
        )

    st.dataframe(
        contribution_targets,
        column_config={
            "Page": st.column_config.LinkColumn(
                "Page",
                display_text=r"#(.*)$",
                width="medium",
            ),
            "Section": st.column_config.LinkColumn(
                "Section",
                display_text=r"#(.*)$",
                width="medium",
            ),
            "Issue": st.column_config.TextColumn("Issue", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Last updated": st.column_config.TextColumn("Last updated", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        height=230,
    )


def route_with_label(url: str, label: str) -> str:
    return f"{url}#{label}"


def contribution_status(target_id: str) -> str:
    return st.session_state.contribution_statuses.get(target_id, "Open")


def contribution_last_updated(target_id: str) -> str:
    return st.session_state.contribution_updated_at.get(target_id, "Not recorded")


def related_pages_read_count(target: dict) -> tuple[int, int]:
    related_pages = suggested_related_pages(target)
    read_pages = set(st.session_state.recently_viewed_articles)
    read_pages.update(item["title"] for item in get_watchlist())
    return sum(1 for page in related_pages if page in read_pages), max(1, len(related_pages))


def suggested_related_pages(target: dict) -> list[str]:
    pages = [target["articleTitle"]]
    article = get_article(target["articleTitle"])
    if article:
        pages.extend(article.get("links", [])[:6])
    return dedupe_page_titles(pages)


def related_pages_for_editor(target: dict, article: dict | None) -> list[str]:
    pages: list[str] = []
    pages.extend(item["title"] for item in get_watchlist())
    pages.extend(st.session_state.recently_viewed_articles)
    if article:
        pages.append(article["title"])
        pages.extend(article.get("links", [])[:8])
    else:
        pages.append(target["articleTitle"])
    return dedupe_page_titles(pages)[:12]


def related_context_summaries(article: dict | None) -> list[dict[str, str]]:
    if not article:
        return []

    titles = dedupe_page_titles(
        [article["title"], *article.get("links", [])[:6], *st.session_state.recently_viewed_articles[:4]]
    )
    summaries: list[dict[str, str]] = []
    for title in titles[:8]:
        related = get_article(title)
        if related:
            summaries.append(
                {
                    "title": related["title"],
                    "summary": related.get("summary", ""),
                    "type": related.get("type", "document"),
                }
            )
    return summaries


def dedupe_page_titles(titles: list[str]) -> list[str]:
    seen: set[str] = set()
    pages: list[str] = []
    for title in titles:
        clean_title = display_title(title)
        key = clean_title.lower()
        if key not in seen:
            seen.add(key)
            pages.append(clean_title)
    return pages


def render_contribution_editor(target_id: str) -> None:
    target = get_contribution_target(target_id)
    if not target:
        render_index_page(
            "Contribution not found",
            [],
            "The requested contribution target is not available in the current archive.",
        )
        return

    article = get_article(target["articleTitle"])
    excerpt = article_excerpt(article)
    public_target = {key: value for key, value in target.items() if key != "canonAnswer"}

    render_contribution_edit_tabs(target)
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="WikiArticle-title">Editing section: {escape(target["sectionTitle"])}</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="WikiNotice">
            You are editing a protected section. Changes to this section require editorial review before publication.
            Only selected protected sections are open for public revision in this prototype.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_edit_section_metadata(target)

    st.markdown('<h2 class="WikiArticle-sectionTitle">Current section text</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="WikiSourceBox">{render_wiki_text(excerpt)}</div>', unsafe_allow_html=True)

    render_related_pages_panel(public_target, article)

    with st.form(f"ContributionForm_{target_id}"):
        st.markdown(
            """
            <div class="WikiEditorLabel">Proposed revision</div>
            <div class="WikiMeta">Write in a neutral encyclopedia style. Avoid unsupported claims.</div>
            """,
            unsafe_allow_html=True,
        )
        contribution_text = st.text_area(
            "Proposed revision",
            height=220,
            label_visibility="collapsed",
            placeholder=(
                "Write the proposed section text here. Use neutral wording and cite related pages where useful."
            ),
        )
        edit_summary = st.text_input(
            "Edit summary",
            placeholder="Briefly describe the reason for this revision",
        )
        preview_col, diff_col, submit_col = st.columns([1, 1, 1.6])
        preview_requested = preview_col.form_submit_button("Show preview")
        diff_requested = diff_col.form_submit_button("Show changes")
        submitted = submit_col.form_submit_button("Submit changes for review")

    if preview_requested:
        render_revision_preview(contribution_text)
    elif diff_requested:
        render_revision_diff(excerpt, contribution_text)
    elif submitted:
        if not contribution_text.strip():
            st.warning("Add proposed revision text before submitting changes for review.")
        else:
            submitted_at = timestamp_label()
            with st.spinner("Posting revision to editorial review..."):
                try:
                    review = review_contribution(
                        target_id,
                        contribution_text,
                        st.session_state.discovered_clues,
                        st.session_state.recently_viewed_articles,
                        [item["title"] for item in get_watchlist()],
                        related_context_summaries(article),
                        excerpt,
                        edit_summary,
                    )
                except Exception as exc:  # noqa: BLE001 - show setup/API errors in the app.
                    st.error(str(exc))
                else:
                    apply_contribution_review(
                        target,
                        contribution_text,
                        review,
                        edit_summary,
                        submitted_at,
                    )
                    render_review_summary(target, review, submitted_at)

    render_editorial_discussion(target_id)
    st.markdown("</div>", unsafe_allow_html=True)


def render_contribution_edit_tabs(target: dict) -> None:
    article_title = target["articleTitle"]
    tabs = [
        ("Article", article_url(article_title, "article")),
        ("Discussion", article_url(article_title, "discussion")),
        ("Edit", contribution_url(target["id"])),
        ("View history", article_url(article_title, "history")),
    ]
    links = []
    for label, href in tabs:
        active = " is-active" if label == "Edit" else ""
        links.append(f'<a class="{active.strip()}" href="{href}">{escape(label)}</a>')
    st.markdown(f'<div class="WikiTabs WikiEditTabs">{"".join(links)}</div>', unsafe_allow_html=True)


def render_edit_section_metadata(target: dict) -> None:
    st.markdown(
        f"""
        <div class="WikiEditPanel WikiEditMetadata">
            <div><strong>Article:</strong> <a href="{article_url(target["articleTitle"])}">{escape(target["articleTitle"])}</a></div>
            <div><strong>Section:</strong> {escape(target["sectionTitle"])}</div>
            <div><strong>Issue:</strong> {escape(section_issue_label(target))}</div>
            <div><strong>Status:</strong> {escape(contribution_status(target["id"]))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_issue_label(target: dict) -> str:
    kind = str(target.get("kind") or "Requires review")
    if "missing" in kind.lower():
        return "Incomplete"
    if "disputed" in kind.lower():
        return "Disputed"
    return "Requires review"


def render_revision_preview(contribution_text: str) -> None:
    st.markdown('<h2 class="WikiArticle-sectionTitle">Preview</h2>', unsafe_allow_html=True)
    if not contribution_text.strip():
        st.markdown('<div class="WikiNotice">No proposed revision text to preview.</div>', unsafe_allow_html=True)
        return
    st.markdown(f'<div class="WikiSourceBox">{render_wiki_text(contribution_text)}</div>', unsafe_allow_html=True)


def render_revision_diff(current_text: str, proposed_text: str) -> None:
    st.markdown('<h2 class="WikiArticle-sectionTitle">Changes</h2>', unsafe_allow_html=True)
    if not proposed_text.strip():
        st.markdown('<div class="WikiNotice">No proposed revision text to compare.</div>', unsafe_allow_html=True)
        return
    diff = difflib.unified_diff(
        current_text.splitlines(),
        proposed_text.splitlines(),
        fromfile="Current section text",
        tofile="Proposed revision",
        lineterm="",
    )
    diff_text = "\n".join(diff) or "No textual changes detected."
    st.markdown(
        f'<div class="WikiDiffText">{escape(diff_text).replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )


def article_excerpt(article: dict | None) -> str:
    if not article:
        return "No article text is available yet. Contributors may start from the target context."
    paragraphs = split_paragraphs(article.get("body", ""))
    return "\n\n".join(paragraphs[:2]) or article.get("summary", "")


def render_related_pages_panel(target: dict, article: dict | None) -> None:
    st.markdown('<h2 class="WikiArticle-sectionTitle">Related pages</h2>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="WikiNotice">
            Use previously viewed or watched pages as supporting context for your revision.
        </div>
        """,
        unsafe_allow_html=True,
    )

    pages = related_pages_for_editor(target, article)
    if not pages:
        st.markdown(
            '<div class="WikiNotice">No related pages have been opened or watched yet.</div>',
            unsafe_allow_html=True,
        )
        return

    items = "".join(
        f'<li><a href="{article_url(page)}">{escape(page)}</a></li>'
        for page in pages
    )
    st.markdown(f'<ul class="WikiSourceList">{items}</ul>', unsafe_allow_html=True)


def apply_contribution_review(
    target: dict,
    contribution_text: str,
    review: dict,
    edit_summary: str,
    submitted_at: str,
) -> None:
    target_id = target["id"]
    decision = review["decision"]
    status = {
        "approved": "Approved",
        "pending": "Pending review",
        "needs_revision": "Needs revision",
        "rejected": "Not accepted",
    }[decision]
    st.session_state.contribution_statuses[target_id] = status
    st.session_state.contribution_updated_at[target_id] = submitted_at

    profile = st.session_state.contributor_profile
    profile["submittedEdits"] += 1
    profile["prestige"] = max(0, profile["prestige"] + review["prestigeChange"])
    if decision == "approved":
        profile["approvedEdits"] += 1
        st.session_state.approved_patches[target_id] = {
            "articleTitle": target["articleTitle"],
            "sectionTitle": target["sectionTitle"],
            "text": review.get("articlePatch") or contribution_text,
        }
    elif decision == "rejected":
        profile["rejectedEdits"] += 1
    profile["pendingEdits"] = sum(
        1
        for status in st.session_state.contribution_statuses.values()
        if status in {"Pending review", "Needs revision"}
    )

    st.session_state.review_threads.setdefault(target_id, []).append(
        {
            "contribution": contribution_text,
            "editSummary": edit_summary.strip(),
            "review": review,
            "submittedAt": submitted_at,
            "submittedBy": st.session_state.contributor_profile["name"],
            "articleTitle": target["articleTitle"],
            "sectionTitle": target["sectionTitle"],
        }
    )
    st.session_state.inbox_messages.insert(0, review["inboxMessage"])
    maybe_unlock_archive_thread()


def maybe_unlock_archive_thread() -> None:
    profile = st.session_state.contributor_profile
    unlocked = profile["unlockedMysteries"]
    if profile["approvedEdits"] >= 2 and "The Kanzaki Radio Silence" not in unlocked:
        unlocked.append("The Kanzaki Radio Silence")
        st.session_state.inbox_messages.insert(
            0,
            {
                "from": "WikiTheory Review Board",
                "subject": "New archive thread available",
                "body": (
                    "Your approved revisions have increased your archive access. "
                    "A placeholder thread, 'The Kanzaki Radio Silence,' is now visible on your profile."
                ),
            },
        )


def render_review_summary(target: dict, review: dict, submitted_at: str) -> None:
    st.markdown(
        f"""
        <div class="WikiNotice">
            Your revision has been submitted for editorial review.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_pending_revision_box(target, review, submitted_at)


def render_pending_revision_box(target: dict, review: dict, submitted_at: str) -> None:
    st.markdown(
        f"""
        <div class="WikiEditPanel WikiPendingRevision">
            <div><strong>Pending revision</strong></div>
            <div><strong>Article:</strong> {escape(target["articleTitle"])}</div>
            <div><strong>Section:</strong> {escape(target["sectionTitle"])}</div>
            <div><strong>Status:</strong> {escape(public_review_status(review))}</div>
            <div><strong>Submitted by:</strong> {escape(st.session_state.contributor_profile["name"])}</div>
            <div><strong>Time:</strong> {escape(submitted_at)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def public_review_status(review: dict) -> str:
    explicit = str(review.get("publicStatusText") or "").strip()
    if explicit:
        return explicit
    return {
        "approved": "Approved",
        "pending": "Pending review",
        "needs_revision": "Needs revision",
        "rejected": "Not accepted",
    }.get(review.get("decision"), "Pending review")


def render_editorial_discussion(target_id: str) -> None:
    thread = st.session_state.review_threads.get(target_id, [])
    st.markdown('<h2 class="WikiArticle-sectionTitle">Editorial discussion</h2>', unsafe_allow_html=True)
    if not thread:
        st.markdown(
            '<div class="WikiNotice">No public discussion has been posted for this section yet.</div>',
            unsafe_allow_html=True,
        )
        return

    for entry in reversed(thread):
        review = entry["review"]
        st.markdown(
            f"""
            <div class="WikiDiscussionPost">
                <div><strong>Pending revision</strong></div>
                <div class="WikiMeta">
                    {escape(entry.get("sectionTitle", "Section"))} on {escape(entry.get("articleTitle", "Article"))}
                    submitted by {escape(entry.get("submittedBy", "GuestEditor"))}
                    at {escape(entry.get("submittedAt", "Not recorded"))}
                </div>
                <div class="WikiTalkExcerpt">{escape(entry["contribution"])}</div>
                <div class="WikiMeta">Edit summary: {escape(entry.get("editSummary") or "No summary provided.")}</div>
                <div class="WikiMeta">Status: {escape(public_review_status(review))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for comment in review["editorComments"]:
            st.markdown(
                f"""
                <div class="WikiTalkComment">
                    <p><strong>{escape(comment["editor"])}:</strong> {escape(comment["comment"])}</p>
                    <div class="WikiSignature">-- {escape(comment["editor"])}, WikiTheory editor</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_category_page(category: str) -> None:
    matching = [
        article for article in list_articles() if category in article.get("categories", [])
    ]
    render_index_page(
        f"Category:{category}",
        matching,
        "Category links collect WikiTheory entries by archive theme.",
    )


def render_watchlist_page() -> None:
    watched_pages = get_watchlist()
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown('<h1 class="WikiArticle-title">Watchlist</h1>', unsafe_allow_html=True)
    if not watched_pages:
        st.markdown('<div class="WikiNotice">No watched pages yet.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    header = st.columns([1.8, 0.8, 1.1, 0.9, 1.4])
    for column, label in zip(header, ["Page", "Type", "Last viewed", "Status", "Notes"]):
        column.markdown(f"**{label}**")

    for item in watched_pages:
        article = get_article(item["title"])
        row = st.columns([1.8, 0.8, 1.1, 0.9, 1.4])
        row[0].markdown(f"[{item['title']}]({article_url(item['title'])})")
        row[1].write(article.get("type", "missing") if article else "missing")
        row[2].write(item.get("lastViewed") or "Not viewed")
        row[3].write(watchlist_status(item["title"]))
        row[4].write(item.get("notes") or "No notes")
    st.markdown("</div>", unsafe_allow_html=True)


def watchlist_status(title: str) -> str:
    if article_exists(title):
        return "Page available"
    return "Not yet written"


def render_placeholder_page(page: str) -> None:
    articles = list_articles()
    if page == "People":
        render_index_page(page, [article for article in articles if article["type"] == "person"])
    elif page == "Places":
        render_index_page(page, [article for article in articles if article["type"] == "place"])
    elif page == "Organizations":
        render_index_page(page, [article for article in articles if article["type"] == "organization"])
    elif page == "Documents":
        render_index_page(page, [article for article in articles if article["type"] == "document"])
    elif page == "Mystery index":
        render_index_page(page, articles, "All currently saved and seeded WikiTheory entries.")
    elif page == "Contributor profile":
        render_profile_page()
    else:
        render_index_page(page, articles, "Navigation page for the prototype archive.")


def render_index_page(title: str, articles: list[dict], description: str = "") -> None:
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown(
        f'<h1 class="WikiArticle-title">{escape(title)}</h1>',
        unsafe_allow_html=True,
    )
    if description:
        st.markdown(f'<div class="WikiNotice">{escape(description)}</div>', unsafe_allow_html=True)

    if articles:
        for article in articles:
            st.markdown(
                f'- [{article["title"]}]({article_url(article["title"])}) '
                f'<span class="WikiMeta">({article["type"]})</span>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="WikiNotice">No entries in this section yet.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_inbox_page() -> None:
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown('<h1 class="WikiArticle-title">Inbox</h1>', unsafe_allow_html=True)
    st.markdown(
        '<div class="WikiMeta">Contributor notices and editorial replies</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.inbox_messages:
        for message in st.session_state.inbox_messages:
            st.markdown(
                f"""
                <div class="WikiDiscussionPost">
                    <div class="WikiMeta">From: {escape(message["from"])}</div>
                    <strong>{escape(message["subject"])}</strong>
                    <p>{escape(message["body"])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="WikiNotice">No inbox messages yet.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_profile_page() -> None:
    profile = st.session_state.contributor_profile
    st.markdown('<div class="WikiLayout WikiArticle">', unsafe_allow_html=True)
    st.markdown('<h1 class="WikiArticle-title">Contributor Profile</h1>', unsafe_allow_html=True)
    st.markdown(
        '<div class="WikiMeta">WikiTheory account record and archive access</div>',
        unsafe_allow_html=True,
    )

    with st.form("ContributorNameForm"):
        name = st.text_input("Contributor name", value=profile["name"])
        saved = st.form_submit_button("Update profile")
    if saved and name.strip():
        profile["name"] = name.strip()
        st.success("Contributor profile updated.")

    st.dataframe(
        [
            {"Field": "Contributor", "Value": profile["name"]},
            {"Field": "Prestige level", "Value": prestige_level(profile["prestige"])},
            {"Field": "Prestige points", "Value": str(profile["prestige"])},
            {"Field": "Approved edits", "Value": str(profile["approvedEdits"])},
            {"Field": "Rejected edits", "Value": str(profile["rejectedEdits"])},
            {"Field": "Pending review", "Value": str(profile["pendingEdits"])},
            {"Field": "Submitted revisions", "Value": str(profile["submittedEdits"])},
        ],
        column_config={
            "Field": st.column_config.TextColumn("Field", width="medium"),
            "Value": st.column_config.TextColumn("Value", width="large"),
        },
        hide_index=True,
        use_container_width=True,
        height=280,
    )

    st.markdown('<h2 class="WikiArticle-sectionTitle">Archive access</h2>', unsafe_allow_html=True)
    for mystery in profile["unlockedMysteries"]:
        st.markdown(f"- {mystery}")
    st.markdown("</div>", unsafe_allow_html=True)


def prestige_level(points: int) -> str:
    if points >= 80:
        return "Theory Curator"
    if points >= 55:
        return "Senior Editor"
    if points >= 35:
        return "Field Archivist"
    if points >= 15:
        return "Verified Contributor"
    return "New Contributor"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "page"
