"""Unit test per redundancy detection, value classification e composite score."""

from mcp_manager.utils.capabilities import (
    compute_redundancy,
    classify_value,
    compute_composite_score,
)


class TestRedundancy:
    """Verifica che i server ridondanti vengano correttamente identificati."""

    def test_filesystem_is_redundant(self):
        r = compute_redundancy("io.github.bytedance/mcp-server-filesystem", "filesystem access")
        assert r["redundant"] is True
        assert r["redundancy_score"] >= 50

    def test_browser_is_redundant(self):
        r = compute_redundancy("microsoft/playwright-mcp", "Browser automation")
        assert r["redundant"] is True

    def test_terminal_is_redundant(self):
        r = compute_redundancy("io.github.RipperMercs/terminalfeed", "Terminal commands")
        assert r["redundant"] is True

    def test_memory_is_redundant(self):
        r = compute_redundancy("com.letta/memory-mcp", "Persistent memory")
        assert r["redundant"] is True


class TestNonRedundant:
    """Verifica che i server NON ridondanti non vengano flaggati."""

    def test_kubernetes_not_redundant(self):
        r = compute_redundancy("io.github.containers/kubernetes-mcp-server", "K8s cluster management")
        assert r["redundant"] is False

    def test_database_not_redundant(self):
        r = compute_redundancy("ai.waystation/postgres", "PostgreSQL queries")
        assert r["redundant"] is False

    def test_cloudflare_not_redundant(self):
        r = compute_redundancy("com.cloudflare.mcp/mcp", "Cloudflare API")
        assert r["redundant"] is False

    def test_sentry_not_redundant(self):
        r = compute_redundancy("io.github.getsentry/sentry-mcp", "Error tracking")
        assert r["redundant"] is False

    def test_jira_not_redundant(self):
        r = compute_redundancy("io.github.deepwired/mcp-jira", "Jira issue tracking")
        assert r["redundant"] is False

    def test_docker_not_redundant(self):
        r = compute_redundancy("io.github.alissaitteke/docker-mcp", "Docker management")
        assert r["redundant"] is False

    def test_figma_not_redundant(self):
        r = compute_redundancy("com.figma.mcp/mcp", "Figma design API")
        assert r["redundant"] is False

    def test_semantic_code_search_not_redundant(self):
        r = compute_redundancy("io.github.example/code-search-mcp", "Semantic code search")
        assert r["redundant"] is False

    def test_stripe_not_redundant(self):
        r = compute_redundancy("io.github.stripe/agent-toolkit", "Payments integration")
        assert r["redundant"] is False


class TestCompositeScore:
    """Verifica formula dello score composito."""

    def test_all_zero(self):
        assert compute_composite_score(0, 0, 0) == 0.0

    def test_max(self):
        assert compute_composite_score(100, 0, 100) == 100.0

    def test_half(self):
        s = compute_composite_score(50, 50, 50)
        # 50*0.4 + 50*0.3 + 50*0.3 = 20 + 15 + 15 = 50
        assert s == 50.0, f"Expected 50, got {s}"

    def test_no_trust_some_value(self):
        s = compute_composite_score(0, 50, 80)
        # 0*0.4 + 50*0.3 + 80*0.3 = 0 + 15 + 24 = 39
        assert s == 39.0, f"Expected 39, got {s}"


class TestValueClassification:
    """Verifica classificazione del valore d'uso."""

    def test_database(self):
        v = classify_value("test/pg-server", "PostgreSQL database with SQL queries")
        assert v["value_type"] == "database"

    def test_cloud_devops(self):
        v = classify_value("test/k8s", "Kubernetes cluster management and deployment")
        assert v["value_type"] == "cloud_devops"

    def test_project_management(self):
        v = classify_value("test/jira-mcp", "Jira issue tracking and sprint management")
        assert v["value_type"] == "project_management"

    def test_monitoring(self):
        v = classify_value("test/sentry", "Error tracking, APM and observability")
        assert v["value_type"] == "monitoring"

    def test_payments(self):
        v = classify_value("test/stripe", "Stripe payment processing and billing")
        assert v["value_type"] == "payments"

    def test_analytics(self):
        v = classify_value("test/bi-dashboard", "Business analytics KPI dashboard")
        assert v["value_type"] == "analytics"

    def test_ai_ml(self):
        v = classify_value("test/inference-server", "ML model inference and serving")
        assert v["value_type"] == "ai_ml"

    def test_multi_label(self):
        v = classify_value("test/multi", "PostgreSQL monitoring with Grafana on K8s")
        assert len(v.get("value_types", [])) >= 2

    def test_uncategorized(self):
        v = classify_value("test/obscure", "Something completely unknown")
        assert v["value_type"] == "uncategorized"
        assert v["value_score"] == 30


class TestRedundantValueClassification:
    """Server ridondanti devono avere valore basso."""

    def test_redundant_filesystem(self):
        v = classify_value("test/filesystem", "filesystem access and file operations")
        assert v["value_type"] == "redundant"
        assert v["value_score"] <= 30
