<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology" version="3.34.6-Prizren">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option name="name" type="QString" value=""/>
      <Option name="properties"/>
      <Option name="type" type="QString" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling enabled="false" zoomedOutResamplingMethod="nearestNeighbour" zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2"/>
    </provider>
    <rasterrenderer band="1" type="singlebandpseudocolor" classificationMin="1" classificationMax="65535" alphaBand="-1" nodataColor="" opacity="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Exact</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" maximumValue="65535" classificationMode="1" clip="0" minimumValue="1" labelPrecision="0">
          <colorramp name="[source]" type="gradient">
            <Option type="Map">
              <Option name="color1" type="QString" value="25,110,25,255"/>
              <Option name="color2" type="QString" value="0,0,0,255"/>
              <Option name="direction" type="QString" value="ccw"/>
              <Option name="discrete" type="QString" value="0"/>
              <Option name="rampType" type="QString" value="gradient"/>
              <Option name="spec" type="QString" value="rgb"/>
              <Option name="stops" type="QString" value="1.52593e-05;34,139,34,255;rgb;ccw:0.00303659;255,165,0,255;rgb;ccw:0.0305033;227,26,28,255;rgb;ccw"/>
            </Option>
          </colorramp>
          <item label="1" color="#196e19" value="1" alpha="255"/>
          <item label="2" color="#228b22" value="2" alpha="255"/>
          <item label="200" color="#ffa500" value="200" alpha="255"/>
          <item label="2000" color="#e31a1c" value="2000" alpha="255"/>
          <item label="65535" color="#000000" value="65535" alpha="255"/>
          <rampLegendSettings prefix="" maximumLabel="" minimumLabel="" direction="0" orientation="2" useContinuousLegend="1" suffix="">
            <numericFormat id="basic">
              <Option type="Map">
                <Option name="decimal_separator" type="invalid"/>
                <Option name="decimals" type="int" value="6"/>
                <Option name="rounding_type" type="int" value="0"/>
                <Option name="show_plus" type="bool" value="false"/>
                <Option name="show_thousand_separator" type="bool" value="true"/>
                <Option name="show_trailing_zeros" type="bool" value="false"/>
                <Option name="thousand_separator" type="invalid"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation colorizeStrength="100" colorizeRed="255" grayscaleMode="0" colorizeGreen="128" invertColors="0" colorizeOn="0" saturation="0" colorizeBlue="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
