def build_root_html() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PM MVP Hello</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 2rem;
        color: #032147;
      }
      h1 {
        margin-bottom: 0.5rem;
      }
      #api-result {
        margin-top: 1rem;
        color: #209dd7;
        font-weight: bold;
      }
      button {
        background: #753991;
        color: white;
        border: 0;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <h1>Hello World</h1>
    <p>This page is served by FastAPI from inside Docker.</p>
    <button id="load-api" type="button">Call /api/hello</button>
    <div id="api-result">Not called yet.</div>
    <script>
      const button = document.getElementById("load-api");
      const result = document.getElementById("api-result");

      button.addEventListener("click", async () => {
        result.textContent = "Loading...";
        try {
          const response = await fetch("/api/hello");
          const data = await response.json();
          result.textContent = data.message;
        } catch (error) {
          result.textContent = "API call failed";
        }
      });
    </script>
  </body>
</html>
"""
