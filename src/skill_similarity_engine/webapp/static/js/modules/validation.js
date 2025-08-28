/**
 * Validation Module for SkillEngine
 * Provides comprehensive form validation utilities
 */

window.SkillEngine = window.SkillEngine || {};

SkillEngine.Validation = {
    /**
     * Validation rules registry
     */
    rules: {
        required: (value) => value !== null && value !== undefined && value.toString().trim() !== '',
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        minLength: (min) => (value) => value && value.length >= min,
        maxLength: (max) => (value) => value && value.length <= max,
        numeric: (value) => !isNaN(parseFloat(value)) && isFinite(value),
        integer: (value) => Number.isInteger(Number(value)),
        range: (min, max) => (value) => {
            const num = Number(value);
            return num >= min && num <= max;
        },
        jobProfileId: (value) => /^[A-Z]\d{4}\.\d+$/.test(value),
        percentage: (value) => {
            const num = Number(value);
            return num >= 0 && num <= 100;
        }
    },

    /**
     * Validate a single field
     */
    validateField(value, rules) {
        const errors = [];
        
        for (const rule of rules) {
            if (typeof rule === 'string') {
                // Simple rule name
                if (!this.rules[rule](value)) {
                    errors.push(this.getErrorMessage(rule, value));
                }
            } else if (typeof rule === 'object') {
                // Rule with parameters
                const ruleName = Object.keys(rule)[0];
                const ruleParams = rule[ruleName];
                
                if (Array.isArray(ruleParams)) {
                    if (!this.rules[ruleName](...ruleParams)(value)) {
                        errors.push(this.getErrorMessage(ruleName, value, ruleParams));
                    }
                } else {
                    if (!this.rules[ruleName](ruleParams)(value)) {
                        errors.push(this.getErrorMessage(ruleName, value, ruleParams));
                    }
                }
            } else if (typeof rule === 'function') {
                // Custom validation function
                const result = rule(value);
                if (result !== true) {
                    errors.push(result || 'Validation failed');
                }
            }
        }
        
        return errors;
    },

    /**
     * Validate an entire form
     */
    validateForm(formData, schema) {
        const errors = {};
        let isValid = true;
        
        for (const [fieldName, rules] of Object.entries(schema)) {
            const fieldValue = formData[fieldName];
            const fieldErrors = this.validateField(fieldValue, rules);
            
            if (fieldErrors.length > 0) {
                errors[fieldName] = fieldErrors;
                isValid = false;
            }
        }
        
        return { isValid, errors };
    },

    /**
     * Get error message for a validation rule
     */
    getErrorMessage(ruleName, value, params) {
        const messages = {
            required: 'This field is required',
            email: 'Please enter a valid email address',
            minLength: `Must be at least ${params} characters long`,
            maxLength: `Must be no more than ${params} characters long`,
            numeric: 'Must be a valid number',
            integer: 'Must be a whole number',
            range: `Must be between ${params[0]} and ${params[1]}`,
            jobProfileId: 'Must be a valid job profile ID (e.g., R0123.4)',
            percentage: 'Must be between 0 and 100'
        };
        
        return messages[ruleName] || 'Invalid value';
    },

    /**
     * Real-time validation for form fields
     */
    attachRealTimeValidation(formId, schema) {
        const form = document.getElementById(formId);
        if (!form) {
            console.warn(`Form with ID '${formId}' not found`);
            return;
        }

        for (const fieldName of Object.keys(schema)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (!field) continue;

            const validateAndDisplay = () => {
                const errors = this.validateField(field.value, schema[fieldName]);
                this.displayFieldErrors(field, errors);
            };

            // Attach event listeners
            field.addEventListener('blur', validateAndDisplay);
            field.addEventListener('input', () => {
                // Clear errors on input, validate on blur
                this.clearFieldErrors(field);
            });
        }
    },

    /**
     * Display validation errors for a field
     */
    displayFieldErrors(field, errors) {
        this.clearFieldErrors(field);
        
        if (errors.length === 0) {
            field.classList.remove('border-red-500', 'border-red-300');
            field.classList.add('border-green-500');
            return;
        }

        // Add error styling
        field.classList.remove('border-green-500', 'border-gray-300');
        field.classList.add('border-red-500');

        // Create error container
        const errorContainer = document.createElement('div');
        errorContainer.className = 'validation-errors mt-1 text-sm text-red-600';
        errorContainer.setAttribute('data-field-errors', field.name);

        errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'flex items-center';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-circle mr-1"></i>
                <span>${error}</span>
            `;
            errorContainer.appendChild(errorDiv);
        });

        // Insert after field
        field.parentNode.insertBefore(errorContainer, field.nextSibling);
    },

    /**
     * Clear validation errors for a field
     */
    clearFieldErrors(field) {
        // Remove error styling
        field.classList.remove('border-red-500', 'border-green-500');
        field.classList.add('border-gray-300');

        // Remove error messages
        const errorContainer = field.parentNode.querySelector(`[data-field-errors="${field.name}"]`);
        if (errorContainer) {
            errorContainer.remove();
        }
    },

    /**
     * Career Analysis specific validation schemas
     */
    schemas: {
        careerAnalysisForm: {
            job_from: ['required', 'jobProfileId'],
            analysis_mode: ['required'],
            top_n: ['required', 'integer', { range: [1, 10] }],
            similarity_min: ['required', 'percentage'],
            similarity_max: ['required', 'percentage'],
            primary_algorithm: ['required']
        },
        
        careerAnalysisSpecificMode: {
            job_from: ['required', 'jobProfileId'],
            job_to: ['required'],
            analysis_mode: ['required'],
            similarity_min: ['required', 'percentage'],
            similarity_max: ['required', 'percentage'],
            primary_algorithm: ['required']
        }
    },

    /**
     * Custom validators for specific use cases
     */
    customValidators: {
        similarityRange: (formData) => {
            const min = Number(formData.similarity_min);
            const max = Number(formData.similarity_max);
            
            if (min >= max) {
                return 'Maximum similarity must be greater than minimum similarity';
            }
            return true;
        },

        specificModeTargets: (formData) => {
            if (formData.analysis_mode === 'specific' && (!formData.job_to || formData.job_to.trim() === '')) {
                return 'Target job is required for specific transition analysis';
            }
            return true;
        }
    },

    /**
     * Validate career analysis form with custom logic
     */
    validateCareerAnalysisForm(formData) {
        // Choose schema based on analysis mode
        const schema = formData.analysis_mode === 'specific' 
            ? this.schemas.careerAnalysisSpecificMode 
            : this.schemas.careerAnalysisForm;

        // Basic validation
        const { isValid, errors } = this.validateForm(formData, schema);

        // Custom validation
        const customErrors = [];
        
        // Similarity range validation
        const rangeValidation = this.customValidators.similarityRange(formData);
        if (rangeValidation !== true) {
            customErrors.push(rangeValidation);
        }

        // Specific mode validation
        const specificValidation = this.customValidators.specificModeTargets(formData);
        if (specificValidation !== true) {
            customErrors.push(specificValidation);
        }

        return {
            isValid: isValid && customErrors.length === 0,
            fieldErrors: errors,
            formErrors: customErrors
        };
    },

    /**
     * Display form-level validation messages
     */
    displayFormErrors(containerId, errors) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        if (errors.length === 0) return;

        errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'flex items-center p-3 text-sm text-red-800 bg-red-100 rounded-md mb-2';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${error}</span>
            `;
            container.appendChild(errorDiv);
        });
    },

    /**
     * Display success message
     */
    displaySuccessMessage(containerId, message) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        const successDiv = document.createElement('div');
        successDiv.className = 'flex items-center p-3 text-sm text-green-800 bg-green-100 rounded-md';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle mr-2"></i>
            <span>${message}</span>
        `;
        container.appendChild(successDiv);
    }
};

console.log('✅ Validation module loaded');
