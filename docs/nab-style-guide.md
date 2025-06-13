# NAB Skills Intelligence Platform - Design System & Style Guide

> **Inspired by**: Eightfold.ai, Gloat, and modern SaaS platforms  
> **Framework**: Flask + Tailwind CSS  
> **Target Users**: NAB Future Skills team, HR professionals, employees

---

## 🎨 Visual Identity & Brand

### Core Philosophy
- **Clean, minimal, professional SaaS aesthetic**
- **Data-driven and analytical** (not marketing-focused)
- **Enterprise-grade credibility** with modern usability
- **NAB heritage** through selective red accents on black foundation

### Visual Tone
- Sophisticated and trustworthy
- Focus on **clarity over decoration**
- Information hierarchy that guides user attention
- **Accessible** and inclusive design patterns

---

## 🖋️ Typography System

### Font Stack
```html
<!-- Google Fonts Import -->
<link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700&family=Source+Sans+Pro:wght@300;400;500;600&display=swap" rel="stylesheet">
```

### Font Usage
- **Headers**: `font-epilogue` (Epilogue) - clean, modern, professional
- **Body Text**: `font-source` (Source Sans Pro) - highly readable, data-friendly
- **Code/IDs**: `font-mono` (system monospace) - job IDs, skill codes

### Tailwind Font Classes
```css
/* Add to Tailwind config */
fontFamily: {
  'epilogue': ['Epilogue', 'sans-serif'],
  'source': ['Source Sans Pro', 'sans-serif'],
}
```

### Typography Scale
- **Page Titles**: `text-3xl md:text-4xl font-epilogue font-bold`
- **Section Headers**: `text-xl md:text-2xl font-epilogue font-semibold`
- **Card Titles**: `text-lg font-epilogue font-medium`
- **Body Text**: `text-sm md:text-base font-source`
- **Labels**: `text-xs font-source font-medium uppercase tracking-wide`
- **Captions**: `text-xs font-source text-gray-400`

### Text Alignment
- **All text is left-aligned** (`text-left`) - never centered
- Exception: Loading states and empty states may use center alignment

---

## 🎨 Color System

### Primary Palette
```css
/* Tailwind Config Colors */
colors: {
  'nab': {
    'black': '#000000',    // Primary background
    'red': '#dc2626',      // Red-600 - primary accent
    'red-dark': '#b91c1c', // Red-700 - hover states
    'red-light': '#f87171', // Red-400 - disabled states
  }
}
```

### Usage Patterns
- **Primary Background**: `bg-black` (main app background)
- **Card Backgrounds**: `bg-white` or `bg-gray-50` (content readability)
- **Text on Dark**: `text-white` or `text-gray-100`
- **Text on Light**: `text-black` or `text-gray-900`
- **Primary Actions**: `bg-red-600 hover:bg-red-700`
- **Secondary Actions**: `border border-red-600 text-red-600 hover:bg-red-600 hover:text-white`

### Accessibility
- **Minimum contrast ratio**: 4.5:1 for normal text, 3:1 for large text
- **Red accents**: Only for highlights, never for critical information alone
- **Status colors**: Green for success, amber for warnings (maintain contrast)

---

## 📐 Layout System

### Container & Spacing
```html
<!-- Standard page container -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <!-- Content with consistent vertical rhythm -->
  <div class="space-y-6 py-6">
    <!-- Components here -->
  </div>
</div>
```

### Grid Systems
- **Dashboard Layouts**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- **Two-column forms**: `grid grid-cols-1 lg:grid-cols-2 gap-8`
- **Detail views**: `grid grid-cols-1 lg:grid-cols-3 gap-8` (sidebar + main)

### Responsive Breakpoints
- **Mobile**: `< 768px` - single column, touch-friendly
- **Tablet**: `768px - 1024px` - two columns, compact
- **Desktop**: `> 1024px` - full layout, optimal information density

---

## 🧩 Component Library

### 1. Navigation Bar
```html
<nav class="bg-black border-b border-gray-800">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between h-16">
      <!-- Logo -->
      <div class="flex items-center">
        <a href="/" class="font-epilogue font-bold text-xl text-white hover:text-red-600 transition-colors">
          Skills Intelligence
        </a>
      </div>
      
      <!-- Navigation Links -->
      <div class="hidden md:flex items-center space-x-8">
        <a href="/dashboard" class="text-gray-300 hover:text-white transition-colors">Dashboard</a>
        <a href="/jobs" class="text-gray-300 hover:text-white transition-colors">Job Explorer</a>
        <a href="/pathways" class="text-gray-300 hover:text-white transition-colors">Career Pathways</a>
      </div>
    </div>
  </div>
</nav>
```

