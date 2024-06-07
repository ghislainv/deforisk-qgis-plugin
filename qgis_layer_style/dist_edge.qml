<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology" version="3.34.6-Prizren">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option type="QString" value="" name="name"/>
      <Option name="properties"/>
      <Option type="QString" value="collection" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2" zoomedOutResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer classificationMin="30" classificationMax="1000" type="singlebandpseudocolor" alphaBand="-1" band="1" nodataColor="" opacity="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader classificationMode="3" minimumValue="30" colorRampType="INTERPOLATED" maximumValue="1000" clip="0" labelPrecision="0">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option type="QString" value="227,26,28,255" name="color1"/>
              <Option type="QString" value="34,139,34,255" name="color2"/>
              <Option type="QString" value="ccw" name="direction"/>
              <Option type="QString" value="0" name="discrete"/>
              <Option type="QString" value="gradient" name="rampType"/>
              <Option type="QString" value="rgb" name="spec"/>
              <Option type="QString" value="0.0721649;255,165,0,255;rgb;ccw:0.484536;255,255,178,255;rgb;ccw" name="stops"/>
            </Option>
          </colorramp>
          <item label=">=30" alpha="255" value="30" color="#e31a1c"/>
          <item label=">=100" alpha="255" value="100" color="#ffa500"/>
          <item label=">=500" alpha="255" value="500" color="#ffffb2"/>
          <item label=">=1000" alpha="255" value="1000" color="#228b22"/>
          <rampLegendSettings maximumLabel="" suffix="" orientation="2" prefix="" minimumLabel="" useContinuousLegend="1" direction="0">
            <numericFormat id="basic">
              <Option type="Map">
                <Option type="invalid" name="decimal_separator"/>
                <Option type="int" value="6" name="decimals"/>
                <Option type="int" value="0" name="rounding_type"/>
                <Option type="bool" value="false" name="show_plus"/>
                <Option type="bool" value="true" name="show_thousand_separator"/>
                <Option type="bool" value="false" name="show_trailing_zeros"/>
                <Option type="invalid" name="thousand_separator"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" gamma="1" contrast="0"/>
    <huesaturation colorizeOn="0" colorizeRed="255" colorizeStrength="100" saturation="0" colorizeBlue="128" grayscaleMode="0" colorizeGreen="128" invertColors="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
