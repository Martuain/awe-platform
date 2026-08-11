export default function Home() {
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "64px 24px" }}>
      <p style={{ letterSpacing: 2, textTransform: "uppercase", fontSize: 12 }}>AWE Studio · Genesis 0.1.0</p>
      <h1 style={{ fontSize: 56, lineHeight: 1.05, margin: "24px 0" }}>
        From business knowledge to engineered digital experiences.
      </h1>
      <p style={{ fontSize: 20, lineHeight: 1.6, maxWidth: 720 }}>
        AWE is an AI-native, API-first website engineering platform.
        The first vertical slice is Business Discovery.
      </p>
      <section style={{ marginTop: 48, padding: 24, border: "1px solid #ddd", borderRadius: 16 }}>
        <h2>Genesis walking skeleton</h2>
        <ol>
          <li>Create a project through the API.</li>
          <li>Start Business Discovery.</li>
          <li>Capture structured business knowledge.</li>
          <li>Approve the context before downstream generation.</li>
        </ol>
      </section>
    </main>
  );
}
