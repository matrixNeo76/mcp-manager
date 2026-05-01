"""Evaluate MCP servers against pi built-in capabilities.

Determines if an MCP server is redundant (pi already has it)
and how much value it adds (what pi CAN'T do).
"""

import json
import re
import warnings
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Expected capabilities.json version (increment when adding/removing categories)
CAPABILITIES_VERSION = 2

# Cache capabilities
_caps: dict | None = None


def _load_capabilities() -> dict:
  global _caps
  if _caps is not None:
    return _caps
  path = DATA_DIR / "capabilities.json"
  with open(path, encoding="utf-8") as f:
    data = json.load(f)

  # Version check
  meta = data.get("_meta", {})
  ver = meta.get("version")
  if ver is not None and ver != CAPABILITIES_VERSION:
    warnings.warn(
      f"capabilities.json version {ver} != expected {CAPABILITIES_VERSION}. "
      "Update CAPABILITIES_VERSION in capabilities.py to match."
    )

  _caps = data
  return _caps


# ---- Value classification map ----
VALUE_CLASSIFICATION: list[dict[str, Any]] = [
  # Database & Storage — high value, pi has none of these
  {
    "value_type": "database",
    "value_score": 90,
    "label": "[DB] Database",
    "keywords": [
      "postgres", "postgresql", "mysql", "sqlite", "mongodb", "redis",
      "couchdb", "dynamodb", "database", "db query", "sql query",
      "data source", "data connection", "bigquery", "snowflake",
      "clickhouse", "cockroachdb", "mariadb", "oracle db"
    ],
  },
  # Cloud / DevOps — high value
  {
    "value_type": "cloud_devops",
    "value_score": 85,
    "label": "[Cloud] Cloud/DevOps",
    "keywords": [
      "kubernetes", "k8s", "docker", "container", "aws", "azure",
      "gcp", "cloudflare", "terraform", "cloud", "deploy",
      "helm", "istio", "cloud run", "lambda", "ec2", "s3"
    ],
  },
  # Project Management — high value
  {
    "value_type": "project_management",
    "value_score": 80,
    "label": "[PM] Project Mgmt",
    "keywords": [
      "jira", "linear", "asana", "notion", "clickup", "trello",
      "monday.com", "project manag", "issue tracker", "task",
      "sprint", "backlog", "shortcut", "pivotal"
    ],
  },
  # Communication — high value
  {
    "value_type": "communication",
    "value_score": 80,
    "label": "[Chat] Communication",
    "keywords": [
      "slack", "discord", "teams", "mattermost", "rocket.chat",
      "email", "gmail", "outlook", "send message", "channel",
      "post message", "notification"
    ],
  },
  # Monitoring / Observability
  {
    "value_type": "monitoring",
    "value_score": 80,
    "label": "[Mon] Monitoring",
    "keywords": [
      "sentry", "datadog", "new relic", "grafana", "prometheus",
      "error tracking", "log", "observability", "apm",
      "status page", "uptime", "alert"
    ],
  },
  # Design / Creative
  {
    "value_type": "design",
    "value_score": 75,
    "label": "[Design] Design",
    "keywords": [
      "figma", "sketch", "canva", "design", "ui design",
      "component", "prototype", "design system", "image gen"
    ],
  },
  # Payments / Commerce
  {
    "value_type": "payments",
    "value_score": 85,
    "label": "[$] Payments",
    "keywords": [
      "stripe", "paypal", "payment", "checkout", "invoice",
      "billing", "subscription", "revenue", "financial"
    ],
  },
  # Media processing
  {
    "value_type": "media",
    "value_score": 75,
    "label": "[Media] Media",
    "keywords": [
      "youtube", "vimeo", "video", "audio", "image",
      "transcribe", "media", "spotify", "music"
    ],
  },
  # Map / Geolocation
  {
    "value_type": "geolocation",
    "value_score": 70,
    "label": "[Geo] Geolocation",
    "keywords": [
      "map", "geocode", "geo", "location", "address",
      "google maps", "openstreetmap", "coordinates"
    ],
  },
  # Analytics / Business Intelligence
  {
    "value_type": "analytics",
    "value_score": 75,
    "label": "[BI] Analytics/BI",
    "keywords": [
      "analytics", "dashboard", "reporting", "business intelligence",
      "bi tool", "kpi", "metric", "chart", "data viz",
      "visualization", "insight", "data studio", "looker"
    ],
  },
  # AI / Machine Learning
  {
    "value_type": "ai_ml",
    "value_score": 85,
    "label": "[AI] AI/ML",
    "keywords": [
      "inference", "embedding", "llm", "model serving",
      "ml pipeline", "ai model", "machine learning",
      "deep learning", "neural network", "vector embedding",
      "model deploy", "training", "fine tuning"
    ],
  },
  # E-commerce / CMS
  {
    "value_type": "ecommerce_cms",
    "value_score": 70,
    "label": "[Shop] E-commerce/CMS",
    "keywords": [
      "shopify", "woocommerce", "wordpress", "contentful",
      "airtable", "notion database", "cms", "ecommerce"
    ],
  },
]


