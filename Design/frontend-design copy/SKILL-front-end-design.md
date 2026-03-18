---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Brand Color Scheme (Default for All HTML Pages)

**IMPORTANT**: For all HTML pages created within the Vertical AI project, use this official brand color palette as the foundation. Additional colors can be added only if explicitly specified in future prompts.

### Official Color Palette

```css
:root {
    /* Primary Brand Colors */
    --brand-emerald: #059669;        /* Emerald 600 - Primary Action/Text */
    --brand-teal: #0d9488;           /* Teal 600 - Secondary/Gradient */
    --brand-cyan: #06b6d4;           /* Cyan 500 - Accents */

    /* Background Colors */
    --brand-bg-emerald-50: #ecfdf5;  /* Light Emerald Background */
    --brand-bg-teal-50: #f0fdfa;     /* Light Teal Background */
    --brand-bg-cyan-50: #ecfeff;     /* Light Cyan Background */
    
    /* Neutral Colors */
    --brand-white: #ffffff;
    --brand-gray-50: #f9fafb;
    --brand-gray-100: #f3f4f6;
    --brand-gray-800: #1f2937;       /* Dark Text */
    
    /* Semantic Mappings */
    --color-primary: var(--brand-emerald);
    --color-secondary: var(--brand-teal);
    --color-bg-gradient: linear-gradient(to bottom right, var(--brand-bg-emerald-50), var(--brand-bg-teal-50), var(--brand-bg-cyan-50));
    --color-text-main: var(--brand-gray-800);
}
```

### Usage Guidelines

- **Primary Actions**: Use `--brand-teal` or `--brand-dark-teal` for buttons, links, and CTAs
- **Backgrounds**: 
  - Dark theme: `--brand-shadow-grey` as base
  - Light theme: `--brand-white-smoke` or `--brand-light-cyan` as base
- **Accents**: `--brand-tropical-teal` for highlights, hover states, and secondary elements
- **Consistency**: Always use CSS variables for colors to maintain brand consistency
- **Extensions**: Only add additional colors if explicitly requested in the prompt

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
