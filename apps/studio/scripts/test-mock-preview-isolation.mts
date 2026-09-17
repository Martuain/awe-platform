import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { safeArtifactPreviewHtml } from "../app/lib/safe-artifact-preview.ts";

const input = `<!doctype html><html><head><base href="/"><script>alert(1)</script></head><body>
<nav><a href="/about" target="_self">About</a><a href="about">About relative</a><a href="#awe-mock-page-home">Home</a><a href="https://example.com">External</a></nav>
<form action="/contact" method="get" target="_self"><button type="submit">Send</button></form>
</body></html>`;

const output = safeArtifactPreviewHtml(input);
assert.equal(output.includes('<base href="/">'), false);
assert.match(output, /<base href="about:srcdoc">/);
assert.equal(output.includes("<script"), false);
assert.match(output, /href="#awe-mock-page-about"/);
assert.match(output, /href="#awe-mock-page-home"/);
assert.equal(output.includes("https://example.com"), false);
assert.equal(output.includes('target="_self"'), false);
assert.equal(output.includes('action="/contact"'), false);
assert.match(output, /data-awe-mock-navigation="disabled"/);
assert.match(output, /onsubmit="return false"/);

const pageSource = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
assert.match(pageSource, /handleMockFrameLoad/);
assert.match(pageSource, /sandbox="allow-same-origin"/);
assert.match(pageSource, /document\.addEventListener\("click", handleClick, true\)/);
assert.match(pageSource, /click\.preventDefault\(\)/);

console.log("Customer Website Mock navigation isolation: PASS");
