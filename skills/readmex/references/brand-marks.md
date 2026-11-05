# Optional node brand marks

A brand mark is decoration beside an independently truthful node label and semantic type. Omit it unless the node names a real technology/product and the visual helps a README reader.

Use an existing bundled brand identifier through `brand`, or a verified URL plus SHA-256. Keep the literal product name in `label`; never let a logo prove compatibility or imply an unsupported integration. The renderer prepares/validates the brand material before layout and embeds the resolved mark into the standalone SVG. Network/source failures must not be disguised as successful captures.

Brand rails consume node width. If the logo collides with text, widen the node, shorten the truthful label, or omit optional decoration. Do not shrink required node text below its floor. Preview at 900 and 360 pixels; a decorative mark may disappear at mobile width as long as the readable node name preserves meaning.

Project logos discovered in the repository belong in the README page header/hero. Avoid substituting an unrelated generic icon or generated logo when a real project logo exists.
