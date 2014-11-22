<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.w3.org/1999/xhtml">
  <xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/report">
    <html lang="en">
      <head>
        <link href="report.css" rel="stylesheet" type="text/css" />
        <title>Report</title>
      </head>
      <body>
        <table>
        <xsl:for-each select="file"><xsl:if test="@code != 0">
        <tr>
        <td><xsl:value-of select="@path" /></td>
        <td><xsl:value-of select="@code" /></td>
        <td><pre><xsl:value-of select="." /></pre></td>
        </tr>
        </xsl:if></xsl:for-each>
        </table>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
