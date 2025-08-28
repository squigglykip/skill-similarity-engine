/**
 * Range Slider Module for SkillEngine
 * Provides dual-range slider functionality for similarity configuration
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.RangeSlider = {
    /**
     * Initialize a dual-range slider
     */
    initDualRange(config) {
        const {
            minInputId,
            maxInputId,
            displayId,
            fillId,
            onUpdate,
            minValue = 0,
            maxValue = 100,
            step = 1
        } = config;

        const minInput = document.getElementById(minInputId);
        const maxInput = document.getElementById(maxInputId);
        const display = document.getElementById(displayId);
        const fill = document.getElementById(fillId);

        if (!minInput || !maxInput) {
            console.warn(`Range slider inputs not found: ${minInputId}, ${maxInputId}`);
            return;
        }

        const updateDisplay = () => {
            let minVal = parseInt(minInput.value);
            let maxVal = parseInt(maxInput.value);

            // Ensure min is less than max
            if (minVal >= maxVal) {
                minVal = maxVal - step;
                minInput.value = minVal;
            }

            // Update display
            if (display) {
                display.textContent = `${minVal}% - ${maxVal}%`;
            }

            // Update fill visualization
            if (fill) {
                this.updateRangeFill(fill, minVal, maxVal, minValue, maxValue);
            }

            // Call update callback
            if (onUpdate) {
                onUpdate(minVal, maxVal);
            }
        };

        // Attach event listeners
        minInput.addEventListener('input', updateDisplay);
        maxInput.addEventListener('input', updateDisplay);

        // Initial update
        updateDisplay();

        return {
            getValues: () => ({
                min: parseInt(minInput.value),
                max: parseInt(maxInput.value)
            }),
            setValues: (min, max) => {
                minInput.value = min;
                maxInput.value = max;
                updateDisplay();
            },
            updateDisplay
        };
    },

    /**
     * Initialize a single range slider
     */
    initSingleRange(config) {
        const {
            inputId,
            displayId,
            onUpdate,
            formatValue = (val) => val,
            labelText = ''
        } = config;

        const input = document.getElementById(inputId);
        const display = document.getElementById(displayId);

        if (!input) {
            console.warn(`Range slider input not found: ${inputId}`);
            return;
        }

        const updateDisplay = () => {
            const value = parseInt(input.value);
            
            if (display) {
                display.textContent = formatValue(value);
            }

            if (onUpdate) {
                onUpdate(value);
            }
        };

        // Attach event listener
        input.addEventListener('input', updateDisplay);

        // Initial update
        updateDisplay();

        return {
            getValue: () => parseInt(input.value),
            setValue: (value) => {
                input.value = value;
                updateDisplay();
            },
            updateDisplay
        };
    },

    /**
     * Update range fill visualization
     */
    updateRangeFill(fillElement, minVal, maxVal, minBound, maxBound) {
        const range = maxBound - minBound;
        const leftPercent = ((minVal - minBound) / range) * 100;
        const rightPercent = ((maxVal - minBound) / range) * 100;
        
        fillElement.style.left = `${leftPercent}%`;
        fillElement.style.width = `${rightPercent - leftPercent}%`;
    },

    /**
     * Create a dual-range slider from scratch
     */
    createDualRangeSlider(containerId, config) {
        const {
            minValue = 0,
            maxValue = 100,
            step = 1,
            initialMin = minValue,
            initialMax = maxValue,
            label = 'Range',
            unit = '',
            onUpdate
        } = config;

        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container not found: ${containerId}`);
            return;
        }

        // Create HTML structure
        container.innerHTML = `
            <div class="dual-range-slider-container">
                <div class="flex items-center justify-between mb-3">
                    <label class="text-sm font-medium text-gray-700">${label}</label>
                    <span class="range-display text-sm font-semibold text-red-600">${initialMin}${unit} - ${initialMax}${unit}</span>
                </div>
                <div class="dual-range-slider">
                    <div class="range-track">
                        <div class="range-fill"></div>
                    </div>
                    <input type="range" class="range-slider range-slider-min" 
                           min="${minValue}" max="${maxValue}" value="${initialMin}" step="${step}">
                    <input type="range" class="range-slider range-slider-max" 
                           min="${minValue}" max="${maxValue}" value="${initialMax}" step="${step}">
                </div>
                <div class="flex justify-between text-xs text-gray-500 mt-1">
                    <span>${minValue}${unit}</span>
                    <span>${Math.round((minValue + maxValue) / 4)}${unit}</span>
                    <span>${Math.round((minValue + maxValue) / 2)}${unit}</span>
                    <span>${Math.round((3 * (minValue + maxValue)) / 4)}${unit}</span>
                    <span>${maxValue}${unit}</span>
                </div>
            </div>
        `;

        // Initialize functionality
        const minInput = container.querySelector('.range-slider-min');
        const maxInput = container.querySelector('.range-slider-max');
        const display = container.querySelector('.range-display');
        const fill = container.querySelector('.range-fill');

        return this.initDualRange({
            minInputId: minInput.id || `${containerId}-min`,
            maxInputId: maxInput.id || `${containerId}-max`,
            displayId: display.id || `${containerId}-display`,
            fillId: fill.id || `${containerId}-fill`,
            onUpdate,
            minValue,
            maxValue,
            step
        });
    },

    /**
     * Accessibility enhancements
     */
    enhanceAccessibility(sliderId) {
        const slider = document.getElementById(sliderId);
        if (!slider) return;

        // Add ARIA labels
        const inputs = slider.querySelectorAll('input[type="range"]');
        inputs.forEach((input, index) => {
            input.setAttribute('role', 'slider');
            input.setAttribute('aria-orientation', 'horizontal');
            
            if (inputs.length === 2) {
                input.setAttribute('aria-label', index === 0 ? 'Minimum value' : 'Maximum value');
            } else {
                input.setAttribute('aria-label', 'Slider value');
            }
        });

        // Add keyboard navigation help
        const helpText = document.createElement('div');
        helpText.className = 'sr-only';
        helpText.textContent = 'Use arrow keys to adjust values';
        slider.appendChild(helpText);
    },

    /**
     * Preset configurations for common use cases
     */
    presets: {
        similarity: {
            minValue: 0,
            maxValue: 100,
            step: 5,
            initialMin: 0,
            initialMax: 95,
            label: 'Similarity Range',
            unit: '%'
        },
        
        pathwayCount: {
            minValue: 1,
            maxValue: 10,
            step: 1,
            initialValue: 3,
            label: 'Number of Pathways',
            unit: ''
        },
        
        confidence: {
            minValue: 50,
            maxValue: 100,
            step: 10,
            initialMin: 70,
            initialMax: 100,
            label: 'Confidence Range',
            unit: '%'
        }
    },

    /**
     * Create slider with preset configuration
     */
    createPresetSlider(containerId, presetName, customConfig = {}) {
        const preset = this.presets[presetName];
        if (!preset) {
            console.warn(`Preset not found: ${presetName}`);
            return;
        }

        const config = { ...preset, ...customConfig };
        
        if (preset.initialValue !== undefined) {
            // Single range slider
            return this.initSingleRange({
                inputId: containerId,
                ...config
            });
        } else {
            // Dual range slider
            return this.createDualRangeSlider(containerId, config);
        }
    },

    /**
     * Validate range values
     */
    validateRange(min, max, bounds = { min: 0, max: 100 }) {
        const errors = [];
        
        if (min < bounds.min) {
            errors.push(`Minimum value cannot be less than ${bounds.min}`);
        }
        
        if (max > bounds.max) {
            errors.push(`Maximum value cannot be greater than ${bounds.max}`);
        }
        
        if (min >= max) {
            errors.push('Minimum value must be less than maximum value');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    },

    /**
     * Format range for display
     */
    formatRange(min, max, options = {}) {
        const {
            unit = '',
            separator = ' - ',
            precision = 0
        } = options;
        
        const formatValue = (val) => {
            return precision > 0 ? val.toFixed(precision) : val.toString();
        };
        
        return `${formatValue(min)}${unit}${separator}${formatValue(max)}${unit}`;
    },

    /**
     * Convert range to API format
     */
    toApiFormat(min, max, scale = 1) {
        return {
            min: min / scale,
            max: max / scale,
            range: [min / scale, max / scale]
        };
    }
};

console.log('✅ Range Slider module loaded');
