from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
STORE_DIR = BASE_DIR / "wiki_mystery_store"
ARTICLES_PATH = STORE_DIR / "articles.json"
WATCHLIST_PATH = STORE_DIR / "watchlist.json"
CANON_PATH = BASE_DIR / "wiki_mystery_canon.md"
MAIN_ARTICLE = "Mizukawa Disappearance Case"

ARTICLE_TYPES = {
    "case",
    "person",
    "place",
    "organization",
    "document",
    "investigation",
    "theory",
    "timeline",
    "record",
    "event",
    "rumor",
    "object",
}

LINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


CONTRIBUTION_TARGETS: list[dict[str, Any]] = [
    {
        "id": "cause-of-disappearance",
        "articleTitle": "Mizukawa Disappearance Case",
        "kind": "Missing section",
        "sectionTitle": "Cause of disappearance",
        "context": (
            "The public article still treats flood conditions and poor coordination as the main explanation."
        ),
        "difficulty": "Hard",
        "requiredClues": [
            "The weather report from the night of the disappearance was edited two days later.",
            "Shirohane Clinic closed one week after Emi Kuroda vanished.",
        ],
        "canonAnswer": (
            "Emi was not simply lost in the flood. She discovered the connection between Shirohane Clinic, "
            "the edited weather report, and society land records, and was moved through the clinic service road."
        ),
    },
    {
        "id": "clinic-closure-reason",
        "articleTitle": "Shirohane Clinic",
        "kind": "Disputed claim",
        "sectionTitle": "Reason for closure",
        "context": (
            "The closure notice cites storm damage and debt, but the timing has been disputed by contributors."
        ),
        "difficulty": "Medium",
        "requiredClues": [
            "Shirohane Clinic closed one week after Emi Kuroda vanished.",
            "The folklore society owned the land behind the clinic.",
        ],
        "canonAnswer": (
            "The clinic closed because Emi's disappearance risked exposing unauthorized sleep and memory studies "
            "and the archive shed behind the clinic."
        ),
    },
    {
        "id": "final-known-movements",
        "articleTitle": "Emi Kuroda",
        "kind": "Missing section",
        "sectionTitle": "Final known movements",
        "context": (
            "The biography lacks a careful account of where Emi went after asking about the clinic."
        ),
        "difficulty": "Medium",
        "requiredClues": [
            "Emi's last school essay mentioned hearing festival bells from a place where there was no shrine.",
            "Shirohane Clinic closed one week after Emi Kuroda vanished.",
        ],
        "canonAnswer": (
            "Emi visited Shirohane Clinic and likely found a patient ledger or related record before being moved "
            "through the west ridge area during the storm."
        ),
    },
    {
        "id": "weather-revisions-authenticity",
        "articleTitle": "Kawabe River Weather Report",
        "kind": "Disputed claim",
        "sectionTitle": "Authenticity of revisions",
        "context": (
            "Editors disagree about whether the revised flood report was routine clerical cleanup or a cover story."
        ),
        "difficulty": "Hard",
        "requiredClues": [
            "The weather report from the night of the disappearance was edited two days later.",
        ],
        "canonAnswer": (
            "The weather report was revised two days later to exaggerate flood severity and make the disappearance "
            "look less suspicious."
        ),
    },
    {
        "id": "society-clinic-property",
        "articleTitle": "Mizukawa Folklore Preservation Society",
        "kind": "Missing section",
        "sectionTitle": "Connection to clinic property",
        "context": (
            "The society page mentions archive work but does not explain why its land records matter."
        ),
        "difficulty": "Medium",
        "requiredClues": [
            "The folklore society owned the land behind the clinic.",
            "Emi's last school essay mentioned hearing festival bells from a place where there was no shrine.",
        ],
        "canonAnswer": (
            "The society owned land and archive rooms behind Shirohane Clinic, helping conceal access routes and "
            "making folklore rumors a useful distraction from clinic records."
        ),
    },
]


EDITOR_PERSONAS = [
    "ArchivistMori: cautious, asks for better citations and careful phrasing.",
    "CivicLedger: focused on documents, land records, and timelines.",
    "LanternField: interested in folklore but skeptical of overclaiming.",
    "NullRevision: strict about unsupported claims and article neutrality.",
]


ARTICLE_ROLE_HINTS = {
    "case": ["case", "disappearance"],
    "person": ["emi", "kuroda", "student", "person"],
    "place": ["town", "road", "bridge", "ridge", "reservoir"],
    "organization": ["clinic", "society", "office", "archive"],
    "document": ["report", "notice", "statement", "bulletin", "records", "ledger"],
    "investigation": ["investigation", "inquiry", "search"],
    "timeline": ["timeline", "chronology", "movements"],
    "theory": ["theory", "rumor"],
}


SECTION_TEMPLATES = {
    "case": [
        "Disappearance",
        "Missing person",
        "Initial search",
        "Investigation",
        "Later developments",
        "Public theories",
        "Related records",
        "See also",
    ],
    "person": [
        "Early life",
        "Disappearance",
        "Last known movements",
        "Personal writings",
        "Later references",
        "See also",
    ],
    "organization": [
        "Establishment",
        "Services",
        "Closure",
        "Records and ownership",
        "Connection to later inquiries",
        "See also",
    ],
    "document": [
        "Contents",
        "Publication history",
        "Revisions",
        "Disputed authenticity",
        "Archive status",
        "See also",
    ],
    "record": [
        "Contents",
        "Custody",
        "Referenced properties",
        "Archive status",
        "See also",
    ],
    "investigation": [
        "Scope",
        "Timeline",
        "Witness summaries",
        "Documentary record",
        "Competing interpretations",
        "See also",
    ],
    "place": [
        "Geography",
        "History",
        "Local institutions",
        "1998 flood",
        "Public records",
        "Related incidents",
    ],
    "timeline": [
        "Chronology",
        "Reported movements",
        "Documented gaps",
        "Later reconstruction",
        "See also",
    ],
    "theory": [
        "Summary",
        "Support cited by contributors",
        "Objections",
        "Related pages",
    ],
}


SEED_ARTICLES: dict[str, dict[str, Any]] = {
    "mizukawa disappearance case": {
        "title": "Mizukawa Disappearance Case",
        "type": "event",
        "summary": "A 1998 missing-person case in Mizukawa officially attributed to flooding and local confusion.",
        "body": (
            "The [[Mizukawa Disappearance Case]] refers to the unresolved disappearance of "
            "[[Emi Kuroda]], a second-year student who vanished on 17 September 1998 near "
            "[[Mizukawa Town]]. Contemporary summaries described the case as a confused "
            "storm-night investigation, with officers moving between washed-out roads, "
            "temporary shelters, and the old bus depot.\n\n"
            "The official report tied the disappearance to flood conditions along the "
            "Kawabe River. Later local accounts questioned this explanation, especially "
            "after readers noticed differences between the early radio bulletin and the "
            "[[Kawabe River Weather Report]]. Emi had reportedly asked classmates about "
            "[[Shirohane Clinic]] and borrowed a pamphlet from the [[Mizukawa Folklore "
            "Preservation Society]] two days before she was last seen.\n\n"
            "The case remains a common subject in local newsletters, amateur chronology "
            "projects, and rumors about the [[West Ridge Service Road]]. Most public "
            "versions emphasize missing paperwork and overworked police rather than a "
            "deliberate coverup."
        ),
        "links": [
            "Emi Kuroda",
            "Mizukawa Town",
            "Kawabe River Weather Report",
            "Shirohane Clinic",
            "Mizukawa Folklore Preservation Society",
            "West Ridge Service Road",
        ],
        "clues": [
            "The weather report from the night of the disappearance was edited two days later."
        ],
        "infobox": {
            "Date": "17 September 1998",
            "Location": "Mizukawa Town, Kawabe River valley",
            "Related people": "Emi Kuroda",
        },
    },
    "mizukawa town": {
        "title": "Mizukawa Town",
        "type": "place",
        "summary": "A fictional rural town known for river terraces, shuttered clinics, and a persistent missing-person legend.",
        "body": (
            "[[Mizukawa Town]] is a small riverside municipality bordered by cedar hills, "
            "rice terraces, and the Kawabe River. Before the late 1990s, it was mostly "
            "known for paper lantern workshops and a minor summer archive maintained by "
            "the [[Mizukawa Folklore Preservation Society]].\n\n"
            "The town's reputation changed after the [[Mizukawa Disappearance Case]]. "
            "Visitors often searched for landmarks named in the case, including "
            "[[Shirohane Clinic]], the old [[West Ridge Service Road]], and the flood gauge "
            "near Minami Bridge. Local guides discouraged this attention, arguing that the "
            "story had been distorted by rumor columns and copied maps.\n\n"
            "Municipal records list several land transfers in the years before 1998. One "
            "transfer placed a storage parcel behind Shirohane Clinic under the control of "
            "a society trust, a detail that became important only after the clinic's sudden "
            "closure."
        ),
        "links": [
            "Mizukawa Disappearance Case",
            "Mizukawa Folklore Preservation Society",
            "Shirohane Clinic",
            "West Ridge Service Road",
            "Minami Bridge Flood Gauge",
        ],
        "clues": [
            "The folklore society owned the land behind the clinic."
        ],
        "infobox": {
            "Region": "Kawabe River valley",
            "Known for": "1998 disappearance case",
            "Civic archive": "Mizukawa Folklore Preservation Society",
        },
    },
    "emi kuroda": {
        "title": "Emi Kuroda",
        "type": "person",
        "summary": "A Mizukawa student whose 1998 disappearance became the center of a disputed local case.",
        "body": (
            "[[Emi Kuroda]] was a student at Mizukawa North High School and the missing "
            "person at the center of the [[Mizukawa Disappearance Case]]. Teachers "
            "described her as quiet, precise, and unusually interested in municipal "
            "records. Her notebook reportedly contained copied street names, clinic hours, "
            "and a list of people connected to [[Shirohane Clinic]].\n\n"
            "In the week before her disappearance, Emi submitted a short essay titled "
            "[[Bells on the West Ridge]]. The essay described hearing festival bells from "
            "a ridge where no shrine was active. This detail was later treated as folklore "
            "color by newspaper columns, but several classmates said Emi mentioned it while "
            "asking about the [[Mizukawa Folklore Preservation Society]].\n\n"
            "Emi was last reported near the bus depot during heavy rain. The earliest "
            "witness summaries placed her farther west than the final police timeline."
        ),
        "links": [
            "Mizukawa Disappearance Case",
            "Shirohane Clinic",
            "Bells on the West Ridge",
            "Mizukawa Folklore Preservation Society",
            "Mizukawa North High School",
        ],
        "clues": [
            "Emi's last school essay mentioned hearing festival bells from a place where there was no shrine."
        ],
        "infobox": {
            "Born": "1981",
            "Disappeared": "17 September 1998",
            "School": "Mizukawa North High School",
        },
    },
    "shirohane clinic": {
        "title": "Shirohane Clinic",
        "type": "organization",
        "summary": "A closed community clinic near Mizukawa's west ridge, often mentioned in accounts of the 1998 case.",
        "body": (
            "[[Shirohane Clinic]] was a private community clinic built on the western edge "
            "of [[Mizukawa Town]]. Its public services included vaccinations, sleep "
            "consultations, and seasonal health screenings. Former residents later recalled "
            "that the clinic kept unusual evening hours during the summer of 1998.\n\n"
            "The clinic appears repeatedly in documents related to the [[Mizukawa "
            "Disappearance Case]]. [[Emi Kuroda]] was seen near its lane shortly before "
            "she vanished, and the building's rear parcel bordered a storage shed listed "
            "under the [[Mizukawa Folklore Preservation Society]]. Staff declined most "
            "press requests after the case.\n\n"
            "Shirohane Clinic closed the week after Emi disappeared. The official reason "
            "was storm damage and debt, although the archived damage estimate is shorter "
            "than comparable claims from the same flood."
        ),
        "links": [
            "Mizukawa Town",
            "Mizukawa Disappearance Case",
            "Emi Kuroda",
            "Mizukawa Folklore Preservation Society",
            "Shirohane Closure Notice",
        ],
        "clues": [
            "Shirohane Clinic closed one week after Emi Kuroda vanished."
        ],
        "infobox": {
            "Opened": "1974",
            "Closed": "24 September 1998",
            "Location": "West edge of Mizukawa Town",
        },
    },
    "mizukawa folklore preservation society": {
        "title": "Mizukawa Folklore Preservation Society",
        "type": "organization",
        "summary": "A local archive group whose land records and folklore pamphlets overlap with the Mizukawa case.",
        "body": (
            "The [[Mizukawa Folklore Preservation Society]] was founded to collect songs, "
            "festival notes, and oral histories from the Kawabe River valley. Its best "
            "known pamphlet, [[Bells on the West Ridge]], described impossible festival "
            "sounds heard before fires, floods, and landslides.\n\n"
            "The society became controversial after the [[Mizukawa Disappearance Case]] "
            "because its officers controlled several parcels near [[Shirohane Clinic]]. "
            "One parcel included an archive shed behind the clinic, though society members "
            "claimed it was used only for lantern frames and festival banners.\n\n"
            "Several amateur researchers argue that the society's folklore material was "
            "used to distract from mundane records: land deeds, weather forms, and clinic "
            "appointment ledgers. Others treat the society as a convenient scapegoat for "
            "the town's broader secrecy."
        ),
        "links": [
            "Bells on the West Ridge",
            "Mizukawa Disappearance Case",
            "Shirohane Clinic",
            "Mizukawa Town",
            "Archive Shed Parcel",
        ],
        "clues": [],
        "infobox": {
            "Founded": "1956",
            "Focus": "Local folklore and festival archives",
            "Notable text": "Bells on the West Ridge",
        },
    },
}