def compute_redundancy(server_name: str, description: str) -> dict[str, Any]:
  """Compute how redundant an MCP server is vs pi built-in capabilities.

  Returns:
    redundancy_score: 0 (unique) to 100 (completely redundant)
    redundant_category: str | None — which pi category it maps to
    redundant_reason: str | None
  """
  caps = _load_capabilities()
  name_lower = server_name.lower()
  desc_lower = description.lower()
  text = f"{name_lower} {desc_lower}"

  best_match = None
  best_score = 0

  for cat_key, cat_data in caps["categories"].items():
    score = 0

    # Match by name patterns
    for pattern in cat_data.get("replaces_mcp_name_patterns", []):
      if pattern.lower() in name_lower:
        score += 40

    # Match by keywords (but skip false positives)
    for kw in cat_data.get("replaces_mcp_keywords", []):
      if kw.lower() in text:
        # Special case: 'container' in a cloud/kubernetes context is NOT redundant
        if kw == "container" and ("kubernetes" in text or "k8s" in text or "cloud" in text):
          continue
        # Special case: 'code search' or 'semantic search' is NOT web search
        if kw in ("search", "web search") and ("code search" in text or "semantic search" in text or "codebase search" in text):
          continue
        score += 15

    # Check against known redundant examples
    for example in cat_data.get("redundant_examples", []):
      if example.lower().split("/")[-1] in name_lower:
        score = 100
        break

    # Bonus: penalize generic API wrappers (low redundancy)
    api_keywords = ["api", "integration", "wrapper", "client for", "sdk for"]
    has_api = any(kw in text for kw in api_keywords)
    if has_api:
      score = max(0, score - 20)

    # Override: if a HIGH-value classification matches, don't flag as redundant
    # This prevents cloud/infra names like "containers" from triggering false positives
    if score >= 50 and best_match in ("filesystem", "shell"):
      # Only these categories can truly be redundant
      pass
    elif score >= 50:
      # For other categories, check if they might be cloud/third-party
      cloud_hints = ["cloud", "kubernetes", "k8s", "docker", "deploy", "cluster"]
      infra_hints = ["api", "integration", "service", "platform", "connect"]
      if any(h in text for h in cloud_hints) or any(h in text for h in infra_hints):
        score = max(0, score - 40) # Reduce redundancy if it's cloud/infra API

    if score > best_score:
      best_score = score
      best_match = cat_key

  # Clamp and classify
  score = min(100, best_score)

  result: dict[str, Any] = {
    "redundancy_score": score,
    "redundant": score >= 50,
    "redundant_category": best_match,
    "redundant_reason": None,
  }

  if score >= 50 and best_match:
    cat = caps["categories"].get(best_match, {})
    result["redundant_reason"] = (
      f"pi ha già {cat.get('label', best_match)} built-in: "
      f"{', '.join(cat.get('builtin_tools', []))}"
    )

  return result


