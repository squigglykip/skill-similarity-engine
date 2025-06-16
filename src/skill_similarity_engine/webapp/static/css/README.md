# CSS Architecture - Skill Similarity Engine

## Overview
This project uses a modular CSS architecture combining TailwindCSS with custom CSS files for optimal maintainability and performance.

## File Structure
```
static/css/
├── variables.css       # CSS custom properties and design tokens
├── main.css           # Base styles and component library
├── job-explorer.css   # Job Explorer page specific styles
├── career-pathways.css # Career Pathways page specific styles
├── dashboard.css      # Dashboard/Index page specific styles
├── components.css     # Components showcase page specific styles
└── README.md          # This documentation
```

## CSS Loading Order
The CSS files are loaded in this specific order in `base.html`:

1. **TailwindCSS** (CDN) - Utility classes
2. **variables.css** - Design system tokens
3. **main.css** - Base styles and components
4. **Page-specific CSS** - job-explorer.css, career-pathways.css, dashboard.css, components.css

## Design System Variables
All design tokens are centralized in `variables.css`:

- **Colors**: NAB brand colors, blue system, grays, semantic colors
- **Typography**: Font families, sizes, weights, line heights
- **Spacing**: Consistent spacing scale
- **Layout**: Border radius, shadows, transitions
- **Component tokens**: Specific values for sliders, cards, charts

## TailwindCSS Usage Guidelines

### ✅ Use TailwindCSS for:
- Layout (flexbox, grid, positioning)
- Spacing (margins, padding)
- Typography (font sizes, weights)
- Basic colors and backgrounds
- Responsive design
- State variants (hover, focus, active)

### ❌ Use Custom CSS for:
- Complex animations and transitions
- Component-specific styling (sliders, custom charts)
- Browser-specific styles (-webkit-, -moz-)
- Highly interactive elements
- Design system tokens and variables

## Component Naming Convention
- Use semantic class names: `.job-profile-card`, `.similarity-slider`
- Prefix with component name: `.job-search-input`, `.job-search-dropdown`
- Use BEM-like modifiers: `.similar-job-item`, `.skill-category-card`

## CSS Custom Properties Usage
All custom CSS should reference design tokens:

```css
/* ✅ Good */
.my-component {
    color: var(--color-blue-600);
    padding: var(--spacing-4);
    border-radius: var(--border-radius-lg);
    transition: all var(--transition-base);
}

/* ❌ Avoid */
.my-component {
    color: #2563eb;
    padding: 16px;
    border-radius: 8px;
    transition: all 0.2s ease-in-out;
}
```

## Responsive Design
- Use TailwindCSS responsive prefixes: `sm:`, `md:`, `lg:`, `xl:`, `2xl:`
- Breakpoints are defined in `variables.css` for JavaScript usage
- Custom CSS should use media queries for complex responsive behavior

## Performance Considerations
- TailwindCSS is loaded via CDN for development
- Custom CSS files are modular and page-specific
- Use CSS custom properties to reduce duplicate values
- Leverage browser caching with proper file organization

## Future Enhancements
- Consider TailwindCSS compilation for production
- Add CSS purging for unused styles
- Implement CSS-in-JS for dynamic components
- Add CSS linting and formatting tools

## Example Usage
```html
<!-- Combine TailwindCSS with custom classes -->
<div class="job-profile-card bg-white rounded-lg shadow-lg p-6">
    <input class="similarity-slider flex-1 h-2 bg-gray-200 rounded-lg">
    <div class="skill-category-card p-4 border border-gray-200 rounded-lg">
        <span class="skill-badge inline-flex items-center px-2 py-1 rounded-full">
            Skill Name
        </span>
    </div>
</div>
```

This approach provides the best of both worlds: rapid development with TailwindCSS utilities and maintainable, semantic custom components. 