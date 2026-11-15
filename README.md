# LUNAR EXPLORER

**Where, and when, to land at the Moon's south pole.**

NASA Space Apps Challenge 2026 · Challenge: *CLPS Lunar Mission Browser* · **Team DexLab 1** · Jazan, Saudi Arabia · team 25

| | |
|---|---|
| 🏠 **Project home** (start here: tool, video and resources) | https://basilsltan62-del.github.io/lunar-explorer/ |
| ▶ **Open the tool** | https://basilsltan62-del.github.io/lunar-explorer/app/ |
| 🎯 **Guided demo** (5 steps inside the tool) | https://basilsltan62-del.github.io/lunar-explorer/app/?demo=1 |
| 🎬 **Project video** | https://youtu.be/V679JfIw5YE |
| 🎞 **Animated presentation** (14 scenes, voice-over script) | https://basilsltan62-del.github.io/lunar-explorer/presentation.html |
| 📄 **7 slides** | [English (PDF)](slides/LUNAR_EXPLORER_7_slides_EN.pdf) · [Arabic (PDF)](slides/LUNAR_EXPLORER_7_slides_AR.pdf) |
| 📘 **User guide** | [English (PDF)](guide/LUNAR_EXPLORER_User_Guide_EN.pdf) · [Arabic (PDF)](guide/LUNAR_EXPLORER_User_Guide_AR.pdf) |
| 📊 **Validation data** | [validation/validation_300_points.csv](validation/validation_300_points.csv) |

---

## The problem

At the lunar south pole the Sun never rises: it circles the horizon, never more than about 1.5° high at the pole itself and about 2° at the sites in this tool. A lander there needs two lines of sight: one to the Sun for power, one to Earth for its radio link. A ridge 100 km away can cut either, and Earth itself rises and sets over a cycle of about 27 days. Commercial (CLPS) landers live about 14 days, so choosing the wrong two weeks can cost the whole mission. In March 2025 the CLPS lander IM-2 (Athena) came to rest on its side in a crater near Mons Mouton; its solar panels could not keep the batteries charged and the mission ended within a day. The tool includes the IM-2 landing area among its seven named sites.

## What the tool does

For any point you click and any start date, LUNAR EXPLORER:

1. computes the **real terrain horizon** of the site in 360 directions from NASA LOLA elevation data, including the Moon's curvature;
2. checks, **hour by hour**, whether the Sun and Earth are above that horizon (positions from NASA JPL Horizons);
3. turns the result into a **decision board**: sunlight, Earth link, darkness, slope, battery and water, each with a colour and a confidence. Every tile opens the law, the data and the numbers behind it;
4. **suggests a better date or site**, and plans a **rover route** to the nearest likely cold trap;
5. **checks itself live** against NASA's published illumination maps.

**Example: same site, same lander, 16 days apart** (Connecting Ridge, 14-day stay, small lander)

