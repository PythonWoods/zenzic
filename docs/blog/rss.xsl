<?xml version="1.0" encoding="utf-8"?>
<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml" data-md-color-scheme="slate">
      <head>
        <title><xsl:value-of select="/rss/channel/title"/> RSS Feed</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <link rel="stylesheet" href="/assets/css/zenzic-tailwind.min.css"/>
        <link rel="stylesheet" href="/assets/css/extra.css"/>
        <style>
          body { padding: 2rem; max-width: 800px; margin: 0 auto; background: var(--md-default-bg-color); color: var(--md-default-fg-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
          .post { margin-bottom: 2.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--zz-border-subtle); }
          .post a { color: var(--md-typeset-a-color); text-decoration: none; }
          .post a:hover { text-decoration: underline; }
          .notice { background: var(--md-code-bg-color); border: 1px solid var(--zz-border-subtle); padding: 1rem; border-radius: 8px; margin-bottom: 2rem; }
        </style>
      </head>
      <body>
        <div class="notice">
          <strong>This is an RSS feed.</strong> You can subscribe to this feed in any RSS reader.
        </div>
        <h1 class="text-3xl font-bold mb-2"><xsl:value-of select="/rss/channel/title"/></h1>
        <p class="text-gray-500 mb-8"><xsl:value-of select="/rss/channel/description"/></p>
        <hr class="mb-8" style="border-top: 1px solid var(--zz-border-subtle);"/>
        <xsl:for-each select="/rss/channel/item">
          <div class="post">
            <h2 class="text-xl font-bold mb-1">
              <a href="{link}">
                <xsl:value-of select="title"/>
              </a>
            </h2>
            <div class="text-xs text-gray-500 mb-4">Published on <xsl:value-of select="pubDate"/></div>
            <div class="prose prose-invert md-typeset">
              <xsl:value-of select="description" disable-output-escaping="yes"/>
            </div>
          </div>
        </xsl:for-each>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
