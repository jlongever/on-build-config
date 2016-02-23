<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>
    <xsl:template match="/">
        <unitTest version="1">
            <file path="">
                <xsl:apply-templates/>
            </file>
        </unitTest>
    </xsl:template>

    <xsl:template match="testsuite">
        <xsl:for-each select="testcase">
            <xsl:choose>
            <xsl:when test="failure != ''">
                <xsl:text disable-output-escaping="yes"><![CDATA[<testCase name="]]></xsl:text>
                <xsl:value-of select="@name"/>
                <xsl:text disable-output-escaping="yes"><![CDATA[" duration="]]></xsl:text>
                <xsl:value-of select="format-number(@time, '0')" />
                <xsl:text disable-output-escaping="yes"><![CDATA[">]]></xsl:text>
                <xsl:text disable-output-escaping="yes"><![CDATA[<failure message="failed">]]></xsl:text>
                <xsl:for-each select="failure">
                  <xsl:value-of select="."/>
                </xsl:for-each>
                <xsl:text disable-output-escaping="yes"><![CDATA[</failure>]]></xsl:text>
                <xsl:text disable-output-escaping="yes"><![CDATA[</testCase>]]></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text disable-output-escaping="yes"><![CDATA[<testCase name="]]></xsl:text>
                <xsl:value-of select="@name"/>
                <xsl:text disable-output-escaping="yes"><![CDATA[" duration="]]></xsl:text>
                <xsl:value-of select="format-number(@time, '0')" />
                <xsl:text disable-output-escaping="yes"><![CDATA["/>]]></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