### 2. Dashboard Cards
```html
<!-- Metric Card -->
<div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-600">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-xs font-source font-medium text-gray-500 uppercase tracking-wide">Jobs Analyzed</p>
      <p class="text-2xl font-epilogue font-bold text-gray-900">2,847</p>
    </div>
    <div class="p-3 bg-red-100 rounded-full">
      <!-- Icon here -->
    </div>
  </div>
  <div class="mt-4">
    <p class="text-sm font-source text-gray-600">↑ 12% from last month</p>
  </div>
</div>

<!-- Data Card -->
<div class="bg-white rounded-lg shadow-md overflow-hidden">
  <div class="px-6 py-4 border-b border-gray-200">
    <h3 class="text-lg font-epilogue font-medium text-gray-900">Top Skills in Demand</h3>
  </div>
  <div class="p-6">
    <!-- Chart or data visualization here -->
  </div>
</div>
```

### 3. Buttons
```html
<!-- Primary Button -->
<button class="bg-red-600 hover:bg-red-700 text-white font-source font-medium px-6 py-2 rounded-md transition-colors duration-200">
  Analyze Skills
</button>

<!-- Secondary Button -->
<button class="border border-red-600 text-red-600 hover:bg-red-600 hover:text-white font-source font-medium px-6 py-2 rounded-md transition-colors duration-200">
  View Details
</button>

<!-- Tertiary Button -->
<button class="text-red-600 hover:text-red-700 font-source font-medium px-4 py-2 transition-colors duration-200">
  Learn More →
</button>
```

### 4. Search & Filters
```html
<div class="bg-white rounded-lg shadow-md p-6">
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Search -->
    <div>
      <label class="block text-xs font-source font-medium text-gray-700 uppercase tracking-wide mb-2">
        Search Jobs
      </label>
      <input type="text" 
             class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
             placeholder="e.g. Data Scientist">
    </div>
    
    <!-- Filter -->
    <div>
      <label class="block text-xs font-source font-medium text-gray-700 uppercase tracking-wide mb-2">
        Job Family
      </label>
      <select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500">
        <option>All Families</option>
        <option>Technology</option>
        <option>Risk & Compliance</option>
      </select>
    </div>
    
    <!-- Action -->
    <div class="flex items-end">
      <button class="bg-red-600 hover:bg-red-700 text-white font-source font-medium px-6 py-2 rounded-md transition-colors duration-200">
        Search
      </button>
    </div>
  </div>
</div>
```

### 5. Data Tables
```html
<div class="bg-white rounded-lg shadow-md overflow-hidden">
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
      <tr>
        <th class="px-6 py-3 text-left text-xs font-source font-medium text-gray-500 uppercase tracking-wider">
          Job Title
        </th>
        <th class="px-6 py-3 text-left text-xs font-source font-medium text-gray-500 uppercase tracking-wider">
          Similarity Score
        </th>
        <th class="px-6 py-3 text-left text-xs font-source font-medium text-gray-500 uppercase tracking-wider">
          Skills Overlap
        </th>
      </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
      <!-- Rows here -->
    </tbody>
  </table>
</div>
```

---

## 📊 Data Visualization Patterns

### Similarity Scores
```html
<!-- Progress Bar Style -->
<div class="flex items-center space-x-3">
  <span class="text-sm font-source font-medium text-gray-900">87%</span>
  <div class="flex-1 bg-gray-200 rounded-full h-2">
    <div class="bg-red-600 h-2 rounded-full" style="width: 87%"></div>
  </div>
</div>

<!-- Badge Style -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-source font-medium bg-red-100 text-red-800">
  High Match
</span>
```

### Skills Lists
```html
<div class="space-y-2">
  <div class="flex flex-wrap gap-2">
    <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-source font-medium bg-gray-100 text-gray-800">
      Python
    </span>
    <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-source font-medium bg-gray-100 text-gray-800">
      Data Analysis
    </span>
    <!-- More skills -->
  </div>
</div>
```

### Empty States
```html
<div class="text-center py-12">
  <div class="text-gray-400 mb-4">
    <!-- Icon -->
  </div>
  <h3 class="text-lg font-epilogue font-medium text-gray-900">No results found</h3>
  <p class="text-sm font-source text-gray-500 mt-2">
    Try adjusting your search criteria or explore different job families.
  </p>
  <button class="mt-4 bg-red-600 hover:bg-red-700 text-white font-source font-medium px-4 py-2 rounded-md transition-colors duration-200">
    Reset Filters
  </button>
</div>
```