STRUCTURED_SEED_ARTICLES: dict[str, dict[str, Any]] = {
    "mizukawa disappearance case": {
        "title": "Mizukawa Disappearance Case",
        "articleType": "case",
        "summary": (
            "The 1998 disappearance of Mizukawa student Emi Kuroda, officially associated "
            "with flood conditions and later disputed through municipal records."
        ),
        "leadParagraphs": [
            (
                "The Mizukawa Disappearance Case was a missing-person inquiry opened after "
                "[[Emi Kuroda]], a second-year student in [[Mizukawa Town]], failed to return "
                "home on 17 September 1998. The first public notices described a storm-night "
                "search complicated by washed roads, intermittent telephone service, and "
                "evacuations along the Kawabe River.[1] The case became the best-known entry "
                "in the town's post-flood archive because several ordinary records, including "
                "weather bulletins and clinic notices, were later found to have conflicting dates."
            ),
            (
                "Public summaries usually treat the matter as an unresolved local inquiry "
                "rather than a single solved incident. The main article gives an overview of "
                "the disappearance, while details about the flood bulletin, clinic closure, "
                "family statements, and later document disputes are maintained in linked pages "
                "such as [[Kawabe River Weather Report]], [[Shirohane Clinic closure notice]], "
                "and [[Investigation into the Mizukawa disappearance]].[2]"
            ),
        ],
        "infobox": {
            "title": "Mizukawa disappearance",
            "imageCaption": "Fictional archive map of the Kawabe River valley",
            "fields": [
                {"label": "Date", "value": "17 September 1998"},
                {"label": "Location", "value": "[[Mizukawa Town]], Kawabe River valley"},
                {"label": "Missing person", "value": "[[Emi Kuroda]]"},
                {"label": "Last seen", "value": "Bus depot and west ridge route"},
                {"label": "Reported by", "value": "[[Kuroda family statement|Kuroda family]]"},
                {"label": "Investigating agency", "value": "Kawabe Regional Police Office"},
                {"label": "Status", "value": "Unresolved"},
                {
                    "label": "Related inquiries",
                    "value": "[[1998 Mizukawa flood inquiry]]; [[Archive Bulletin 44-B]]",
                },
            ],
        },
        "sections": [
            {
                "heading": "Disappearance",
                "paragraphs": [
                    (
                        "Kuroda was last accounted for after leaving a study session at "
                        "Mizukawa North High School during heavy rain. Early notes place her "
                        "near the town bus depot, while a later reconstruction moves the final "
                        "confirmed sighting westward toward the clinic road.[3] The discrepancy "
                        "is one reason the page for [[Emi Kuroda's final known movements]] is "
                        "kept separate from the general biography."
                    ),
                    (
                        "The official chronology emphasizes flood warnings and transport "
                        "delays. Contemporary residents, however, also remembered a narrow "
                        "window in which traffic briefly resumed on the [[West Ridge Service "
                        "Road]]. That road connected the clinic lane, a storage parcel, and "
                        "the older agricultural route above the Kawabe River, making it a "
                        "recurring feature in later timelines without establishing a final "
                        "explanation."
                    ),
                ],
            },
            {
                "heading": "Missing person",
                "paragraphs": [
                    (
                        "Emi Kuroda was sixteen or seventeen years old at the time of the "
                        "case, depending on whether later copied school records used her class "
                        "year or birth year. Teachers described her as quiet and exacting, "
                        "with an unusual interest in maps, municipal notices, and small "
                        "differences between public announcements.[4] Her short essay "
                        "[[Bells on the West Ridge]] was repeatedly quoted by newspapers, "
                        "although the essay itself was not an investigation record."
                    ),
                    (
                        "The family's first statement asked residents to report ordinary "
                        "sightings rather than rumors. Later clippings show a change in tone "
                        "after Kuroda's relatives requested copies of the weather logs and "
                        "clinic visitor ledger. The surviving text of that request is covered "
                        "under [[Kuroda family statement]]."
                    ),
                ],
            },
            {
                "heading": "Initial search",
                "paragraphs": [
                    (
                        "The search began as a storm response, with volunteer firefighters "
                        "checking bus stops, evacuation rooms, and low bridges. The riverbank "
                        "search was limited by high water and by conflicting reports about "
                        "which roads had closed before nightfall.[5] Searchers did not record "
                        "a full sweep of the clinic lane until the following morning."
                    ),
                    (
                        "A later civic review found that several forms used during the search "
                        "were copied from flood-response templates rather than missing-person "
                        "templates. The finding did not prove misconduct, but it helped create "
                        "a lasting dispute over whether the case was treated too quickly as a "
                        "weather casualty."
                    ),
                ],
            },
            {
                "heading": "Investigation",
                "paragraphs": [
                    (
                        "The police file drew on witness statements, school attendance "
                        "records, river patrol notes, and a short telephone log from "
                        "[[Shirohane Clinic]]. The clinic was not publicly described as a "
                        "suspect location, but its appearance in the log led later editors to "
                        "cross-reference the page with [[Shirohane Clinic closure notice]]."
                    ),
                    (
                        "The [[Kawabe River Weather Report]] became important because the "
                        "storm's severity was used to explain gaps in the search. A more "
                        "detailed comparison of the original bulletin and the revised copy is "
                        "maintained in that article rather than summarized here. The case page "
                        "therefore records only that the weather record became disputed after "
                        "the disappearance."
                    ),
                ],
            },
            {
                "heading": "Later developments",
                "paragraphs": [
                    (
                        "Interest in the case revived after the [[Mizukawa Municipal Archive]] "
                        "cataloged a set of flood and property papers under a single cabinet "
                        "heading. The batch included the clinic closure notice, a partial "
                        "police bulletin, and references to [[Folklore Preservation Society "
                        "land records]].[6] The grouping was likely administrative, but it "
                        "encouraged comparisons between records that had previously been "
                        "treated as unrelated."
                    ),
                    (
                        "No public file identifies a final cause of disappearance. The most "
                        "cautious later accounts describe the matter as an unresolved case "
                        "with documentary irregularities. More expansive theories connect the "
                        "clinic, the service road, and society property, but those claims are "
                        "handled in narrower articles where supporting records can be weighed."
                    ),
                ],
            },
            {
                "heading": "Public theories",
                "paragraphs": [
                    (
                        "Local newsletter writers proposed explanations involving a river "
                        "accident, a voluntary flight, a mistaken police timeline, and a "
                        "cover story built around flood damage. WikiTheory articles avoid "
                        "selecting a final theory in the overview page. Instead, the article "
                        "network distinguishes documented facts from later interpretations."
                    ),
                    (
                        "Folklore-based accounts often focus on bells, ridge paths, and the "
                        "society's summer pamphlets. Document-based accounts focus on the "
                        "clinic closure, the revised weather bulletin, and the property parcel "
                        "behind the clinic. Both traditions shaped how the case was discussed, "
                        "but neither is treated as complete on this page."
                    ),
                ],
            },
            {
                "heading": "Related records",
                "paragraphs": [
                    (
                        "Frequently cited records include [[Archive Bulletin 44-B]], "
                        "[[Kawabe River Weather Report]], [[Shirohane Clinic closure notice]], "
                        "and [[1998 Mizukawa flood inquiry]]. The records are not consistent "
                        "in format or purpose: some are police notices, others are municipal "
                        "indexes, and others are copied archive cards."
                    ),
                    (
                        "The best starting points for readers are the person page for "
                        "[[Emi Kuroda]], the place article for [[Mizukawa Town]], and the "
                        "institutional entries for [[Shirohane Clinic]] and [[Mizukawa "
                        "Folklore Preservation Society]]. Each page includes a narrower "
                        "summary and links to records that belong more naturally there."
                    ),
                ],
            },
            {
                "heading": "See also",
                "paragraphs": [
                    (
                        "[[Investigation into the Mizukawa disappearance]]; [[Emi Kuroda's "
                        "final known movements]]; [[West Ridge Service Road]]; [[Kuroda "
                        "family statement]]; [[Mizukawa Municipal Archive]]."
                    )
                ],
            },
        ],
        "links": [
            "Emi Kuroda",
            "Mizukawa Town",
            "Kawabe River Weather Report",
            "Shirohane Clinic",
            "Shirohane Clinic closure notice",
            "Investigation into the Mizukawa disappearance",
            "Emi Kuroda's final known movements",
            "1998 Mizukawa flood inquiry",
            "West Ridge Service Road",
            "Kuroda family statement",
            "Mizukawa Municipal Archive",
            "Folklore Preservation Society land records",
            "Archive Bulletin 44-B",
        ],
        "clues": [
            "The weather report from the night of the disappearance was edited two days later."
        ],
        "references": [
            "Mizukawa Municipal Archive, Flood Response Summary, 1998.",
            "Kawabe Regional Police Office, Missing Persons Bulletin 44-B, partially redacted.",
            "Mizukawa North High School, attendance and class circular extracts, September 1998.",
            "Mizukawa Community Newsletter, November 1998 case retrospective.",
            "Municipal Records Desk, Cabinet 7 transfer index, revised 2002.",
        ],
        "externalLinks": [
            "WikiTheory archive portal: Mizukawa case index",
            "Fictional transcript collection: Kawabe valley public notices",
        ],
        "categories": [
            "1998 incidents",
            "Mizukawa Town",
            "Missing person cases",
            "Unresolved local inquiries",
            "Fictional archive records",
        ],
    },
    "emi kuroda": {
        "title": "Emi Kuroda",
        "articleType": "person",
        "summary": (
            "Mizukawa North High School student whose 1998 disappearance became the center "
            "of a disputed local inquiry."
        ),
        "leadParagraphs": [
            (
                "Emi Kuroda was a student at Mizukawa North High School and the missing "
                "person at the center of the [[Mizukawa Disappearance Case]]. Public records "
                "describe her as a second-year student living with her family in [[Mizukawa "
                "Town]], while later accounts emphasize her habit of copying civic notices "
                "and comparing small differences between public bulletins.[1]"
            ),
            (
                "The biography is intentionally limited to Kuroda's life, writings, and "
                "documented movements. Arguments about the clinic, the flood bulletin, and "
                "property records are summarized here only when they affect her movements; "
                "the fuller record is maintained in pages such as [[Emi Kuroda's final known "
                "movements]] and [[Kuroda family statement]]."
            ),
        ],
        "infobox": {
            "title": "Emi Kuroda",
            "imageCaption": "Fictional school registry image, cropped in archive copy",
            "fields": [
                {"label": "Full name", "value": "Emi Kuroda"},
                {"label": "Born", "value": "1981 or 1982"},
                {"label": "Disappeared", "value": "17 September 1998"},
                {"label": "School", "value": "Mizukawa North High School"},
                {"label": "Known for", "value": "[[Mizukawa Disappearance Case]]"},
                {"label": "Associated places", "value": "[[Mizukawa Town]]; [[West Ridge Service Road]]"},
            ],
        },
        "sections": [
            {
                "heading": "Early life",
                "paragraphs": [
                    (
                        "Kuroda's early life is recorded mostly through school forms, a "
                        "short local scholarship notice, and later interviews with teachers. "
                        "She was described as careful with dates and unusually interested in "
                        "maps. One teacher recalled that she borrowed a municipal directory "
                        "to check whether old lane names still appeared on official forms.[2]"
                    ),
                    (
                        "A small number of copied class materials also suggest that Kuroda "
                        "treated civic paperwork as a practical puzzle rather than as a "
                        "formal research interest. She annotated bus times, clinic hours, "
                        "and old street names in the margins of ordinary notebooks. Later "
                        "writers sometimes exaggerated this habit into detective work, but "
                        "the surviving school references support a quieter description: a "
                        "student attentive to records that most classmates ignored."
                    ),
                    (
                        "The family lived within walking distance of the bus depot and the "
                        "river terraces. This ordinary geography became important only after "
                        "the disappearance, when witness summaries disagreed about whether "
                        "Kuroda remained near the depot or moved toward the west ridge road."
                    ),
                ],
            },
            {
                "heading": "Disappearance",
                "paragraphs": [
                    (
                        "Kuroda disappeared during heavy rain on 17 September 1998. Early "
                        "notices asked residents to report sightings near bus stops, school "
                        "shelters, and the low road toward [[Shirohane Clinic]]. The first "
                        "search notes treated flood conditions as the central obstacle, a "
                        "framing later questioned in the [[1998 Mizukawa flood inquiry]]."
                    )
                ],
            },
            {
                "heading": "Last known movements",
                "paragraphs": [
                    (
                        "The last known movements page separates confirmed sightings from "
                        "later reconstruction. The most stable account places Kuroda near "
                        "the depot after school, then records an unconfirmed movement toward "
                        "the clinic lane. Her name also appears beside a telephone note in a "
                        "clinic log, but the surviving copy does not explain why the call was "
                        "made.[3]"
                    ),
                    (
                        "Kuroda had reportedly asked classmates about clinic hours and about "
                        "a folklore pamphlet held by the [[Mizukawa Folklore Preservation "
                        "Society]]. Those details do not by themselves explain the "
                        "disappearance, but they link her biography to several records that "
                        "were reexamined after 1998."
                    ),
                ],
            },
            {
                "heading": "Personal writings",
                "paragraphs": [
                    (
                        "Her best-known school essay, [[Bells on the West Ridge]], described "
                        "hearing festival bells from a ridge where no shrine was active. "
                        "Newspaper columns later treated the essay as eerie folklore, while "
                        "document-focused editors treat it mainly as evidence that she had "
                        "been asking about the western route before the storm."
                    )
                ],
            },
            {
                "heading": "Later references",
                "paragraphs": [
                    (
                        "Kuroda is referenced in the [[Kawabe River Weather Report]], "
                        "[[Archive Bulletin 44-B]], and the family's public statement. These "
                        "records use different tones: administrative, investigative, and "
                        "personal. Their differences explain why WikiTheory keeps the "
                        "biographical article separate from the case overview."
                    )
                ],
            },
            {
                "heading": "See also",
                "paragraphs": [
                    (
                        "[[Mizukawa Disappearance Case]]; [[Emi Kuroda's final known "
                        "movements]]; [[Kuroda family statement]]; [[Bells on the West Ridge]]."
                    )
                ],
            },
        ],
        "links": [
            "Mizukawa Disappearance Case",
            "Mizukawa Town",
            "Emi Kuroda's final known movements",
            "Kuroda family statement",
            "Shirohane Clinic",
            "Mizukawa Folklore Preservation Society",
            "Bells on the West Ridge",
            "Archive Bulletin 44-B",
        ],
        "clues": [
            "Emi's last school essay mentioned hearing festival bells from a place where there was no shrine."
        ],
        "references": [
            "Mizukawa North High School, class register extract, 1998.",
            "Mizukawa Municipal Archive, student notices folder, box 12.",
            "Kawabe Regional Police Office, telephone-note appendix, partially redacted.",
        ],
        "externalLinks": ["WikiTheory archive portal: Kuroda family clipping index"],
        "categories": ["People", "Mizukawa Town", "Missing person cases", "1998 incidents"],
    },
    "shirohane clinic": {
        "title": "Shirohane Clinic",
        "articleType": "organization",
        "summary": (
            "A closed community clinic on Mizukawa's western edge, repeatedly cited in "
            "records connected to the 1998 disappearance."
        ),
        "leadParagraphs": [
            (
                "Shirohane Clinic was a private community clinic located near the western "
                "edge of [[Mizukawa Town]]. It offered vaccinations, seasonal health "
                "screenings, and sleep consultations before closing shortly after the "
                "[[Mizukawa Disappearance Case]].[1]"
            ),
            (
                "The clinic article records public services, property references, and the "
                "closure notice. It does not assert a complete explanation for the "
                "disappearance; those interpretations are discussed through the "
                "[[Investigation into the Mizukawa disappearance]] and supporting records."
            ),
        ],
        "infobox": {
            "title": "Shirohane Clinic",
            "imageCaption": "Fictional municipal facade photograph, archive copy",
            "fields": [
                {"label": "Founded", "value": "1974"},
                {"label": "Closed", "value": "24 September 1998"},
                {"label": "Location", "value": "West edge of [[Mizukawa Town]]"},
                {"label": "Purpose", "value": "Community clinic and sleep consultations"},
                {"label": "Related locations", "value": "[[West Ridge Service Road]]; archive shed parcel"},
                {"label": "Related records", "value": "[[Shirohane Clinic closure notice]]"},
            ],
        },
        "sections": [
            {
                "heading": "Establishment",
                "paragraphs": [
                    (
                        "The clinic opened in 1974 as a small private practice serving the "
                        "west ridge and river-terrace neighborhoods. Municipal directories "
                        "list it as a clinic rather than a hospital, with two examination "
                        "rooms and a rear service entrance facing older agricultural land.[2]"
                    ),
                    (
                        "Its position made it useful to families who lived above the flood "
                        "plain, especially during winter road closures. Older advertisements "
                        "presented the clinic as modest and local: vaccination mornings, "
                        "school checkups, and general consultations. This ordinary public "
                        "profile is one reason later records are treated cautiously; the "
                        "clinic was not a dramatic institution in public life before 1998."
                    )
                ],
            },
            {
                "heading": "Services",
                "paragraphs": [
                    (
                        "Public services included vaccinations, health checks, and sleep "
                        "consultations advertised through school and community circulars. "
                        "Former residents later remembered evening appointments in the "
                        "summer of 1998, although the surviving public appointment sheets "
                        "are incomplete."
                    ),
                    (
                        "The sleep consultation program appears in three forms: a clinic "
                        "notice, a school health circular, and a municipal health-services "
                        "directory. None of those forms explains the program in detail. "
                        "WikiTheory therefore treats the program as a documented service, "
                        "not as proof of any single theory about the disappearance."
                    )
                ],
            },
            {
                "heading": "Closure",
                "paragraphs": [
                    (
                        "Shirohane Clinic closed one week after Kuroda disappeared. The "
                        "official notice cited storm damage and debt, but the estimate "
                        "attached to the notice was shorter than comparable flood claims "
                        "from the same week.[3] The discrepancy is summarized in "
                        "[[Shirohane Clinic closure notice]]."
                    )
                ],
            },
            {
                "heading": "Records and ownership",
                "paragraphs": [
                    (
                        "The rear parcel behind the clinic bordered land associated with "
                        "the [[Mizukawa Folklore Preservation Society]]. Later indexes "
                        "refer to an archive shed, festival banner storage, and a shared "
                        "service lane. These property details are documented more fully in "
                        "[[Folklore Preservation Society land records]]."
                    ),
                    (
                        "The same indexes show why the clinic became difficult to separate "
                        "from surrounding organizations after the case. A health office file, "
                        "a society parcel card, and a service-road maintenance note describe "
                        "adjacent spaces with different administrative labels. Later editors "
                        "often disagree about whether that overlap reflects concealment or "
                        "the untidy filing habits of a small town."
                    )
                ],
            },
            {
                "heading": "Connection to later inquiries",
                "paragraphs": [
                    (
                        "The clinic appears in the case file because of a short telephone "
                        "log, a lane sighting, and its rapid closure. None of those details "
                        "alone resolves the case, but together they made the clinic a central "
                        "node in later document-based theories."
                    ),
                    (
                        "The clinic entry therefore links outward to the closure notice, "
                        "property records, and investigation overview instead of presenting "
                        "a single conclusion. That division mirrors the archive itself, where "
                        "health records, land records, and police-adjacent notes were held "
                        "under separate headings."
                    ),
                    (
                        "This structure also keeps routine medical history separate from "
                        "later suspicion, a distinction repeatedly requested in fictional "
                        "editorial notes."
                    )
                ],
            },
            {
                "heading": "See also",
                "paragraphs": [
                    (
                        "[[Mizukawa Disappearance Case]]; [[Shirohane Clinic closure notice]]; "
                        "[[West Ridge Service Road]]; [[Folklore Preservation Society land records]]."
                    )
                ],
            },
        ],
        "links": [
            "Mizukawa Town",
            "Mizukawa Disappearance Case",
            "Shirohane Clinic closure notice",
            "West Ridge Service Road",
            "Mizukawa Folklore Preservation Society",
            "Folklore Preservation Society land records",
            "Investigation into the Mizukawa disappearance",
        ],
        "clues": ["Shirohane Clinic closed one week after Emi Kuroda vanished."],
        "references": [
            "Mizukawa Municipal Directory, health services list, 1974-1998.",
            "West Ridge Property Index, service-lane appendix.",
            "Shirohane Clinic Closure Notice, archived copy, October 1998.",
        ],
        "externalLinks": ["WikiTheory archive portal: Shirohane files"],
        "categories": ["Organizations", "Mizukawa Town", "1998 incidents", "Fictional archive records"],
    },
    "mizukawa town": {
        "title": "Mizukawa Town",
        "articleType": "place",
        "summary": (
            "A fictional Kawabe River valley town known in WikiTheory for flood records, "
            "local archives, and the 1998 disappearance case."
        ),
        "leadParagraphs": [
            (
                "Mizukawa Town is a small fictional municipality in the Kawabe River valley, "
                "bordered by cedar hills, rice terraces, and older service roads. In local "
                "records it was known for paper lantern workshops and a summer archive before "
                "the 1998 flood season changed its public reputation.[1]"
            ),
            (
                "The town page functions as a place article. It summarizes geography and "
                "institutions, while the specific disappearance inquiry is handled under "
                "[[Mizukawa Disappearance Case]] and related record pages."
            ),
        ],
        "infobox": {
            "title": "Mizukawa Town",
            "imageCaption": "Fictional overview map from the municipal archive",
            "fields": [
                {"label": "Location", "value": "Kawabe River valley"},
                {"label": "Region", "value": "Northern river terraces"},
                {"label": "Known for", "value": "1998 flood records and local archive disputes"},
                {"label": "Nearby landmarks", "value": "Kawabe River; [[West Ridge Service Road]]"},
                {"label": "Related incidents", "value": "[[Mizukawa Disappearance Case]]"},
            ],
        },
        "sections": [
            {
                "heading": "Geography",
                "paragraphs": [
                    (
                        "The town is arranged along the Kawabe River, with lower streets near "
                        "the depot and higher lanes along the west ridge. The geography matters "
                        "in case records because a small change in road status could alter "
                        "whether the clinic lane was reachable during heavy rain."
                    ),
                    (
                        "Older maps divide the town into three practical zones: the river "
                        "terrace, the depot streets, and the west ridge. Public notices from "
                        "1998 use those zones inconsistently, which later made witness "
                        "summaries harder to compare. A phrase such as west road could refer "
                        "to the service road, the clinic lane, or the higher agricultural "
                        "track depending on the office that wrote it."
                    )
                ],
            },
            {
                "heading": "History",
                "paragraphs": [
                    (
                        "Before 1998, Mizukawa appeared mainly in regional directories as a "
                        "market town with lantern workshops, school sports notices, and a "
                        "modest folklore collection. The public archive grew from volunteer "
                        "collecting rather than from a large municipal museum."
                    ),
                    (
                        "That volunteer archive culture shaped the records that survive. "
                        "Festival programs, school clippings, oral-history forms, and land "
                        "cards were sometimes stored together because the same local families "
                        "maintained them. The overlap is useful to readers, but it also means "
                        "that later catalog headings can imply connections that original "
                        "documents did not state directly."
                    )
                ],
            },
            {
                "heading": "Local institutions",
                "paragraphs": [
                    (
                        "Important local institutions include the [[Mizukawa Municipal "
                        "Archive]], [[Mizukawa Folklore Preservation Society]], Mizukawa "
                        "North High School, and the former [[Shirohane Clinic]]. Their records "
                        "overlap more often than their public missions suggest."
                    )
                ],
            },
            {
                "heading": "1998 flood",
                "paragraphs": [
                    (
                        "The 1998 flood affected transport, telephone service, and emergency "
                        "shelters. It also produced records later used to explain delays in "
                        "the disappearance search. The weather and response documents are "
                        "covered in [[Kawabe River Weather Report]] and [[1998 Mizukawa flood inquiry]]."
                    )
                ],
            },
            {
                "heading": "Public records",
                "paragraphs": [
                    (
                        "Municipal papers from the late 1990s include land transfers, service "
                        "road maintenance logs, flood notices, and a small number of redacted "
                        "police bulletins. The archive's later decision to index several "
                        "files together contributed to renewed interest in the case."
                    ),
                    (
                        "The most cited index is the cabinet 7 transfer sheet, which placed "
                        "weather notes, clinic paperwork, and society parcel cards near one "
                        "another. The sheet is an archive convenience rather than a confession "
                        "of related events, but it gave later contributors a path through "
                        "records that had previously been searched one office at a time."
                    )
                ],
            },
            {
                "heading": "Related incidents",
                "paragraphs": [
                    (
                        "Mizukawa is most often linked with the disappearance of [[Emi Kuroda]], "
                        "but its fictional archive also contains older flood and folklore "
                        "entries that provide context rather than direct explanation."
                    ),
                    (
                        "The town article therefore acts as a map of institutions and routes. "
                        "Readers can move from the civic overview to the clinic, weather "
                        "report, archive, and society records without treating the town "
                        "itself as a single cause of the case. That distinction is important "
                        "because many later theories rely on geography while disagreeing "
                        "about intent."
                    )
                ],
            },
        ],
        "links": [
            "Mizukawa Disappearance Case",
            "Mizukawa Municipal Archive",
            "Mizukawa Folklore Preservation Society",
            "Shirohane Clinic",
            "West Ridge Service Road",
            "Kawabe River Weather Report",
            "1998 Mizukawa flood inquiry",
            "Emi Kuroda",
        ],
        "clues": ["The folklore society owned the land behind the clinic."],
        "references": [
            "Mizukawa Municipal Archive, town directory, 1998 edition.",
            "Kawabe Valley Survey Office, road and river terrace index.",
            "Mizukawa Community Newsletter, flood-season issue, October 1998.",
        ],
        "externalLinks": ["WikiTheory archive portal: Mizukawa place index"],
        "categories": ["Places", "Mizukawa Town", "Kawabe River valley", "Fictional archive records"],
    },
    "mizukawa folklore preservation society": {
        "title": "Mizukawa Folklore Preservation Society",
        "articleType": "organization",
        "summary": (
            "A local archive group whose pamphlets and land records became entangled with "
            "later readings of the Mizukawa case."
        ),
        "leadParagraphs": [
            (
                "The Mizukawa Folklore Preservation Society was founded in 1956 to collect "
                "songs, festival notes, and oral histories from the Kawabe River valley. "
                "Its records were small and irregular, but several were later cited in "
                "connection with the [[Mizukawa Disappearance Case]].[1]"
            ),
            (
                "The society page distinguishes folklore material from property records. "
                "The former shaped local rumor; the latter created a documented connection "
                "between society officers, storage parcels, and land near [[Shirohane Clinic]]."
            ),
        ],
        "infobox": {
            "title": "Mizukawa Folklore Preservation Society",
            "imageCaption": "Fictional newsletter masthead, 1978",
            "fields": [
                {"label": "Founded", "value": "1956"},
                {"label": "Status", "value": "Dormant volunteer society"},
                {"label": "Headquarters", "value": "[[Mizukawa Town]]"},
                {"label": "Purpose", "value": "Folklore collection and festival records"},
                {"label": "Related records", "value": "[[Folklore Preservation Society land records]]"},
            ],
        },
        "sections": [
            {
                "heading": "Establishment",
                "paragraphs": [
                    (
                        "The society began as a volunteer association attached to lantern "
                        "festivals and school history projects. Its minutes describe oral "
                        "history work, storage of banners, and publication of small pamphlets "
                        "rather than formal research."
                    ),
                    (
                        "Early officers were teachers, shop owners, and retirees who wanted "
                        "to preserve songs before families left the river valley. The society "
                        "had no large staff, and its records often combine meeting notes with "
                        "receipts, parcel references, and festival correspondence. This mixed "
                        "paper trail later made the organization easy to overstate and hard "
                        "to dismiss."
                    )
                ],
            },
            {
                "heading": "Activities",
                "paragraphs": [
                    (
                        "Members collected stories about ridge bells, river lights, and "
                        "unreliable paths after storms. The best-known pamphlet, [[Bells on "
                        "the West Ridge]], later drew attention because [[Emi Kuroda]] had "
                        "mentioned it before the disappearance."
                    ),
                    (
                        "The pamphlets were usually short, unsigned, and sold or distributed "
                        "at local events. They mixed older oral accounts with practical notes "
                        "about paths, shrines, and weather-damaged bridges. In the article "
                        "network, those pamphlets matter less as supernatural claims than as "
                        "evidence of which west ridge locations were familiar to residents."
                    )
                ],
            },
            {
                "heading": "Records and ownership",
                "paragraphs": [
                    (
                        "The society controlled or co-signed several small parcels, including "
                        "one behind Shirohane Clinic. Public minutes describe storage use, "
                        "but property indexes show access from the clinic lane and the "
                        "[[West Ridge Service Road]].[2]"
                    ),
                    (
                        "The property records include routine details: repairs to a shed roof, "
                        "storage of lantern frames, and access permissions during festival "
                        "weeks. Their later importance comes from geography rather than from "
                        "their wording. A parcel described as harmless storage still sat at "
                        "a point where clinic, society, and service-road records overlapped."
                    )
                ],
            },
            {
                "heading": "Connection to later inquiries",
                "paragraphs": [
                    (
                        "After 1998, document-focused researchers argued that the society's "
                        "folklore reputation distracted attention from ordinary land and "
                        "storage records. Other editors caution that owning a parcel does not "
                        "by itself establish motive or a complete account."
                    ),
                    (
                        "The society is therefore treated as an archive node, not as a solved "
                        "answer. Its pages point readers toward land records, the clinic, and "
                        "municipal indexing practices while leaving questions of intent to "
                        "the investigation and contribution review systems."
                    ),
                    (
                        "Several later contributors also note that folklore language can make "
                        "ordinary paperwork seem more mysterious than it is. The article keeps "
                        "those traditions visible because they shaped witness memory and local "
                        "press coverage, but it separates them from the property cards that "
                        "can be checked against municipal indexes."
                    ),
                    (
                        "That separation gives the page its main editorial role. It preserves "
                        "the society as a plausible source of misleading local language while "
                        "directing concrete claims to dated documents, named parcels, and "
                        "archive custody notes."
                    )
                ],
            },
            {
                "heading": "See also",
                "paragraphs": [
                    (
                        "[[Folklore Preservation Society land records]]; [[Bells on the West "
                        "Ridge]]; [[Shirohane Clinic]]; [[Mizukawa Municipal Archive]]."
                    )
                ],
            },
        ],
        "links": [
            "Mizukawa Disappearance Case",
            "Mizukawa Town",
            "Shirohane Clinic",
            "Folklore Preservation Society land records",
            "Bells on the West Ridge",
            "West Ridge Service Road",
            "Mizukawa Municipal Archive",
        ],
        "clues": [],
        "references": [
            "Mizukawa Folklore Preservation Society, annual minutes, 1956-1998.",
            "Mizukawa Municipal Archive, parcel ledger cross-reference, cabinet 7.",
            "Community Folklore Circular, summer issue, 1997.",
        ],
        "externalLinks": ["WikiTheory archive portal: folklore society papers"],
        "categories": ["Organizations", "Local folklore", "Mizukawa Town", "Fictional archive records"],
    },
    "kawabe river weather report": {
        "title": "Kawabe River Weather Report",
        "articleType": "document",
        "summary": (
            "A flood bulletin used in the official explanation of the 1998 disappearance "
            "and later disputed because of revisions to its archive copy."
        ),
        "leadParagraphs": [
            (
                "The Kawabe River Weather Report is the common name for a regional flood "
                "bulletin covering the night of 17 September 1998. The report is frequently "
                "cited because the official explanation of the [[Mizukawa Disappearance "
                "Case]] relied on difficult weather and road closures.[1]"
            ),
            (
                "The document article records the report's contents and revisions. It does "
                "not decide the full case; it identifies why the bulletin became disputed "
                "and links to the [[1998 Mizukawa flood inquiry]] for broader context."
            ),
        ],
        "infobox": {
            "title": "Kawabe River Weather Report",
            "imageCaption": "Fictional weather bureau form, archive reproduction",
            "fields": [
                {"label": "Date issued", "value": "17 September 1998"},
                {"label": "Office", "value": "Kawabe Regional Weather Desk"},
                {"label": "Archive location", "value": "[[Mizukawa Municipal Archive]]"},
                {"label": "Subject", "value": "River level, rainfall, and road closures"},
                {"label": "Status", "value": "Revised archive copy disputed"},
                {"label": "Related records", "value": "[[1998 Mizukawa flood inquiry]]"},
            ],
        },
        "sections": [
            {
                "heading": "Contents",
                "paragraphs": [
                    (
                        "The report lists rainfall bands, river gauge notes, and road "
                        "closures affecting the Kawabe River valley. The version cited in "
                        "the police summary emphasizes dangerous water levels near Minami "
                        "Bridge and delays to westbound transport.[2]"
                    ),
                    (
                        "The document is not a narrative account. It is a practical bulletin "
                        "with times, abbreviations, and short office notes. Its importance "
                        "comes from how those notes were later used to justify search delays "
                        "and road assumptions in the disappearance file."
                    )
                ],
            },
            {
                "heading": "Publication history",
                "paragraphs": [
                    (
                        "A short radio bulletin was issued during the storm and transcribed "
                        "for the municipal file. The typed archive copy was added later with "
                        "a separate filing stamp. Routine transcription was common during "
                        "flood responses, making the existence of a later copy notable but "
                        "not automatically suspicious."
                    )
                ],
            },
            {
                "heading": "Revisions",
                "paragraphs": [
                    (
                        "The archive copy contains revisions entered two days after the "
                        "disappearance. The changes increase the emphasis on impassable roads "
                        "and severe river conditions. The revisions are the document's main "
                        "importance in WikiTheory, but their full implication is weighed "
                        "against other records rather than settled here.[3]"
                    ),
                    (
                        "A revision by itself can be routine; flood offices often corrected "
                        "forms after emergency work ended. The dispute here is narrower: the "
                        "timing, the wording, and the way the revised copy later supported a "
                        "simple flood explanation. Readers are directed to the flood inquiry "
                        "for the broader comparison."
                    )
                ],
            },
            {
                "heading": "Disputed authenticity",
                "paragraphs": [
                    (
                        "Some editors argue that the revision reflects normal cleanup after "
                        "a chaotic weather event. Others point to its timing, the clinic "
                        "closure, and the missing-person bulletin as reasons to treat the "
                        "copy carefully. The dispute is cross-referenced with [[Archive "
                        "Bulletin 44-B]] and [[Shirohane Clinic closure notice]]."
                    )
                ],
            },
            {
                "heading": "Archive status",
                "paragraphs": [
                    (
                        "The report survives as a typed municipal copy and a shorter radio "
                        "transcript. The comparison table is maintained by the fictional "
                        "archive rather than by the weather desk."
                    ),
                    (
                        "Because neither copy is a complete case file, the page treats the "
                        "report as supporting context and directs broader claims to the flood "
                        "inquiry and investigation pages."
                    )
                ],
            },
            {
                "heading": "See also",
                "paragraphs": [
                    (
                        "[[1998 Mizukawa flood inquiry]]; [[Mizukawa Disappearance Case]]; "
                        "[[Mizukawa Municipal Archive]]; [[Archive Bulletin 44-B]]."
                    )
                ],
            },
        ],
        "links": [
            "Mizukawa Disappearance Case",
            "1998 Mizukawa flood inquiry",
            "Mizukawa Municipal Archive",
            "Archive Bulletin 44-B",
            "Shirohane Clinic closure notice",
            "Mizukawa Town",
        ],
        "clues": [
            "The weather report from the night of the disappearance was edited two days later."
        ],
        "references": [
            "Kawabe Regional Weather Desk, river bulletin, 17 September 1998.",
            "Mizukawa Municipal Archive, flood report transcription sheet.",
            "1998 Mizukawa flood inquiry, appendix C, copy comparison.",
        ],
        "externalLinks": ["WikiTheory archive portal: flood bulletin comparison"],
        "categories": ["Documents", "1998 incidents", "Mizukawa Town", "Fictional archive records"],
    },
    "investigation into the mizukawa disappearance": {
        "title": "Investigation into the Mizukawa disappearance",
        "articleType": "investigation",
        "summary": "Overview of police, civic, and volunteer inquiries following Emi Kuroda's disappearance.",
        "leadParagraphs": [
            (
                "The investigation into the Mizukawa disappearance combined a missing-person "
                "inquiry with flood-response documentation. It drew on witness statements, "
                "school notes, road-closure forms, and partial clinic records."
            )
        ],
        "infobox": {
            "title": "Investigation",
            "fields": [
                {"label": "Opened", "value": "17 September 1998"},
                {"label": "Subject", "value": "[[Emi Kuroda]]"},
                {"label": "Related case", "value": "[[Mizukawa Disappearance Case]]"},
                {"label": "Status", "value": "Unresolved public file"},
            ],
        },
        "sections": [
            {
                "heading": "Scope",
                "paragraphs": [
                    (
                        "The inquiry initially focused on the storm-night search and then "
                        "expanded to document conflicts after archive copies were compared."
                    )
                ],
            },
            {
                "heading": "Documentary record",
                "paragraphs": [
                    (
                        "Frequently cited records include [[Archive Bulletin 44-B]], "
                        "[[Kawabe River Weather Report]], and [[Shirohane Clinic closure notice]]."
                    )
                ],
            },
            {
                "heading": "Competing interpretations",
                "paragraphs": [
                    (
                        "One interpretation sees ordinary flood confusion; another sees a "
                        "cluster of revised or conveniently timed records. WikiTheory keeps "
                        "both interpretations visible until a contributor revision is reviewed."
                    )
                ],
            },
        ],
        "links": [
            "Mizukawa Disappearance Case",
            "Emi Kuroda",
            "Kawabe River Weather Report",
            "Archive Bulletin 44-B",
            "Shirohane Clinic closure notice",
        ],
        "references": [
            "Kawabe Regional Police Office, investigation summary, 1998.",
            "Mizukawa Municipal Archive, case cross-reference sheet.",
        ],
        "categories": ["Unresolved local inquiries", "1998 incidents", "Fictional archive records"],
    },
    "shirohane clinic closure notice": {
        "title": "Shirohane Clinic closure notice",
        "articleType": "document",
        "summary": "Archived notice announcing the closure of Shirohane Clinic one week after Emi Kuroda vanished.",
        "leadParagraphs": [
            (
                "The Shirohane Clinic closure notice is a short public document dated 24 "
                "September 1998. It states that [[Shirohane Clinic]] would close because of "
                "storm damage and debt, but the attached estimate is unusually brief."
            )
        ],
        "infobox": {
            "title": "Closure notice",
            "fields": [
                {"label": "Date issued", "value": "24 September 1998"},
                {"label": "Author", "value": "[[Shirohane Clinic]] administration"},
                {"label": "Archive location", "value": "[[Mizukawa Municipal Archive]]"},
                {"label": "Subject", "value": "Clinic closure after 1998 storm"},
            ],
        },
        "sections": [
            {
                "heading": "Contents",
                "paragraphs": [
                    (
                        "The notice gives a practical explanation for closure and asks "
                        "patients to request records by post. It does not mention the "
                        "[[Mizukawa Disappearance Case]]."
                    )
                ],
            },
            {
                "heading": "Disputed authenticity",
                "paragraphs": [
                    (
                        "The notice is not considered forged, but editors dispute whether "
                        "the stated damage explains the timing. The related property and "
                        "service-lane records are handled on separate pages."
                    )
                ],
            },
        ],
        "links": ["Shirohane Clinic", "Mizukawa Municipal Archive", "Mizukawa Disappearance Case"],
        "references": ["Shirohane Clinic Closure Notice, archived copy, October 1998."],
        "categories": ["Documents", "Organizations", "1998 incidents"],
    },
    "emi kuroda's final known movements": {
        "title": "Emi Kuroda's final known movements",
        "articleType": "timeline",
        "summary": "A reconstruction of confirmed and disputed sightings before Emi Kuroda disappeared.",
        "leadParagraphs": [
            (
                "Emi Kuroda's final known movements are reconstructed from school records, "
                "witness notes, and later archive comparisons. The page separates confirmed "
                "events from disputed westward sightings."
            )
        ],
        "infobox": {
            "title": "Final known movements",
            "fields": [
                {"label": "Date", "value": "17 September 1998"},
                {"label": "Person", "value": "[[Emi Kuroda]]"},
                {"label": "Related route", "value": "[[West Ridge Service Road]]"},
                {"label": "Case", "value": "[[Mizukawa Disappearance Case]]"},
            ],
        },
        "sections": [
            {
                "heading": "Chronology",
                "paragraphs": [
                    (
                        "Kuroda left school during heavy rain, was placed near the depot in "
                        "early statements, and was later associated with the clinic lane by "
                        "a disputed witness summary."
                    )
                ],
            },
            {
                "heading": "Documented gaps",
                "paragraphs": [
                    (
                        "The main gap is the interval between the depot sighting and the "
                        "first formal missing-person call. That gap overlaps with road "
                        "conditions described in the [[Kawabe River Weather Report]]."
                    )
                ],
            },
        ],
        "links": ["Emi Kuroda", "Mizukawa Disappearance Case", "West Ridge Service Road", "Kawabe River Weather Report"],
        "references": ["Kawabe Regional Police Office, witness-summary timeline, 1998."],
        "categories": ["Timelines", "Missing person cases", "1998 incidents"],
    },
    "1998 mizukawa flood inquiry": {
        "title": "1998 Mizukawa flood inquiry",
        "articleType": "investigation",
        "summary": "A civic review of flood response records later used to reassess the disappearance timeline.",
        "leadParagraphs": [
            (
                "The 1998 Mizukawa flood inquiry reviewed evacuation notices, road closures, "
                "and river bulletins from the storm week. It became relevant to the "
                "[[Mizukawa Disappearance Case]] because the search timeline depended on "
                "those records."
            )
        ],
        "infobox": {
            "title": "Flood inquiry",
            "fields": [
                {"label": "Opened", "value": "1999"},
                {"label": "Subject", "value": "Mizukawa flood response"},
                {"label": "Key record", "value": "[[Kawabe River Weather Report]]"},
            ],
        },
        "sections": [
            {
                "heading": "Scope",
                "paragraphs": [
                    (
                        "The inquiry compared weather bulletins, municipal closure notices, "
                        "and evacuation room logs. It did not reopen the missing-person case "
                        "directly."
                    )
                ],
            },
            {
                "heading": "Documentary record",
                "paragraphs": [
                    (
                        "Appendix C compares the original flood bulletin with the revised "
                        "copy held by the municipal archive."
                    )
                ],
            },
        ],
        "links": ["Mizukawa Disappearance Case", "Kawabe River Weather Report", "Mizukawa Municipal Archive"],
        "references": ["Mizukawa Civic Review Committee, flood inquiry appendix, 1999."],
        "categories": ["Unresolved local inquiries", "1998 incidents", "Documents"],
    },
    "west ridge service road": {
        "title": "West Ridge Service Road",
        "articleType": "place",
        "summary": "A narrow road above Mizukawa linking the clinic lane with older storage parcels.",
        "leadParagraphs": [
            (
                "West Ridge Service Road is a narrow route above [[Mizukawa Town]]. It is "
                "cited in case timelines because it connected [[Shirohane Clinic]], storage "
                "land, and higher ground during the 1998 storm."
            )
        ],
        "infobox": {
            "title": "West Ridge Service Road",
            "fields": [
                {"label": "Location", "value": "West ridge above [[Mizukawa Town]]"},
                {"label": "Known for", "value": "Disputed access route in 1998 records"},
                {"label": "Related places", "value": "[[Shirohane Clinic]]; society archive shed"},
            ],
        },
        "sections": [
            {
                "heading": "Geography",
                "paragraphs": [
                    (
                        "The road runs above the lower river terrace and avoids some flood "
                        "zones, though washouts were reported on side lanes."
                    )
                ],
            },
            {
                "heading": "Related incidents",
                "paragraphs": [
                    (
                        "Later timelines mention the road when discussing whether movement "
                        "between the depot, clinic lane, and storage parcel was possible."
                    )
                ],
            },
        ],
        "links": ["Mizukawa Town", "Shirohane Clinic", "Mizukawa Disappearance Case", "Folklore Preservation Society land records"],
        "references": ["Kawabe Valley Survey Office, west ridge road index, 1998."],
        "categories": ["Places", "Mizukawa Town", "Fictional archive records"],
    },
    "kuroda family statement": {
        "title": "Kuroda family statement",
        "articleType": "document",
        "summary": "Public request from Emi Kuroda's family asking residents to report ordinary sightings.",
        "leadParagraphs": [
            (
                "The Kuroda family statement was a public notice released after [[Emi Kuroda]] "
                "was reported missing. It asked residents to send practical information and "
                "discouraged rumor."
            )
        ],
        "infobox": {
            "title": "Family statement",
            "fields": [
                {"label": "Date issued", "value": "September 1998"},
                {"label": "Author", "value": "Kuroda family"},
                {"label": "Subject", "value": "[[Emi Kuroda]]"},
            ],
        },
        "sections": [
            {
                "heading": "Contents",
                "paragraphs": [
                    (
                        "The statement lists clothing, routes, and contacts, then asks "
                        "readers not to confuse searchers with copied rumors."
                    )
                ],
            },
            {
                "heading": "Later references",
                "paragraphs": [
                    (
                        "A later family request sought access to weather and clinic records, "
                        "which linked the statement to document-focused inquiry pages."
                    )
                ],
            },
        ],
        "links": ["Emi Kuroda", "Mizukawa Disappearance Case", "Kawabe River Weather Report", "Shirohane Clinic"],
        "references": ["Kuroda Family Statement, clipping archive copy, 1998."],
        "categories": ["Documents", "Missing person cases", "1998 incidents"],
    },
    "mizukawa municipal archive": {
        "title": "Mizukawa Municipal Archive",
        "articleType": "organization",
        "summary": "Local archive holding flood, property, school, and police-adjacent copies used by WikiTheory editors.",
        "leadParagraphs": [
            (
                "The Mizukawa Municipal Archive is the fictional civic archive where many "
                "late-1990s case records are cataloged. Its cabinet indexes connect flood "
                "forms, property notes, and copied police bulletins."
            )
        ],
        "infobox": {
            "title": "Mizukawa Municipal Archive",
            "fields": [
                {"label": "Location", "value": "[[Mizukawa Town]]"},
                {"label": "Purpose", "value": "Municipal records and community archive"},
                {"label": "Known holdings", "value": "[[Kawabe River Weather Report]]; [[Archive Bulletin 44-B]]"},
            ],
        },
        "sections": [
            {
                "heading": "Collections",
                "paragraphs": [
                    (
                        "Relevant holdings include flood response sheets, land records, "
                        "closure notices, and a small set of redacted police-adjacent copies."
                    )
                ],
            },
            {
                "heading": "Connection to later inquiries",
                "paragraphs": [
                    (
                        "The archive's 2002 cabinet index placed several records near each "
                        "other, encouraging contributors to compare documents that had not "
                        "originally been filed as one case file."
                    )
                ],
            },
        ],
        "links": ["Mizukawa Town", "Kawabe River Weather Report", "Archive Bulletin 44-B", "Folklore Preservation Society land records"],
        "references": ["Mizukawa Municipal Archive, public catalog introduction, 2002."],
        "categories": ["Organizations", "Fictional archive records", "Mizukawa Town"],
    },
    "folklore preservation society land records": {
        "title": "Folklore Preservation Society land records",
        "articleType": "record",
        "summary": "Property records showing parcels and storage rights associated with the folklore society.",
        "leadParagraphs": [
            (
                "The Folklore Preservation Society land records are property cards and "
                "transfer notes associated with the [[Mizukawa Folklore Preservation Society]]. "
                "They are important because one parcel bordered [[Shirohane Clinic]]."
            )
        ],
        "infobox": {
            "title": "Land records",
            "fields": [
                {"label": "Date range", "value": "1978-1998"},
                {"label": "Custodian", "value": "[[Mizukawa Municipal Archive]]"},
                {"label": "Related land", "value": "Clinic rear parcel and archive shed"},
            ],
        },
        "sections": [
            {
                "heading": "Contents",
                "paragraphs": [
                    (
                        "The cards list storage rights, festival banner use, and access notes "
                        "from the clinic lane to older ridge paths."
                    )
                ],
            },
            {
                "heading": "Referenced properties",
                "paragraphs": [
                    (
                        "The most cited property is a rear parcel behind Shirohane Clinic, "
                        "later associated with competing interpretations of the case."
                    )
                ],
            },
        ],
        "links": ["Mizukawa Folklore Preservation Society", "Shirohane Clinic", "West Ridge Service Road", "Mizukawa Municipal Archive"],
        "references": ["Mizukawa Municipal Archive, parcel ledger cross-reference, cabinet 7."],
        "categories": ["Records", "Local folklore", "Mizukawa Town"],
    },
    "archive bulletin 44-b": {
        "title": "Archive Bulletin 44-B",
        "articleType": "document",
        "summary": "Partially redacted missing-person bulletin copied into the municipal archive.",
        "leadParagraphs": [
            (
                "Archive Bulletin 44-B is a partially redacted missing-person bulletin "
                "associated with the [[Mizukawa Disappearance Case]]. It is cited for its "
                "timeline notes and cross-references to flood records."
            )
        ],
        "infobox": {
            "title": "Bulletin 44-B",
            "fields": [
                {"label": "Date issued", "value": "September 1998"},
                {"label": "Office", "value": "Kawabe Regional Police Office"},
                {"label": "Archive location", "value": "[[Mizukawa Municipal Archive]]"},
                {"label": "Status", "value": "Partially redacted copy"},
            ],
        },
        "sections": [
            {
                "heading": "Contents",
                "paragraphs": [
                    (
                        "The bulletin summarizes witness statements, road closures, and "
                        "search assignments. Several names and one time range are redacted "
                        "in the public copy."
                    )
                ],
            },
            {
                "heading": "Archive status",
                "paragraphs": [
                    (
                        "The municipal copy is not the originating police file. WikiTheory "
                        "therefore treats the bulletin as a useful index rather than a full "
                        "investigation record."
                    )
                ],
            },
        ],
        "links": ["Mizukawa Disappearance Case", "Kawabe River Weather Report", "Mizukawa Municipal Archive", "Emi Kuroda"],
        "references": ["Kawabe Regional Police Office, Missing Persons Bulletin 44-B, public copy."],
        "categories": ["Documents", "Missing person cases", "Fictional archive records"],
    },
}