| Start date | Earth in view | Longest link outage | Verdict |
|---|---|---|---|
| 2027-09-01 | 18% | 276 h | Not ready |
| 2027-08-16 (the tool's suggestion) | 98% | 6 h | Go |

## How to use it

1. **Ask in one sentence:** site, start date, length of stay and vehicle. Change any of the four and everything recalculates.
2. **Read the decision board.** Tap any tile to see how its number was computed.
3. **Ask "What should I do?"** for a better date or site, plan a route, or run the live check against NASA.

The tool is one self-contained HTML file: it works **offline** (download `app/index.html` and open it in any modern browser), on desktop and phone, in **Arabic and English**. No server, no sign-in.

## NASA data

| Dataset | Mission / instrument | Used for |
|---|---|---|
| LOLA polar elevation model **LDEM_80S_80M** (80 m) [1][5] | Lunar Reconnaissance Orbiter · LOLA laser altimeter | horizons of the seven named sites at 80 m; a 240 m grid built from it for the map, slope, rover routes and points you pick |
| **JPL Horizons** ephemeris, hourly, 2027–2028 [2] | NASA/JPL Solar System Dynamics | Sun and Earth positions and distances |
| LOLA team **polar illumination products**: AVGVISIB, AVGVISIB_EARTH, LPSR (240 m) [3][4] | NASA GSFC Planetary Geodesy Data Archive | map layers, ice-stability index, and the yardstick for our own results |

The raw NASA files are not stored in this repository because of their size; they are available from the links in the references.

## Method

| Law | Formula | Why |
|---|---|---|
| Horizon angle | H(A) = max over d of atan((z(d) − z₀ − d²/2R) / d) | a distant ridge can hide a Sun only 1.5° high |
| Visible Sun disc | f = clamp((h☉ + 0.266° − H) / 0.533°) | at the pole the Sun spends hours half-hidden |
| Line of sight to Earth | h⊕ − H > 0.5° | a direct link needs Earth above the skyline |
| Solar power | P = 1361 · (1 AU / r)² · η · A · f | watts, not percentages |
| Survival battery | E = P_survive · t_dark | the vehicle must stay warm through the longest darkness |

Rover routes use A* search over slope and illumination. Tools: Python (NumPy, SciPy, Pillow) for data preparation; HTML/JavaScript with Web Workers for the tool.

## Validation

| Check | Result |
|---|---|
| Live check, 300 random points vs NASA's annual sunlight map (one run, data in `validation/`; each run draws new points, so the numbers vary slightly) | correlation r = 0.966 · mean absolute difference 3.7 points · bias −3.5 (our tool is slightly conservative) · 92% of points within ±10 |
| Full map, 1.1 million cells | correlation r = 0.987 · mean difference 3.0 points · 99.9% of NASA's mapped permanent shadow falls inside ours (ours is larger, so the tool errs on the dark side) |
| Sun and Earth geometry vs JPL Horizons computed from the lunar surface, 13 dates | elevation within 0.001° · azimuth within 0.01° |

**Caveat:** NASA's illumination map is itself a model built from LOLA terrain. Agreement shows that our method is implemented correctly; it does not, on its own, prove ground truth.

## Limits

- Water ice is unconfirmed anywhere; our ice index is geometric.
- Reflected light from nearby slopes is not modelled.
- Rocks and pits smaller than one grid cell are invisible.
- Terrain data end at 80°S.
- Vehicle and rover values are assumptions you can edit.

**Next:** Diviner temperature and LEND hydrogen data for a measured ice layer, comparison with real shadow images, relay satellites and the north pole, crewed sorties and Artemis candidate regions.

## Repository contents

| Path | Content |
|---|---|
| `index.html` | project home page: tool, video and resources (English, with Arabic) |
| `app/index.html` | the tool (single self-contained file; opens in English, Arabic from the EN/ع button) |
| `presentation.html` | animated presentation with Arabic/English toggle, voice-over script and the project video |
| `slides/`, `guide/` | the 7-slide deck and the user guide, English and Arabic (PDF) |
| `validation/` | 300-point comparison with NASA's map (CSV) |
| `src/tool/` | source of the tool (JavaScript, CSS) and the build script |
| `src/data-prep/` | Python scripts that read the NASA data and prepare the tool's data |

## Use of AI

AI tool used: **Claude (Anthropic)**. It helped write and debug the code and the data-preparation scripts, and helped draft the texts, translations and presentation materials (slides, animated presentation).

Team DexLab 1 chose the challenge and the questions, made the design decisions, tested the tool across its versions and reviewed its numbers and texts. Every result in the tool is computed from NASA data by the code in this repository. No image here was generated by AI: every picture is drawn by code from NASA data.

## Team

LUNAR EXPLORER is part of DexLab's ongoing work on lunar and Mars mapping tools.

**Team DexLab 1** · Jazan, Saudi Arabia · team 25 · NASA Space Apps Challenge 2026

- **Azez Hana**: team leader and scientific supervision; UX and testing
- **Francisco Acousta**: video, voice-over and design; UX and testing
- **Dominico Acousta**: video, voice-over and design; UX and testing

## License

Code: MIT (see `LICENSE`). NASA data are in the public domain; images in this repository are derived from NASA data.

## References

1. Smith, D. E., et al. (2010). The Lunar Orbiter Laser Altimeter investigation on the Lunar Reconnaissance Orbiter mission. *Space Science Reviews*, 150, 209–241. https://ui.adsabs.harvard.edu/abs/2010SSRv..150..209S/abstract
2. NASA / JPL Solar System Dynamics. Horizons System. https://ssd.jpl.nasa.gov/horizons/
3. Mazarico, E., Neumann, G. A., Smith, D. E., Zuber, M. T., & Torrence, M. H. (2011). Illumination conditions of the lunar polar regions using LOLA topography. *Icarus*, 211, 1066–1081. https://ntrs.nasa.gov/citations/20120010094
4. NASA GSFC Planetary Geodesy Data Archive. Lunar Polar Illumination (AVGVISIB, LPSR products, 2016). https://pgda.gsfc.nasa.gov/products/69
5. LRO LOLA Gridded Data Records, polar elevation model LDEM_80S_80M. NASA PDS. https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/
6. Gläser, P., et al. (2014). Illumination conditions at the lunar south pole using high resolution Digital Terrain Models from LOLA. *Icarus*, 243, 78–90. https://ui.adsabs.harvard.edu/abs/2014Icar..243...78G
7. Anthropic. Claude (AI assistant), used as described under "Use of AI". https://www.anthropic.com/claude

---

**بالعربية:** LUNAR EXPLORER أداة لتخطيط البعثات عند القطب الجنوبي للقمر. تحسب الأفق الحقيقي لأي نقطة من بيانات ناسا، وترصد الشمس والأرض ساعة بساعة، وتحوّل ذلك إلى قرار، وتختبر نفسها مقابل خرائط ناسا المنشورة. تعمل بالعربية والإنكليزية وبلا إنترنت. فريق DexLab 1 · جازان، المملكة العربية السعودية.
