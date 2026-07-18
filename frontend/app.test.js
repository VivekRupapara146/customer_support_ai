const assert = require("assert");
const { isFallbackReply, isValidSessionIdFormat, sanitizeAgentList, stripTrailingSlashes, ALL_DOMAINS } = require("./app.js");

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

console.log("\nFrontend unit tests complete.");
