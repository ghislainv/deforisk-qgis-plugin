<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.6-Prizren" styleCategories="Symbology">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" type="QString" name="name"/>
      <Option name="properties"/>
      <Option value="collection" type="QString" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false"/>
    </provider>
    <rasterrenderer opacity="1" type="singlebandpseudocolor" alphaBand="-1" band="1" nodataColor="" classificationMin="1" classificationMax="65535">
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
        <colorrampshader classificationMode="1" clip="0" labelPrecision="0" colorRampType="INTERPOLATED" maximumValue="65535" minimumValue="1">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option value="25,110,25,255" type="QString" name="color1"/>
              <Option value="0,0,0,255" type="QString" name="color2"/>
              <Option value="ccw" type="QString" name="direction"/>
              <Option value="0" type="QString" name="discrete"/>
              <Option value="gradient" type="QString" name="rampType"/>
              <Option value="rgb" type="QString" name="spec"/>
              <Option value="1.52593e-05;34,139,34,255;rgb;ccw:0.00303659;227,26,28,255;rgb;ccw:0.0305033;255,165,0,255;rgb;ccw" type="QString" name="stops"/>
            </Option>
          </colorramp>
          <item value="1" color="#196e19" label="1" alpha="255"/>
          <item value="2" color="#228b22" label="2" alpha="255"/>
          <item value="200" color="#e31a1c" label="200" alpha="255"/>
          <item value="2000" color="#ffa500" label="2000" alpha="255"/>
          <item value="65535" color="#000000" label="65535" alpha="255"/>
          <rampLegendSettings suffix="" useContinuousLegend="1" direction="0" minimumLabel="" prefix="" maximumLabel="" orientation="2">
            <numericFormat id="basic">
              <Option type="Map">
                <Option type="invalid" name="decimal_separator"/>
                <Option value="6" type="int" name="decimals"/>
                <Option value="0" type="int" name="rounding_type"/>
                <Option value="false" type="bool" name="show_plus"/>
                <Option value="true" type="bool" name="show_thousand_separator"/>
                <Option value="false" type="bool" name="show_trailing_zeros"/>
                <Option type="invalid" name="thousand_separator"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" gamma="1" brightness="0"/>
    <huesaturation colorizeRed="255" colorizeBlue="128" grayscaleMode="0" colorizeOn="0" colorizeGreen="128" colorizeStrength="100" invertColors="0" saturation="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
