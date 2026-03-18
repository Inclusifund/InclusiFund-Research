# Vertical AI Brand Color Palette

This is the official brand color scheme for all HTML pages and frontend interfaces within the Vertical AI project.

## Color Palette

![Brand Colors](/Users/royalreece/.gemini/antigravity/brain/af8469e2-7ac0-4d3e-905a-fb123ecbaecc/uploaded_media_1770573913066.png)

### Primary Brand Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Dark Teal** | `#005461` | Primary dark accent, deep CTAs, dark mode primary |
| **Teal** | `#008080` | Main brand color, primary buttons, links, highlights |
| **Tropical Teal** | `#6BB6B6` | Light accent, hover states, secondary elements |

### Neutral Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Shadow Grey** | `#1F2232` | Dark backgrounds, dark theme base |
| **Light Cyan** | `#D5ECEC` | Soft backgrounds, light theme accents |
| **White Smoke** | `#F4F4F4` | Light backgrounds, cards, panels |

## CSS Implementation

```css
:root {
    /* Primary Brand Colors */
    --brand-dark-teal: #005461;      /* Dark Teal - Primary dark accent */
    --brand-teal: #008080;           /* Teal - Main brand color */
    --brand-tropical-teal: #6BB6B6;  /* Tropical Teal - Light accent */
    
    /* Neutral Colors */
    --brand-shadow-grey: #1F2232;    /* Shadow Grey - Dark backgrounds */
    --brand-light-cyan: #D5ECEC;     /* Light Cyan - Soft backgrounds */
    --brand-white-smoke: #F4F4F4;    /* White Smoke - Light backgrounds */
    
    /* Semantic Mappings */
    --color-primary: var(--brand-teal);
    --color-primary-dark: var(--brand-dark-teal);
    --color-primary-light: var(--brand-tropical-teal);
    --color-bg-dark: var(--brand-shadow-grey);
    --color-bg-light: var(--brand-white-smoke);
    --color-bg-soft: var(--brand-light-cyan);
}
```

## Usage Examples

### Light Theme Example
```css
body {
    background-color: var(--brand-white-smoke);
    color: var(--brand-shadow-grey);
}

.button-primary {
    background-color: var(--brand-teal);
    color: white;
}

.button-primary:hover {
    background-color: var(--brand-dark-teal);
}

.accent {
    color: var(--brand-tropical-teal);
}
```

### Dark Theme Example
```css
body {
    background-color: var(--brand-shadow-grey);
    color: var(--brand-white-smoke);
}

.button-primary {
    background-color: var(--brand-teal);
    color: white;
}

.button-primary:hover {
    background-color: var(--brand-tropical-teal);
}

.card {
    background-color: rgba(0, 128, 128, 0.1);
    border: 1px solid var(--brand-dark-teal);
}
```

## Design Principles

1. **Consistency**: Always use CSS variables for colors
2. **Hierarchy**: Use darker teals for primary actions, lighter for secondary
3. **Contrast**: Ensure sufficient contrast between text and backgrounds
4. **Flexibility**: Additional colors can be added only when explicitly requested
5. **Accessibility**: Maintain WCAG AA standards for color contrast

## Color Psychology

- **Teal**: Trust, professionalism, calmness, stability
- **Grey**: Neutrality, sophistication, balance
- **Cyan**: Freshness, clarity, innovation

This palette creates a professional, trustworthy, and modern aesthetic suitable for social impact and community-focused applications.