SEED_ARTICLES.update(STRUCTURED_SEED_ARTICLES)


def normalize_title(title: str) -> str:
    cleaned = " ".join(str(title or "").strip().split())
    return cleaned.lower()


def display_title(title: str) -> str:
    cleaned = " ".join(str(title or "").strip().split())
    if not cleaned:
        return MAIN_ARTICLE
    return cleaned


def read_hidden_canon() -> str:
    return CANON_PATH.read_text(encoding="utf-8")


def _load_generated_articles() -> dict[str, dict[str, Any]]:
    if not ARTICLES_PATH.exists():
        return {}

    try:
        with ARTICLES_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}
    return {
        normalize_title(article.get("title", key)): normalize_article(article, key)
        for key, article in data.items()
        if isinstance(article, dict)
    }


def _write_generated_articles(articles: dict[str, dict[str, Any]]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    with ARTICLES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(articles, handle, indent=2, ensure_ascii=False)


def get_article(title: str) -> dict[str, Any] | None:
    key = normalize_title(title)
    if key in SEED_ARTICLES:
        return normalize_article(SEED_ARTICLES[key], title)
    return _load_generated_articles().get(key)


def save_article(article: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_article(article, article.get("title", "Untitled Article"))
    articles = _load_generated_articles()
    articles[normalize_title(normalized["title"])] = normalized
    _write_generated_articles(articles)
    return normalized


def list_articles() -> list[dict[str, Any]]:
    merged = {
        key: normalize_article(value, value.get("title", key))
        for key, value in SEED_ARTICLES.items()
    }
    merged.update(_load_generated_articles())
    return sorted(merged.values(), key=lambda article: article.get("title", ""))


def getArticle(title: str) -> dict[str, Any] | None:
    return get_article(title)


def saveArticle(article: dict[str, Any]) -> dict[str, Any]:
    return save_article(article)


def listArticles() -> list[dict[str, Any]]:
    return list_articles()


def get_watchlist() -> list[dict[str, str]]:
    return sorted(
        _load_watchlist().values(),
        key=lambda item: item.get("title", ""),
    )


def add_to_watchlist(title: str) -> dict[str, str]:
    watchlist = _load_watchlist()
    clean_title = display_title(title)
    key = normalize_title(clean_title)
    current = watchlist.get(key, {})
    watchlist[key] = {
        "title": clean_title,
        "lastViewed": current.get("lastViewed") or timestamp_label(),
        "notes": current.get("notes", ""),
    }
    _write_watchlist(watchlist)
    return watchlist[key]


def remove_from_watchlist(title: str) -> None:
    watchlist = _load_watchlist()
    watchlist.pop(normalize_title(title), None)
    _write_watchlist(watchlist)


def is_watched(title: str) -> bool:
    return normalize_title(title) in _load_watchlist()


def mark_watched_viewed(title: str) -> None:
    watchlist = _load_watchlist()
    key = normalize_title(title)
    if key not in watchlist:
        return
    watchlist[key]["lastViewed"] = timestamp_label()
    _write_watchlist(watchlist)


def getWatchlist() -> list[dict[str, str]]:
    return get_watchlist()


def addToWatchlist(title: str) -> dict[str, str]:
    return add_to_watchlist(title)


def removeFromWatchlist(title: str) -> None:
    remove_from_watchlist(title)


def isWatched(title: str) -> bool:
    return is_watched(title)


def get_contribution_targets() -> list[dict[str, Any]]:
    return [public_contribution_target(target) for target in CONTRIBUTION_TARGETS]


def get_contribution_target(target_id: str) -> dict[str, Any] | None:
    for target in CONTRIBUTION_TARGETS:
        if target["id"] == target_id:
            return dict(target)
    return None


def public_contribution_target(target: dict[str, Any]) -> dict[str, Any]:
    public = dict(target)
    public.pop("canonAnswer", None)
    return public


def article_exists(title: str) -> bool:
    return get_article(title) is not None


def is_seed_article(title: str) -> bool:
    return normalize_title(title) in SEED_ARTICLES


def is_generated_article(title: str) -> bool:
    key = normalize_title(title)
    return key not in SEED_ARTICLES and key in _load_generated_articles()


def _load_watchlist() -> dict[str, dict[str, str]]:
    if not WATCHLIST_PATH.exists():
        return {}

    try:
        with WATCHLIST_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    watchlist: dict[str, dict[str, str]] = {}
    for key, item in data.items():
        if not isinstance(item, dict):
            continue
        title = display_title(item.get("title") or key)
        watchlist[normalize_title(title)] = {
            "title": title,
            "lastViewed": str(item.get("lastViewed") or ""),
            "notes": str(item.get("notes") or ""),
        }
    return watchlist


def _write_watchlist(watchlist: dict[str, dict[str, str]]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    with WATCHLIST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(watchlist, handle, indent=2, ensure_ascii=False)


def timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def plan_article_role(title: str) -> str:
    key = normalize_title(title)
    if "final known movements" in key or "timeline" in key or "chronology" in key:
        return "timeline"
    if "investigation" in key or "inquiry" in key or "search" in key:
        return "investigation"
    if "land records" in key or key.endswith(" records") or "ledger" in key:
        return "record"
    if any(term in key for term in ["report", "notice", "statement", "bulletin", "record"]):
        return "document"
    if "case" in key or "disappearance" in key:
        return "case"
    if any(term in key for term in ARTICLE_ROLE_HINTS["person"]):
        return "person"
    if any(term in key for term in ARTICLE_ROLE_HINTS["place"]):
        return "place"
    if any(term in key for term in ARTICLE_ROLE_HINTS["organization"]):
        return "organization"
    if any(term in key for term in ARTICLE_ROLE_HINTS["theory"]):
        return "theory"
    return "document"


def normalize_article_type(value: Any, title: str) -> str:
    article_type = str(value or "").strip().lower()
    if article_type == "event":
        return "case" if "disappear" in normalize_title(title) or "case" in normalize_title(title) else "investigation"
    if article_type == "rumor":
        return "theory"
    if article_type == "object":
        return "record"
    if article_type in ARTICLE_TYPES:
        return article_type
    return plan_article_role(title)


def section_template_for(article_type: str) -> list[str]:
    return SECTION_TEMPLATES.get(article_type, SECTION_TEMPLATES["document"])


def article_word_target(article_type: str) -> str:
    if article_type == "case":
        return "900-1400 words"
    if article_type in {"person", "place", "organization", "investigation"}:
        return "500-900 words"
    if article_type in {"document", "record", "timeline", "theory"}:
        return "400-700 words"
    return "200-350 words only if the page is intentionally incomplete"


def reveal_budget_for_role(article_type: str) -> str:
    budgets = {
        "case": "Broad overview only. Link outward for details and do not state a final explanation.",
        "person": "Personal context and documented movements. Avoid resolving the whole case.",
        "place": "Geography, institutions, and records. Mention the case only as local context.",
        "organization": "Institutional connection and records. Do not state a complete motive.",
        "document": "One suspicious detail or conflict. Link to the wider inquiry for interpretation.",
        "record": "Custody, fields, and referenced properties. Avoid explaining the whole case.",
        "investigation": "Conflicting interpretations and document trail. Keep the answer unsettled.",
        "timeline": "Chronology and gaps. Do not infer more than the records support.",
        "theory": "Summarize support and objections without confirming the hidden canon.",
    }
    return budgets.get(article_type, budgets["document"])


def normalize_article(article: dict[str, Any], fallback_title: str) -> dict[str, Any]:
    title = display_title(article.get("title") or fallback_title)
    article_type = normalize_article_type(article.get("articleType") or article.get("type"), title)
    summary = str(article.get("summary") or f"A Mizukawa archive entry about {title}.").strip()
    lead_paragraphs = normalize_lead_paragraphs(article, title, summary)
    sections = normalize_sections(article, article_type, title, lead_paragraphs, summary)
    body = article_body_text(lead_paragraphs, sections)
    infobox = normalize_infobox(article.get("infobox"), title, article_type)
    references = _string_list(article.get("references"))
    categories = _string_list(article.get("categories"))
    external_links = _string_list(article.get("externalLinks") or article.get("external_links"))

    explicit_links = article.get("links", [])
    if not isinstance(explicit_links, list):
        explicit_links = []

    linked_texts = [summary, *lead_paragraphs, body]
    linked_texts.extend(field["value"] for field in infobox["fields"])
    text_links = extract_links_from_texts(linked_texts)

    clean_links = []
    for link in [*explicit_links, *text_links]:
        clean_link = display_title(str(link))
        if clean_link and normalize_title(clean_link) != normalize_title(title):
            clean_links.append(clean_link)

    clues = article.get("clues", [])
    if not isinstance(clues, list):
        clues = []

    incomplete_sections = normalize_incomplete_sections(article.get("incompleteSections"))
    incomplete_sections.extend(incomplete_sections_for_article(title))

    normalized = {
        "title": title,
        "type": article_type,
        "articleType": article_type,
        "summary": summary,
        "leadParagraphs": lead_paragraphs,
        "sections": sections,
        "body": body,
        "links": dedupe_titles(clean_links)[:link_limit_for_type(article_type)],
        "clues": [str(clue).strip() for clue in clues if str(clue).strip()][:1],
        "infobox": infobox,
        "references": references,
        "externalLinks": external_links,
        "categories": categories,
        "incompleteSections": dedupe_incomplete_sections(incomplete_sections),
    }
    if not normalized["references"]:
        normalized["references"] = fallback_references(normalized)
    if not normalized["externalLinks"]:
        normalized["externalLinks"] = fallback_external_links(normalized)
    if not normalized["categories"]:
        normalized["categories"] = fallback_categories(normalized)
    return normalized


def normalize_lead_paragraphs(article: dict[str, Any], title: str, summary: str) -> list[str]:
    lead = _string_list(article.get("leadParagraphs") or article.get("lead_paragraphs"))
    if lead:
        return lead[:3]

    body_paragraphs = split_text_paragraphs(str(article.get("body") or ""))
    if body_paragraphs:
        return body_paragraphs[:2]
    return [summary or f"{title} is a short file in the Mizukawa archive."]


def normalize_sections(
    article: dict[str, Any],
    article_type: str,
    title: str,
    lead_paragraphs: list[str],
    summary: str,
) -> list[dict[str, Any]]:
    raw_sections = article.get("sections")
    sections: list[dict[str, Any]] = []
    if isinstance(raw_sections, list):
        for item in raw_sections:
            if not isinstance(item, dict):
                continue
            heading = str(item.get("heading") or item.get("title") or "").strip()
            if not heading or normalize_title(heading) in {"references", "external links", "categories"}:
                continue
            paragraphs = _string_list(item.get("paragraphs"))
            if not paragraphs and str(item.get("body") or item.get("text") or "").strip():
                paragraphs = split_text_paragraphs(str(item.get("body") or item.get("text") or ""))
            if paragraphs:
                sections.append({"heading": heading, "paragraphs": paragraphs[:4]})

    if sections:
        return sections

    body_paragraphs = split_text_paragraphs(str(article.get("body") or ""))
    if body_paragraphs:
        remaining = body_paragraphs[len(lead_paragraphs) :] or body_paragraphs[1:]
    else:
        remaining = []
    if not remaining:
        remaining = [summary or f"{title} has not been fully cataloged."]

    headings = section_template_for(article_type)
    for index, paragraph in enumerate(remaining):
        heading = headings[min(index, len(headings) - 1)]
        if normalize_title(heading) == "see also":
            heading = "Archive status"
        sections.append({"heading": heading, "paragraphs": [paragraph]})
    return sections


def normalize_infobox(value: Any, title: str, article_type: str) -> dict[str, Any]:
    infobox: dict[str, Any] = value if isinstance(value, dict) else {}
    box_title = str(infobox.get("title") or title).strip()
    image_caption = str(infobox.get("imageCaption") or infobox.get("image_caption") or "").strip()
    fields: list[dict[str, str]] = []

    raw_fields = infobox.get("fields")
    if isinstance(raw_fields, list):
        for item in raw_fields:
            if isinstance(item, dict):
                add_infobox_field(fields, item.get("label") or item.get("key"), item.get("value"))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                add_infobox_field(fields, item[0], item[1])

    if not fields:
        for key, field_value in infobox.items():
            if key in {"title", "imageCaption", "image_caption", "fields", "type", "articleType"}:
                continue
            add_infobox_field(fields, key, field_value)

    if not fields:
        defaults = {
            "case": [("Status", "Unresolved"), ("Related archive", "[[Mizukawa Municipal Archive]]")],
            "person": [("Known for", "[[Mizukawa Disappearance Case]]")],
            "place": [("Region", "Kawabe River valley")],
            "organization": [("Status", "Archive entry")],
            "document": [("Archive location", "[[Mizukawa Municipal Archive]]")],
            "record": [("Custodian", "[[Mizukawa Municipal Archive]]")],
            "investigation": [("Status", "Public file incomplete")],
            "timeline": [("Subject", title)],
            "theory": [("Status", "Disputed interpretation")],
        }
        for label, field_value in defaults.get(article_type, defaults["document"]):
            add_infobox_field(fields, label, field_value)

    return {"title": box_title, "imageCaption": image_caption, "fields": fields[:10]}


def add_infobox_field(fields: list[dict[str, str]], label: Any, value: Any) -> None:
    clean_label = str(label or "").strip()
    clean_value = str(value or "").strip()
    if not clean_label or not clean_value:
        return
    if normalize_title(clean_label) in {"type", "article type", "articletype"}:
        return
    fields.append({"label": clean_label, "value": clean_value})


def article_body_text(lead_paragraphs: list[str], sections: list[dict[str, Any]]) -> str:
    paragraphs = [*lead_paragraphs]
    for section in sections:
        paragraphs.extend(_string_list(section.get("paragraphs")))
    return "\n\n".join(paragraphs).strip()


def split_text_paragraphs(body: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body or "") if paragraph.strip()]


def extract_links_from_texts(texts: list[str]) -> list[str]:
    links: list[str] = []
    for text in texts:
        links.extend(extract_links(text))
    return dedupe_titles(links)


def link_limit_for_type(article_type: str) -> int:
    if article_type == "case":
        return 15
    if article_type in {"investigation", "place", "organization", "person"}:
        return 10
    return 8


def extract_links(body: str) -> list[str]:
    links: list[str] = []
    for match in LINK_PATTERN.findall(body or ""):
        target = match.split("|", 1)[0].strip()
        if target:
            links.append(target)
    return dedupe_titles(links)


def incomplete_sections_for_article(title: str) -> list[dict[str, Any]]:
    return [
        {
            "id": target["id"],
            "title": target["sectionTitle"],
            "kind": target["kind"],
            "status": "open",
            "requiredClues": target["requiredClues"],
        }
        for target in CONTRIBUTION_TARGETS
        if normalize_title(target["articleTitle"]) == normalize_title(title)
    ]


def normalize_incomplete_sections(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    sections: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        section_id = str(item.get("id") or slug_from_text(item.get("title", ""))).strip()
        title = str(item.get("title") or item.get("sectionTitle") or "Untitled section").strip()
        status = str(item.get("status") or "open").strip().lower()
        if status not in {"open", "under discussion", "approved", "rejected"}:
            status = "open"
        sections.append(
            {
                "id": section_id,
                "title": title,
                "kind": str(item.get("kind") or "Missing section").strip(),
                "status": status,
                "requiredClues": _string_list(item.get("requiredClues")),
            }
        )
    return sections


def dedupe_incomplete_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for section in sections:
        key = str(section.get("id") or slug_from_text(section.get("title", "")))
        if key and key not in seen:
            seen.add(key)
            result.append(section)
    return result


def slug_from_text(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "section"


def dedupe_titles(titles: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for title in titles:
        clean_title = display_title(title)
        key = normalize_title(clean_title)
        if key and key not in seen:
            seen.add(key)
            result.append(clean_title)
    return result


def related_summaries(title: str, limit: int = 5) -> list[dict[str, Any]]:
    target_key = normalize_title(title)
    target_words = {
        word
        for word in re.findall(r"[a-z0-9]+", target_key)
        if len(word) > 2 and word not in {"the", "and", "case"}
    }

    scored: list[tuple[int, dict[str, Any]]] = []
    for article in list_articles():
        article_key = normalize_title(article["title"])
        if article_key == target_key:
            continue
        article_words = set(re.findall(r"[a-z0-9]+", article_key))
        link_keys = {normalize_title(link) for link in article.get("links", [])}
        score = len(target_words & article_words)
        if target_key in link_keys:
            score += 4
        if any(word in normalize_title(article.get("summary", "")) for word in target_words):
            score += 1
        if score:
            scored.append((score, article))

    if not scored:
        scored = [(1, article) for article in list_articles()[:limit]]

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "title": article["title"],
            "summary": article.get("summary", ""),
            "links": article.get("links", [])[:5],
        }
        for _, article in scored[:limit]
    ]


def generate_article(title: str, discovered_clues: list[str] | None = None) -> dict[str, Any]:
    discovered_clues = discovered_clues or []
    article_title = display_title(title)
    article_role = plan_article_role(article_title)
    payload = {
        "hidden_canon": read_hidden_canon(),
        "article_title": article_title,
        "article_role": article_role,
        "word_target": article_word_target(article_role),
        "section_template": section_template_for(article_role),
        "reveal_budget": reveal_budget_for_role(article_role),
        "related_existing_articles": related_summaries(title),
        "network_targets": [
            "Investigation into the Mizukawa disappearance",
            "Kawabe River Weather Report",
            "Shirohane Clinic closure notice",
            "Emi Kuroda's final known movements",
            "1998 Mizukawa flood inquiry",
            "West Ridge Service Road",
            "Kuroda family statement",
            "Mizukawa Municipal Archive",
            "Folklore Preservation Society land records",
            "Archive Bulletin 44-B",
        ],
        "discovered_clues": discovered_clues[-8:],
        "schema": {
            "title": "Article title",
            "articleType": "case | person | place | organization | document | investigation | theory | timeline | record",
            "summary": "One short summary sentence.",
            "leadParagraphs": ["paragraph 1", "paragraph 2"],
            "infobox": {
                "title": "Displayed infobox title",
                "imageCaption": "optional fictional caption",
                "fields": [
                    {"label": "Date", "value": "17 September 1998"},
                    {"label": "Location", "value": "[[Mizukawa Town]], Kawabe River valley"},
                ],
            },
            "sections": [
                {"heading": "Article-specific heading", "paragraphs": ["paragraph", "paragraph"]}
            ],
            "links": ["Mizukawa Town", "Shirohane Clinic"],
            "clues": ["optional hidden support signal, at most one"],
            "references": ["fictional in-universe citation"],
            "externalLinks": ["fictional in-universe index link"],
            "categories": ["fictional wiki category"],
        },
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You write original fictional wiki entries for a non-graphic mystery game. "
                "Return only valid JSON in the requested schema. Keep continuity with the canon, "
                "related summaries, and the article role. Write like a neutral encyclopedia article: "
                "dense, factual prose, not dramatic or novelistic. Use article-specific headings from "
                "the supplied section template when they fit. Use fictional citation markers such as "
                "[1], [2], and [3] in the prose, and provide matching fictional in-universe references. "
                "Generate a right-side infobox with labels appropriate to the article type; never expose "
                "raw schema labels such as Type. Do not reveal the full mystery in one article. Include "
                "brief summaries of related facts and link to separate pages for details. Follow the "
                "reveal budget exactly. Avoid self-links. Case or overview articles should include "
                "8-15 internal links; smaller pages should include 4-8. Include 2-5 fictional references, "
                "1-3 fictional external links, and 3-6 categories. At most one hidden support signal may "
                "go in clues. No real Wikipedia text, real assets, gore, explicit violence, sexual content, "
                "or self-harm details."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False),
        },
    ]

    data = _chat_json(messages, max_tokens=2200, temperature=0.5)
    return save_article(normalize_article(data, title))


def score_theory(
    theory: str,
    discovered_clues: list[str] | None = None,
    reveal_answer: bool = False,
) -> dict[str, Any]:
    payload = {
        "hidden_canon": read_hidden_canon(),
        "player_theory": theory,
        "discovered_clues": discovered_clues or [],
        "reveal_answer": reveal_answer,
        "response_schema": {
            "accuracy_percentage": 0,
            "got_right": ["brief bullet"],
            "missed": ["brief bullet"],
            "feedback": "spoiler-light unless reveal_answer is true",
            "answer": "only include when reveal_answer is true",
        },
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You judge a player's theory for a fictional mystery game. Return only valid JSON. "
                "Be concise, fair, and non-graphic. If reveal_answer is false, give spoiler-light hints."
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    data = _chat_json(messages, max_tokens=650, temperature=0.2)
    return {
        "accuracy_percentage": _coerce_percentage(data.get("accuracy_percentage", 0)),
        "got_right": _string_list(data.get("got_right")),
        "missed": _string_list(data.get("missed")),
        "feedback": str(data.get("feedback", "")).strip(),
        "answer": str(data.get("answer", "")).strip() if reveal_answer else "",
    }


def review_contribution(
    target_id: str,
    contribution_text: str,
    discovered_clues: list[str] | None = None,
    recently_viewed_articles: list[str] | None = None,
    watched_articles: list[str] | None = None,
    related_article_summaries: list[dict[str, Any]] | None = None,
    current_article_excerpt: str = "",
    edit_summary: str = "",
) -> dict[str, Any]:
    target = get_contribution_target(target_id)
    if not target:
        raise ValueError(f"Unknown contribution target: {target_id}")

    article = get_article(target["articleTitle"])
    related_article = {
        "title": article["title"] if article else target["articleTitle"],
        "summary": article.get("summary", "") if article else "",
        "type": article.get("type", "document") if article else "document",
        "links": article.get("links", [])[:6] if article else [],
    }

    payload = {
        "section_canon_summary": target["canonAnswer"],
        "target_section": public_contribution_target(target),
        "related_article": related_article,
        "recently_viewed_articles": (recently_viewed_articles or [])[-8:],
        "watched_articles": watched_articles or [],
        "related_article_summaries": related_article_summaries or related_summaries(target["articleTitle"]),
        "hidden_support_signals": (discovered_clues or [])[-8:],
        "player_contribution": contribution_text,
        "current_article_excerpt": current_article_excerpt,
        "edit_summary": edit_summary,
        "editor_personas": EDITOR_PERSONAS,
        "response_schema": {
            "decision": "approved | pending | needs_revision | rejected",
            "accuracyScore": 0,
            "canonMatches": ["brief match"],
            "missedPoints": ["brief missing point"],
            "editorComments": [
                {"editor": "ArchivistMori", "comment": "talk page style comment"}
            ],
            "publicStatusText": "Pending review | Approved | Needs revision | Not accepted",
            "prestigeChange": 0,
            "approvedPatch": "optional approved article text",
            "inboxMessage": {
                "from": "Editor name",
                "subject": "Review result",
                "body": "Message text",
            },
        },
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are the fictional WikiTheory editorial review board. Return only valid JSON. "
                "Compare a contributor's article-style revision against the hidden section canon, "
                "current article excerpt, edit summary, recently viewed pages, watched pages, related "
                "article summaries, and target metadata. "
                "Keep feedback in-universe as wiki editorial "
                "discussion. Do not reveal the full hidden answer when rejecting or asking for revision. "
                "Use 2-4 editor persona comments written like talk-page notes. Approve only if the revision is substantially accurate, "
                "neutral in tone, and supported by related pages. Avoid the words clue, clues, correct answer, "
                "mystery solved, guessed right, accuracy score, or game. Keep all content non-graphic."
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    data = _chat_json(messages, max_tokens=850, temperature=0.25)
    return normalize_review_response(data, target, contribution_text)


def _chat_json(messages: list[dict[str, str]], max_tokens: int, temperature: float) -> dict[str, Any]:
    load_dotenv(ROOT_DIR / ".env")
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to src/.env or your shell environment.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("WIKI_MYSTERY_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return _parse_json_object(content)


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        data = json.loads(content[start : end + 1])

    if not isinstance(data, dict):
        raise ValueError("OpenAI response was JSON, but not a JSON object.")
    return data


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_review_response(
    data: dict[str, Any],
    target: dict[str, Any],
    contribution_text: str,
) -> dict[str, Any]:
    decision = str(data.get("decision", "needs_revision")).strip().lower()
    if decision not in {"approved", "pending", "needs_revision", "rejected"}:
        decision = "needs_revision"

    accuracy = _coerce_percentage(data.get("accuracyScore", data.get("accuracy_score", 0)))
    prestige_change = _coerce_signed_int(data.get("prestigeChange", 0))
    if decision == "approved" and prestige_change <= 0:
        prestige_change = 12
    elif decision in {"pending", "needs_revision"} and prestige_change < 0:
        prestige_change = 0
    elif decision == "rejected" and prestige_change > 0:
        prestige_change = 0

    comments = normalize_editor_comments(data.get("editorComments"))
    if not comments:
        comments = fallback_editor_comments(decision, target)

    article_patch = str(data.get("approvedPatch") or data.get("articlePatch") or "").strip()
    if decision == "approved" and not article_patch:
        article_patch = contribution_text.strip()

    inbox = data.get("inboxMessage", {})
    if not isinstance(inbox, dict):
        inbox = {}

    return {
        "decision": decision,
        "accuracyScore": accuracy,
        "canonMatches": _string_list(data.get("canonMatches")),
        "missedPoints": _string_list(data.get("missedPoints")),
        "editorComments": comments[:4],
        "publicStatusText": normalize_public_status_text(data.get("publicStatusText"), decision),
        "prestigeChange": prestige_change,
        "articlePatch": article_patch,
        "inboxMessage": {
            "from": str(inbox.get("from") or "WikiTheory Review Board").strip(),
            "subject": str(inbox.get("subject") or review_subject(decision, target)).strip(),
            "body": str(inbox.get("body") or review_body(decision, target)).strip(),
        },
    }


def normalize_public_status_text(value: Any, decision: str) -> str:
    text = str(value or "").strip()
    if text:
        return text
    return {
        "approved": "Approved",
        "pending": "Pending review",
        "needs_revision": "Needs revision",
        "rejected": "Not accepted",
    }.get(decision, "Pending review")


def normalize_editor_comments(value: Any) -> list[dict[str, str]]:
    comments: list[dict[str, str]] = []
    if not isinstance(value, list):
        return comments

    for item in value:
        if isinstance(item, dict):
            editor = str(item.get("editor") or item.get("from") or "WikiTheoryEditor").strip()
            comment = str(item.get("comment") or item.get("body") or "").strip()
        else:
            raw = str(item).strip()
            if ":" in raw:
                editor, comment = raw.split(":", 1)
                editor = editor.strip()
                comment = comment.strip()
            else:
                editor = "WikiTheoryEditor"
                comment = raw
        if editor and comment:
            comments.append({"editor": editor, "comment": comment})
    return comments


def fallback_editor_comments(decision: str, target: dict[str, Any]) -> list[dict[str, str]]:
    section = target["sectionTitle"]
    if decision == "approved":
        return [
            {
                "editor": "CivicLedger",
                "comment": f"The revision to '{section}' connects the archive evidence clearly enough for approval.",
            },
            {
                "editor": "ArchivistMori",
                "comment": "I would still prefer cautious wording, but the cited line of reasoning is usable.",
            },
        ]
    if decision == "pending":
        return [
            {
                "editor": "ArchivistMori",
                "comment": f"The revision to '{section}' has been posted for further editorial review.",
            },
            {
                "editor": "CivicLedger",
                "comment": "The wording should remain tied to named archive pages and dated records.",
            },
        ]
    if decision == "rejected":
        return [
            {
                "editor": "NullRevision",
                "comment": "The revision overstates what the visible archive material supports.",
            },
            {
                "editor": "LanternField",
                "comment": "The folklore angle may be relevant, but it needs stronger documentary grounding.",
            },
        ]
    return [
        {
            "editor": "ArchivistMori",
            "comment": f"The '{section}' draft is promising, but it needs a tighter connection to related pages.",
        },
        {
            "editor": "CivicLedger",
            "comment": "Please anchor the timeline more directly before this can be approved.",
        },
    ]


def review_subject(decision: str, target: dict[str, Any]) -> str:
    if decision == "approved":
        return "Your contribution was approved"
    if decision == "pending":
        return "Your contribution is pending review"
    if decision == "rejected":
        return "Your contribution was not accepted"
    return "Your contribution needs revision"


def review_body(decision: str, target: dict[str, Any]) -> str:
    article = target["articleTitle"]
    section = target["sectionTitle"]
    if decision == "approved":
        return (
            f"Your revision to '{section}' on '{article}' has been reviewed and approved. "
            "Thank you for your contribution to WikiTheory."
        )
    if decision == "pending":
        return (
            f"Your revision to '{section}' on '{article}' has been submitted for editorial review. "
            "Watch the discussion thread for editor comments."
        )
    if decision == "rejected":
        return (
            f"Your revision to '{section}' on '{article}' was not accepted. "
            "Please review the related pages before submitting a new revision."
        )
    return (
        f"Your revision to '{section}' on '{article}' has useful material but needs revision. "
        "The editorial discussion includes suggested evidence to connect more carefully."
    )


def fallback_references(article: dict[str, Any]) -> list[str]:
    title = article.get("title", "Untitled file")
    article_type = article.get("type", "document")
    location = infobox_value(article.get("infobox", {}), "Location") or infobox_value(
        article.get("infobox", {}), "Region"
    )
    references = [
        f"Mizukawa Municipal Archive, file note for {title}, 1998.",
        "Regional Police Bulletin No. 44, partially redacted local copy.",
    ]
    if location:
        references.append(f"Kawabe Valley Survey Office, {location} field index.")
    elif article_type in {"person", "case"}:
        references.append("Kuroda Family Statement, private clipping archive.")
    else:
        references.append("Mizukawa North Library, community newsletter index.")
    return references[:4]


def infobox_value(infobox: Any, label: str) -> str:
    if not isinstance(infobox, dict):
        return ""
    fields = infobox.get("fields")
    if isinstance(fields, list):
        for field in fields:
            if not isinstance(field, dict):
                continue
            if normalize_title(field.get("label", "")) == normalize_title(label):
                return str(field.get("value") or "").strip()
    value = infobox.get(label)
    return str(value or "").strip()


def fallback_external_links(article: dict[str, Any]) -> list[str]:
    title = article.get("title", "Untitled file")
    article_type = article.get("type", "document")
    if article_type == "case":
        return ["WikiTheory archive portal: Mizukawa case index"]
    if article_type in {"document", "record"}:
        return [f"WikiTheory archive portal: document file for {title}"]
    return [f"WikiTheory archive portal: entry index for {title}"]


def fallback_categories(article: dict[str, Any]) -> list[str]:
    title = article.get("title", "")
    body = article.get("body", "")
    article_type = article.get("type", "document")
    text = normalize_title(f"{title} {body}")
    categories = ["Mizukawa Town"]

    if "1998" in text:
        categories.append("1998 incidents")
    if "disappear" in text or "emi kuroda" in text:
        categories.append("Unresolved disappearances")
    if "clinic" in text or article_type == "organization":
        categories.append("Organizations")
    if "folklore" in text or "bell" in text:
        categories.append("Local folklore")
    if "weather" in text or "report" in text:
        categories.append("Documents")
    if article_type == "case":
        categories.append("Missing person cases")
    if article_type == "person":
        categories.append("People")
    if article_type == "place":
        categories.append("Places")
    if article_type in {"document", "record"}:
        categories.append("Documents")

    return dedupe_titles(categories)[:6]


def _coerce_percentage(value: Any) -> int:
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    match = re.search(r"\d+", str(value))
    if not match:
        return 0
    return max(0, min(100, int(match.group(0))))


def _coerce_signed_int(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"-?\d+", str(value))
    if not match:
        return 0
    return int(match.group(0))
