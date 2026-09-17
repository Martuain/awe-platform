/**
 * Prepare the Customer Website Mock for an isolated iframe srcDoc.
 *
 * The mock is a review artifact, not an AWE Studio application document.
 * Internal website links are therefore rewritten to same-document fragments
 * and the srcDoc gets an explicit about:srcdoc base so fragment navigation can
 * never resolve against the embedding Studio document.
 */
export function safeArtifactPreviewHtml(html: string): string {
  const sanitized = html
    .replace(/<base\b[^>]*>/gi, "")
    .replace(/\s(?:target)=(['"])[^'"]*\1/gi, "")
    .replace(/\s(?:href)=(['"])([^'"]*)\1/gi, (_match, quote, href: string) => {
      const trimmed = href.trim();
      if (trimmed.startsWith("#")) return ` href=${quote}${trimmed}${quote}`;

      // Keep customer-site internal paths inside the mock document. The mock
      // renderer uses awe-mock-page-* IDs, so /about becomes #awe-mock-page-about.
      if (/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(trimmed)) return "";
      const path = trimmed.split(/[?#]/, 1)[0].replace(/^\/+|\/+$/g, "");
      if (!path) return ` href=${quote}#awe-mock-page-home${quote}`;
      const id = path.replace(/\//g, "-").replace(/[^a-zA-Z0-9_-]/g, "-");
      return ` href=${quote}#awe-mock-page-${id}${quote}`;
    })
    .replace(/\s(?:action|method|target)=(['"])[^'"]*\1/gi, "")
    .replace(/<form\b/gi, '<form onsubmit="return false" data-awe-mock-navigation="disabled"')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi, "")
    .replace(/<script\b[^>]*\/\s*>/gi, "");

  // srcDoc's fallback base can be the embedding document. Make the mock's
  // fragment navigation unambiguously resolve against its own document.
  return sanitized.replace(
    /<head(\b[^>]*)>/i,
    '<head$1><base href="about:srcdoc">',
  );
}
