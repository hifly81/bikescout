# Changelog - BikeScout

## [1.3.2]
* analysis - sonarcube revision ([4ec5e0a](https://github.com/hifly81/bikescout/commit/4ec5e0abd74b26ea556e34306e327d2930e7f36f))
* release: prepare version 1.3.2 ([6677cbe](https://github.com/hifly81/bikescout/commit/6677cbe116d2e861acc6776d0ffb620cefc5f9e8))
* site/race - added capoliveri 2026 analysis ([aa6886a](https://github.com/hifly81/bikescout/commit/aa6886a76ee74b5dc58ddbb76f0cd31421d440de))
* feat: added agents skills ([ff5bb70](https://github.com/hifly81/bikescout/commit/ff5bb708fb76a1dd4e8c3cdea36f0441734928e4))
* fix: tool trail scout simple is not returning a validate result ([058c03f](https://github.com/hifly81/bikescout/commit/058c03ff8d565cb1ee65837468ea1e37543a697f))
* docs: added configs for the popular MCP clients  - part 2 ([83db1eb](https://github.com/hifly81/bikescout/commit/83db1eb53f689e0511205186c10f33775abb941f))
* docs: added configs for the popular MCP clients ([067b4df](https://github.com/hifly81/bikescout/commit/067b4df113a086c2517b77a0ced460ddc6871932))
* refactor(logic): implement fitness-aware duration estimation to ensure nutritional safety ([e0ac201](https://github.com/hifly81/bikescout/commit/e0ac201b0ea722e2404a4ab3de09a599916e1f1d))
* site: added race analysis section ([d21d04b](https://github.com/hifly81/bikescout/commit/d21d04bc775589d92ed62abfa69b1590c41a4011))
* perf(core): replace slow geodetic loop with fast equirectangular distance approximation ([9b95207](https://github.com/hifly81/bikescout/commit/9b95207d1787394be3aaabac7ca23e1553693e14))
* feat(weather): add wind direction data to enable alignment scoring ([6a1921f](https://github.com/hifly81/bikescout/commit/6a1921f2c57a0be24640e8b061d80a39ab492c2d))
* refactor(nutrition): pivot to personalized physiological intelligence ([b314f9d](https://github.com/hifly81/bikescout/commit/b314f9d88ca665558b5daa6b551659addd2a781c))
* feat: add weight and gender-aware sweat rate scaling to nutrition engine ([ef739de](https://github.com/hifly81/bikescout/commit/ef739defc5c4f61617fe29506ecb73a2b2754e36))
* feat(mud): add seasonal saturation bias ([d6e6ab6](https://github.com/hifly81/bikescout/commit/d6e6ab6d1aade03db5324e869bfcaf1be8dc2336))
* fix(logic): geodetic segmet impl with step = 5 ([8c30d62](https://github.com/hifly81/bikescout/commit/8c30d628184c46aeba517d80a145bce3aac64bba))
* fix(logic): correctly override surface_analysis with None in response payload ([0b86b5d](https://github.com/hifly81/bikescout/commit/0b86b5df12bac1b5bb7300ac4b9e1232a8b81fc1))
* fix(routing): diversify second fallback attempt by stripping waytype extras ([bf65eee](https://github.com/hifly81/bikescout/commit/bf65eeed4c2e872091b5f22e60df912fc73012b7))
* fix pydantic validation error when map is excluded ([b112d1e](https://github.com/hifly81/bikescout/commit/b112d1e74b1423c276eadee558b06987e57b0764))
* Update README to remove social media badges ([c45c357](https://github.com/hifly81/bikescout/commit/c45c3579eec5ac4c6d59a0a0e07590db7593de79))
* doc site part2 ([575aebb](https://github.com/hifly81/bikescout/commit/575aebbbc07efd97fe70ea069d2cae250c38dbba))
* doc site ([0cd0087](https://github.com/hifly81/bikescout/commit/0cd00875c68dac78cc781bbb91938f93f2da34a9))
* Implement mobile menu toggle functionality ([3e20036](https://github.com/hifly81/bikescout/commit/3e2003603864289e49509d7bc166df242bf98fb5))
* Update CHANGELOG for version 1.3.1 release ([b79c0b3](https://github.com/hifly81/bikescout/commit/b79c0b3de00f0e91160f359818f83c05c78d4ac6))

## [1.3.1]
* release: prepare version 1.3.1 ([2e35ebf](https://github.com/hifly81/bikescout/commit/2e35ebf77503531715162b3bfbc857aca2a27d51))
* docs: add warning about implicit output schemas and parsing hallucinations ([d1e5704](https://github.com/hifly81/bikescout/commit/d1e5704a1e1a531d4cd8d54dc5e0934fb52b434d))
* refactor(compatibility): implement surface aggregation and tactical normalization ([1985892](https://github.com/hifly81/bikescout/commit/19858921639a0b3343536858dda8b58de049c800))
* refactor(geodetics): improve aero-tactical wind analysis ([dd99281](https://github.com/hifly81/bikescout/commit/dd99281b94cda929d8c2f7ec33d72b727a09b927))
* feat(mud-engine): add categorical mud_risk_label to payload ([26ec31c](https://github.com/hifly81/bikescout/commit/26ec31c23d627e1869ca2be37fbb80daa7fd95c5))
* feat(mud-engine): implement timezone-aware TAEL� v3.2 reservoir model ([c377aaa](https://github.com/hifly81/bikescout/commit/c377aaaabb73161d3bd4584eb880ea34b6806919))
* refactor: optimize weather normalization and add solar altitude engine ([14bb70b](https://github.com/hifly81/bikescout/commit/14bb70bd3dc8c4e45eb96735db0efaa94c9f8b35))
* Simplify documentation link descriptions in README ([ad86e1f](https://github.com/hifly81/bikescout/commit/ad86e1f6511464545126b26d2df9732bc932acd0))
* changelog ([33e8d6e](https://github.com/hifly81/bikescout/commit/33e8d6e8904172f24e46a86301bc38bdda07a391))

## [1.3.0]
* Prepare release 1.3.0 ([100f872](https://github.com/hifly81/bikescout/commit/100f8721b992a07a97acb3a739c62c4118656d76))
* feat(mud): fix numeric risk bug & formalize TAEL� v3.1 engine ([b17889a](https://github.com/hifly81/bikescout/commit/b17889a1c536c08dc88200e310352608de58d646))
* fix(altimetry): resolve X-axis compression using WGS-84 geodesics ([dc9aa99](https://github.com/hifly81/bikescout/commit/dc9aa99f1a418d9dd50e16b204362cb0636590b5))
* refactor(geodetic): internalize bearing calculation and clean API ([8a56adc](https://github.com/hifly81/bikescout/commit/8a56adc5e14d91e9a0e9ae9df34e694ccb22f3a3))
* removed strava tool ([4e19c52](https://github.com/hifly81/bikescout/commit/4e19c52fd0bc568c5fda15420e520a5a423e7931))
* feat(planner): implement high-precision solar engine and thermal scoring ([1d926e5](https://github.com/hifly81/bikescout/commit/1d926e59d2d0dbf8d32601576f4fefb19065e0ac))
* fix(visibility): implement high-precision solar visibility algorithm ([6149e8d](https://github.com/hifly81/bikescout/commit/6149e8dfe3272f339f90d67d82ab962c186f33f2))
* fix(planner): implement frost and extreme temperature penalties ([7dc8fbb](https://github.com/hifly81/bikescout/commit/7dc8fbb34b3913bcc270314f100e1fff32ae460c))
* refactor: - Added  as an integer field for precise physics calculations. ([d9ac849](https://github.com/hifly81/bikescout/commit/d9ac849f00d931913de77d77b71475b0ba524084))
* fix: ensure case-insensitive bike_type matching in analyze_compatibility ([5acc381](https://github.com/hifly81/bikescout/commit/5acc38182e1d543d169272e142bba417c1ae0c3a))
* fix(gpx): correct healed_points metric in tactical export ([5226bbc](https://github.com/hifly81/bikescout/commit/5226bbc7b09f0a87c179505bd465dc54f558c14c))
* feature: add A->B routing capability to Master Orchestrator ([8a8d3ff](https://github.com/hifly81/bikescout/commit/8a8d3ff66eac5a8025774e0f873b59cfe5dd6f97))
* refactor: replace static speed constants with ([ae1d05d](https://github.com/hifly81/bikescout/commit/ae1d05d3c1c4bae836006cb903e9e2035183fb32))
* feature: implement dual transport support (stdio/sse) ([e61fa92](https://github.com/hifly81/bikescout/commit/e61fa92fd512ecda5f0c6ae11a7900ac472c708e))
* feature: simplify trail_scout tool for better LLM orchestration ([bc04996](https://github.com/hifly81/bikescout/commit/bc04996a7cc4203d9314dff26177c413cfc492e3))
* feature: scouting:gpx method now return a URI with the gpx track ([7958985](https://github.com/hifly81/bikescout/commit/7958985dfd25011d129650f7eef64ae1932da4f8))
* fix: harden map generation with GeoJSON validation and 2D fallback ([4b98964](https://github.com/hifly81/bikescout/commit/4b989640b74bcaa4b0401b46d12db0c757fc54d3))
*     routing_payload = {         coordinates: [[lon, lat]],         options: {round_trip: {length: mission.radius_km * 1000, seed: mission.seed}},         elevation: true,         extra_info: [surface, steepness]     } ([d31ee28](https://github.com/hifly81/bikescout/commit/d31ee28321449b74b794f38bbaa6eba507f1723b))
* feature: elevation_profile_image methos now return a URI with the altimetry profile image ([7c992dd](https://github.com/hifly81/bikescout/commit/7c992dd5bf07d60618dbcb178b93ee2b2ae6d855))

## [1.2.2-release]
* release: version 1.2.2 part 2 ([c2d5bab](https://github.com/hifly81/bikescout/commit/c2d5bab71f37e72a413f02dae4cd5ffff770b042))

## [1.2.2]
* release: version 1.2.2 ([454633c](https://github.com/hifly81/bikescout/commit/454633cf59a08ea1a5279c0246c2389379381f2e))
* feature: created MCP resources ([dedea2b](https://github.com/hifly81/bikescout/commit/dedea2be60e5640b56aa2522795887b96579a211))
* bug: tool poi_scout has now the correct range for radius_km, max 2kn ([39ba8f3](https://github.com/hifly81/bikescout/commit/39ba8f37d8490658349a86628af89a497d229cd9))
* bug: tool hydration_scout now has the correct scale for intensity_Score, 1 to 5 ([106864c](https://github.com/hifly81/bikescout/commit/106864c094fcb9ed25c745df2f7fb33d504ddcec))
* Revise BikeScout project description for clarity ([4581b50](https://github.com/hifly81/bikescout/commit/4581b5015a2b31ec215ca992ae0412b42deaf7da))
* Clarify examples in data ingestion and AI reasoning ([577842d](https://github.com/hifly81/bikescout/commit/577842dbdf37998496fd1d28824e3c1367505c29))
* AGPL-3.0 and update footer ([3dae427](https://github.com/hifly81/bikescout/commit/3dae427c32faf15a0d73abafa2d08723f40b4e0d))
* Change license to AGPL-3.0 and update footer ([82ba387](https://github.com/hifly81/bikescout/commit/82ba387383aad97365217ebe2f35f4b9202c3ae5))
* Update license link and footer information in tael.html ([1fa180c](https://github.com/hifly81/bikescout/commit/1fa180caa5ab8240b976d447ff2f0c3077785c83))
* AGPL-3.0 and update footer ([fb220d4](https://github.com/hifly81/bikescout/commit/fb220d4bd72d454ec38bc5fb30bfb549b7c06078))
* AGPL-3.0 and update footer ([9d7481b](https://github.com/hifly81/bikescout/commit/9d7481b0d02486f83335732f2fd8f936e8417df8))
* AGPL-3.0 and update footer ([0768c84](https://github.com/hifly81/bikescout/commit/0768c845bfcd8ec6e6ea42e36bfe341931eed7bf))
* Change license URL and enhance footer details ([f2af85d](https://github.com/hifly81/bikescout/commit/f2af85d2c2c356b8d0ee2c9a1855746fcef619e6))
* AGPL-3.0 and update footer ([e9b5b24](https://github.com/hifly81/bikescout/commit/e9b5b24fdbbd18edd171e1122f073a0986fe684d))
* Change license to AGPL-3.0 and update footer ([f02b782](https://github.com/hifly81/bikescout/commit/f02b7829e70d916c9e04c421b57f6ee96c4b09bf))
* Change license to AGPL-3.0 and update footer ([55a169c](https://github.com/hifly81/bikescout/commit/55a169c5583555502019310a374d37f2ca06c3a9))
* AGPL-3.0 and update footer ([c532e62](https://github.com/hifly81/bikescout/commit/c532e62245fd3f51a38bd11de86cd7346ecbfec8))
* Update license link and footer information ([ccaf54e](https://github.com/hifly81/bikescout/commit/ccaf54e669e5235e50c457f99541316f8c2047ac))
* Change license to AGPL-3.0 and update footer ([425dcd3](https://github.com/hifly81/bikescout/commit/425dcd3a1c8c3c8c94ad006b6a6bc410a83cfd50))
* Change license to AGPL-3.0 and update footer ([957a0dc](https://github.com/hifly81/bikescout/commit/957a0dca58619093469621f0c4f6001045b16b91))
* Update API documentation with license and data sources ([2cd3b7c](https://github.com/hifly81/bikescout/commit/2cd3b7c94e2ad70f39592b20ea38265b68496219))
* Change license to AGPL-3.0 and update footer ([908faff](https://github.com/hifly81/bikescout/commit/908faff74a80187afd0a02d5eae35dc355968d87))
* Change license to AGPL-3.0 and update footer ([6beea84](https://github.com/hifly81/bikescout/commit/6beea84960720d100d5c957917b05f24609e9777))
* Change license to AGPL-3.0 and update footer ([e2c1d60](https://github.com/hifly81/bikescout/commit/e2c1d604cc49f4f2ae8c10ccd81221d8a628cd04))
* Change license to AGPL-3.0 and update footer ([87c43ba](https://github.com/hifly81/bikescout/commit/87c43ba91d05fadf4808410fcf15fc74e0544618))
* Change license link to AGPL-3.0 and update footer ([7f03f1f](https://github.com/hifly81/bikescout/commit/7f03f1fe897a0aa36415490c7c51bb89651a8119))
* Update license information to AGPLv3 ([52a3e9a](https://github.com/hifly81/bikescout/commit/52a3e9a01b1ba589d396bc22715bfb85c4d6bd86))
* AGPL v3 ([c96aa99](https://github.com/hifly81/bikescout/commit/c96aa994fa65d7652905a18021b45260e14193cb))
* Enhance footer with licensing and disclaimer details ([318a5d7](https://github.com/hifly81/bikescout/commit/318a5d7319b74ab0d88e2abe1320d883073ecfd2))
* Add license and copyright information to weather.py ([aa2bdc8](https://github.com/hifly81/bikescout/commit/aa2bdc85fcaf826500c010c5cebda7c05ab650f0))
* Add copyright and license information to surface.py ([040ebad](https://github.com/hifly81/bikescout/commit/040ebad550e99c52d8bc041ddfcd79bf376dae17))
* Add copyright and license information to strava.py ([58387f7](https://github.com/hifly81/bikescout/commit/58387f764d769a44c0e5ae8fee2378d80e82d7c6))
* Add copyright and license comments to scouting.py ([4f63c18](https://github.com/hifly81/bikescout/commit/4f63c1832e02fe2c81e8093750bc6e873da6944a))
* Add copyright and license information to poi.py ([ca9f1e6](https://github.com/hifly81/bikescout/commit/ca9f1e62850469bfb3a71e4e01d1ff7dd80f51c9))
* Add licensing and copyright information ([52a4db2](https://github.com/hifly81/bikescout/commit/52a4db2dc7c0a41fcfbe882e1d14a6659b30ed66))
* Add license and copyright comments to mud.py ([0bf9d35](https://github.com/hifly81/bikescout/commit/0bf9d35f3a3d1fcb5cbe53f4ae95445d743515cd))
* Add copyright and license information to maps.py ([3734ef2](https://github.com/hifly81/bikescout/commit/3734ef2036741dc043883fdb96b6c23f7a8eff81))
* Add copyright and license information to gonogo.py ([3be476f](https://github.com/hifly81/bikescout/commit/3be476fadae61fc4f9e14ddff1812c3d3e484812))
* Add copyright and license information to geophysic.py ([0574728](https://github.com/hifly81/bikescout/commit/0574728fd47e68729994549c7d3fb8527e6a741c))
* Add copyright and license comments to geocoding.py ([53cc019](https://github.com/hifly81/bikescout/commit/53cc019cff6c108ebc528fc260c12fe7de814d8a))
* Add license and header comments to bike_setup.py ([780583c](https://github.com/hifly81/bikescout/commit/780583c429a61b9ced84b1772bd2a2af3bd33d38))
* Add license and copyright comments to battery.py ([1aece83](https://github.com/hifly81/bikescout/commit/1aece839eda68482d190411a7715be5a655360a5))
* Add copyright and license information to altimetry.py ([4c726f9](https://github.com/hifly81/bikescout/commit/4c726f9860ce367cfbc7cd0198c98d0e3c514901))
* Add copyright and license information ([cda6fd4](https://github.com/hifly81/bikescout/commit/cda6fd4efa5969c7ad77291bf1d1510bc0978493))
* Add license and copyright information to schemas.py ([d7ada87](https://github.com/hifly81/bikescout/commit/d7ada874fcafa354c7f960f1fda58f36615f29db))
* Add copyright and license information ([a314880](https://github.com/hifly81/bikescout/commit/a314880cb2f3019c9b26144af06251882c2b9065))
* Add copyright and license information ([3959720](https://github.com/hifly81/bikescout/commit/39597207328ba86662787a216e66a33097cda11f))
* Add copyright and license comments to mcp_server.py ([b65b088](https://github.com/hifly81/bikescout/commit/b65b08829bfe15588c1be327247c57766c7bc6ed))
* AGPL-3.0-only ([49a4a3d](https://github.com/hifly81/bikescout/commit/49a4a3d7616aaf28991bfad516b1e825a2aebda8))
* AGPL-3.0 ([919a8e1](https://github.com/hifly81/bikescout/commit/919a8e158f3d0d9ff25513e27066c57a2ee71169))
* Change license to AGPL-3.0 and explain rationale ([5507aa3](https://github.com/hifly81/bikescout/commit/5507aa3981faf3b379f2b6060b7a9964b17f0d2d))
* Add LICENSE file ([92c36cd](https://github.com/hifly81/bikescout/commit/92c36cd686f7e5b0bff34e229c5eb626eb66a2c6))
* Update index.html ([5060ec8](https://github.com/hifly81/bikescout/commit/5060ec84df2f31758a43cc1336362bb5db5985fa))

## [1.2.1]
* release: prepare version 1.2.1 ([0f795ea](https://github.com/hifly81/bikescout/commit/0f795ea491178ceb0496c7054e33858230c4b7f2))
* feature: Advanced Post-Ride Analytics and Model Calibration Loop  - Fix #68 ([bcf6a8e](https://github.com/hifly81/bikescout/commit/bcf6a8efad987870370e75a1b02e6c1c3e572070))
* feature: Implementation of a Physics-Based Energy Model (E-MTB Power Simulation)  - Fix #58 ([a5b4542](https://github.com/hifly81/bikescout/commit/a5b45425e963d7c03782dbca580faf6610a78a23))
* feature: Implementing Production-Grade Geocoding with Caching, Rate-Limiting, and Result Ranking  - Fix #60 ([bdcbb70](https://github.com/hifly81/bikescout/commit/bdcbb70802d5b39404c7b74d0c6830d6f245b196))
* feature: implemented Implementing a Metabolic Flux Model and Correcting Intensity Scaling  - Fix #65 ([92413cf](https://github.com/hifly81/bikescout/commit/92413cfeb126a27b995f18f77ec0971c61fc0745))
* feature: implemented the TAEL v2.0 Reservoir Model (Time-Integrated Solar Drying & Soil Saturation) - Fix #64 ([2e6c83f](https://github.com/hifly81/bikescout/commit/2e6c83f3d0d59f10d45094faebae500f077a0fc0))
* Update latest version to 1.2.0 in index.html ([3d89f99](https://github.com/hifly81/bikescout/commit/3d89f99152f5c4a128520365f5c941f9de9280f7))

## [1.2.0]
* refactoring: tools params reinforced with defaults ([4e5ebc0](https://github.com/hifly81/bikescout/commit/4e5ebc0b3b1d3b09a9c2447ce62d8b5f7a786fa7))
* release: prepare version 1.2.0 ([1ddfdc1](https://github.com/hifly81/bikescout/commit/1ddfdc1ca43682961cc17af31923e0160950cc2c))
* site: features in indx page ([94f12ba](https://github.com/hifly81/bikescout/commit/94f12baa49c7f5a9d6a80ef1605b729ed86d1772))
* refactoring: race analysys pdf report powered ([6580796](https://github.com/hifly81/bikescout/commit/6580796c067f737cd5589e1e91de17915308b7e0))
* refactoring: race analysis with pdf report analysis ([b0632e0](https://github.com/hifly81/bikescout/commit/b0632e052f24684254b57cc751e12d938683e71e))
* refactoring: race analysis v2 ([5b42fcb](https://github.com/hifly81/bikescout/commit/5b42fcb6c023e1853e5c2e3d73839235a0bbeebe))
* feature: Implementing Timezone-Aware Synchronization and Multi-Factor Risk Scoring - Fix #70 ([f7a9ae1](https://github.com/hifly81/bikescout/commit/f7a9ae14d54b6666a232865999df4dbc3567c39e))
* reafctoring: race analysys as module ([412f549](https://github.com/hifly81/bikescout/commit/412f549a2ec249b306473e51a41441ac479e37de))
* refactor: Future-Date Predictive Audit (Integrating Weather, Mud, and Hydration for Pro-Racing) - Fix #75 ([998d29a](https://github.com/hifly81/bikescout/commit/998d29a7877fe246ba2edbfbd64abac74a8b85fc))
* refactoring: move site html in blog and encyclopedia folders ([5c3d712](https://github.com/hifly81/bikescout/commit/5c3d712ec9781bb8387ed81bf119c61e878f06c3))
* Update latest version to 1.1.2 in index.html ([ea55487](https://github.com/hifly81/bikescout/commit/ea55487d7d858c961e877e8907482ac68c96344e))

## [1.1.2]
* Prepare for Release 1.1.2 ([d828316](https://github.com/hifly81/bikescout/commit/d8283160d660305b5733ad7423a05739757458e3))
* Fix #44 Site: move index in site/ folder ([f843230](https://github.com/hifly81/bikescout/commit/f84323082b83cab7990c1fecca49917a00632404))
* refactor: upgrade to geodetic engine v1.1.2 with WGS-84 precision and integrated bearing telemetry - Fix #61 ([973d812](https://github.com/hifly81/bikescout/commit/973d812bb67f084464e2c8ae42f4b42a162337f4))
* Update blog post content for Giro 2024 Stage 2 ([fe0a184](https://github.com/hifly81/bikescout/commit/fe0a1840178f731012d09e18bc47f51dd937f134))
* Revise Giro d'Italia 2024 Stage 2 description ([8d23a2d](https://github.com/hifly81/bikescout/commit/8d23a2dd2691ae325e971de1d1178175f37a0b83))
* Remove elevation data source from README ([a255fef](https://github.com/hifly81/bikescout/commit/a255fefc485281a5a27cc2528f7e4b4072487468))
* Update section title from 'Cat 1 Finale' to 'Stage' ([f153058](https://github.com/hifly81/bikescout/commit/f1530589caaa56b0ab7075674f79595cab825683))
* blog refactoring ([b5dc2d8](https://github.com/hifly81/bikescout/commit/b5dc2d8d0460ef9b4b24ad1bad40eb34aa8d52a0))

## [1.1.1]
* release 1.1.1 ([1d06339](https://github.com/hifly81/bikescout/commit/1d06339749aa675589c5815dd91e38d1a57fea3a))
* removed Stadia,Fix #74 ([ec44264](https://github.com/hifly81/bikescout/commit/ec44264e49ce314ae90695342d8fc494e3d7d9ce))
* Remove badge for hifly81/bikescout ([3825108](https://github.com/hifly81/bikescout/commit/3825108d6e12523f4be7a8d3ef831c63b3ff8adc))

## [1.1.0]
* Implemented logic for Pro-Race Mode: GPX Track Analysis & Pro-Cycling Performance Insights - Fix #72 ([a8e9439](https://github.com/hifly81/bikescout/commit/a8e943918df644d31bdb8382093e51e636d7a1ab))
* added target date in tools ([c327cd7](https://github.com/hifly81/bikescout/commit/c327cd7dbda4c7fa4f1ff3a442b4468e8eaf88d9))
* removed unecessary default args in tools ([e217005](https://github.com/hifly81/bikescout/commit/e217005771f069a78e9df2938d92d52514689ca5))
* Update bikescout_ollama.md with API docs link ([3f8142b](https://github.com/hifly81/bikescout/commit/3f8142b52ae2f5ff160afa998261f2f4f2075719))
* Update README with Docker teardown instructions ([98ce350](https://github.com/hifly81/bikescout/commit/98ce350cffeb8e63f2398b1350b6912fe2849ab2))
* info for ollama ([73ca21b](https://github.com/hifly81/bikescout/commit/73ca21b508facb149b247bad2363195586154eaf))
* Refactor BikeScout deployment instructions ([4192175](https://github.com/hifly81/bikescout/commit/4192175ca986c3ae6c4767749db2f0483ababdc8))
* Clarify LLM Key requirements in README ([f5b973b](https://github.com/hifly81/bikescout/commit/f5b973b7d6ceda938b6b86a453f5e7426b25e1d9))
* Update README.md ([1de5aaf](https://github.com/hifly81/bikescout/commit/1de5aaf961568374f1a487b89c80811fa7c5a8ac))

## [1.0.3]
* added info for OpenClaw and Ollama ([ef7dab0](https://github.com/hifly81/bikescout/commit/ef7dab0dc310293abe1317d1b3da84f0f31f25df))
* mastering SEO ([a79c300](https://github.com/hifly81/bikescout/commit/a79c3002f88855fe1cffa9624bba1148fcb48a84))
* Update header title for BikeScout ([017009f](https://github.com/hifly81/bikescout/commit/017009f1b55b358443e3f6d8884a3dedea521065))
* Add JSON-LD structured data for BikeScout ([6d2f512](https://github.com/hifly81/bikescout/commit/6d2f5123b9273fd8375bede2a6d978b8b878e9e5))
* Update wallsense.html ([0c606e5](https://github.com/hifly81/bikescout/commit/0c606e552c436e46b2aed885815c4f3bc67dcdbb))
* Add structured data for BikeScout application ([cb006d2](https://github.com/hifly81/bikescout/commit/cb006d245b4cae1de5a2fa0e7a939db4e0c9cad7))
* Update tael.html ([eaac356](https://github.com/hifly81/bikescout/commit/eaac356e508f5f3c4172eeb1f0ae7467c6c9ec05))
* Add structured data for BikeScout application ([0f32a1a](https://github.com/hifly81/bikescout/commit/0f32a1a5178de2f6186edddbb8eb2c35ef5992dd))
* Add structured data for BikeScout application ([8c9313e](https://github.com/hifly81/bikescout/commit/8c9313e717f1d0730da7220075f2fcdaad90de35))
* Update s_scale_enc.html ([cd145f6](https://github.com/hifly81/bikescout/commit/cd145f67ead51bdd0ced368f974f26077709bab7))
* Add JSON-LD structured data for BikeScout ([ea99abc](https://github.com/hifly81/bikescout/commit/ea99abc9c7bb94fe4eee7f08dfd26a9ee48264c8))
* Update pro_climb_enc.html ([3cec3b7](https://github.com/hifly81/bikescout/commit/3cec3b784bbf0a57400e8c6099c14ce4ca5cc4cc))
* Update hydration_scout_enc.html ([29a746b](https://github.com/hifly81/bikescout/commit/29a746b1784376131f9cb451e70c6f4b8470bdb8))
* Add structured data for BikeScout application ([7ff01d3](https://github.com/hifly81/bikescout/commit/7ff01d3897dbd50808c93e13c831b10dae881ec2))
* Update geodesic_accuracy_enc.html ([42865dc](https://github.com/hifly81/bikescout/commit/42865dc2d730a00d2af868ce5b025882c4495fbc))
* Update dst_enc.html ([45a260f](https://github.com/hifly81/bikescout/commit/45a260f3013dc8164dc3ded628895546d546b2f6))
* Update cycling_encyclopedia.html ([928887a](https://github.com/hifly81/bikescout/commit/928887ade63321665edb7a6e2491b5e69a81f6a8))
* Add structured data for BikeScout application ([03ca4e2](https://github.com/hifly81/bikescout/commit/03ca4e243788f202a54d961ae83ef912ad4879b5))
* Add structured data for BikeScout application ([72f6f9a](https://github.com/hifly81/bikescout/commit/72f6f9a03895774cbaa32a41c6f2a77722145cbb))
* Add JSON-LD structured data for BikeScout ([7db2875](https://github.com/hifly81/bikescout/commit/7db28751f56fd7ce7a959ab66767f64d268bf0ad))
* Revise JSON-LD for BikeScout application ([54f6662](https://github.com/hifly81/bikescout/commit/54f666236cea3308e3e12aaa43ef779876b02f93))
* Update title and header for clarity and branding ([dce5cc6](https://github.com/hifly81/bikescout/commit/dce5cc6fa15cb6a5f6b292bec58d985d9dd6c72a))

## [1.0.2]
* Implemented logic for Metabolic & Hydration Planning Tool - Fix #48 ([1559cc4](https://github.com/hifly81/bikescout/commit/1559cc44db7ac13260598a943130ab8e6a5ae060))
* Refactor README to improve documentation structure ([ec30904](https://github.com/hifly81/bikescout/commit/ec309047ee8a0b473e2e98cf75bb45be4791bcd8))
* Update print statement from 'Hello' to 'Goodbye' ([8e43a13](https://github.com/hifly81/bikescout/commit/8e43a13b943cd92faf86bc09794066f84af145ff))
* Update README with new feature descriptions ([fedbe7d](https://github.com/hifly81/bikescout/commit/fedbe7d55f90c0e23370030461ef6de8c800b556))
* refactored site - part 2 ([f1ace0d](https://github.com/hifly81/bikescout/commit/f1ace0d67c412e6871a9974aa2223a7f46f3a3ca))
* refactored site ([9dcd0b3](https://github.com/hifly81/bikescout/commit/9dcd0b310278f23dd0f2bf5be54699a41e6d3aef))
* Update file paths in README.md ([d629d59](https://github.com/hifly81/bikescout/commit/d629d5954406f6acbb0b548b04da39a5f734f71d))

## [1.0.1]
* Implemented logic for Payload Management & GPX Offloading - Fix #50 ([65b751b](https://github.com/hifly81/bikescout/commit/65b751b059368b9c9ebc3819e3fe65c8a99e26e6))
* Readme 1.0.0 ([7f9a3d9](https://github.com/hifly81/bikescout/commit/7f9a3d9975180562906973d46f5be4b5e44df453))

## [1.0.0]
* Implemented logic for Evolve Prompt into Skills - Fix #41 ([e5a62bf](https://github.com/hifly81/bikescout/commit/e5a62bfbaa94851e05c494797aa5c8073514fc24))
* Implemented logic for E-Bike Battery Consumption Prediction  - Fix #45 ([f9a052c](https://github.com/hifly81/bikescout/commit/f9a052ccf425b6ac62bde9a1c2708f050dc7fad6))
* Implemented logic for Replace Linear Sanitization with Simple Moving Average (SMA) for Elevation Data - Fix #46 ([19083a2](https://github.com/hifly81/bikescout/commit/19083a224ea0afa6f85a1e19d31e1cfb7042f09a))
* Implemented logic for Elevation Profile Generator - Fix #49 ([4fab9d6](https://github.com/hifly81/bikescout/commit/4fab9d670b91e61020f3e78a82fb85f63383d2c0))
* Implemented logic for  Fitness-Level Awareness  - Fix #52 ([8fcddd4](https://github.com/hifly81/bikescout/commit/8fcddd43739dc28c1235187009067ff0cc104851))
* Implemented logic for Physics-Based Compatibility Logic  - Fix #53 ([1b1c370](https://github.com/hifly81/bikescout/commit/1b1c3702ac2533c4ecf48da02a244ab12dbdf61d))
* Implemented logic for Context-Driven Schemas - Fix #51 ([77b39cc](https://github.com/hifly81/bikescout/commit/77b39ccf3449157fc29bec312c3eba29d9e21559))
* Doc: created page, how to obtian a Strava key ([f371829](https://github.com/hifly81/bikescout/commit/f371829228bef98093077efd6eca2491802f5ee0))
* Bump to version 1.0.0 ([f6e062e](https://github.com/hifly81/bikescout/commit/f6e062e0ba8830157dec0d4d2ff12dda3256ceda))
* added glama.json ([3786a97](https://github.com/hifly81/bikescout/commit/3786a973fe74c4c5c50b88e17b57a850a4a68b85))

## [0.9.5]
* added new tool: ride_window_planner ([e94b8ae](https://github.com/hifly81/bikescout/commit/e94b8aee40fc30b05e19123b991ba1f47f72fc27))
* Working in README ([0d870a4](https://github.com/hifly81/bikescout/commit/0d870a4f6edd9e14ea581c64477fa5d56746513e))
* added addiitonal args in tool trail_scout ([eab8b51](https://github.com/hifly81/bikescout/commit/eab8b5131b5736574105f1ed75d4b24f6ef1d3ec))
* Update GitHub link in index.html ([d60e315](https://github.com/hifly81/bikescout/commit/d60e3157724c7d7a9440e27bff9c9bf4a19dd85e))
* Update README with MCP client integration details ([2d318ef](https://github.com/hifly81/bikescout/commit/2d318ef7b50148a690027d49d98e2fdc98dc9d63))
* Site: index main title - 3 ([c58cef6](https://github.com/hifly81/bikescout/commit/c58cef6898a4f7d146c6553d5f1029d77f56602e))
* Site: index main title - 2 ([9db5da0](https://github.com/hifly81/bikescout/commit/9db5da08e0279289a481a086bfb5ca44157c67c1))
* Site: index main title ([d5b2c88](https://github.com/hifly81/bikescout/commit/d5b2c88ade51c29da84daa3e9f4d271d172eb5e2))
* Site: added 3 new entries for encyclopedia ([20a4d20](https://github.com/hifly81/bikescout/commit/20a4d20379758cf73c3c9f861fe84c8a8821df5d))
* Site: fix regression in menu for mobile - 3 ([393f370](https://github.com/hifly81/bikescout/commit/393f37091868f65cdc8b170d7c49bb6b660fabe1))
* Site: fix regression in menu for mobile - 2 ([7f78f87](https://github.com/hifly81/bikescout/commit/7f78f8732798fd88b1002b786d946c7f8b946f66))
* Site: fix regression in menu for mobile ([280c68a](https://github.com/hifly81/bikescout/commit/280c68ac6f6549cab33f7379f038df2d65b898aa))

## [0.9.4]
* added site: encyclopedia ([6832d86](https://github.com/hifly81/bikescout/commit/6832d86577e3c679d46df4c736e723b0fb35b9c3))
* added glama badge ([3c94e8c](https://github.com/hifly81/bikescout/commit/3c94e8ce07f3c566b91f0477c94ea0e826c42b09))

## [0.9.3]
* Implemented haversine_distance utility to correct latitude distortion. ([416f6a8](https://github.com/hifly81/bikescout/commit/416f6a8b2891443a28399e2f90ca90f65b264771))
* added additional args to trail_scout tool: include_gpx, include_map, output_level ([b595ed6](https://github.com/hifly81/bikescout/commit/b595ed624cda589afedfbe41a0c07e98dc5e377f))
* get_surface_analyzer removed mock mud risk impl and integrated with Tael ([328a0f8](https://github.com/hifly81/bikescout/commit/328a0f8ad0e33b770b16cf98e57fab7383ded697))
* added Stadia Maps integration. Implemented Logc for GPX Generator Refinement (generate_tactical_gpx) - Fix #38 ([7f6a15e](https://github.com/hifly81/bikescout/commit/7f6a15e3b03d38842de8b471e7af7b9c6875d9ee))
* added payload_version in tools ([a38c02a](https://github.com/hifly81/bikescout/commit/a38c02a7bcd3d38716f32c1cf77d42d6e16f3421))
* Bump to version 0.9.3 ([9654e4e](https://github.com/hifly81/bikescout/commit/9654e4e9e29306d40b3879b0c33e8ca2076e90fd))
* chore: upgrade to standalone fastmcp package to support remote HTTP/SSE connections ([2d46140](https://github.com/hifly81/bikescout/commit/2d4614097643afe22640f3321cf2f7106a41480d))

## [0.9.2]
* added tael algo ([2353ee4](https://github.com/hifly81/bikescout/commit/2353ee477c2ae9f5a960490f562bfcf119471d23))
* added live demo ([2b32e5b](https://github.com/hifly81/bikescout/commit/2b32e5bbc5d1e9a4aaa4f16c355ff0de360cef5d))
* Update README with video and remove broken link ([5a8f2db](https://github.com/hifly81/bikescout/commit/5a8f2db1fcf62e773c5fdd900a2da599d6467fa1))
* Update README with asset link ([884a896](https://github.com/hifly81/bikescout/commit/884a896c97fc462231ec4ce786e41561f6da2cfe))
* publications in about section ([f8db6f9](https://github.com/hifly81/bikescout/commit/f8db6f96152ad07df15290320492d2596d2637f7))

## [0.9.1]
* refactored prompts section. Fix #32 Fix #33 ([82da884](https://github.com/hifly81/bikescout/commit/82da884152039ae132892faf6ac2fde947af5045))
* Add Google Analytics tracking script to why_mcp.html ([9dd332d](https://github.com/hifly81/bikescout/commit/9dd332dd754a9fed2cce70ed1302c8c4939f3aba))
* Add Google Analytics tracking script ([abf4a7e](https://github.com/hifly81/bikescout/commit/abf4a7e93818e947e4bda8f42f4ec7beab3801da))
* Add Google Analytics tracking script ([c41337e](https://github.com/hifly81/bikescout/commit/c41337e4b43c1e1c2c1825f3304877fe9a843239))
* Add Google Analytics tracking script to hello_bikers.html ([c84897d](https://github.com/hifly81/bikescout/commit/c84897d1bd0f318c89618b6fcd84bff3388952f4))
* Add Google Analytics tracking script to blog.html ([5e8f19b](https://github.com/hifly81/bikescout/commit/5e8f19bf07feda45ff92cb7881d5f56ccf69d372))
* Integrate Google Analytics tracking script ([679e816](https://github.com/hifly81/bikescout/commit/679e816af0c93f65adf6b27820d83ed331323a7f))
* Integrate Google Tag Manager into index.html ([12ad39c](https://github.com/hifly81/bikescout/commit/12ad39c18da70e6f3c4ce4aa90b562f472dc9846))
* Add new URLs to sitemap.xml ([bb262c5](https://github.com/hifly81/bikescout/commit/bb262c5d4b8e8c62bd748b302bbbd49e611777cb))
* Add team and technology stack information to humans.txt ([2d490a2](https://github.com/hifly81/bikescout/commit/2d490a2cd96b2ab0cf14684dd25830614045da56))
* Create robots.txt for web crawler directives ([ce36330](https://github.com/hifly81/bikescout/commit/ce363304c7e655be542556c409f51325781fc082))
* Add CITATION.cff for project citation information ([6033a20](https://github.com/hifly81/bikescout/commit/6033a20320dc3cd45fd5d1328603a6b53b439062))

## [0.9.0]
* Update version badge to 0.9.0 ([f2a338c](https://github.com/hifly81/bikescout/commit/f2a338ccecc1f9cc074a24f3e1854648e141ed4d))
* implemented logic for Integration with Strava API for Historical Activity Analysis - #23 ([3f9d2a0](https://github.com/hifly81/bikescout/commit/3f9d2a0c8304407ddd2788ebe240af058bfcc2c5))

## [0.8.3]
* added Quickstart steps in README ([9003c79](https://github.com/hifly81/bikescout/commit/9003c7995a72a478653405986460e41ce23931f6))
* implemented logic for Evolution of Mud Risk Engine: From Static Sensitivity to Environmental Contextualization - no phase 2 - #26 ([ef4bd77](https://github.com/hifly81/bikescout/commit/ef4bd7728edd2f85491f22d31b90b67970d1aaa7))
* implemented logic for Dynamic Tire Intelligence: Context-Aware Pressure & Setup Calculations  - Fix #27 ([54ef73b](https://github.com/hifly81/bikescout/commit/54ef73b149142e7f00ba5e18dceacce11e837945))
* Fix grammatical errors and improve sentence flow ([b328692](https://github.com/hifly81/bikescout/commit/b328692708233cf2e6c4bd6d35882287001c08a3))
* Update article structure and add mobile menu script ([f55c620](https://github.com/hifly81/bikescout/commit/f55c62035110ad5b2533b641cf95df8b9b22bd9b))
* Add new blog articles about cycling events ([1312067](https://github.com/hifly81/bikescout/commit/13120673c5d4508c0c7005bc3db49f7afed4cf8c))
* Refactor header and footer structure in roubaix_2026.html ([684625f](https://github.com/hifly81/bikescout/commit/684625f85baccd91f8318c47a7df65c4f9f0ec30))
* Create roubaix_2026.html for race analysis ([e2191a6](https://github.com/hifly81/bikescout/commit/e2191a659b54b05e0fc1ba5455cf90b50daf5572))
* Fix markdown formatting for section headers in README ([ff1cb0d](https://github.com/hifly81/bikescout/commit/ff1cb0d3a8b027feabb7cbfcc651b96444df9faa))
* Update README.md ([2a36911](https://github.com/hifly81/bikescout/commit/2a369116b69b8e24324a8d36e592e28f101601e8))
* Fix syntax error in mud_index calculation ([b1d3477](https://github.com/hifly81/bikescout/commit/b1d34776687d3dba2f37a355039b18c8edb87d2b))
* Revise content on elevation data and tire intelligence ([7cb861c](https://github.com/hifly81/bikescout/commit/7cb861c988ca1433245eaeff763f0f8ba4f2f2b2))
* Update metric card styling in index.html ([965d797](https://github.com/hifly81/bikescout/commit/965d7970b9a7ca22189d4db0c7dd34cc5435477c))
* Fix punctuation in blog article paragraph ([9d42297](https://github.com/hifly81/bikescout/commit/9d4229781516cd3db2db432d33dfbf791efe953c))
* Enhance footer with project tags ([6341ea6](https://github.com/hifly81/bikescout/commit/6341ea6ce0812563345a2572480749fcea4d2c88))
* Fix punctuation and formatting in why_mcp.html ([c0f6c0e](https://github.com/hifly81/bikescout/commit/c0f6c0ee02a1ddc7af58c8422905ac6b901489d0))
* Implement mobile menu for site navigation ([ed9d5f5](https://github.com/hifly81/bikescout/commit/ed9d5f5a3a16cc8c5edd96335b27c8d177e57dd7))
* Swap content of two articles in blog.html ([d01d597](https://github.com/hifly81/bikescout/commit/d01d5971779cdb2555c867be057cf132597a172d))
* Update blog title from 'Field Notes' to 'BikeScout Blog' ([5bf1701](https://github.com/hifly81/bikescout/commit/5bf1701dbee154e41c6b020941c6413607bb28e7))
* Revise title, meta tags, and article content ([fedd231](https://github.com/hifly81/bikescout/commit/fedd2318c552d534d069cb8cbf1fcc3e731fd097))
* Remove transmission received header from HTML ([39aff88](https://github.com/hifly81/bikescout/commit/39aff881b41e65f2a1d753143f9f46908bd9f079))
* Update blog article titles and links ([e6e7270](https://github.com/hifly81/bikescout/commit/e6e72706998e4c33f973b8bf51728a7a8a8e4f48))
* Add new HTML page for MCP architecture overview ([450d388](https://github.com/hifly81/bikescout/commit/450d3884e7738c65351a7de0cf548b2ca90cc167))
* refactored index page ([61bd553](https://github.com/hifly81/bikescout/commit/61bd5538848471b74fbd870923a9571c368feeef))
* refactored about page ([4dd1cd9](https://github.com/hifly81/bikescout/commit/4dd1cd9744dfafde65e3e266941d13ef1932862e))

## [0.8.2]
* implemented logic for GPX Enrichment with Smart Waypoints  - Fix #12 ([dab08b6](https://github.com/hifly81/bikescout/commit/dab08b691709929c1ea3da94825610f6f327fbf8))

## [0.8.1]
* added site pages ([740a30e](https://github.com/hifly81/bikescout/commit/740a30e5ccc5f187f13679ebde758bb0ae20167e))

## [0.8.0]
* implemented logic for redictive Mud Risk Analysis - Fix #10 ([49ffe66](https://github.com/hifly81/bikescout/commit/49ffe661d499902fc23f80ff0870b84583ea34b3))
* implemented logic for POI Scout - Fix #5 ([1cda252](https://github.com/hifly81/bikescout/commit/1cda2520fe5903345fd32bb9acc47b9a9e81e894))
* implemented logic for Surface-Aware Routing - Fix #6 ([5972db9](https://github.com/hifly81/bikescout/commit/5972db9bac6a86bbc210cc019a97bbac8e673ac0))

## [0.7.3]
* implemented logic for Advanced Technical Difficulty (MTB/SAC Scale) - Fix #11 ([b2fac53](https://github.com/hifly81/bikescout/commit/b2fac53be3064333f5048f3a051e162587f41dee))
* implemented logic for bike type differentiator, MTB, Enduro, Road ([5cc70bb](https://github.com/hifly81/bikescout/commit/5cc70bb3e3f0f44da740ea2a995c3b6c151fddef))
* implemented logic for Climb Categorization - Fix #7 ([e95f117](https://github.com/hifly81/bikescout/commit/e95f11776653652733619999e4e14a39d6a6e03f))
* implemented logic for Bike Setup Compatibility - Fix #9 ([1172f66](https://github.com/hifly81/bikescout/commit/1172f668808ede2b64f7805d7891a0c577a4cbd5))
* Bump version from 0.7.1 to 0.7.2 ([933aebd](https://github.com/hifly81/bikescout/commit/933aebd575a80437513afe57afa8340f9e33be85))

## [0.7.2]
* refactoring: prommpts and resources are now separated from mcp_server ([69372f0](https://github.com/hifly81/bikescout/commit/69372f0fb158e0ccaf3d40af08cabd3b81b86348))
* added prompt Dolomiti Fix #19 ([79328b3](https://github.com/hifly81/bikescout/commit/79328b390476ad2d362d713f284139d4dd9307e4))
* Delete smithery.yaml ([7bf2b70](https://github.com/hifly81/bikescout/commit/7bf2b7072b481a9e4820fa02871e252d2a9abee5))
* Add startCommand configuration to smithery.yaml ([35129a6](https://github.com/hifly81/bikescout/commit/35129a6ddd007c707866831c97cb104d6e209dcb))

## [0.7.1]
* Update version badge to 0.7.1 ([6f3aef5](https://github.com/hifly81/bikescout/commit/6f3aef55b2101eef5e3ad08c5c52bda3778e1b04))
* Bump version to 0.7.1 and update project metadata ([64e71ac](https://github.com/hifly81/bikescout/commit/64e71acfb5fe295802afe46090ada7990264c951))
* Add initial HTML structure for BikeScout website ([fe8e60b](https://github.com/hifly81/bikescout/commit/fe8e60bba9bca31751a144fd201f659f04cf1057))

## [0.7.0]
* added first prompt and resources ([13141bf](https://github.com/hifly81/bikescout/commit/13141bf0d5996bd6889f1ab52b745923be317211))

## [0.6.2]
* added info in pyproject.toml ([4421a92](https://github.com/hifly81/bikescout/commit/4421a9223307abce143b552979b34010b747a841))

## [0.6.1]
* release for PyPi - part 3 ([662ba9e](https://github.com/hifly81/bikescout/commit/662ba9e5c16e241e23a680ac7e70b055465365ad))
* release for PyPi - part 2 ([cdda44c](https://github.com/hifly81/bikescout/commit/cdda44cef4c487623f0421cb6431cc345c3b776d))
* release for PyPi - part 2 ([50805ea](https://github.com/hifly81/bikescout/commit/50805ead190733d3ee105d650d90b0fdf495c8de))
* release for PyPi ([5a810d4](https://github.com/hifly81/bikescout/commit/5a810d4bb103dc2959726c14be3030fdc3efacc4))
* README added contrib section ([0f717ce](https://github.com/hifly81/bikescout/commit/0f717ce62d3e74a52b0be07158a2d5917eb77322))
* Update version badge to 0.5.1 ([9ad40a4](https://github.com/hifly81/bikescout/commit/9ad40a455e049557424f60b58ddcec28e51a9da2))

## [0.5.1]
* README added new section ([c842d23](https://github.com/hifly81/bikescout/commit/c842d23175262229a1958e001a2ad34b7817f621))

## [0.5.0]
* added geocoding tool ([a95b3e5](https://github.com/hifly81/bikescout/commit/a95b3e521c24e564cf264ae8dd16912dae7be27e))

## [0.4.0]
* added badges ([9d81b4e](https://github.com/hifly81/bikescout/commit/9d81b4edd79788d9d6a20fec04b5ba601d6554a1))
* Fix #3 - Refine Trail Difficulty Grading Logic ([ab38134](https://github.com/hifly81/bikescout/commit/ab38134c75cbdd1791beb17c2306f7d220af18a0))
* Fix #4 - improved weather forecast advices ([400c4c2](https://github.com/hifly81/bikescout/commit/400c4c2c97d27d8b8fdad3f42576a91b2c4b9ceb))
* Refactor weather API URL to use constant ([14a9314](https://github.com/hifly81/bikescout/commit/14a9314aaf5bce242a63b60027158c2ab66e4335))

## [0.3.1]
* Update version badge in README.md to 0.3.1 ([1df50a7](https://github.com/hifly81/bikescout/commit/1df50a7e1c421ff7f57956c7f36eaa4c0b4edda0))
* Revise license and add data attributions ([f3126bc](https://github.com/hifly81/bikescout/commit/f3126bce3902fcaeac7b6314af847505fb2fef1c))
* Add GitHub Actions workflow to summarize new issues ([30e26f7](https://github.com/hifly81/bikescout/commit/30e26f76fa6951fda3da8a57afa7a1be2adb1236))
* Add Pylint workflow for Python code analysis ([15fc0d3](https://github.com/hifly81/bikescout/commit/15fc0d3f9e319ffa7e84cf53cb6bd7427cd9e71e))
* Add CodeQL analysis workflow configuration ([df506db](https://github.com/hifly81/bikescout/commit/df506db81870868c04a8fab5b68fcdd49ac9752a))
* Add GitHub Actions workflow for greetings ([9085b54](https://github.com/hifly81/bikescout/commit/9085b5452fc1b7c6cb00d72e6657ee2d09ec298b))
* Update version badge to 0.3.0 in README.md ([60dae19](https://github.com/hifly81/bikescout/commit/60dae199526e80d0265ff2cd7fc9541f35922b34))

## [0.3.0]
* added tool surface analysis ([4f11888](https://github.com/hifly81/bikescout/commit/4f11888171d1826c04d73ba137b2137bbe35f510))

## [0.2.0]
* added tool: weather forecast ([6e06716](https://github.com/hifly81/bikescout/commit/6e06716b238341fa0544c1eadf6e5692ccee2864))

## [0.1.0]
* added examples ([83a0490](https://github.com/hifly81/bikescout/commit/83a0490f5d4b0172f837d523b8d8000984ca75a2))
* first commit ([0334da0](https://github.com/hifly81/bikescout/commit/0334da01cc10f9c3b03ebf899c2549c8cb9437fc))
