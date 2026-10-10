# app/core/swagger_ui.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse


def _with_email_label(swagger_page: HTMLResponse) -> HTMLResponse:
    html = swagger_page.body.decode("utf-8")
    custom_script = """
<script>
  (function () {
    function renameUsernameToEmail() {
      const labels = document.querySelectorAll("label");
      labels.forEach((label) => {
        const text = (label.textContent || "").trim().toLowerCase();
        if (text === "username:") {
          label.textContent = "Email:";
        }
      });

      const usernameInput = document.querySelector("input[type='text']");
      if (usernameInput && !usernameInput.placeholder) {
        usernameInput.placeholder = "email@example.com";
      }
    }

    const observer = new MutationObserver(renameUsernameToEmail);
    observer.observe(document.body, { childList: true, subtree: true });
    renameUsernameToEmail();
  })();
</script>
"""
    return HTMLResponse(
        html.replace("</body>", f"{custom_script}</body>"),
        status_code=swagger_page.status_code,
    )


def setup_custom_docs(app_v1: FastAPI):
    @app_v1.get("/api/v1/docs", include_in_schema=False)
    async def custom_swagger_ui_v1():
        page = get_swagger_ui_html(
            openapi_url="/api/v1/openapi.json",
            title="АРМ застройщика — Swagger UI v1",
            swagger_js_url="/dist/swagger-ui-bundle.js",
            swagger_css_url="/dist/swagger-ui.css",
            oauth2_redirect_url="/api/v1/docs/oauth2-redirect",
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,
            },
        )
        return _with_email_label(page)

    @app_v1.get("/api/v1/docs/oauth2-redirect", include_in_schema=False)
    async def swagger_oauth2_redirect_v1():
        return get_swagger_ui_oauth2_redirect_html()

    @app_v1.get("/api/v2/docs", include_in_schema=False)
    async def custom_swagger_ui_v2():
        page = get_swagger_ui_html(
            openapi_url="/api/v2/openapi.json",
            title="АРМ застройщика — Swagger UI v2",
            swagger_js_url="/dist/swagger-ui-bundle.js",
            swagger_css_url="/dist/swagger-ui.css",
            oauth2_redirect_url="/api/v2/docs/oauth2-redirect",
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,
            },
        )
        return _with_email_label(page)

    @app_v1.get("/api/v2/docs/oauth2-redirect", include_in_schema=False)
    async def swagger_oauth2_redirect_v2():
        return get_swagger_ui_oauth2_redirect_html()