def classify_value(server_name: str, description: str) -> dict[str, Any]:
  """Classify what VALUE an MCP server adds beyond pi's built-in capabilities.

  Returns:
    value_type: str — primary category of value
    value_score: int — 0-100 how much value it adds
    value_label: str — human-readable label
    value_match_confidence: str — high/medium/low
    value_types: list[str] — ALL matching categories (multi-label)
  """
  text = f"{server_name.lower()} {description.lower()}"

  # First check if it's redundant — low value if so
  redundancy = compute_redundancy(server_name, description)
  if redundancy["redundant"]:
    return {
      "value_type": "redundant",
      "value_score": max(5, 30 - redundancy["redundancy_score"]),
      "value_label": " [RED] Ridondante",
      "value_match_confidence": "high",
      "value_types": ["redundant"],
    }

  # Collect ALL matching categories (multi-label)
  matches: list[dict] = []
  for classification in VALUE_CLASSIFICATION:
    keywords = classification["keywords"]
    match_count = sum(1 for kw in keywords if kw.lower() in text)

    if match_count >= 3:
      matches.append({
        "value_type": classification["value_type"],
        "value_score": classification["value_score"],
        "value_label": classification["label"],
        "value_match_confidence": "high",
      })
    elif match_count >= 1:
      matches.append({
        "value_type": classification["value_type"],
        "value_score": classification["value_score"] - 10,
        "value_label": classification["label"],
        "value_match_confidence": "medium",
      })

  if not matches:
    return {
      "value_type": "uncategorized",
      "value_score": 30,
      "value_label": " Generico",
      "value_match_confidence": "low",
      "value_types": [],
    }

  # Sort by score descending, pick best as primary
  matches.sort(key=lambda x: (-x["value_score"], x["value_match_confidence"] == "high"))
  primary = matches[0]

  return {
    "value_type": primary["value_type"],
    "value_score": primary["value_score"],
    "value_label": primary["value_label"],
    "value_match_confidence": primary["value_match_confidence"],
    "value_types": [m["value_type"] for m in matches],
  }


def compute_composite_score(
  trust_score: float,
  redundancy_score: float,
  value_score: float,
) -> float:
  """Compute a composite score that balances trust, non-redundancy, and value.

  Weights:
    trust (40%) — stars, recency, forks
    non-redundancy (30%) — pi non ha nulla di simile
    value (30%) — quanto valore aggiunge come integrazione esterna

  If trust and value are both zero, composite is 0 (not 30 from non-redundancy)
  to avoid misleading scores for unvetted servers.
  """
  if trust_score == 0 and value_score == 0:
    return 0.0

  non_redundancy = 100 - redundancy_score
  return round(
    trust_score * 0.40
    + non_redundancy * 0.30
    + value_score * 0.30,
    1,
  )


def get_redundancy_help() -> str:
  """Return a markdown summary of pi built-in capabilities for LLM context."""
  caps = _load_capabilities()
  lines = [
    "##  pi Built-in Capabilities",
    "",
    "Questi strumenti sono GIÀ disponibili in pi. MCP server che li duplicano sono RIDONDANTI:",
    "",
  ]
  for cat_key, cat_data in caps["categories"].items():
    tools = ", ".join(cat_data.get("builtin_tools", []))
    sources = cat_data.get("builtin_sources", [])
    extras = f" + sources: {', '.join(sources)}" if sources else ""
    lines.append(f"- **{cat_data['label']}**: {tools}{extras}")

  lines.extend([
    "",
    "##  Categorie di VALORE (cosa pi NON ha)",
    "",
    "Questi MCP server AGGIUNGONO valore perché pi non ha queste capacità:",
    "",
  ])
  for v in VALUE_CLASSIFICATION:
    lines.append(f"- **{v['label']}**: {v['value_score']}/100 — {', '.join(v['keywords'][:5])}...")

  return "\n".join(lines)
