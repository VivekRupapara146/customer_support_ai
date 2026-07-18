const assert = require("assert");
const { isFallbackReply, isValidSessionIdFormat, sanitizeAgentList, stripTrailingSlashes, escapeHtml, renderLimitedMarkdown, ALL_DOMAINS } = require("./app.js");

function test(name, fn) {
  try {
    fn();
    console.log(`${name}: PASS`);
  } catch (e) {
    console.log(`${name}: FAIL - ${e.message}`);
    process.exitCode = 1;
  }
}

test("isFallbackReply detects the honest fallback phrase", () => {
  const fallbackText = "I don't have enough information in our knowledge base to answer that confidently.";
  assert.strictEqual(isFallbackReply(fallbackText), true);
});

test("isFallbackReply returns false for a normal grounded answer", () => {
  assert.strictEqual(isFallbackReply("Your refund will be processed within 5-7 business days."), false);
});

test("isFallbackReply handles non-string input safely", () => {
  assert.strictEqual(isFallbackReply(null), false);
  assert.strictEqual(isFallbackReply(undefined), false);
  assert.strictEqual(isFallbackReply(42), false);
});

test("isValidSessionIdFormat accepts a well-formed UUID-like id", () => {
  assert.strictEqual(isValidSessionIdFormat("8f2a91d3-1234-4abc-9def-1234567890ab"), true);
});

test("isValidSessionIdFormat rejects path-traversal-style input", () => {
  assert.strictEqual(isValidSessionIdFormat("../../etc/passwd"), false);
});

test("isValidSessionIdFormat rejects overly long input", () => {
  assert.strictEqual(isValidSessionIdFormat("a".repeat(100)), false);
});

test("sanitizeAgentList keeps only known domains", () => {
  const result = sanitizeAgentList(["billing", "made_up_category", "technical"]);
  assert.deepStrictEqual(result, ["billing", "technical"]);
});

test("sanitizeAgentList handles non-array input safely", () => {
  assert.deepStrictEqual(sanitizeAgentList(null), []);
  assert.deepStrictEqual(sanitizeAgentList("billing"), []);
});

test("ALL_DOMAINS matches the backend's 5 support categories", () => {
  assert.deepStrictEqual(ALL_DOMAINS.sort(), ["billing", "complaint", "faq", "product", "technical"].sort());
});

// --- Regression tests for the real double-slash bug found in production ---
// (config.js had a trailing slash -> requests went to ".../onrender.com//auth/login",
// which the backend rejected. This was misdiagnosed as a CORS bug at first because
// the failure appeared on the CORS preflight OPTIONS request.)

test("stripTrailingSlashes removes a single trailing slash (the actual prod bug)", () => {
  assert.strictEqual(
    stripTrailingSlashes("https://techmart-support-backend-5h0x.onrender.com/"),
    "https://techmart-support-backend-5h0x.onrender.com"
  );
});

test("stripTrailingSlashes removes multiple trailing slashes", () => {
  assert.strictEqual(stripTrailingSlashes("https://example.com///"), "https://example.com");
});

test("stripTrailingSlashes leaves a clean URL unchanged", () => {
  assert.strictEqual(stripTrailingSlashes("https://example.com"), "https://example.com");
});

// --- Markdown rendering tests (fixes the "**bold**" showing as literal asterisks bug) ---

test("renderLimitedMarkdown converts **bold** to <strong>", () => {
  const result = renderLimitedMarkdown("This is **important** text.");
  assert.strictEqual(result, "<p>This is <strong>important</strong> text.</p>");
});

test("renderLimitedMarkdown converts bullet lines to a list", () => {
  const result = renderLimitedMarkdown("* First point\n* Second point");
  assert.strictEqual(result, "<ul><li>First point</li><li>Second point</li></ul>");
});

test("renderLimitedMarkdown handles the real Gemini output pattern from the bug report", () => {
  const realOutput = "To request a refund:\n\n*   **Product Returns:** 30-day window.\n*   **Premium Subscriptions:** 7 days.";
  const result = renderLimitedMarkdown(realOutput);
  assert.ok(result.includes("<strong>Product Returns:</strong>"));
  assert.ok(result.includes("<strong>Premium Subscriptions:</strong>"));
  assert.ok(result.includes("<ul>") && result.includes("<li>"));
});

test("CRITICAL: renderLimitedMarkdown escapes raw HTML/script tags — never an XSS vector", () => {
  const malicious = "<script>alert('xss')</script> and <img src=x onerror=alert(1)>";
  const result = renderLimitedMarkdown(malicious);
  assert.ok(!result.includes("<script>"), "raw <script> tag must never survive into rendered HTML");
  assert.ok(!result.includes("<img "), "raw <img> tag must never survive as a live element");
  assert.ok(result.includes("&lt;script&gt;"), "should be escaped to inert text instead");
  assert.ok(result.includes("&lt;img"), "img tag should be escaped to inert text, not a live element");
});

test("CRITICAL: a poisoned RAG chunk containing HTML is neutralized", () => {
  // Simulates a malicious/compromised document making it into retrieved context.
  const poisonedContext = "Refund policy is 30 days. <a href=\"javascript:alert(1)\">click here</a>";
  const result = renderLimitedMarkdown(poisonedContext);
  assert.ok(!result.includes('href="javascript:'), "raw href/javascript: URI must not survive");
});

test("escapeHtml escapes all five dangerous characters", () => {
  const result = escapeHtml(`<>&"'`);
  assert.strictEqual(result, "&lt;&gt;&amp;&quot;&#39;");
});

console.log("\nFrontend unit tests complete.");