---

## 🔧 Technical Implementation

### Tailwind Configuration
```javascript
// In base.html <script> tag
tailwind.config = {
  theme: {
    extend: {
      fontFamily: {
        'epilogue': ['Epilogue', 'sans-serif'],
        'source': ['Source Sans Pro', 'sans-serif'],
      },
      colors: {
        'nab': {
          'red': '#dc2626',
          'red-dark': '#b91c1c',
          'red-light': '#f87171',
        }
      }
    }
  }
}
```

### Flask Template Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Skills Intelligence{% endblock %}</title>
  
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700&family=Source+Sans+Pro:wght@300;400;500;600&display=swap" rel="stylesheet">
  
  <!-- Tailwind Config -->
  <script>/* Tailwind config here */</script>
</head>
<body class="bg-black min-h-screen">
  <!-- Navigation -->
  {% include 'components/navigation.html' %}
  
  <!-- Main Content -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    {% block content %}{% endblock %}
  </main>
  
  <!-- Footer -->
  {% include 'components/footer.html' %}
</body>
</html>
```

---

## ♿ Accessibility Guidelines

### WCAG Compliance
- **Level AA** compliance for all interactive elements
- **Keyboard navigation** for all functionality
- **Screen reader** compatible semantic HTML
- **Focus indicators** visible and high-contrast

### Implementation Checklist
- [ ] All images have meaningful `alt` attributes
- [ ] Form inputs have associated `<label>` elements
- [ ] Interactive elements have `role` attributes where needed
- [ ] Color is not the only way to convey information
- [ ] Text contrast meets WCAG AA standards (4.5:1)

---

## 🚀 Component Development Workflow

### 1. Design in Isolation
- Create components in `/components` page first
- Test with sample data
- Ensure responsive behavior

### 2. Integration
- Move successful components to main pages
- Maintain consistency across implementations
- Document any variations needed

### 3. Testing
- Test with real database data
- Verify performance with large datasets
- Ensure mobile usability

---

## 📝 Content Guidelines

### Voice & Tone
- **Professional but approachable**
- **Data-focused** language
- **Action-oriented** button text
- **Clear, concise** descriptions

### Terminology
- Use "Skills" not "Competencies"
- Use "Job Profiles" not "Roles" 
- Use "Career Pathways" not "Career Paths"
- Use "Similarity Score" not "Match Percentage"

---

This design system creates a modern, professional skills intelligence platform that feels like a premium SaaS product while maintaining NAB's brand identity through strategic use of black and red.

## Workflow Components

### Multi-Step Process Indicator
For career pathway exploration and white paper generation workflows that require multiple steps.

```html
<div class="bg-gray-900 border border-gray-700 rounded-lg p-6 mb-6">
  <nav aria-label="Progress">
    <ol class="flex items-center">
      <li class="relative">
        <div class="flex items-center">
          <div class="relative w-8 h-8 flex items-center justify-center bg-red-600 rounded-full">
            <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </div>
          <span class="ml-3 text-sm font-medium text-white">Select Starting Role</span>
        </div>
      </li>
      <li class="relative ml-8">
        <div class="flex items-center">
          <div class="absolute inset-0 flex items-center" aria-hidden="true">
            <div class="h-0.5 w-full bg-gray-700"></div>
          </div>
          <div class="relative w-8 h-8 flex items-center justify-center bg-red-600 rounded-full border-2 border-black">
            <span class="h-2.5 w-2.5 bg-white rounded-full"></span>
          </div>
          <span class="ml-3 text-sm font-medium text-white">Filter Options</span>
        </div>
      </li>
      <li class="relative ml-8">
        <div class="flex items-center">
          <div class="absolute inset-0 flex items-center" aria-hidden="true">
            <div class="h-0.5 w-full bg-gray-700"></div>
          </div>
          <div class="relative w-8 h-8 flex items-center justify-center bg-gray-700 rounded-full border-2 border-gray-700">
            <span class="h-2.5 w-2.5 bg-gray-500 rounded-full"></span>
          </div>
          <span class="ml-3 text-sm font-medium text-gray-400">View Results</span>
        </div>
      </li>
    </ol>
  </nav>
</div>
```

**Usage**: Perfect for the career pathway explorer flow (Select Role → Filter → Results) and white paper generation (Select Type → Configure → Generate). 